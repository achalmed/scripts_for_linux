"""script_registro_tiempo/lib/sp_rest.py — entrega `para-sp.json` a Super Productivity por su API REST local.

La API (Ajustes → Misceláneo → «Local REST API», 127.0.0.1:3876, desde la 18) crea y edita tareas pero no escribe
tiempo por día ni crea proyectos; por eso aquí solo se deja el JSON en las notas de una tarea portadora, y el plugin
`plugin-sp/` lo aplica desde dentro. Con la aplicación cerrada no hay servidor: la entrega se salta y la próxima
pasada la repite (el historial ya quedó en el vault).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

URL = os.environ.get("SP_REST_URL", "http://127.0.0.1:3876")   # la variable solo la usan las pruebas
TIMEOUT_S = 15
PORTADORA = "Datos del registro de tiempo"


class NoDisponible(RuntimeError):
    pass


def _pedir(metodo: str, ruta: str, cuerpo: dict | None = None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(URL + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            respuesta = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode()).get("error", {}).get("message", "")
        except ValueError:
            detalle = ""
        raise NoDisponible(f"{metodo} {ruta}: HTTP {e.code} {detalle}".strip()) from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise NoDisponible(f"Super Productivity no responde en {URL} (¿cerrado o sin la API REST activada?)") from e
    if not respuesta.get("ok"):
        raise NoDisponible(f"{metodo} {ruta}: {respuesta.get('error', {}).get('message', 'error')}")
    return respuesta.get("data")


def notas(datos: dict) -> str:
    return ("Lo escribe scripts-linux/script_registro_tiempo y lo lee el plugin «Registro de tiempo». "
            "No se edita ni se marca como hecha.\n\n```json\n"
            + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + "\n```\n")


def nombres() -> tuple[dict[str, str], dict[str, str]]:
    """({proyecto en minúsculas: id}, {etiqueta en minúsculas: id}) de lo que existe en SP."""
    proyectos = {p["title"].lower(): p["id"] for p in _pedir("GET", "/projects") or [] if not p.get("isArchived")}
    etiquetas = {t["title"].lower(): t["id"] for t in _pedir("GET", "/tags") or []}
    return proyectos, etiquetas


def crear(cuerpo: dict, padre: str | None = None) -> str:
    """Crea una tarea (o subtarea de `padre`, que hereda proyecto y etiquetas) y devuelve su id."""
    if padre:
        cuerpo = {k: v for k, v in cuerpo.items() if k not in ("projectId", "tagIds")} | {"parentId": padre}
    return _pedir("POST", "/tasks", cuerpo)["id"]


def entregar(datos: dict, proyecto: str) -> str:
    """Crea o actualiza la tarea portadora; devuelve qué hizo."""
    salud = _pedir("GET", "/health")
    if not (salud or {}).get("rendererReady"):
        raise NoDisponible("Super Productivity está arrancando; se reintenta en la próxima pasada")
    q = urllib.parse.quote(PORTADORA)
    existentes = [t for t in _pedir("GET", f"/tasks?query={q}&includeDone=true") or [] if t.get("title") == PORTADORA]
    texto = notas(datos)
    if existentes:
        _pedir("PATCH", f"/tasks/{existentes[0]['id']}", {"notes": texto, "isDone": False})
        return "tarea portadora actualizada"
    proyectos = [p for p in _pedir("GET", f"/projects?query={urllib.parse.quote(proyecto)}") or []
                 if p.get("title") == proyecto]
    cuerpo = {"title": PORTADORA, "notes": texto}
    if proyectos:
        cuerpo["projectId"] = proyectos[0]["id"]
    _pedir("POST", "/tasks", cuerpo)
    return "tarea portadora creada" + ("" if proyectos else " (en la bandeja; el plugin la mueve a su proyecto)")
