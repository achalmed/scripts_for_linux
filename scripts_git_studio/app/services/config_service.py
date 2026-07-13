"""
services/config_service.py — Registro central de repositorios.

Port fiel del parser YAML ligero de backend/script_git_sync_respos/
lib/config.sh: mismo archivo (repos-config.yml), mismo formato de dos y
cuatro espacios, mismos valores por defecto. La GUI y los scripts CLI
sync.sh / status.sh comparten este archivo, por lo que un repo agregado
desde la aplicación queda disponible de inmediato en la línea de comandos
y viceversa.

Añade lo que la GUI exige: escritura del archivo (alta/baja/edición de
repos) conservando el formato documentado que el parser Bash entiende.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.paths import REPOS_CONFIG_FILE

DEFAULT_COMMIT_MESSAGE = "update: sincronización automática de contenidos"

_RE_BASE_DIR = re.compile(r"^base_directory:\s*(.*?)\s*$")
_RE_DEFAULT_MSG = re.compile(r'^default_commit_message:\s*"?(.*?)"?\s*$')
_RE_NAME = re.compile(r"^  - name:\s*(.*?)\s*$")
_RE_BRANCH = re.compile(r"^    branch:\s*(.*?)\s*$")
_RE_ENABLED = re.compile(r"^    enabled:\s*(.*?)\s*$")


@dataclass
class RepoEntry:
    name: str
    branch: str = "main"
    enabled: bool = True


@dataclass
class ReposConfig:
    base_dir: str = ""
    default_commit_message: str = DEFAULT_COMMIT_MESSAGE
    repos: list[RepoEntry] = field(default_factory=list)

    def repo_path(self, name: str) -> str:
        return os.path.join(self.base_dir, name)

    def enabled_repos(self) -> list[RepoEntry]:
        return [r for r in self.repos if r.enabled]

    def find(self, name: str) -> RepoEntry | None:
        for repo in self.repos:
            if repo.name == name:
                return repo
        return None


class ConfigService:
    """Lee y escribe repos-config.yml (el mismo que usan los scripts CLI)."""

    def __init__(self, config_file: str | Path | None = None):
        self.config_file = Path(config_file or REPOS_CONFIG_FILE)

    # ------------------------------------------------------------- lectura
    def load(self) -> ReposConfig:
        """Port de config_load(): parsea base_directory,
        default_commit_message y la lista de repositorios."""
        config = ReposConfig()
        if not self.config_file.is_file():
            return config

        current: RepoEntry | None = None
        for line in self.config_file.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("#"):
                continue
            if match := _RE_NAME.match(line):
                current = RepoEntry(name=match.group(1))
                config.repos.append(current)
            elif (match := _RE_BRANCH.match(line)) and current:
                current.branch = match.group(1)
            elif (match := _RE_ENABLED.match(line)) and current:
                current.enabled = match.group(1) == "true"
            elif match := _RE_BASE_DIR.match(line):
                # Expandir ~ sin depender de eval (igual que el Bash)
                config.base_dir = os.path.expanduser(match.group(1))
            elif match := _RE_DEFAULT_MSG.match(line):
                config.default_commit_message = (
                    match.group(1) or DEFAULT_COMMIT_MESSAGE)
        return config

    # ------------------------------------------------------------ escritura
    def save(self, config: ReposConfig) -> None:
        """Regenera repos-config.yml en el FORMATO REQUERIDO que documenta
        el propio archivo (2 espacios + '- name:', 4 espacios para branch
        y enabled), para que el parser ligero de lib/config.sh lo siga
        entendiendo sin cambios."""
        lines = [
            "# =============================================================================",
            "# repos-config.yml — Configuración de git-sync",
            "# =============================================================================",
            "# Compartido entre Git Studio (GUI) y los scripts CLI sync.sh / status.sh.",
            "# Editable a mano o desde la página «Repositorios» de la aplicación.",
            "#",
            "# FORMATO REQUERIDO (el parser es ligero, no es YAML genérico):",
            "#   - 'name' con exactamente 2 espacios + \"- \" antes",
            "#   - 'branch' y 'enabled' con exactamente 4 espacios antes",
            "#   - No uses comillas, anchors, listas inline ni anidación adicional",
            "# =============================================================================",
            "",
            "# Directorio base donde están todos los repositorios (una carpeta por repo)",
            f"base_directory: {self._contract_home(config.base_dir)}",
            "",
            "# Lista de repositorios a gestionar",
            "repositories:",
            "",
        ]
        for repo in config.repos:
            lines.append(f"  - name: {repo.name}")
            lines.append(f"    branch: {repo.branch}")
            lines.append(f"    enabled: {'true' if repo.enabled else 'false'}")
            lines.append("")

        lines.append("# Mensaje de commit por defecto cuando no se pasa -m")
        lines.append(
            f'default_commit_message: "{config.default_commit_message}"')
        lines.append("")
        self.config_file.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _contract_home(path: str) -> str:
        home = os.path.expanduser("~")
        if path.startswith(home):
            return "~" + path[len(home):]
        return path
