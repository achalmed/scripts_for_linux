"""script_registro_tiempo/lib/cli.py — argumentos: tres órdenes, todas simulan sin --aplicar."""
from __future__ import annotations

import argparse

import config


def build_argument_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Registro de tiempo: reúne KOReader, Zotero, ActivityWatch y Super Productivity en el vault "
                    "y prepara lo que el plugin de Super Productivity importa. Sin --aplicar solo muestra.")
    p.add_argument("--version", action="version", version=f"{config.APP_NAME} {config.VERSION}")
    sub = p.add_subparsers(dest="orden", required=True)

    r = sub.add_parser("recoger", help="lee las fuentes y escribe historial, informe semanal y para-sp.json")
    r.add_argument("--dias", type=int, default=config.DIAS_POR_DEFECTO,
                   help=f"días hacia atrás que se recalculan (por defecto {config.DIAS_POR_DEFECTO})")
    r.add_argument("--sin-aw", action="store_true", help="no consulta ActivityWatch")
    r.add_argument("--sin-sp", action="store_true", help="no entrega los datos a Super Productivity (API REST)")
    r.add_argument("--desde-timer", action="store_true", help="modo del timer: aplica y solo registra avisos")

    pn = sub.add_parser("planificar", help="crea en Super Productivity las tareas de un plan en sintaxis corta")
    pn.add_argument("archivo", help="archivo con una tarea por línea (subtareas con dos espacios y guion); «-» = stdin")
    ru = sub.add_parser("rutina", help="crea en Super Productivity las tareas de la rutina (registro-tiempo.yml)")
    ru.add_argument("--dias", type=int, default=config.DIAS_RUTINA,
                    help=f"cuántos días desde hoy (por defecto {config.DIAS_RUTINA}: hoy y mañana)")
    ru.add_argument("--desde-timer", action="store_true", help="modo del timer: aplica y calla si SP está cerrado")
    no = sub.add_parser("notas", help="lleva las notas .md del vault a SP como tareas de lectura")
    mk = sub.add_parser("minka", help="trae a SP las tareas del despacho asignadas a ti en Minka (y cierra las cerradas)")
    mk.add_argument("--desde-timer", action="store_true",
                    help="modo del timer: aplica y calla si falta la dirección, Minka no responde o SP está cerrado")
    cu = sub.add_parser("cursos", help="cuadra los proyectos de cursos con el currículo y reparte sus fechas")
    cu.add_argument("--desde-timer", action="store_true", help="modo del timer: aplica y calla si SP está cerrado")
    pl = sub.add_parser("plugin", help="empaqueta el plugin de Super Productivity en un .zip para subirlo")
    t = sub.add_parser("timer", help="instala el timer systemd de usuario (cada hora)")
    for s in (r, pn, ru, no, mk, cu, pl, t):
        s.add_argument("--aplicar", action="store_true", help="escribe (sin esto, solo simula)")
        s.add_argument("-v", "--verbose", action="store_true", help="más detalle en el registro")
    return p
