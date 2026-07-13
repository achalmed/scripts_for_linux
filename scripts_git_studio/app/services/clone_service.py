"""
services/clone_service.py — Descarga (clonado) de repositorios.

Port fiel de backend/script_git_download_respos/lib/cloner.sh y del
despachador de main.sh: mismos modos (todos / lista / uno), mismo
tratamiento de forks y exclusiones, carpeta existente = omitido,
dry-run de extremo a extremo, snapshot sin .git (-s) y los tres
contadores del resumen final (descargados / omitidos / fallidos).
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from app.services import git_service
from app.services.github_service import RemoteRepo
from app.workers.function_worker import OperationCancelled

ST_CLONED = "descargado"
ST_SKIPPED = "omitido"
ST_FAILED = "fallido"


@dataclass
class CloneOptions:
    user: str
    dest_dir: str
    depth: str = "1"            # "1" | "N" | "full"/"0" = historial completo
    protocol: str = "ssh"       # ssh | https
    branch: str = ""
    strip_git: bool = False     # snapshot sin carpeta .git
    include_forks: bool = False
    exclude: list[str] = field(default_factory=list)
    dry_run: bool = False


@dataclass
class CloneItem:
    name: str
    status: str
    note: str = ""


@dataclass
class CloneReport:
    dry_run: bool
    items: list[CloneItem] = field(default_factory=list)

    def count(self, status: str) -> int:
        return sum(1 for item in self.items if item.status == status)


def _clone_one(options: CloneOptions, name: str, message_cb) -> CloneItem:
    """Port de clone_repo(): clona un repo en una subcarpeta homónima;
    omite si ya existe y respeta dry-run."""

    def say(level: str, text: str) -> None:
        if message_cb:
            message_cb(level, text)

    url = git_service.build_clone_url(options.user, name, options.protocol)
    dest = Path(options.dest_dir) / name

    if dest.is_dir():
        say("warn", f"La carpeta '{name}' ya existe, se omite. "
                    "(Bórrala o muévela para re-descargarla)")
        return CloneItem(name, ST_SKIPPED, "ya existe")

    if options.dry_run:
        say("info", f"[DRY-RUN] Se clonaría: {url} "
                    f"(profundidad: {options.depth})")
        return CloneItem(name, ST_CLONED, "simulación")

    flags = git_service.build_clone_flags(options.depth, options.branch)
    say("info", f"Clonando {name} (profundidad: {options.depth})…")
    result = git_service.clone(url, str(dest), flags)
    if not result.ok:
        say("error", f"Falló la descarga de {name}: {result.output}")
        return CloneItem(name, ST_FAILED, result.output.splitlines()[-1]
                         if result.output else "")

    # Port de _finish_clone(): strip opcional de .git
    if options.strip_git:
        shutil.rmtree(dest / ".git", ignore_errors=True)
        say("ok", f"{name} descargado (snapshot sin historial git).")
        return CloneItem(name, ST_CLONED, "snapshot sin .git")

    say("ok", f"{name} descargado.")
    return CloneItem(name, ST_CLONED)


def clone_repos(options: CloneOptions, repos: list[RemoteRepo],
                progress_cb=None, cancel_cb=None,
                message_cb=None) -> CloneReport:
    """Clona la lista dada aplicando el filtro de forks y exclusiones
    (port del bucle de _clone_all_repos; para los modos lista/único se
    pasa la selección ya hecha y los filtros no descartan nada)."""
    report = CloneReport(dry_run=options.dry_run)
    total = len(repos) or 1

    for index, repo in enumerate(repos, start=1):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        if progress_cb:
            progress_cb(int((index - 1) * 100 / total), repo.name)

        if repo.is_fork and not options.include_forks:
            if message_cb:
                message_cb("warn", f"Omitiendo '{repo.name}' (es un fork).")
            report.items.append(CloneItem(repo.name, ST_SKIPPED, "fork"))
            continue

        if repo.name in options.exclude:
            if message_cb:
                message_cb("warn",
                           f"Omitiendo '{repo.name}' (en lista de exclusión).")
            report.items.append(
                CloneItem(repo.name, ST_SKIPPED, "excluido"))
            continue

        report.items.append(_clone_one(options, repo.name, message_cb))

    if progress_cb:
        progress_cb(100, "completado")
    return report
