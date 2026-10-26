"""script_registro_tiempo/lib/plan.py — líneas en sintaxis corta de Super Productivity → tareas para la API REST.

Acepta el formato del exportador del vault (`meta/docs/super-productivity.md`: `<texto> +<proyecto> #<tag> <estimado>
@<AAAA-MM-DD>`) y el del plan diario (`Título #tag @HH:MM 0m/1h`, subtareas con dos espacios y guion). La API REST no
interpreta la sintaxis corta (eso lo hace la barra «Añadir tarea»): aquí se traduce a campos. Proyectos y etiquetas
se buscan por nombre; una etiqueta que no existe se informa y se deja fuera (la API no crea etiquetas).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

RE_TAG = re.compile(r"(?<!\S)#([\wáéíóúñü/-]+)", re.IGNORECASE)
RE_PROYECTO = re.compile(r"(?<!\S)\+([\wáéíóúñü-]+)", re.IGNORECASE)
RE_ESTIMADO = re.compile(r"(?:(?:\d+h)?(?:\d+m)?/)?((?:\d+h)(?:\d+m)?|\d+m)")
RE_ARROBA = re.compile(r"(?<!\S)@(\S+)")
RE_DURACION = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?$")


@dataclass
class Tarea:
    titulo: str
    proyecto: str = ""
    etiquetas: list[str] = field(default_factory=list)
    estimado_ms: int = 0
    dia: str = ""
    hora: str = ""
    subtareas: list["Tarea"] = field(default_factory=list)


def _duracion_ms(texto: str) -> int:
    m = RE_DURACION.match(texto)
    if not texto or not m or not any(m.groups()):
        return 0
    return (int(m.group(1) or 0) * 60 + int(m.group(2) or 0)) * 60000


def _fecha(valor: str, hoy: date) -> tuple[str, str]:
    """(día, hora) desde @AAAA-MM-DD, @hoy, @mañana o @HH:MM."""
    v = valor.lower()
    if v in ("hoy", "today"):
        return hoy.isoformat(), ""
    if v in ("mañana", "manana", "tomorrow"):
        return (hoy + timedelta(days=1)).isoformat(), ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v, ""
    if re.fullmatch(r"\d{1,2}:\d{2}", v):
        return hoy.isoformat(), v.zfill(5)
    return "", ""


def linea(texto: str, hoy: date) -> Tarea | None:
    texto = texto.strip()
    if not texto or texto.startswith(("<!--", "##", "```")):
        return None
    texto = re.sub(r"^[-*]\s+(\[[ xX]\]\s+)?", "", texto)
    t = Tarea(titulo="")
    t.etiquetas = RE_TAG.findall(texto)
    p = RE_PROYECTO.findall(texto)
    t.proyecto = p[0].replace("-", " ") if p else ""
    for arroba in RE_ARROBA.findall(texto):
        dia, hora = _fecha(arroba, hoy)
        t.dia, t.hora = dia or t.dia, hora or t.hora
    resto = RE_ARROBA.sub("", RE_PROYECTO.sub("", RE_TAG.sub("", texto)))
    palabras = []
    for palabra in resto.split():
        m = RE_ESTIMADO.fullmatch(palabra)   # «30m», «1h30m» o «0m/1h» (gastado/estimado: manda el estimado)
        if m:
            t.estimado_ms = _duracion_ms(m.group(1))
        else:
            palabras.append(palabra)
    t.titulo = " ".join(palabras).strip()
    return t if t.titulo else None


def leer(texto: str, hoy: date) -> list[Tarea]:
    """Tareas con sus subtareas (una línea con sangría y guion es subtarea de la anterior sin sangría)."""
    tareas: list[Tarea] = []
    for cruda in texto.splitlines():
        es_sub = bool(re.match(r"^\s{2,}[-*]\s", cruda)) and bool(tareas)
        t = linea(cruda, hoy)
        if not t:
            continue
        (tareas[-1].subtareas if es_sub else tareas).append(t)
    return tareas


def cuerpo(t: Tarea, proyectos: dict[str, str], etiquetas: dict[str, str]) -> tuple[dict, list[str]]:
    """(cuerpo para POST /tasks, avisos)."""
    avisos: list[str] = []
    c: dict = {"title": t.titulo}
    if t.estimado_ms:
        c["timeEstimate"] = t.estimado_ms
    if t.proyecto:
        pid = proyectos.get(t.proyecto.lower())
        if pid:
            c["projectId"] = pid
        else:
            avisos.append(f"«{t.titulo}»: el proyecto «{t.proyecto}» no existe; va a la bandeja")
    ids = []
    for e in t.etiquetas:
        tid = etiquetas.get(e.lower())
        (ids.append(tid) if tid else avisos.append(f"«{t.titulo}»: la etiqueta «{e}» no existe; se omite"))
    if ids:
        c["tagIds"] = ids
    if t.dia and t.hora:
        c["dueWithTime"] = int(datetime.fromisoformat(f"{t.dia}T{t.hora}").astimezone().timestamp() * 1000)
    elif t.dia:
        c["dueDay"] = t.dia
    return c, avisos
