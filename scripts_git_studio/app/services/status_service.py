"""
services/status_service.py — Recolección del estado de los repositorios.

Port fiel de backend/script_git_sync_respos/lib/status_reporter.sh
(status_collect_repo): mismos estados, misma prioridad de clasificación
y mismo fetch previo al conteo ahead/behind (corrección del Bug 2).

Devuelve datos estructurados (RepoStatus) en lugar de líneas separadas
por «|», para alimentar directamente el modelo de tabla de la GUI.
"""

from dataclasses import dataclass

from app.services import git_service
from app.services.config_service import ReposConfig
from app.workers.function_worker import OperationCancelled

# Códigos de estado (orden de prioridad, mayor a menor) — mismos textos
# que status_reporter.sh para que el usuario CLI no note diferencia.
STATUS_UNCOMMITTED = "CAMBIOS SIN COMMIT"
STATUS_UNPUSHED = "COMMITS SIN PUSH"
STATUS_BEHIND = "COMMITS REMOTOS (PULL NECESARIO)"
STATUS_DIVERGED = "DIVERGIDO (PULL + PUSH)"
STATUS_CLEAN = "SINCRONIZADO"
STATUS_MISSING = "NO ENCONTRADO"
STATUS_NOT_REPO = "NO ES REPO GIT"


@dataclass
class RepoStatus:
    name: str
    path: str
    branch: str = "?"
    status: str = STATUS_MISSING
    uncommitted: int = 0
    ahead: int = 0
    behind: int = 0
    last_commit: str = ""
    enabled: bool = True

    @property
    def needs_attention(self) -> bool:
        return self.status not in (STATUS_CLEAN,)

    def changes_summary(self) -> str:
        """Misma leyenda que la tabla CLI: M:n ↑n ↓n / ✓."""
        parts = []
        if self.uncommitted > 0:
            parts.append(f"M:{self.uncommitted}")
        if self.ahead > 0:
            parts.append(f"↑{self.ahead}")
        if self.behind > 0:
            parts.append(f"↓{self.behind}")
        return " ".join(parts) if parts else "✓"


def collect_repo(path: str, name: str, fetch: bool = True,
                 enabled: bool = True) -> RepoStatus:
    """Port de status_collect_repo(): recolecta el estado de UN repo."""
    import os

    if not os.path.isdir(path):
        return RepoStatus(name, path, status=STATUS_MISSING, enabled=enabled)
    if not git_service.is_repo(path):
        return RepoStatus(name, path, status=STATUS_NOT_REPO, enabled=enabled)

    branch = git_service.current_branch(path) or "?"

    # Corrección Bug 2: fetch antes de calcular behind/ahead.
    # El fallo (sin red) es silencioso; los contadores quedarán en 0.
    if fetch:
        git_service.fetch_remote(path)

    uncommitted = git_service.count_uncommitted(path)
    ahead = git_service.count_ahead(path, branch)
    behind = git_service.count_behind(path, branch)
    last_commit = git_service.last_commit_summary(path)

    # Determinar estado (orden de prioridad, igual que el Bash)
    if uncommitted > 0:
        status = STATUS_UNCOMMITTED
    elif ahead > 0 and behind > 0:
        status = STATUS_DIVERGED
    elif ahead > 0:
        status = STATUS_UNPUSHED
    elif behind > 0:
        status = STATUS_BEHIND
    else:
        status = STATUS_CLEAN

    return RepoStatus(name, path, branch, status, uncommitted, ahead,
                      behind, last_commit, enabled)


def collect_all(config: ReposConfig, fetch: bool = True,
                only_enabled: bool = False,
                progress_cb=None, cancel_cb=None,
                message_cb=None) -> list[RepoStatus]:
    """Recolecta el estado de todos los repos del registro (para el
    FunctionWorker: reporta progreso por repo y admite cancelación)."""
    repos = config.enabled_repos() if only_enabled else config.repos
    total = len(repos) or 1
    results: list[RepoStatus] = []

    for index, repo in enumerate(repos, start=1):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        if progress_cb:
            progress_cb(int(index * 100 / total), repo.name)

        row = collect_repo(config.repo_path(repo.name), repo.name,
                           fetch=fetch, enabled=repo.enabled)
        results.append(row)

        if message_cb and row.status in (STATUS_MISSING, STATUS_NOT_REPO):
            message_cb("warn", f"{repo.name}: {row.status} ({row.path})")

    return results


def recent_activity(config: ReposConfig, days: int = 7,
                    progress_cb=None, cancel_cb=None,
                    message_cb=None) -> list[tuple[str, int]]:
    """Port de status_print_activity(): commits por repo en N días."""
    rows: list[tuple[str, int]] = []
    repos = config.enabled_repos()
    total = len(repos) or 1
    for index, repo in enumerate(repos, start=1):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        if progress_cb:
            progress_cb(int(index * 100 / total), repo.name)
        path = config.repo_path(repo.name)
        if not git_service.is_repo(path):
            continue
        count = git_service.recent_commit_count(path, days)
        if count > 0:
            rows.append((repo.name, count))
    return rows
