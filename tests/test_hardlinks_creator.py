"""tests/test_hardlinks_creator.py — exclusiones del creador de hardlinks a cualquier profundidad (2026-10-08).

Con la búsqueda en el hub, los pubs anidados (`_pubs/<pub>/_site`, `_pubs/<pub>/_extensions`) quedaban dentro porque
las exclusiones solo valían en la raíz; un nombre suelto excluye ahora la carpeta donde esté."""
import os
import sys
from pathlib import Path

CREADOR = Path(__file__).resolve().parents[1] / "script_hardlinks-creator"
sys.path.insert(0, str(CREADOR))

from lib.scanner import build_exclusion_set, scan_files  # noqa: E402


def _arbol(tmp_path):
    for rel in ("assets/a.css", "_pubs/p1/assets/a.css", "_pubs/p1/_site/assets/a.css",
                "_pubs/p1/_extensions/x/a.css", "_site/a.css", "solo/aqui/a.css", "_partials/a.css"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("igual\n", encoding="utf-8")


def test_nombre_suelto_excluye_a_cualquier_profundidad(tmp_path):
    _arbol(tmp_path)
    excl = build_exclusion_set(str(tmp_path), ["_site", "_extensions/", "solo/aqui"])
    grupos = scan_files(str(tmp_path), "a.css", excl)
    rutas = sorted(os.path.relpath(r, tmp_path) for g in grupos.values() for r in g)
    assert rutas == ["_partials/a.css", "_pubs/p1/assets/a.css", "assets/a.css"]


def test_ruta_con_barra_solo_excluye_esa_carpeta(tmp_path):
    _arbol(tmp_path)
    excl = build_exclusion_set(str(tmp_path), ["_pubs/p1/assets"])
    rutas = {os.path.relpath(r, tmp_path) for g in scan_files(str(tmp_path), "a.css", excl).values() for r in g}
    assert "_pubs/p1/assets/a.css" not in rutas and "assets/a.css" in rutas
