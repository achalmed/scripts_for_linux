"""
services/git_service.py — Operaciones Git de bajo nivel.

Port fiel de backend/script_git_sync_respos/lib/git_ops.sh: conserva las
correcciones documentadas allí (Bug 1: detección de cambios en repos sin
HEAD; Bug 2: fetch previo antes de contar ahead/behind; contadores en 0
cuando no hay upstream en vez de fallar) y añade la construcción de URLs
y flags de clonado de backend/script_git_download_respos/lib/cloner.sh.

Es la ÚNICA implementación de comandos git de la aplicación: sincroniza-
ción, estado, clonado y reportes la reutilizan. Ningún otro módulo debe
invocar git directamente.
"""

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class GitResult:
    ok: bool
    output: str = ""


def _run(path: str | None, *args: str, timeout: int = 300) -> GitResult:
    """Ejecuta git (-C path) capturando stdout+stderr combinados."""
    argv = ["git"]
    if path:
        argv += ["-C", path]
    argv += list(args)
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, errors="replace",
            timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return GitResult(False, str(exc))
    output = (proc.stdout + proc.stderr).strip()
    return GitResult(proc.returncode == 0, output)


def git_available() -> bool:
    return shutil.which("git") is not None


# ------------------------------------------------------------------ estado

def is_repo(path: str) -> bool:
    """Port de git_is_repo()."""
    import os
    return os.path.isdir(os.path.join(path, ".git"))


def current_branch(path: str) -> str:
    return _run(path, "branch", "--show-current").output


def has_upstream(path: str, branch: str) -> bool:
    """Port de git_has_upstream()."""
    return _run(path, "rev-parse", "--abbrev-ref",
                f"{branch}@{{upstream}}").ok


def fetch_remote(path: str) -> bool:
    """Port de git_fetch_remote(): fetch silencioso; si no hay red los
    contadores quedarán en 0 (fallo silencioso, igual que el Bash)."""
    return _run(path, "fetch", "--quiet", "origin", timeout=120).ok


def has_local_changes(path: str) -> bool:
    """Port de git_has_local_changes(), con una corrección adicional al
    original: diff-index HEAD no ve archivos NUEVOS sin trackear, por lo
    que sync.sh omitía repos cuyo único cambio era un archivo nuevo
    (mientras status.sh sí los contaba como «CAMBIOS SIN COMMIT»).
    status --porcelain detecta modificados, staged y nuevos por igual, y
    además funciona en repos sin ningún commit (Bug 1 del original)."""
    return bool(_run(path, "status", "--porcelain").output)


def count_uncommitted(path: str) -> int:
    """Port de git_count_uncommitted()."""
    output = _run(path, "status", "--short").output
    return len(output.splitlines()) if output else 0


def count_ahead(path: str, branch: str) -> int:
    """Port de git_count_ahead(): 0 si no hay upstream (no falla)."""
    if not has_upstream(path, branch):
        return 0
    result = _run(path, "rev-list", f"origin/{branch}..{branch}", "--count")
    return int(result.output) if result.ok and result.output.isdigit() else 0


def count_behind(path: str, branch: str) -> int:
    """Port de git_count_behind(): 0 si no hay upstream (no falla)."""
    if not has_upstream(path, branch):
        return 0
    result = _run(path, "rev-list", f"{branch}..origin/{branch}", "--count")
    return int(result.output) if result.ok and result.output.isdigit() else 0


def last_commit_summary(path: str) -> str:
    """Port de git_last_commit_summary()."""
    result = _run(path, "log", "-1", "--format=%h – %s (%cr)")
    return result.output if result.ok and result.output else "(sin commits)"


def recent_commit_count(path: str, days: int = 7) -> int:
    """Port de git_recent_commit_count()."""
    result = _run(path, "log", f"--since={days} days ago", "--oneline")
    return len(result.output.splitlines()) if result.output else 0


def status_short(path: str) -> str:
    return _run(path, "status", "--short").output


# ------------------------------------------------------------ mutaciones

def pull(path: str) -> GitResult:
    """Port de git_pull()."""
    return _run(path, "pull", timeout=600)


def add_all(path: str) -> GitResult:
    """Port de git_add_all()."""
    return _run(path, "add", "-A")


def commit(path: str, message: str) -> GitResult:
    """Port de git_commit()."""
    return _run(path, "commit", "-m", message)


def push(path: str) -> GitResult:
    """Port de git_push()."""
    return _run(path, "push", timeout=600)


# ---------------------------------------------------------------- clonado

def build_clone_url(user: str, repo_name: str, protocol: str = "ssh") -> str:
    """Port de build_clone_url() (lib/cloner.sh)."""
    if protocol == "ssh":
        return f"git@github.com:{user}/{repo_name}.git"
    return f"https://github.com/{user}/{repo_name}.git"


def build_clone_flags(depth: str = "1", branch: str = "") -> list[str]:
    """Port de build_clone_flags() (lib/cloner.sh): lista real de
    argumentos, no string spliteado, para que ramas con espacios o
    caracteres glob no se rompan."""
    flags: list[str] = []
    if depth not in ("full", "0"):
        flags += ["--depth", depth]
    if branch:
        flags += ["--branch", branch, "--single-branch"]
    return flags


def clone(url: str, dest_path: str, flags: list[str]) -> GitResult:
    return _run(None, "clone", *flags, url, dest_path, timeout=1800)
