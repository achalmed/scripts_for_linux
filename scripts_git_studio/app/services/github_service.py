"""
services/github_service.py — Consulta de repos vía API de GitHub.

Port fiel de backend/script_git_download_respos/lib/github_api.sh
(fetch_all_repos): misma paginación (100 por página, type=owner), mismo
manejo explícito de errores de la API (rate limit, usuario inexistente)
y de red. Usa urllib de la biblioteca estándar en lugar de curl+jq, lo
que elimina esas dos dependencias para la GUI.
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_PER_PAGE = 100
_TIMEOUT = 30


@dataclass
class RemoteRepo:
    name: str
    is_fork: bool
    description: str = ""
    default_branch: str = "main"


class GitHubApiError(Exception):
    """Error de la API de GitHub traducido a un mensaje útil."""


def fetch_all_repos(user: str, token: str = "") -> list[RemoteRepo]:
    """Obtiene la lista paginada de repos del usuario/organización."""
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "git-studio"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repos: list[RemoteRepo] = []
    page = 1
    while True:
        url = (f"{GITHUB_API_URL}/users/{user}/repos"
               f"?per_page={GITHUB_API_PER_PAGE}&page={page}&type=owner")
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Extraer el mensaje real de la API (port de _report_api_error)
            try:
                body = json.loads(exc.read().decode("utf-8"))
                message = body.get("message", "respuesta no reconocida")
            except (ValueError, OSError):
                message = "respuesta no reconocida"
            raise GitHubApiError(
                f"Error de la API de GitHub: {message}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise GitHubApiError(
                "No se pudo contactar la API de GitHub (¿sin conexión?)."
            ) from exc

        if not isinstance(payload, list) or not payload:
            break

        for item in payload:
            repos.append(RemoteRepo(
                name=item.get("name", ""),
                is_fork=bool(item.get("fork", False)),
                description=item.get("description") or "",
                default_branch=item.get("default_branch") or "main",
            ))
        page += 1

    return repos
