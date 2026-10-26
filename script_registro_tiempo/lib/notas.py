"""script_registro_tiempo/lib/notas.py — las notas .md del vault como tareas de lectura en Super Productivity.

Por cada carpeta de `notas_a_sp.carpetas` (relativas a ~/Documents), una tarea madre por subcarpeta y una subtarea por
nota, con su título (`titulo` del frontmatter o el nombre del archivo), una estimación de lectura por número de
palabras y, en las notas de la tarea, la ruta y el enlace que la abre en Obsidian. Así el autor elige una nota y arranca
el temporizador; el tiempo queda en esa subtarea. La ruta en las notas es la clave: una nota ya presente no se repite,
y una que cambió de nombre aparece como nueva (la vieja se informa, no se borra).
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

PALABRAS_POR_MINUTO = 200   # lectura de estudio, más lenta que la recreativa: criterio de partida, se ajusta con el registro
MARCA = "Archivo: "
RE_TITULO = re.compile(r"^titulo:\s*[\"']?(.+?)[\"']?\s*$", re.MULTILINE)
RE_FRONT = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


RE_CALIBRE = re.compile(r"^calibre_id:\s*(\d+)\s*$", re.MULTILINE)
PUNTERO_MAX_PALABRAS = 300   # una nota que solo apunta a su texto en Calibre no se estima por sus palabras


@dataclass
class Nota:
    ruta: str          # relativa a ~/Documents
    titulo: str
    minutos: int       # 0 = sin estimar (el texto completo está en Calibre)
    grupo: str
    calibre_id: str = ""


def _frontmatter(texto: str) -> str:
    m = RE_FRONT.match(texto)
    return m.group(0) if m else ""


def _titulo(texto: str, archivo: Path) -> str:
    t = RE_TITULO.search(_frontmatter(texto))
    if t:
        return t.group(1).strip()
    nombre = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", archivo.stem)
    return nombre.replace("-", " ").capitalize()


def _nombre_carpeta(carpeta: Path) -> str:
    """El título del README de la carpeta hasta los dos puntos («24 Economía y políticas públicas»), o su nombre."""
    readme = carpeta / "README.md"
    if readme.is_file():
        t = RE_TITULO.search(_frontmatter(readme.read_text(encoding="utf-8", errors="replace")))
        if t:
            return t.group(1).split(":")[0].strip()
    return re.sub(r"^(\d+)-", r"\1 ", carpeta.name).replace("-", " ").capitalize()


def _grupo(archivo: Path, base: Path) -> str:
    """La carpeta inmediata de la nota: una tarea madre por carpeta, con el nombre de su índice."""
    return _nombre_carpeta(archivo.parent)


def leer(raiz: Path, carpetas: list[str]) -> list[Nota]:
    notas: list[Nota] = []
    for c in carpetas:
        base = raiz / c
        for archivo in sorted(base.rglob("*.md")):
            if archivo.name == "README.md" or any(p.startswith(".") for p in archivo.relative_to(base).parts):
                continue
            texto = archivo.read_text(encoding="utf-8", errors="replace")
            palabras = len(RE_FRONT.sub("", texto).split())
            calibre = RE_CALIBRE.search(_frontmatter(texto))
            puntero = bool(calibre) and palabras <= PUNTERO_MAX_PALABRAS
            notas.append(Nota(ruta=str(archivo.relative_to(raiz)), titulo=_titulo(texto, archivo),
                              minutos=0 if puntero else max(5, round(palabras / PALABRAS_POR_MINUTO / 5) * 5),
                              grupo=_grupo(archivo, base), calibre_id=calibre.group(1) if calibre else ""))
    return notas


def texto_notas(n: Nota, vault: str) -> str:
    enlace = "obsidian://open?" + urllib.parse.urlencode({"vault": vault, "file": n.ruta[:-3]}, quote_via=urllib.parse.quote)
    lineas = [f"{MARCA}{n.ruta}", f"Abrir en Obsidian: {enlace}"]
    if n.minutos:
        lineas.append(f"Estimación: {n.minutos} min a {PALABRAS_POR_MINUTO} palabras por minuto.")
    else:
        lineas.append(f"La nota es un puntero: el texto completo está en Calibre (id {n.calibre_id}); se lee allí "
                      "con el temporizador de esta tarea en marcha.")
    return "\n".join(lineas)


def ruta_de(tarea: dict) -> str:
    for linea in (tarea.get("notes") or "").splitlines():
        if linea.startswith(MARCA):
            return linea[len(MARCA):].strip()
    return ""
