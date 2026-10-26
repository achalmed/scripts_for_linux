"""script_registro_tiempo/lib/cursos.py — los proyectos de cursos de SP, cuadrados con el currículo y con fechas móviles.

Cada carril de `cursos:` (registro-tiempo.yml) es una fila de proyectos en orden y unos días de la semana con una sesión
cada uno. Para cada proyecto: las tareas que ya tiene se emparejan con los temas de su currículo
(`docencia/contenido/cursos/<id>/curso.yml`) por palabras del título; las emparejadas ganan en sus notas la línea
«Currículo: …» (título, fechas y estimación del autor se conservan) y los temas que faltan se crean. Después se
reparten las sesiones: cada tarea pendiente ocupa tantas sesiones como su estimación restante, y su fecha es la de su
última sesión, solo dentro del horizonte (`semanas`); lo que queda más allá va sin fecha. Correr la orden de nuevo
recalcula desde hoy con lo que falte: si el autor se atrasa, las fechas se corren y no se acumulan vencidas.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

from lib.rutina import DIAS, _dias

MARCA = "Currículo: "
GENERICAS = {"introduccion", "conceptos", "basicos", "teoria", "modelo", "modelos", "analisis", "parte", "unidad"}
ESTIMADO_POR_DEFECTO_MIN = 90


def palabras(texto: str) -> set[str]:
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z]{4,}", t) if w not in GENERICAS}


@dataclass
class Tema:
    curso: str
    titulo_curso: str
    id: str
    titulo: str

    def linea(self) -> str:
        return f"{MARCA}{self.titulo_curso} ({self.curso}) · tema {self.id} «{self.titulo}»"


@dataclass
class Paso:
    """Una tarea del plan: existente (`tarea`) o por crear (`tema` sin `tarea`)."""
    proyecto: str
    tarea: dict | None = None
    tema: Tema | None = None
    estimado_ms: int = 0
    dia: str = ""
    cambios: dict = field(default_factory=dict)


def temas(carpeta_cursos: Path, ids: list[str]) -> list[Tema]:
    salida: list[Tema] = []
    for c in ids or []:
        f = carpeta_cursos / c / "curso.yml"
        if not f.is_file():
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for u in d.get("unidades") or []:
            for t in u.get("temas") or []:
                salida.append(Tema(curso=c, titulo_curso=d.get("titulo") or c, id=str(t.get("id")), titulo=t.get("titulo") or ""))
    return salida


def _ya_enlazado(tarea: dict, tema: Tema) -> bool:
    return f"({tema.curso}) · tema {tema.id} " in (tarea.get("notes") or "")


def emparejar(lista_temas: list[Tema], tareas: list[dict]) -> list[tuple[dict | Tema, Tema | None]]:
    """La secuencia del proyecto: las tareas del autor en su orden, cada una con su tema (o None), y los temas que faltan
    intercalados detrás de la tarea que cubre el tema anterior del currículo (o al principio).

    Una tarea se enlaza al tema que ya nombra en sus notas o, si no, al de más palabras en común (al menos la mitad de
    las del tema); varias tareas pueden cubrir un mismo tema («Teoría del consumidor I, II y III»)."""
    # Las tareas que creó esta orden (título «<curso> · <id> …») no son del autor: vuelven a su sitio del currículo.
    creadas = {i: t for i, tm in enumerate(lista_temas) for t in tareas
               if t["title"].startswith(f"{tm.titulo_curso} · {tm.id} ") and _ya_enlazado(t, tm)}
    tareas = [t for t in tareas if all(t is not c for c in creadas.values())]
    indice: dict[int, int] = {}            # posición de la tarea → índice del tema que cubre
    for pos, t in enumerate(tareas):
        previo = next((i for i, tm in enumerate(lista_temas) if _ya_enlazado(t, tm)), None)
        if previo is None:
            pt = palabras(t["title"])
            puntos = [(len(palabras(tm.titulo) & pt), -i, i) for i, tm in enumerate(lista_temas)
                      if palabras(tm.titulo) and len(palabras(tm.titulo) & pt) >= max(1, len(palabras(tm.titulo)) // 2)]
            previo = max(puntos)[2] if puntos else None
        if previo is not None:
            indice[pos] = previo
    cubiertos = set(indice.values())
    secuencia: list[tuple[dict | Tema, Tema | None]] = [(t, lista_temas[indice[p]] if p in indice else None)
                                                         for p, t in enumerate(tareas)]
    for i, tm in enumerate(lista_temas):
        if i in cubiertos:
            continue
        anclas = [p for p, j in indice.items() if j < i]
        if anclas:
            mejor = max(anclas, key=lambda p: (indice[p], p))
            destino = next(k for k, (x, _) in enumerate(secuencia) if x is tareas[mejor]) + 1
            while destino < len(secuencia) and (isinstance(secuencia[destino][0], Tema)
                                                or secuencia[destino][0] in creadas.values()):
                destino += 1   # detrás de los temas ya intercalados en esa ancla, en orden del currículo
        else:
            destino = sum(1 for x, _ in secuencia if isinstance(x, Tema) or x in creadas.values())
        secuencia.insert(destino, (creadas.get(i, tm), tm))
    return secuencia


def sesiones(desde: date, dias: list[str] | str, semanas: int):
    """Las fechas de sesión del carril, de hoy al final del horizonte."""
    claves = _dias(dias)
    fin = desde + timedelta(weeks=semanas)
    d = desde
    while d <= fin:
        if DIAS[d.weekday()] in claves:
            yield d
        d += timedelta(days=1)


def _mediana_ms(tareas: list[dict]) -> int:
    est = sorted(t["timeEstimate"] for t in tareas if t.get("timeEstimate"))
    return est[len(est) // 2] if est else ESTIMADO_POR_DEFECTO_MIN * 60000


def planear(carril: dict, tareas_por_proyecto: dict[str, list[dict]], carpeta_cursos: Path, etiquetas: dict[str, str],
            hoy: date, sesion_min: int, semanas: int) -> list[Paso]:
    """Los pasos de un carril con su fecha (o sin ella), sus cambios y lo que hay que crear."""
    ids_tags = [etiquetas[e.lower()] for e in carril.get("etiquetas", []) if e.lower() in etiquetas]
    calendario = list(sesiones(hoy, carril.get("dias", []), semanas)) if carril.get("fechas", True) else []
    i_sesion = 0
    pasos: list[Paso] = []
    for p in carril.get("proyectos", []):
        nombre = p["proyecto"]
        propias = ordenar([t for t in tareas_por_proyecto.get(nombre, []) if not t.get("parentId")])
        mediana = _mediana_ms(propias)
        orden = [(None if isinstance(x, Tema) else x, tm)
                 for x, tm in emparejar(temas(carpeta_cursos, p.get("curriculo", [])), propias)]
        for t, tm in orden:
            if t is not None and t.get("isDone"):
                continue
            paso = Paso(proyecto=nombre, tarea=t, tema=tm)
            paso.estimado_ms = (t.get("timeEstimate") or mediana) if t else mediana
            restante = max(paso.estimado_ms - ((t or {}).get("timeSpent") or 0), sesion_min * 60000)
            n = math.ceil(restante / (sesion_min * 60000))
            if i_sesion + n <= len(calendario):
                paso.dia = calendario[i_sesion + n - 1].isoformat()
            i_sesion += n
            pasos.append(paso)
            if t is None:
                continue   # tema del currículo que falta: se crea con `cuerpo_nuevo`
            notas = t.get("notes") or ""
            if tm is not None and not _ya_enlazado(t, tm):
                paso.cambios["notes"] = (notas.rstrip() + "\n\n" if notas.strip() else "") + tm.linea()
            if ids_tags and sorted(t.get("tagIds") or []) != sorted(ids_tags):
                paso.cambios["tagIds"] = ids_tags
            fecha_actual = t.get("dueDay") or ""
            if paso.dia != fecha_actual or t.get("dueWithTime"):
                paso.cambios["dueDay"] = paso.dia or None
                paso.cambios["dueWithTime"] = None
    return pasos


def subtareas(carril: dict, tareas_por_proyecto: dict[str, list[dict]], etiquetas: dict[str, str]) -> list[tuple[dict, dict]]:
    """Las subtareas de los cursos del carril con las etiquetas del carril (las de cada herramienta dejan de usarse)."""
    ids_tags = sorted(etiquetas[e.lower()] for e in carril.get("etiquetas", []) if e.lower() in etiquetas)
    if not ids_tags:
        return []
    return [(t, {"tagIds": ids_tags}) for p in carril.get("proyectos", [])
            for t in tareas_por_proyecto.get(p["proyecto"], [])
            if t.get("parentId") and sorted(i for i in t.get("tagIds") or [] if i != "TODAY") != ids_tags]


RE_NUMERO = re.compile(r"^\s*(\d+(?:[.,]\d+)*)")


def ordenar(tareas: list[dict]) -> list[dict]:
    """Si la mayoría de las tareas empieza por un número («1.01.», «6.»), ese número manda; si no, el orden del autor."""
    numeradas = [RE_NUMERO.match(t["title"]) for t in tareas]
    if not tareas or sum(1 for m in numeradas if m) < len(tareas) * 0.6:
        return tareas
    def clave(par):
        pos, t = par
        m = RE_NUMERO.match(t["title"])
        return (0, [int(x) for x in re.split(r"[.,]", m.group(1)) if x], pos) if m else (1, [], pos)
    return [t for _, t in sorted(enumerate(tareas), key=clave)]


def cuerpo_nuevo(paso: Paso, proyecto_id: str, ids_tags: list[str]) -> dict:
    c = {"title": f"{paso.tema.titulo_curso} · {paso.tema.id} {paso.tema.titulo}", "projectId": proyecto_id,
         "timeEstimate": paso.estimado_ms,
         "notes": paso.tema.linea()}
    if ids_tags:
        c["tagIds"] = ids_tags
    if paso.dia:
        c["dueDay"] = paso.dia
    return c
