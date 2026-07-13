"""
services/hardlink_service.py — Módulo unificado de hardlinks.

Une las dos herramientas originales en un solo servicio:

* DETECCIÓN — migrada del script Bash (script_hardlinks-detector):
  recorre el árbol, agrupa por (dispositivo, inodo) los archivos con
  st_nlink >= min_links. En Python nativo obtenemos progreso,
  cancelación y datos estructurados sin parsear la salida del script.

* CREACIÓN — REUTILIZA el código Python de script_hardlinks-creator
  (backend/): compute_sha256, build_exclusion_set, scan_files y el
  enlace atómico _atomic_link (rename → link → restaurar) se importan
  directamente; aquí solo se re-orquesta el flujo en dos fases
  (planificar → aplicar) para encajar con la vista previa de la GUI.
"""

import os
import sys
from dataclasses import dataclass, field

from app.utils.format import format_size, timestamp
from app.utils.paths import BACKEND_HL_CREATOR
from app.workers.function_worker import OperationCancelled

# ---------------------------------------------------------------------------
# Reutilización del backend Python (hardlinks-creator)
# Se añade su carpeta a sys.path solo durante el import; los módulos quedan
# cacheados en sys.modules y no vuelven a necesitar la ruta.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(BACKEND_HL_CREATOR))
try:
    from lib.linker import _atomic_link  # noqa: E402
    from lib.scanner import (  # noqa: E402
        build_exclusion_set,
        compute_sha256,
        scan_files,
    )
    from lib.validator import (  # noqa: E402
        same_filesystem,
        validate_write_permission,
    )
finally:
    sys.path.remove(str(BACKEND_HL_CREATOR))

_PROGRESS_EVERY = 200


# ============================================================== DETECCIÓN ===

@dataclass
class HardlinkGroup:
    inode: int
    device: int
    size: int
    nlinks: int
    paths: list[str] = field(default_factory=list)

    @property
    def saved_bytes(self) -> int:
        return self.size * (self.nlinks - 1)


@dataclass
class DetectionResult:
    directory: str
    groups: list[HardlinkGroup] = field(default_factory=list)
    scanned_files: int = 0

    @property
    def total_space_used(self) -> int:
        return sum(g.size for g in self.groups)

    @property
    def total_space_saved(self) -> int:
        return sum(g.saved_bytes for g in self.groups)


def detect_hardlinks(directory: str, min_links: int = 2,
                     progress_cb=None, cancel_cb=None,
                     message_cb=None) -> DetectionResult:
    """Equivalente nativo de scan_hardlinks() (lib/scanner.sh del detector)."""
    result = DetectionResult(directory=directory)
    groups: dict[tuple[int, int], HardlinkGroup] = {}

    for root, dirs, files in os.walk(directory, topdown=True, onerror=None):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()

        for filename in files:
            filepath = os.path.join(root, filename)
            result.scanned_files += 1
            if progress_cb and result.scanned_files % _PROGRESS_EVERY == 0:
                progress_cb(-1, f"{result.scanned_files} archivos — {root}")
            try:
                st = os.lstat(filepath)
            except OSError:
                continue
            if not os.path.isfile(filepath) or st.st_nlink < min_links:
                continue

            key = (st.st_dev, st.st_ino)
            group = groups.get(key)
            if group is None:
                group = HardlinkGroup(inode=st.st_ino, device=st.st_dev,
                                      size=st.st_size, nlinks=st.st_nlink)
                groups[key] = group
            group.paths.append(filepath)

    result.groups = sorted(groups.values(),
                           key=lambda g: (-g.nlinks, g.paths[0]))
    for group in result.groups:
        group.paths.sort()
    if progress_cb:
        progress_cb(100, f"{len(result.groups)} conjunto(s) encontrados")
    return result


# ============================================================== CREACIÓN ====

@dataclass
class LinkCandidate:
    path: str
    valid: bool
    reason: str = ""


@dataclass
class LinkPlanGroup:
    file_hash: str
    source: str
    size: int
    already_linked: list[str] = field(default_factory=list)
    candidates: list[LinkCandidate] = field(default_factory=list)


@dataclass
class LinkPlan:
    filename: str
    directory: str
    groups: list[LinkPlanGroup] = field(default_factory=list)

    @property
    def total_valid(self) -> int:
        return sum(1 for g in self.groups for c in g.candidates if c.valid)


def plan_links(directory: str, filename: str,
               exclusions: list[str] | None = None,
               progress_cb=None, cancel_cb=None,
               message_cb=None) -> LinkPlan:
    """Fase 1 (solo lectura): busca duplicados por contenido y arma el plan.

    Reutiliza scan_files() y build_exclusion_set() del backend, y las
    validaciones de filesystem/permisos de su validator.
    """
    if progress_cb:
        progress_cb(-1, f"Buscando '{filename}' y calculando SHA-256…")

    exclusion_set = build_exclusion_set(directory, exclusions or [])
    hash_groups = scan_files(directory, filename, exclusion_set)
    plan = LinkPlan(filename=filename, directory=directory)

    for file_hash, paths in hash_groups.items():
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        if len(paths) < 2:
            continue

        # Agrupar por inodo: el primer inodo aporta la fuente
        by_inode: dict[int, list[str]] = {}
        for path in sorted(paths):
            try:
                inode = os.stat(path).st_ino
            except OSError:
                continue
            by_inode.setdefault(inode, []).append(path)
        if not by_inode:
            continue

        source_inode = next(iter(by_inode))
        source = by_inode[source_inode][0]
        group = LinkPlanGroup(
            file_hash=file_hash,
            source=source,
            size=os.stat(source).st_size,
            already_linked=by_inode[source_inode][1:],
        )
        for inode, inode_paths in by_inode.items():
            if inode == source_inode:
                continue
            for path in inode_paths:
                if not same_filesystem(source, path):
                    group.candidates.append(LinkCandidate(
                        path, False, "sistema de archivos diferente"))
                elif not validate_write_permission(path):
                    group.candidates.append(LinkCandidate(
                        path, False, "sin permisos de escritura"))
                else:
                    group.candidates.append(LinkCandidate(path, True))
        plan.groups.append(group)

    if progress_cb:
        progress_cb(100, f"{len(plan.groups)} grupo(s) con contenido idéntico")
    return plan


def apply_link_plan(plan: LinkPlan, dry_run: bool = False,
                    progress_cb=None, cancel_cb=None,
                    message_cb=None) -> dict:
    """Fase 2: crea los enlaces del plan con _atomic_link (backend).

    Devuelve un dict de estadísticas compatible con el reporter original.
    """
    stats = dict(groups_found=len(plan.groups), groups_created=0,
                 links_created=0, files_skipped=0, errors=0)
    total = plan.total_valid or 1
    done = 0

    for group in plan.groups:
        stats["files_skipped"] += len(group.already_linked)
        created_in_group = 0
        for cand in group.candidates:
            if cancel_cb and cancel_cb():
                raise OperationCancelled()
            if not cand.valid:
                stats["errors"] += 1
                continue
            done += 1
            if progress_cb:
                progress_cb(int(done * 100 / total), cand.path)
            if dry_run:
                if message_cb:
                    message_cb("info", f"[SIMULACIÓN] Se enlazaría: {cand.path}")
                created_in_group += 1
                stats["links_created"] += 1
                continue
            if _atomic_link(group.source, cand.path):
                if message_cb:
                    message_cb("ok", f"Hard link creado: {cand.path}")
                created_in_group += 1
                stats["links_created"] += 1
            else:
                stats["errors"] += 1
                if message_cb:
                    message_cb("error", f"Fallo al enlazar: {cand.path}")
        if created_in_group:
            stats["groups_created"] += 1
    return stats


# ========================================================== REPORTE MD ======

def build_markdown_report(result: DetectionResult) -> str:
    """Reporte de auditoría en Markdown, portado de lib/report.sh del
    detector (resumen ejecutivo, inventario y top compartidos)."""
    lines = [
        "# Reporte de Auditoría — Hard Links",
        "",
        f"- **Fecha:** {timestamp()}",
        f"- **Directorio analizado:** `{result.directory}`",
        "- **Herramienta:** Filesystem Studio — módulo Hardlinks",
        "",
        "## Resumen Ejecutivo",
        "",
        "| Indicador | Valor |",
        "| --- | ---: |",
        f"| Conjuntos de hard links | {len(result.groups)} |",
        f"| Espacio usado | {format_size(result.total_space_used)} |",
        f"| Espacio ahorrado | {format_size(result.total_space_saved)} |",
        "",
        "## Inventario Completo",
        "",
    ]
    if not result.groups:
        lines.append("Sin conjuntos que inventariar.")
    else:
        lines += ["| # | Archivo | Inodo | Links | Tamaño | Ahorro |",
                  "| ---: | --- | --- | ---: | ---: | ---: |"]
        for num, group in enumerate(result.groups, start=1):
            main_file = os.path.relpath(group.paths[0], result.directory)
            lines.append(
                f"| {num} | `{main_file.replace('|', '\\|')}` | {group.inode} "
                f"| {group.nlinks} | {format_size(group.size)} "
                f"| {format_size(group.saved_bytes)} |")

        lines += ["", "## Detalle de rutas por conjunto", ""]
        for num, group in enumerate(result.groups, start=1):
            lines.append(f"### Conjunto {num} — inodo {group.inode} "
                         f"({group.nlinks} enlaces)")
            lines.append("")
            for path in group.paths:
                rel = os.path.relpath(path, result.directory)
                lines.append(f"- `{rel}`")
            outside = group.nlinks - len(group.paths)
            if outside > 0:
                lines.append(f"- ⚠️ {outside} enlace(s) fuera del directorio "
                             "analizado")
            lines.append("")
    return "\n".join(lines) + "\n"
