#!/usr/bin/env python3
"""script_registro_tiempo/main.py — registro de tiempo del autor, en el vault y hacia Super Productivity.

Solo orquestación; la lógica vive en lib/:

  1. Parsear argumentos            (lib/cli.py)
  2. Logger                        (lib/logger.py)
  3. Validar el archivo del autor  (lib/validator.py)
  4. Orden:
       recoger -> fuentes a registros (lib/recoger.py), historial y para-sp.json (lib/registro.py),
                  nota semanal (lib/informe.py)
       plugin  -> .zip del plugin de Super Productivity (lib/instalar.py)
       timer   -> unidades systemd de usuario (lib/instalar.py)
  5. Resumen. Sin --aplicar nada se escribe.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # corre desde cualquier carpeta

import config
from lib import entorno, informe, instalar, plan, recoger, registro, sp_rest, validator
from lib.cli import build_argument_parser
from lib.logger import setup_logger


def _recoger(args, usuario: dict, log) -> int:
    aplicar = args.aplicar or args.desde_timer
    hoy = date.today()
    r = recoger.pasada(hoy, max(1, args.dias), usuario, not args.sin_aw, log)
    meses = registro.fusionar(entorno.carpeta_datos(), r["dias"])
    hist = {**registro.historial(entorno.carpeta_datos(), config.DIAS_PARA_SP, hoy), **r["dias"]}
    semanas = sorted({informe.lunes(date.fromisoformat(d)) for d in r["dias"]})
    notas = {entorno.carpeta_registro() / f"{s.isoformat()}-semana.md": informe.semana(s, hist, usuario, r["fuentes"])
             for s in semanas}
    sp = registro.para_sp(hist, usuario)
    ruta_sp = entorno.carpeta_estado() / config.ARCHIVO_PARA_SP

    for dia, reg in r["dias"].items():
        log.info("%s · SP %s min · KOReader %s min · Zotero %s min · pantalla %s", dia,
                 round(reg["sp"]["total_min"]), round(reg["koreader"]["total_min"]),
                 round(reg["zotero"]["total_min"]),
                 ", ".join(f"{k} {round(v)}" for k, v in list(reg.get("aw", {}).get("categorias", {}).items())[:4])
                 or "sin datos")
    for nombre, nota in r["fuentes"].items():
        log.debug("fuente %s: %s", nombre, nota)

    if not aplicar:
        log.info("[SIMULACIÓN] escribiría %d mes(es) de historial, %d nota(s) semanal(es), la instantánea de Zotero "
                 "y %s (%d tareas para SP)", len(meses), len(notas), ruta_sp, len(sp["tareas"]))
        return config.EXIT_OK
    for ruta, datos in meses.items():
        registro.escribir_json(ruta, datos, "historial del registro de tiempo de un mes")
    registro.escribir_json(r["ruta_instantanea"], r["instantanea"], "instantánea del tiempo de lectura de Zotero")
    for ruta, texto in notas.items():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
    registro.escribir_json(ruta_sp, sp)
    log.info("escritos: %s; notas: %s; para el plugin: %s", ", ".join(p.name for p in meses),
             ", ".join(p.name for p in notas), ruta_sp)
    if args.sin_sp:
        return config.EXIT_OK
    try:
        log.info("Super Productivity: %s", sp_rest.entregar(sp, config.PROYECTO_SP))
    except sp_rest.NoDisponible as e:
        (log.info if args.desde_timer else log.warning)("Super Productivity: %s", e)
    return config.EXIT_OK


def _planificar(args, log) -> int:
    texto = sys.stdin.read() if args.archivo == "-" else Path(args.archivo).read_text(encoding="utf-8")
    tareas = plan.leer(texto, date.today())
    if not tareas:
        log.error("no hay tareas en %s", args.archivo)
        return config.EXIT_USO
    try:
        proyectos, etiquetas = sp_rest.nombres()
    except sp_rest.NoDisponible as e:
        if args.aplicar:
            log.error("Super Productivity: %s", e)
            return config.EXIT_GENERAL
        proyectos, etiquetas = {}, {}
        log.warning("Super Productivity no responde: la simulación no puede comprobar proyectos ni etiquetas")
    for t in tareas:
        cuerpo, avisos = plan.cuerpo(t, proyectos, etiquetas)
        for aviso in avisos if proyectos or etiquetas else []:
            log.warning("%s", aviso)
        if not args.aplicar:
            log.info("[SIMULACIÓN] %s · %s · %d subtareas", t.titulo,
                     ", ".join(f"{k}={v}" for k, v in cuerpo.items() if k != "title") or "sin campos", len(t.subtareas))
            continue
        padre = sp_rest.crear(cuerpo)
        for s in t.subtareas:
            sp_rest.crear(plan.cuerpo(s, proyectos, etiquetas)[0], padre)
        log.info("creada: %s (%d subtareas)", t.titulo, len(t.subtareas))
    return config.EXIT_OK


def main() -> int:
    args = build_argument_parser().parse_args()
    log = setup_logger(config.APP_NAME, args.verbose)
    try:
        usuario, avisos = validator.cargar_usuario(entorno.archivo_usuario())
    except ValueError as e:
        log.error("%s", e)
        return config.EXIT_USO
    for aviso in avisos:
        log.warning("%s", aviso)

    if args.orden == "recoger":
        return _recoger(args, usuario, log)
    if args.orden == "planificar":
        return _planificar(args, log)
    if args.orden == "plugin":
        destino = entorno.carpeta_estado() / config.NOMBRE_ZIP_PLUGIN
        try:
            archivos = instalar.empaquetar(destino, args.aplicar)
        except FileNotFoundError as e:
            log.error("%s", e)
            return config.EXIT_NO_ENCONTRADO
        log.info("%s %s con %s. Súbelo en Super Productivity: Ajustes → Plugins → subir plugin.",
                 "escrito" if args.aplicar else "[SIMULACIÓN] escribiría", destino, ", ".join(archivos))
        return config.EXIT_OK
    rutas = ", ".join(instalar.instalar_timer(args.aplicar))
    if args.aplicar:
        log.info("escritas %s; registro-tiempo.timer activo", rutas)
    else:
        log.info("[SIMULACIÓN] escribiría %s y activaría registro-tiempo.timer", rutas)
    return config.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
