"""script_registro_tiempo/lib/minka.py — las tareas del despacho (Minka) en Super Productivity, por su API REST.

Minka no escribe en SP (qillqa/docs/decisiones.md, 2026-10-06): ofrece «mis tareas» en JSON, de solo lectura y con la
misma dirección secreta de su calendario (`GET /api/tareas/mias.json`, cabecera `X-Minka-Token`). Esta suite, que es
del autor, las lee y las deja en SP por la API REST local (meta/docs/decisiones.md §5.1 y §5.2). Nada del despacho vive
en el código: la dirección llega por `$DESPACHO_DIR/operaciones/minka/.env` (`MINKA_SUSCRIPCION`), y en SP quedan solo
el título, el estado y el plazo (ni la descripción ni la dirección del servidor).

Reglas (`plan`, puro). Minka manda:
- abierta en Minka y sin tarea en SP → se crea en el proyecto `config.PROYECTO_MINKA`, con el plazo como día planificado
  (SP 18.10 tiene «fecha límite» propia, pero su API REST no la escribe);
- ya en SP → se igualan el título y la línea de estado; el plazo, solo si cambió en Minka (lo que el autor replanifique
  en SP se respeta); cerrada en Minka → hecha en SP;
- hecha en SP y abierta en Minka → se reabre solo si Minka cambió después; si no, se avisa (se cierra allá);
- en SP y ya no entre «mis tareas» (reasignada o borrada) → hecha en SP, con aviso, si la lista vino completa.
La tarea se reconoce por la línea `minka:tarea:<id>` de sus notas; lo que el autor escriba encima se conserva.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

MARCA = "minka:tarea:"
SEPARADOR = "— Minka —"
RUTA_TAREAS = "/api/tareas/mias.json"
RUTA_ICS = "/api/agenda.ics"
TIMEOUT_S = 15
_RE_MARCA = re.compile(r"^" + re.escape(MARCA) + r"(\d+)\s*$", re.M)
_RE_PLAZO = re.compile(r"^Plazo: (\S+(?: \d\d:\d\d)?)\s*$", re.M)


class NoDisponible(RuntimeError):
    pass


# --- la dirección (del .env del despacho) ---------------------------------------------------


def archivo_env(despacho_dir: str | Path) -> Path:
    return Path(os.environ.get("MINKA_ENV") or Path(despacho_dir) / "operaciones" / "minka" / ".env")


def leer_env(ruta: Path) -> dict[str, str]:
    """KEY=VALOR por línea (sin dependencias, como los puentes de OpenProject); vacío si no existe."""
    if not ruta.is_file():
        return {}
    valores = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip("'\"")
    return valores


def conexion(valores: dict[str, str]) -> tuple[str, str] | None:
    """(base, token) desde la dirección copiada de «Ver en otro calendario» (MINKA_SUSCRIPCION) o desde MINKA_URL y
    MINKA_TOKEN; None si falta."""
    url = valores.get("MINKA_SUSCRIPCION", "")
    if url:
        partes = urllib.parse.urlsplit(url)
        token = (urllib.parse.parse_qs(partes.query).get("token") or [""])[0]
        ruta = partes.path[: -len(RUTA_ICS)] if partes.path.endswith(RUTA_ICS) else None
        if ruta is None or not token or partes.scheme not in ("http", "https"):
            raise ValueError("MINKA_SUSCRIPCION no es una dirección de calendario de Minka (…/api/agenda.ics?token=…)")
        return f"{partes.scheme}://{partes.netloc}{ruta}", token
    base, token = valores.get("MINKA_URL", "").rstrip("/"), valores.get("MINKA_TOKEN", "")
    return (base, token) if base and token else None


def leer_tareas(base: str, token: str) -> dict:
    req = urllib.request.Request(base + RUTA_TAREAS, headers={"X-Minka-Token": token, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            datos = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise NoDisponible("Minka no reconoce la dirección (¿se renovó o se revocó en la Agenda?)") from e
        raise NoDisponible(f"Minka respondió HTTP {e.code}") from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise NoDisponible("Minka no responde (¿apagada o fuera de la red del despacho?)") from e
    if not isinstance(datos, dict) or datos.get("version") != 1 or not isinstance(datos.get("tareas"), list):
        raise NoDisponible("Minka devolvió algo que no es «mis tareas» (versión 1)")
    return datos


# --- notas, plazo y marca -------------------------------------------------------------------


def id_de(tarea_sp: dict) -> int | None:
    m = _RE_MARCA.search(tarea_sp.get("notes") or "")
    return int(m.group(1)) if m else None


def _propio(notas: str) -> str:
    """Lo que el autor escribió en las notas (lo de antes del bloque de Minka)."""
    i = notas.find(SEPARADOR)
    return notas[:i].rstrip() if i >= 0 else ""


def _plazo_texto(f: dict) -> str:
    if f.get("vence_en"):
        return datetime.fromisoformat(f["vence_en"]).strftime("%Y-%m-%d %H:%M")
    return f.get("vence_dia") or ""


def notas(f: dict, previas: str = "") -> str:
    lineas = [SEPARADOR, f"Estado en Minka: {f.get('estado_nombre') or f.get('estado')} · prioridad {f.get('prioridad')}"]
    if _plazo_texto(f):
        lineas.append(f"Plazo: {_plazo_texto(f)}")
    lineas.append(f"{MARCA}{f['id']}")
    propio = _propio(previas)
    return (propio + "\n\n" if propio else "") + "\n".join(lineas)


def _ms(iso: str | None) -> int | None:
    return int(datetime.fromisoformat(iso).timestamp() * 1000) if iso else None


def campos_plazo(f: dict) -> dict:
    """El plazo de Minka como día planificado de SP: con hora, `dueWithTime`; sin hora, `dueDay`."""
    if f.get("vence_en"):
        return {"dueWithTime": _ms(f["vence_en"]), "dueDay": None}
    if f.get("vence_dia"):
        return {"dueDay": f["vence_dia"], "dueWithTime": None}
    return {}


# --- el plan (puro) -------------------------------------------------------------------------


def plan(datos: dict, activas: list[dict], archivadas: list[dict], proyecto_id: str | None) -> dict:
    """{crear: [cuerpo], cambiar: [(id_sp, cambios, titulo)], avisos: [texto]} para dejar SP como «mis tareas».
    `activas`: las tareas de SP sin archivar (también las hechas); `archivadas`: las del archivo."""
    en_sp: dict[int, dict] = {}
    for t in activas:
        mid = id_de(t)
        if mid is not None and mid not in en_sp:
            en_sp[mid] = t
    archivadas_ids = {id_de(t) for t in archivadas} - {None}
    salida: dict = {"crear": [], "cambiar": [], "avisos": []}
    vistas: set[int] = set()
    for f in datos.get("tareas") or []:
        mid = int(f["id"])
        vistas.add(mid)
        t = en_sp.get(mid)
        if t is None:
            if mid in archivadas_ids or f.get("cerrada"):
                if not f.get("cerrada"):
                    salida["avisos"].append(f"«{f['titulo'][:60]}» está archivada en SP y sigue abierta en Minka")
                continue
            cuerpo = {"title": f["titulo"], "notes": notas(f), **{k: v for k, v in campos_plazo(f).items() if v is not None}}
            if proyecto_id:
                cuerpo["projectId"] = proyecto_id
            salida["crear"].append(cuerpo)
            continue
        cambios: dict = {}
        if t.get("title") != f["titulo"]:
            cambios["title"] = f["titulo"]
        anterior = _RE_PLAZO.search(t.get("notes") or "")
        if (anterior.group(1) if anterior else "") != _plazo_texto(f):
            for k, v in (campos_plazo(f) or {"dueDay": None, "dueWithTime": None}).items():   # sin plazo: se quita
                if t.get(k) != v:
                    cambios[k] = v
        texto = notas(f, t.get("notes") or "")
        if (t.get("notes") or "") != texto:
            cambios["notes"] = texto
        if f.get("cerrada") and not t.get("isDone"):
            cambios["isDone"] = True
        elif not f.get("cerrada") and t.get("isDone"):
            if (_ms(f.get("actualizado_en")) or 0) > (t.get("doneOn") or 0):
                cambios["isDone"] = False
            else:
                salida["avisos"].append(f"«{f['titulo'][:60]}» está hecha en SP pero abierta en Minka: ciérrela allá")
        if cambios:
            salida["cambiar"].append((t["id"], cambios, f["titulo"]))
    if datos.get("completo"):
        for mid, t in en_sp.items():
            if mid not in vistas and not t.get("isDone"):
                salida["cambiar"].append((t["id"], {"isDone": True}, t.get("title", "")))
                salida["avisos"].append(f"«{t.get('title', '')[:60]}» ya no está entre sus tareas de Minka: se marca hecha")
    return salida
