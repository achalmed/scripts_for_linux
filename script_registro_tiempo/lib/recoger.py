"""script_registro_tiempo/lib/recoger.py — una pasada: de las fuentes a los registros de cada día (sin escribir).

Devuelve lo que se escribiría; `main.py` decide si se escribe. Zotero es la única fuente que suma: su tiempo de hoy
es lo guardado hoy más lo crecido desde la última instantánea.
"""
from __future__ import annotations

from datetime import date, timedelta

import config
from lib import activitywatch, clasificar, entorno, koreader, registro, superproductivity, zotero

REGEX_NAVEGADORES_DEFECTO = "(?i)zen|firefox|chrom|brave|edge|librewolf|waterfox|vivaldi|opera"


def pasada(hoy: date, dias: int, usuario: dict, usar_aw: bool, log) -> dict:
    desde = (hoy - timedelta(days=dias - 1)).isoformat()
    lista_dias = [(hoy - timedelta(days=i)).isoformat() for i in range(dias - 1, -1, -1)]
    fuentes: dict[str, str] = {}

    ko = koreader.leer(entorno.koreader_stats(), desde)
    fuentes["KOReader"] = f"{entorno.koreader_stats().name}, {len(ko)} días con lectura" \
        if entorno.koreader_stats().is_file() else "no se encontró statistics.sqlite3"

    try:
        sp = superproductivity.leer(entorno.sync_sp(), desde, config.PROYECTO_SP)
        fuentes["Super Productivity"] = f"tareas/{config.SYNC_SP}" if entorno.sync_sp().is_file() \
            else f"falta tareas/{config.SYNC_SP}: apunta la sincronización de SP (archivo local) a tareas/"
    except superproductivity.Cifrado:
        sp = {}
        fuentes["Super Productivity"] = "sync-data.json cifrado: desactiva el cifrado o no se lee"

    regex_nav = usuario.get("navegadores_regex", REGEX_NAVEGADORES_DEFECTO)
    aw, nota_aw = (activitywatch.leer(lista_dias, regex_nav) if usar_aw else ({}, "desactivado (--sin-aw)"))
    fuentes["ActivityWatch"] = nota_aw or "ventanas y web"
    if nota_aw:
        log.warning("ActivityWatch: %s", nota_aw)

    ruta_inst = entorno.carpeta_datos() / config.INSTANTANEA_ZOTERO
    anterior = zotero.leer_instantanea(ruta_inst)
    actual = zotero.acumulados(entorno.zotero_db())
    crecido = zotero.diferencia(anterior, actual)
    fuentes["Zotero"] = ("línea base fijada hoy: el tiempo cuenta desde la próxima pasada" if not anterior
                         else f"{len(actual)} ítems con tiempo de lectura")

    guardado = registro.historial(entorno.carpeta_datos(), dias, hoy)
    nuevos: dict[str, dict] = {}
    for dia in lista_dias:
        previo = guardado.get(dia, {})
        reg = {"koreader": ko.get(dia, {"total_min": 0, "libros": {}}),
               "sp": sp.get(dia, {"proyectos": {}, "etiquetas": {}, "hechas": [], "total_min": 0})}
        zot = previo.get("zotero", {"total_min": 0, "items": {}})
        if dia == hoy.isoformat() and crecido:
            items = dict(zot.get("items", {}))
            for titulo, minutos in crecido.items():
                items[titulo] = round(items.get(titulo, 0) + minutos, 1)
            zot = {"total_min": round(sum(items.values()), 1), "items": items}
        reg["zotero"] = zot
        if dia in aw:
            reg["aw"] = clasificar.resumir(aw[dia], usuario.get("categorias", {}), regex_nav)
        elif "aw" in previo:
            reg["aw"] = previo["aw"]   # sin servidor hoy: no se borra lo que ya se midió
        nuevos[dia] = reg
    instantanea = {"fecha": hoy.isoformat(), "items": actual}
    return {"dias": nuevos, "instantanea": instantanea, "ruta_instantanea": ruta_inst, "fuentes": fuentes}
