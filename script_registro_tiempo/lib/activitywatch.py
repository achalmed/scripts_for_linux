"""script_registro_tiempo/lib/activitywatch.py — tiempo por programa y por sitio desde ActivityWatch.

En KDE con Wayland el observador de ventanas es `awatcher` (crea los mismos cubos que aw-watcher-window y
aw-watcher-afk); el tiempo por sitio exige además la extensión aw-watcher-web en el navegador. Sin servidor, o sin
un cubo, la función devuelve lo que haya y dice qué faltó: nunca falla la pasada entera.
Se cuenta solo el tiempo «no ausente» (afk) y, en la web, solo mientras el navegador tiene el foco.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

import config


def _pedir(ruta: str, cuerpo: dict | None = None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(f"{config.AW_URL}{ruta}", data=datos,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=config.AW_TIMEOUT_S) as r:
        return json.loads(r.read().decode())


def cubos() -> dict[str, str] | None:
    """{tipo: id_de_cubo} de ventanas, ausencia y web; None si el servidor no responde."""
    try:
        lista = _pedir("/buckets/")
    except (urllib.error.URLError, OSError, ValueError):
        return None
    elegidos: dict[str, str] = {}
    for cid, info in sorted(lista.items()):
        tipo = info.get("type", "")
        if tipo == "currentwindow":
            elegidos.setdefault("ventana", cid)
        elif tipo == "afkstatus":
            elegidos.setdefault("afk", cid)
        elif tipo == "web.tab.current":
            elegidos.setdefault("web", cid)
    return elegidos


def _periodo(dia: str) -> str:
    ini = datetime.combine(date.fromisoformat(dia), datetime.min.time()).astimezone()
    return f"{ini.isoformat()}/{(ini + timedelta(days=1)).isoformat()}"


def _consulta(c: dict[str, str], regex_navegadores: str) -> list[str]:
    q = [f'ventanas = flood(query_bucket("{c["ventana"]}"));']
    if "afk" in c:
        q += [f'afk = flood(query_bucket("{c["afk"]}"));',
              'ventanas = filter_period_intersect(ventanas, filter_keyvals(afk, "status", ["not-afk"]));']
    q.append('apps = merge_events_by_keys(ventanas, ["app", "title"]);')
    if "web" in c:
        q += [f'web = flood(query_bucket("{c["web"]}"));',
              f'nav = filter_keyvals_regex(ventanas, "app", "{regex_navegadores}");',
              'web = merge_events_by_keys(filter_period_intersect(web, nav), ["url"]);']
    else:
        q.append("web = [];")
    q.append('RETURN = {"apps": apps, "web": web};')
    return q


def leer(dias: list[str], regex_navegadores: str) -> tuple[dict[str, dict], str]:
    """({dia: {"ventanas": [(app, titulo, min)], "dominios": {dominio: min}}}, nota de disponibilidad)."""
    c = cubos()
    if c is None:
        return {}, "ActivityWatch no responde en " + config.AW_URL
    if "ventana" not in c:
        return {}, "ActivityWatch no tiene cubo de ventanas (¿falta awatcher?)"
    nota = "" if "web" in c else "sin cubo web: el tiempo por sitio sale del título de la ventana"
    try:
        respuesta = _pedir("/query/", {"timeperiods": [_periodo(d) for d in dias],
                                       "query": _consulta(c, regex_navegadores)})
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {}, f"la consulta a ActivityWatch falló: {e}"
    resultado: dict[str, dict] = {}
    for dia, bloque in zip(dias, respuesta):
        ventanas = [(ev["data"].get("app", "?"), ev["data"].get("title", ""), ev["duration"] / 60)
                    for ev in bloque.get("apps", [])]
        dominios: dict[str, float] = {}
        for ev in bloque.get("web", []):
            host = (urlsplit(ev["data"].get("url", "")).hostname or "").removeprefix("www.")
            if host:
                dominios[host] = dominios.get(host, 0) + ev["duration"] / 60
        resultado[dia] = {"ventanas": ventanas, "dominios": dominios}
    return resultado, nota
