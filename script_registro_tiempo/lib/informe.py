"""script_registro_tiempo/lib/informe.py — la nota semanal del vault (`tareas/registro/AAAA-MM-DD-semana.md`).

Una nota por semana ISO (nombre: el lunes), generada entera en cada pasada; es lo que la revisión semanal lee en
Obsidian (el skill `productividad-personal` la pide). No se edita: lo que el autor quiera anotar va a su revisión.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import config

DIAS_SEMANA = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")


def lunes(dia: date) -> date:
    return dia - timedelta(days=dia.weekday())


def _h(minutos: float) -> str:
    if minutos < config.MINIMO_MIN:
        return "—"
    h, m = divmod(int(round(minutos)), 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def _sumar(destino: dict, origen: dict) -> None:
    for k, v in (origen or {}).items():
        destino[k] = destino.get(k, 0) + v


def _tabla_top(titulo: str, datos: dict, encabezado: str) -> list[str]:
    filas = [(k, v) for k, v in sorted(datos.items(), key=lambda kv: -kv[1]) if v >= config.MINIMO_MIN]
    if not filas:
        return []
    salida = [f"## {titulo}", "", f"| {encabezado} | tiempo |", "|---|---|"]
    salida += [f"| {k} | {_h(v)} |" for k, v in filas[:config.TOP_INFORME]]
    if len(filas) > config.TOP_INFORME:
        salida.append(f"| (otros {len(filas) - config.TOP_INFORME}) | {_h(sum(v for _, v in filas[config.TOP_INFORME:]))} |")
    return salida + [""]


def semana(inicio: date, hist: dict[str, dict], usuario: dict, fuentes: dict[str, str]) -> str:
    dias = [(inicio + timedelta(days=i)).isoformat() for i in range(7)]
    regs = [hist.get(d, {}) for d in dias]
    anio, num, _ = inicio.isocalendar()
    fin = inicio + timedelta(days=6)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    categorias = usuario.get("categorias", {})
    vigiladas = [c for c, r in categorias.items() if r.get("vigilar")]

    def fila(nombre: str, valores: list[float]) -> str:
        return f"| {nombre} | " + " | ".join(_h(v) for v in valores) + f" | **{_h(sum(valores))}** |"

    lineas = [
        "---", f"id: {inicio.strftime('%Y%m%d')}000000", "tipo: tablero",
        f'titulo: "Registro de tiempo, semana {anio}-W{num:02d}"', "estado: activo", f"creado: {inicio.isoformat()}",
        f"generado: {datetime.now().isoformat(timespec='seconds')}",
        "tags: [tablero, registro-tiempo]", "aliases: []", "AutoNoteMover: disable", "---",
        f"<!-- GENERADO por scripts-linux/script_registro_tiempo ({ahora}); no editar: se regenera con "
        "`main.py recoger --aplicar`. Lo que quieras anotar va a tu revisión semanal. -->",
        "", f"# Registro de tiempo — semana {anio}-W{num:02d} ({inicio:%d/%m} – {fin:%d/%m})", "",
        "## Resumen", "", "| | " + " | ".join(DIAS_SEMANA) + " | total |", "|---|" + "---|" * 8,
        fila("Trabajo registrado en Super Productivity", [r.get("sp", {}).get("total_min", 0) for r in regs]),
        fila("Lectura en KOReader", [r.get("koreader", {}).get("total_min", 0) for r in regs]),
        fila("Lectura en Zotero", [r.get("zotero", {}).get("total_min", 0) for r in regs]),
    ]
    for cat in vigiladas:
        lineas.append(fila(categorias[cat].get("tarea_sp") or cat.replace("_", " ").capitalize(),
                           [r.get("aw", {}).get("categorias", {}).get(cat, 0) for r in regs]))
    lineas.append("| Tareas terminadas | " + " | ".join(str(len(r.get("sp", {}).get("hechas", [])) or "—")
                                                    for r in regs)
                  + f" | **{sum(len(r.get('sp', {}).get('hechas', [])) for r in regs)}** |")
    lineas.append("")

    por_proyecto: dict[str, float] = {}
    libros: dict[str, float] = {}
    apps: dict[str, float] = {}
    dominios: dict[str, float] = {}
    cats: dict[str, float] = {}
    for r in regs:
        _sumar(por_proyecto, r.get("sp", {}).get("proyectos"))
        _sumar(libros, r.get("koreader", {}).get("libros"))
        _sumar(libros, r.get("zotero", {}).get("items"))
        _sumar(apps, r.get("aw", {}).get("apps"))
        _sumar(dominios, r.get("aw", {}).get("dominios"))
        _sumar(cats, r.get("aw", {}).get("categorias"))

    def real(nombre: str) -> float:
        """Un proyecto de SP, «Lectura» (KOReader + Zotero) o una categoría (por su clave o su tarea_sp)."""
        if nombre in por_proyecto:
            return por_proyecto[nombre]
        if nombre.lower() == "lectura":
            return sum(libros.values())
        for cat, regla in categorias.items():
            if nombre in (cat, regla.get("tarea_sp")):
                return cats.get(cat, 0)
        return 0

    metas = usuario.get("metas_semanales_horas", {})
    if metas:
        lineas += ["## Metas de la semana", "", "| qué | meta | real | avance |", "|---|---|---|---|"]
        for nombre, horas in metas.items():
            avance = f"{round(100 * real(nombre) / (horas * 60))} %" if horas else "—"
            lineas.append(f"| {nombre} | {horas} h | {_h(real(nombre))} | {avance} |")
        lineas.append("")
    limites = usuario.get("limites_semanales_horas", {})
    if limites:
        lineas += ["## Límites de la semana", "", "| qué | límite | real | estado |", "|---|---|---|---|"]
        medido = any("aw" in r for r in regs)
        for nombre, horas in limites.items():
            estado = ("excedido" if real(nombre) > horas * 60 else "dentro") if medido else "sin medir"
            lineas.append(f"| {nombre} | {horas} h | {_h(real(nombre))} | {estado} |")
        lineas.append("")

    lineas += _tabla_top("Tiempo en Super Productivity por proyecto", por_proyecto, "proyecto")
    lineas += _tabla_top("Lectura por obra", libros, "obra")
    lineas += _tabla_top("Tiempo frente a la pantalla por categoría", cats, "categoría")
    lineas += _tabla_top("Programas", apps, "programa")
    lineas += _tabla_top("Sitios", dominios, "sitio")
    lineas += ["## Fuentes de esta nota", ""] + [f"- **{k}:** {v}" for k, v in fuentes.items()] + [""]
    return "\n".join(lineas)
