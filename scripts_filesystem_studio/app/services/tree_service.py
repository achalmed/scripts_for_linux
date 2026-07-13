"""
services/tree_service.py — Árboles de directorios.

Reutiliza el enfoque de script_proyect_tree: el trabajo real lo hace el
binario `tree`; aquí solo se construye la línea de comandos (port de
lib/tree_utils.sh: patrón -I, flags de metadatos, cabecera y formatos
txt/md/json) y se ofrece el modo "proyectos" que ejecuta el main.sh
del backend intacto (grupos pub/scripts/campustex/website).
"""

import subprocess
from pathlib import Path

from app.utils.format import timestamp
from app.utils.paths import BACKEND_TREE
from app.workers.function_worker import OperationCancelled

FORMATS = ("txt", "md", "json")
BACKEND_TARGETS = ("all", "pub", "scripts", "campustex", "website", "extra")
VERSION = "1.0.0"


def build_exclude_pattern(exclude_dirs: list[str],
                          exclude_files: list[str]) -> str:
    """Port de build_exclude_pattern(): patrón único separado por '|'."""
    return "|".join([*exclude_dirs, *exclude_files])


def _tree_argv(directory: str, depth: int, pattern: str,
               fmt: str, with_meta: bool) -> list[str]:
    argv = ["tree", "-L", str(depth), "--charset", "UTF-8", "-n"]
    if pattern:
        argv += ["-I", pattern]
    if fmt == "json":
        argv.append("-J")
    elif with_meta:
        argv += ["-h", "-D"]  # META_FLAGS del config original
    argv.append(directory)
    return argv


def _header(directory: str, depth: int, fmt: str, pattern: str) -> str:
    """Port de build_tree_header() (formato txt)."""
    name = Path(directory).name
    excludes = pattern.replace("|", " ")
    return (
        "# ============================================================\n"
        f"# Proyecto : {name}\n"
        f"# Ruta     : {directory}\n"
        f"# Generado : {timestamp()}\n"
        f"# Script   : Filesystem Studio v{VERSION}\n"
        f"# Profund. : {depth} niveles\n"
        f"# Formato  : {fmt}\n"
        f"# Excluye  : {excludes}\n"
        "# ============================================================\n\n"
    )


def generate_tree(directory: str, depth: int,
                  exclude_dirs: list[str], exclude_files: list[str],
                  fmt: str = "txt", with_meta: bool = True,
                  progress_cb=None, cancel_cb=None,
                  message_cb=None) -> str:
    """Genera el árbol y devuelve el documento completo como texto."""
    if progress_cb:
        progress_cb(-1, f"Ejecutando tree sobre {directory}…")

    pattern = build_exclude_pattern(exclude_dirs, exclude_files)
    argv = _tree_argv(directory, depth, pattern, fmt, with_meta)
    if message_cb:
        message_cb("info", "$ " + " ".join(argv))

    proc = subprocess.run(argv, capture_output=True, text=True,
                          errors="replace", timeout=600)
    if cancel_cb and cancel_cb():
        raise OperationCancelled()
    if proc.returncode not in (0, 1):  # tree devuelve >1 en errores reales
        raise RuntimeError(proc.stderr.strip()
                           or f"tree terminó con código {proc.returncode}")
    body = proc.stdout

    if fmt == "json":
        return body
    if fmt == "md":
        # Port de run_tree_markdown(): documento listo para un README/wiki
        name = Path(directory).name
        return (f"# Estructura: {name}\n\n"
                f"> Generado el {timestamp()} con Filesystem Studio v{VERSION}\n"
                f"> Profundidad: {depth} niveles\n\n"
                f"```\n{body}```\n")
    return _header(directory, depth, fmt, pattern) + body


def output_filename(fmt: str) -> str:
    """Nombre canónico del archivo de salida (compatible con el backend)."""
    return "estructura.txt" if fmt == "txt" else f"estructura.{fmt}"


def backend_argv(target: str, fmt: str, depth: int,
                 dry_run: bool) -> tuple[list[str], str]:
    """Comando para ejecutar el script backend intacto (modo proyectos).

    Devuelve (argv, cwd). La salida se muestra en la Consola integrada.
    """
    main_sh = BACKEND_TREE / "main.sh"
    argv = ["bash", str(main_sh), "--target", target, "--format", fmt,
            "--depth", str(depth), "--no-color"]
    if dry_run:
        argv.append("--dry-run")
    return argv, str(BACKEND_TREE)
