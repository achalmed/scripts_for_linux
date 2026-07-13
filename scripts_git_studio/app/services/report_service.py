"""
services/report_service.py — Generación de reportes de estado.

Convierte los datos estructurados de status_service (tabla de estado,
repos que necesitan atención, actividad reciente) en archivos Markdown
o CSV, replicando las secciones del reporte de status.sh.
"""

import csv
from pathlib import Path

from app.services.status_service import STATUS_CLEAN, RepoStatus
from app.utils.format import stamp_for_filename, timestamp


def suggest_filename(fmt: str) -> str:
    return f"git-status-{stamp_for_filename()}.{fmt}"


def write_report(path: str, statuses: list[RepoStatus],
                 activity: list[tuple[str, int]], days: int = 7) -> str:
    """Escribe el reporte en el formato deducido de la extensión."""
    if path.endswith(".csv"):
        _write_csv(path, statuses)
    else:
        _write_markdown(path, statuses, activity, days)
    return path


def _write_csv(path: str, statuses: list[RepoStatus]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["repositorio", "rama", "estado", "sin_commit",
                         "sin_push", "pull_pendiente", "ultimo_commit"])
        for row in statuses:
            writer.writerow([row.name, row.branch, row.status,
                             row.uncommitted, row.ahead, row.behind,
                             row.last_commit])


def _write_markdown(path: str, statuses: list[RepoStatus],
                    activity: list[tuple[str, int]], days: int) -> None:
    clean = sum(1 for s in statuses if s.status == STATUS_CLEAN)
    dirty = len(statuses) - clean
    behind = sum(1 for s in statuses if s.behind > 0)

    lines = [
        "# Reporte de estado de repositorios Git",
        "",
        f"- **Fecha:** {timestamp()}",
        f"- **Repositorios analizados:** {len(statuses)}",
        "",
        "## Resumen global",
        "",
        f"- Sincronizados: **{clean}**",
        f"- Con cambios: **{dirty}**",
        f"- Detrás de origin: **{behind}**",
        "",
        "## Estado detallado",
        "",
        "| Repositorio | Rama | Estado | Cambios | Último commit |",
        "|---|---|---|---|---|",
    ]
    for row in statuses:
        lines.append(f"| {row.name} | {row.branch} | {row.status} "
                     f"| {row.changes_summary()} | {row.last_commit} |")

    attention = [s for s in statuses if s.status != STATUS_CLEAN]
    if attention:
        lines += ["", "## Repositorios que necesitan atención", ""]
        for row in attention:
            lines.append(f"### {row.name}")
            lines.append("")
            lines.append(f"- Rama: `{row.branch}`")
            lines.append(f"- Estado: **{row.status}**")
            if row.uncommitted > 0:
                lines.append(f"- Sin commit: {row.uncommitted} archivos")
            if row.ahead > 0:
                lines.append(f"- Sin push: {row.ahead} commits")
            if row.behind > 0:
                lines.append(f"- Pull pendiente: {row.behind} commits remotos")
            lines.append(f"- Último commit: {row.last_commit}")
            lines.append("")

    lines += ["", f"## Actividad reciente (últimos {days} días)", ""]
    if activity:
        total = sum(count for _, count in activity)
        for name, count in activity:
            lines.append(f"- {name}: {count} commits")
        lines.append("")
        lines.append(f"**Total: {total} commits en {days} días**")
    else:
        lines.append("Sin commits en el período.")

    lines += ["", "> Leyenda: `M:n` archivos modificados sin commit · "
                  "`↑n` commits sin push · `↓n` commits remotos "
                  "(necesita pull) · `✓` sincronizado", ""]

    Path(path).write_text("\n".join(lines), encoding="utf-8")
