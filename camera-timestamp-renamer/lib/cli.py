"""Definición de la interfaz de línea de comandos (argparse con subcomandos).

Cualquier campo de `config.Settings` puede sobreescribirse aquí desde la CLI,
para que puedas ajustar la región de análisis, los umbrales o los workers sin
editar `config.py`.
"""
from __future__ import annotations

import argparse
import dataclasses

from config import APP_NAME, VERSION, Settings, default_settings

_EPILOG = """\
Ejemplos:
  # 1) Analizar sin tocar nada (genera rename_plan.csv y analysis.json)
  python main.py analyze ./fotos

  # 2) Revisar visualmente las lecturas dudosas y las colisiones
  python main.py verify ./fotos

  # 3) Simular el renombrado (por defecto NO cambia nada)
  python main.py apply ./fotos

  # 4) Aplicar de verdad (deja _rename_log.csv y _undo_rename.sh)
  python main.py apply ./fotos --execute

  # 5) Aplicar un plan que editaste a mano
  python main.py apply ./fotos --from-plan rename_plan.csv --execute

  # 6) Deshacer el ultimo renombrado
  python main.py undo ./fotos --execute

  # Ajustar la POSICION del analisis (ej. franja superior completa):
  python main.py analyze ./fotos --crop-left 0 --crop-width 1 --crop-height 0.10
"""


def _add_common(parser: argparse.ArgumentParser) -> None:
    """Añade a un subcomando las flags compartidas (carpeta y ajustes)."""
    parser.add_argument("folder", help="Carpeta con las imágenes")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Salida detallada (DEBUG)")
    parser.add_argument("--workers", type=int,
                        help="Número de procesos en paralelo (0 = todos)")
    parser.add_argument("--limit", type=int,
                        help="Procesar solo las primeras N imágenes (pruebas)")
    parser.add_argument("--log-file", help="Guardar los logs también en este archivo")
    parser.add_argument("--crop-left", type=float, help="Fracción X del recorte (0-1)")
    parser.add_argument("--crop-top", type=float, help="Fracción Y del recorte (0-1)")
    parser.add_argument("--crop-width", type=float, help="Ancho del recorte (0-1)")
    parser.add_argument("--crop-height", type=float, help="Alto del recorte (0-1)")


def build_argument_parser() -> argparse.ArgumentParser:
    """Construye el parser con los subcomandos analyze/apply/verify/undo."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Renombra fotos y videos por la fecha/hora impresa en la imagen.",
        epilog=_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_common(subparsers.add_parser("analyze", help="Analizar sin cambiar nada"))

    apply_parser = subparsers.add_parser("apply", help="Renombrar (simula por defecto)")
    _add_common(apply_parser)
    apply_parser.add_argument("--execute", action="store_true",
                              help="Aplicar de verdad (sin esto solo simula)")
    apply_parser.add_argument("--from-plan",
                              help="Usar un CSV de plan (editado a mano) en vez de re-analizar")

    verify_parser = subparsers.add_parser("verify", help="Montajes de revisión")
    _add_common(verify_parser)
    verify_parser.add_argument("--from-plan", help="Basar los montajes en este CSV")

    undo_parser = subparsers.add_parser("undo", help="Deshacer el último renombrado")
    undo_parser.add_argument("folder", help="Carpeta con las imágenes")
    undo_parser.add_argument("-v", "--verbose", action="store_true")
    undo_parser.add_argument("--log-file")
    undo_parser.add_argument("--execute", action="store_true",
                             help="Aplicar de verdad (sin esto solo simula)")
    return parser


def settings_from_args(args: argparse.Namespace) -> Settings:
    """Fusiona los defaults de config.py con lo que llegó por CLI."""
    # getattr con default None: subcomandos como `undo` no declaran todas
    # estas flags, y su ausencia debe significar "usar el valor por defecto".
    overrides = {
        "workers": getattr(args, "workers", None),
        "limit": getattr(args, "limit", None),
        "crop_left_frac": getattr(args, "crop_left", None),
        "crop_top_frac": getattr(args, "crop_top", None),
        "crop_width_frac": getattr(args, "crop_width", None),
        "crop_height_frac": getattr(args, "crop_height", None),
    }
    applied = {key: value for key, value in overrides.items() if value is not None}
    return dataclasses.replace(default_settings(), **applied)
