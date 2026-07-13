"""
services/sync_service.py — Motor de sincronización.

Port fiel de backend/script_git_sync_respos/lib/sync_engine.sh
(sync_process_repo): mismo flujo pull → add → commit → push, mismas
validaciones previas (directorio, repo git, rama activa) y mismos tres
resultados (sincronizado / sin cambios / error). Un error en un repo
nunca detiene el procesamiento de los siguientes (Bug 4 del original).

Las opciones (check_only, no_pull, mensaje) replican las flags -c/-n/-m
de sync.sh.
"""

from dataclasses import dataclass, field

from app.services import git_service
from app.services.config_service import ReposConfig
from app.workers.function_worker import OperationCancelled

# Resultados por repo (mismos códigos que sync_process_repo)
RESULT_SYNCED = "sincronizado"
RESULT_NO_CHANGES = "sin cambios"
RESULT_ERROR = "error"


@dataclass
class SyncItem:
    name: str
    result: str
    detail: str = ""


@dataclass
class SyncReport:
    check_only: bool
    commit_message: str
    items: list[SyncItem] = field(default_factory=list)

    def count(self, result: str) -> int:
        return sum(1 for item in self.items if item.result == result)


def process_repo(config: ReposConfig, name: str, branch: str,
                 commit_message: str, check_only: bool = False,
                 no_pull: bool = False, message_cb=None) -> SyncItem:
    """Port de sync_process_repo(): sincroniza UN repositorio."""

    def say(level: str, text: str) -> None:
        if message_cb:
            message_cb(level, text)

    path = config.repo_path(name)

    # Validaciones previas
    import os
    if not os.path.isdir(path):
        say("error", f"Directorio no encontrado: {path}")
        return SyncItem(name, RESULT_ERROR, "directorio no encontrado")
    if not git_service.is_repo(path):
        say("error", f"No es un repositorio Git: {path}")
        return SyncItem(name, RESULT_ERROR, "no es un repositorio Git")

    # Verificar rama activa (sin checkout automático, igual que el Bash)
    current = git_service.current_branch(path)
    if current and current != branch:
        say("warn", f"{name}: rama activa '{current}', esperada '{branch}'. "
                    "Continúo en la rama actual (no se hace checkout).")
        branch = current

    # ─── git pull ────────────────────────────────────────────────────────
    if not no_pull and not check_only:
        say("info", f"{name}: actualizando desde remoto (git pull)…")
        result = git_service.pull(path)
        if not result.ok:
            say("error", f"git pull falló en '{name}': {result.output}")
            say("info", f"Resuélvelo manualmente: cd {path} && git pull")
            return SyncItem(name, RESULT_ERROR, "git pull falló")
        say("ok", f"{name}: pull completado")

    # ─── Detectar cambios locales ────────────────────────────────────────
    if not git_service.has_local_changes(path):
        # En modo verificación, detectar también commits remotos pendientes
        if check_only:
            git_service.fetch_remote(path)
            behind = git_service.count_behind(path, branch)
            if behind > 0:
                say("warn", f"{name}: sin cambios locales, pero hay {behind} "
                            "commits remotos pendientes de pull")
                return SyncItem(name, RESULT_NO_CHANGES,
                                f"{behind} commits remotos pendientes")
        say("warn", f"Sin cambios locales en '{name}'")
        return SyncItem(name, RESULT_NO_CHANGES)

    say("info", f"Cambios detectados en '{name}'")

    # ─── Modo verificación: mostrar y salir ──────────────────────────────
    if check_only:
        pending = git_service.status_short(path)
        say("info", f"{name}: cambios pendientes:\n{pending}")
        return SyncItem(name, RESULT_NO_CHANGES, "cambios pendientes (check)")

    # ─── add → commit → push ─────────────────────────────────────────────
    say("info", f"{name}: agregando cambios (git add -A)…")
    if not git_service.add_all(path).ok:
        say("error", f"Falló 'git add' en '{name}'")
        return SyncItem(name, RESULT_ERROR, "git add falló")

    say("info", f"{name}: creando commit: '{commit_message}'")
    result = git_service.commit(path, commit_message)
    if not result.ok:
        say("error", f"Falló 'git commit' en '{name}': {result.output}")
        return SyncItem(name, RESULT_ERROR, "git commit falló")

    say("info", f"{name}: enviando cambios (git push)…")
    result = git_service.push(path)
    if not result.ok:
        say("error", f"Falló 'git push' en '{name}': {result.output}")
        say("info", "Revisa conectividad y permisos del remoto.")
        return SyncItem(name, RESULT_ERROR, "git push falló")

    say("ok", f"'{name}' sincronizado correctamente ✓")
    return SyncItem(name, RESULT_SYNCED)


def sync_repos(config: ReposConfig, names: list[str], commit_message: str,
               check_only: bool = False, no_pull: bool = False,
               progress_cb=None, cancel_cb=None,
               message_cb=None) -> SyncReport:
    """Procesa la lista de repos (equivalente al bucle principal de
    sync.sh): un error en un repo no detiene los demás."""
    report = SyncReport(check_only=check_only, commit_message=commit_message)
    total = len(names) or 1

    for index, name in enumerate(names, start=1):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        if progress_cb:
            progress_cb(int((index - 1) * 100 / total), name)

        entry = config.find(name)
        branch = entry.branch if entry else "main"
        item = process_repo(config, name, branch, commit_message,
                            check_only=check_only, no_pull=no_pull,
                            message_cb=message_cb)
        report.items.append(item)

    if progress_cb:
        progress_cb(100, "completado")
    return report
