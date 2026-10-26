"""script_registro_tiempo/lib/clasificar.py — de programas, títulos y dominios a categorías del autor.

Las reglas viven en `registro-tiempo.yml` (`categorias:`), en orden: gana la primera que coincide. Cada categoría
puede nombrar `dominios` (sufijo: «youtube.com» cubre «m.youtube.com»), `apps` (subcadena del nombre del programa,
sin mayúsculas) y `titulos` (subcadena del título de la ventana). El tiempo del navegador se reparte por dominio si
hay cubo web; si no, por título; lo que no coincide queda en «sin_clasificar», que también se informa.
"""
from __future__ import annotations

import re

SIN_CLASIFICAR = "sin_clasificar"


def _coincide(valor: str, patrones: list[str]) -> bool:
    v = valor.lower()
    return any(p.lower() in v for p in patrones or [])


def _dominio_coincide(host: str, dominios: list[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in dominios or [])


def categoria_de_dominio(host: str, categorias: dict) -> str:
    for nombre, regla in categorias.items():
        if _dominio_coincide(host, regla.get("dominios")):
            return nombre
    return SIN_CLASIFICAR


def categoria_de_ventana(app: str, titulo: str, categorias: dict) -> str:
    for nombre, regla in categorias.items():
        if _coincide(app, regla.get("apps")) or _coincide(titulo, regla.get("titulos")):
            return nombre
    return SIN_CLASIFICAR


def resumir(dia_aw: dict, categorias: dict, regex_navegadores: str) -> dict:
    """{"categorias": {cat: min}, "apps": {app: min}, "dominios": {host: min}} de un día de ActivityWatch."""
    nav = re.compile(regex_navegadores)
    hay_web = bool(dia_aw.get("dominios"))
    cats: dict[str, float] = {}
    apps: dict[str, float] = {}
    for app, titulo, minutos in dia_aw.get("ventanas", []):
        apps[app] = apps.get(app, 0) + minutos
        if hay_web and nav.search(app):
            continue   # el tiempo del navegador lo reparten los dominios
        cat = categoria_de_ventana(app, titulo, categorias)
        cats[cat] = cats.get(cat, 0) + minutos
    for host, minutos in dia_aw.get("dominios", {}).items():
        cat = categoria_de_dominio(host, categorias)
        cats[cat] = cats.get(cat, 0) + minutos
    redondear = lambda d: {k: round(v, 1) for k, v in sorted(d.items(), key=lambda kv: -kv[1])}
    return {"categorias": redondear(cats), "apps": redondear(apps),
            "dominios": redondear(dia_aw.get("dominios", {}))}
