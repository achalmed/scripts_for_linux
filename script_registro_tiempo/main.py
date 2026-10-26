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
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # corre desde cualquier carpeta

import config
from lib import cursos, entorno, informe, instalar, minka, notas, plan, recoger, registro, rutina, sp_rest, validator
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


def _nombres_sp(aplicar: bool, log):
    """(proyectos, etiquetas) de SP; sin SP, vacíos en simulación y None si había que escribir."""
    try:
        return sp_rest.nombres()
    except sp_rest.NoDisponible as e:
        if aplicar:
            log.error("Super Productivity: %s", e)
            return None
        log.warning("Super Productivity no responde: la simulación no comprueba proyectos ni etiquetas")
        return {}, {}


def _rutina(args, usuario: dict, log) -> int:
    bloques_cfg = usuario.get("rutina") or []
    if not bloques_cfg:
        log.error("no hay `rutina:` en %s", entorno.archivo_usuario())
        return config.EXIT_USO
    aplicar = args.aplicar or args.desde_timer
    nombres = _nombres_sp(aplicar, log)
    if nombres is None:
        return config.EXIT_OK if args.desde_timer else config.EXIT_GENERAL
    proyectos, etiquetas = nombres
    ruta_estado = entorno.carpeta_estado() / config.ARCHIVO_RUTINA
    hechas = rutina.creadas(ruta_estado)
    try:   # además del estado, lo que ya está en SP: mismo título el mismo día (sobrevive a cambios de hora)
        en_sp = {(t["title"], t.get("dueDay") or (datetime.fromtimestamp(t["dueWithTime"] / 1000).date().isoformat()
                                                   if t.get("dueWithTime") else "")) for t in sp_rest.tareas(todas=True)}
    except sp_rest.NoDisponible:
        en_sp = set()
    ahora = datetime.now()
    creadas = 0
    for i in range(max(1, args.dias)):
        for t in rutina.bloques(bloques_cfg, date.today() + timedelta(days=i)):
            if rutina.clave(t) in hechas or (t.titulo, t.dia) in en_sp or rutina.ya_paso(t, ahora):
                continue
            if proyectos and t.proyecto and t.proyecto.lower() not in proyectos:
                log.warning("%s %s «%s»: falta el proyecto «%s» (lo crea el plugin desde estructura_sp); se omite",
                            t.dia, t.hora, t.titulo, t.proyecto)
                continue
            cuerpo, avisos = plan.cuerpo(t, proyectos, etiquetas)
            for aviso in avisos if proyectos else []:
                log.warning("%s", aviso)
            if not aplicar:
                log.info("[SIMULACIÓN] %s %s · %s · %d min", t.dia, t.hora or "--:--", t.titulo, t.estimado_ms // 60000)
                continue
            padre = sp_rest.crear(cuerpo)
            for s in t.subtareas:
                sp_rest.crear(plan.cuerpo(s, proyectos, etiquetas)[0], padre)
            hechas.add(rutina.clave(t))
            creadas += 1
    if aplicar:
        rutina.guardar(ruta_estado, hechas, date.today())
        log.info("rutina: %d tareas creadas", creadas)
    return config.EXIT_OK


def _notas(args, usuario: dict, log) -> int:
    cfg = usuario.get("notas_a_sp") or {}
    proyecto = cfg.get("proyecto", config.NOTAS_PROYECTO)
    lista = notas.leer(entorno.raiz(), cfg.get("carpetas", config.NOTAS_CARPETAS))
    nombres = _nombres_sp(args.aplicar, log)
    if nombres is None:
        return config.EXIT_GENERAL
    pid = nombres[0].get(proyecto.lower())
    if not pid and args.aplicar:
        log.error("falta el proyecto «%s» en SP: añádelo a estructura_sp y deja que el plugin lo cree", proyecto)
        return config.EXIT_GENERAL
    todas = sp_rest.tareas(pid, todas=True) if pid else []
    ya = {notas.ruta_de(t) for t in todas} - {""}
    madres = {t["title"]: t["id"] for t in sp_rest.tareas(pid) if not t.get("parentId")} if pid else {}
    faltan = [n for n in lista if n.ruta not in ya]
    for ruta in sorted(ya - {n.ruta for n in lista}):
        log.warning("la nota %s ya no existe (¿cambió de nombre?): su tarea queda como está", ruta)
    log.info("%d notas en %s; %d ya están en SP; %d nuevas", len(lista), proyecto, len(lista) - len(faltan), len(faltan))
    if not args.aplicar:
        for n in faltan[:15]:
            log.info("[SIMULACIÓN] %s › %s (%d min)", n.grupo, n.titulo, n.minutos)
        return config.EXIT_OK
    vault = cfg.get("vault", config.NOTAS_VAULT)
    for n in faltan:
        if n.grupo not in madres:
            madres[n.grupo] = sp_rest.crear({"title": n.grupo, "projectId": pid})
        sp_rest.crear({"title": n.titulo, "timeEstimate": n.minutos * 60000, "notes": notas.texto_notas(n, vault)},
                      madres[n.grupo])
    log.info("creadas %d tareas de lectura en «%s»", len(faltan), proyecto)
    return config.EXIT_OK


def _cursos(args, usuario: dict, log) -> int:
    """Los proyectos de cursos cuadrados con el currículo de docencia y repartidos en sesiones (lib/cursos.py)."""
    cfg = usuario.get("cursos") or {}
    if not cfg.get("carriles"):
        log.error("no hay `cursos.carriles` en %s", entorno.archivo_usuario())
        return config.EXIT_USO
    aplicar = args.aplicar or args.desde_timer
    nombres = _nombres_sp(aplicar, log)
    if nombres is None or not nombres[0]:
        return config.EXIT_OK if args.desde_timer else config.EXIT_GENERAL
    proyectos, etiquetas = nombres
    activas = {t["id"]: t for t in sp_rest.tareas()}
    por_titulo: dict[str, list[dict]] = {}
    for pr in sp_rest.proyectos():   # en el orden en que el autor ve sus tareas (taskIds), luego el resto
        propias = [activas[i] for i in pr.get("taskIds", []) if i in activas]
        vistas = {t["id"] for t in propias}
        propias += [t for t in activas.values() if t.get("projectId") == pr["id"] and t["id"] not in vistas]
        por_titulo[pr["title"].lower()] = propias
    carpeta = Path(entorno.env.CLASS_DIR) / "contenido" / "cursos"
    hoy = date.today()
    todos: list[tuple[dict, list]] = []
    for carril in cfg["carriles"]:
        faltan = [p["proyecto"] for p in carril.get("proyectos", []) if p["proyecto"].lower() not in proyectos]
        for f in faltan:
            log.warning("carril %s: el proyecto «%s» no existe en SP; se salta", carril.get("nombre"), f)
        carril = {**carril, "proyectos": [p for p in carril.get("proyectos", []) if p["proyecto"] not in faltan]}
        tareas_c = {p["proyecto"]: por_titulo.get(p["proyecto"].lower(), []) for p in carril["proyectos"]}
        pasos = cursos.planear(carril, tareas_c, carpeta, etiquetas, hoy, int(cfg.get("sesion_min", 60)),
                               int(cfg.get("semanas", 8)))
        subs = cursos.subtareas(carril, tareas_c, etiquetas)
        pasos += [cursos.Paso(proyecto="", tarea=t, cambios=c) for t, c in subs]
        if subs:
            log.info("carril %s: %d subtareas pasan a las etiquetas del carril", carril.get("nombre"), len(subs))
        todos.append((carril, pasos))
        principales = [p for p in pasos if p.proyecto]   # sin las subtareas que solo cambian de etiqueta
        nuevos = [p for p in principales if p.tarea is None]
        cambios = [p for p in pasos if p.tarea is not None and p.cambios]
        fechados = [p for p in principales if p.dia]
        log.info("carril %s (%s): %d pendientes · %d con fecha hasta %s · %d temas por crear · %d tareas con cambios",
                 carril.get("nombre"), " ".join(carril.get("dias", [])) if isinstance(carril.get("dias"), list)
                 else carril.get("dias", ""), len(principales), len(fechados), fechados[-1].dia if fechados else "—",
                 len(nuevos), len(cambios))
        for p in fechados[:6]:
            log.info("   %s · %s · %s", p.dia, p.proyecto,
                     p.tarea["title"] if p.tarea else f"(nuevo) {p.tema.titulo_curso} · {p.tema.id} {p.tema.titulo}")
    if not aplicar:
        log.info("[SIMULACIÓN] nada se escribió; con --aplicar se crean los temas y se cambian notas, etiquetas y fechas")
        return config.EXIT_OK
    respaldo = entorno.carpeta_datos() / f"respaldo-cursos-{datetime.now():%Y-%m-%d_%H%M%S}.json"
    if any(p.tarea is not None and p.cambios for _, pasos in todos for p in pasos):
        tocadas = [p.tarea for _, pasos in todos for p in pasos if p.tarea is not None and p.cambios]
        registro.escribir_json(respaldo, {"tareas": tocadas}, "copia de las tareas de cursos antes de `main.py cursos`")
        log.info("copia previa: %s (%d tareas)", respaldo, len(tocadas))
    creadas = cambiadas = 0
    for carril, pasos in todos:
        ids_tags = [etiquetas[e.lower()] for e in carril.get("etiquetas", []) if e.lower() in etiquetas]
        for p in pasos:
            if p.tarea is None:
                sp_rest.crear(cursos.cuerpo_nuevo(p, proyectos[p.proyecto.lower()], ids_tags))
                creadas += 1
            elif p.cambios:
                sp_rest.cambiar(p.tarea["id"], p.cambios)
                cambiadas += 1
    log.info("cursos: %d temas creados y %d tareas actualizadas", creadas, cambiadas)
    return config.EXIT_OK


def _minka(args, log) -> int:
    """Las tareas del despacho asignadas al autor en Minka → SP, con su estado y plazo; las cerradas allá, hechas aquí
    (reglas en lib/minka.py). La dirección viene del .env del despacho; nada suyo se escribe fuera de SP."""
    aplicar = args.aplicar or args.desde_timer
    callar = log.info if args.desde_timer else log.warning
    ruta = minka.archivo_env(entorno.env.DESPACHO_DIR)
    try:
        con = minka.conexion(minka.leer_env(ruta))
    except ValueError as e:
        log.error("%s (%s)", e, ruta)
        return config.EXIT_USO
    if con is None:
        callar("Minka: falta MINKA_SUSCRIPCION en %s (puesta en marcha: meta/docs/super-productivity.md)", ruta)
        return config.EXIT_OK if args.desde_timer else config.EXIT_USO
    try:
        datos = minka.leer_tareas(*con)
    except minka.NoDisponible as e:
        callar("Minka: %s", e)
        return config.EXIT_OK if args.desde_timer else config.EXIT_GENERAL
    nombres = _nombres_sp(aplicar, log)
    if nombres is None:
        return config.EXIT_OK if args.desde_timer else config.EXIT_GENERAL
    pid = nombres[0].get(config.PROYECTO_MINKA.lower())
    if nombres[0] and not pid:
        log.warning("falta el proyecto «%s» en SP: las tareas nuevas irán a la bandeja", config.PROYECTO_MINKA)
    try:
        activas = sp_rest.tareas()
        archivadas = [t for t in sp_rest.tareas(todas=True) if t["id"] not in {a["id"] for a in activas}]
    except sp_rest.NoDisponible as e:
        if aplicar:
            log.error("Super Productivity: %s", e)
            return config.EXIT_OK if args.desde_timer else config.EXIT_GENERAL
        activas, archivadas = [], []
    p = minka.plan(datos, activas, archivadas, pid)
    for aviso in p["avisos"]:
        log.warning("%s", aviso)
    log.info("Minka: %d tareas tuyas; en SP, %d nuevas y %d con cambios", len(datos["tareas"]), len(p["crear"]),
             len(p["cambiar"]))
    if not aplicar:
        for c in p["crear"][:15]:
            plazo = next((x for x in c["notes"].splitlines() if x.startswith("Plazo: ")), "sin plazo")
            log.info("[SIMULACIÓN] crearía «%s» (%s)", c["title"], plazo)
        for _, cambios, titulo in p["cambiar"][:15]:
            log.info("[SIMULACIÓN] cambiaría «%s»: %s", titulo, ", ".join(cambios))
        return config.EXIT_OK
    for c in p["crear"]:
        sp_rest.crear(c)
    for tid, cambios, _ in p["cambiar"]:
        sp_rest.cambiar(tid, cambios)
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
    if args.orden == "rutina":
        return _rutina(args, usuario, log)
    if args.orden == "notas":
        return _notas(args, usuario, log)
    if args.orden == "minka":
        return _minka(args, log)
    if args.orden == "cursos":
        return _cursos(args, usuario, log)
    if args.orden == "plugin":
        destino = instalar.SUITE / "dist" / config.NOMBRE_ZIP_PLUGIN   # visible e ignorado por git; se rearma de plugin-sp/
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
