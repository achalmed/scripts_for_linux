"""CLI argument parsing for firma-digital.

Defines every flag in one place; main.py only consumes the parsed
namespace. Help texts are in Spanish (user-facing), following the
project convention.
"""
from __future__ import annotations

import argparse

import config

_EPILOG = """\
Ejemplos:
  # Conversión completa: SVG vectorial + PNG 600 ppp transparente + fondo blanco
  python3 main.py firma.jpg

  # Elegir carpeta y nombre de salida
  python3 main.py firma.jpg -o ~/firmas -n firma_juan_digital

  # Foto con motas de fondo aisladas: sube el filtro de componentes pequeños
  python3 main.py firma_ruidosa.jpg --area-motas 2000 --qa-dir ./qa

  # Solo la versión ráster limpia (rápido, sin vectorizar)
  python3 main.py firma.jpg --solo-mascara

  # Firma tenue: baja el umbral para no perder trazos claros
  python3 main.py firma_clara.jpg --factor-umbral 0.85

  # Simulación: ver el plan (ángulo, cobertura, archivos) sin escribir nada
  python3 main.py firma.jpg --dry-run
"""


def positive_int(raw: str) -> int:
    """argparse type: strictly positive integer."""
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{raw}' no es un número entero")
    if value < 1:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return value


def positive_float(raw: str) -> float:
    """argparse type: strictly positive real number."""
    try:
        value = float(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{raw}' no es un número")
    if value <= 0:
        raise argparse.ArgumentTypeError("debe ser mayor que 0")
    return value


def unit_float(raw: str) -> float:
    """argparse type: real number in the (0, 1] range (a fraction)."""
    try:
        value = float(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{raw}' no es un número")
    if not 0 < value <= 1:
        raise argparse.ArgumentTypeError("debe estar entre 0 (excl.) y 1")
    return value


def build_argument_parser() -> argparse.ArgumentParser:
    """Builds the full parser: input + tuning/output/general flag groups."""
    parser = argparse.ArgumentParser(
        prog=config.APP_NAME,
        description=("Convierte la foto de una firma manuscrita en una firma "
                     "digital limpia: SVG vectorial escalable y PNG de alta "
                     "resolución con fondo transparente."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # re-declared below so the help text is in Spanish
    )
    parser.add_argument(
        "entrada", nargs="?", metavar="FOTO",
        help="foto de la firma a procesar (JPG, PNG...)")

    salida = parser.add_argument_group("Salida")
    salida.add_argument(
        "-o", "--output-dir", metavar="DIR", default=None,
        help=("carpeta donde escribir las salidas "
              "(por defecto: la misma carpeta de la foto)"))
    salida.add_argument(
        "-n", "--nombre", metavar="NOMBRE", default=None,
        help=("nombre base de los archivos generados, sin extensión "
              f"(por defecto: <foto>{config.SUFIJO_NOMBRE})"))
    salida.add_argument(
        "--solo-mascara", action="store_true",
        help=("omite la vectorización: genera solo el PNG ráster limpio "
              "(mucho más rápido; no produce SVG)"))
    salida.add_argument(
        "--qa-dir", metavar="DIR", default=None,
        help=("guarda imágenes de control (mapa de tinta, máscara, ráster del "
              "vector) en esta carpeta para revisar la calidad"))

    ajuste = parser.add_argument_group("Ajuste del procesamiento")
    ajuste.add_argument(
        "--escala", type=positive_int, default=config.ESCALA_TRABAJO,
        metavar="N",
        help=("factor de reescalado de trabajo; mayor = más nítido pero más "
              "lento (por defecto: %(default)s)"))
    ajuste.add_argument(
        "--factor-umbral", type=unit_float, default=config.FACTOR_UMBRAL_OTSU,
        metavar="F",
        help=("multiplicador del umbral de Otsu (<1 conserva trazos tenues) "
              "(por defecto: %(default)s)"))
    ajuste.add_argument(
        "--hist-baja", type=unit_float, default=config.FRACCION_HISTERESIS_BAJA,
        metavar="F",
        help=("umbral bajo de la histéresis como fracción del umbral "
              "(por defecto: %(default)s)"))
    ajuste.add_argument(
        "--area-motas", type=positive_int, default=config.AREA_MINIMA_MOTAS,
        metavar="N",
        help=("área mínima (px² a escala de trabajo) para conservar un "
              "componente; súbela para quitar motas de fondo aisladas "
              "(por defecto: %(default)s)"))
    ajuste.add_argument(
        "--ancho-mm", type=positive_float, default=config.ANCHO_FISICO_MM,
        metavar="MM",
        help=("ancho físico declarado en el SVG, en milímetros "
              "(por defecto: %(default)s)"))
    ajuste.add_argument(
        "--sin-enderezar", action="store_true",
        help="no corregir la inclinación de la firma")

    general = parser.add_argument_group("Generales")
    general.add_argument(
        "-d", "--dry-run", action="store_true",
        help=("simula: analiza la foto y muestra el plan sin vectorizar ni "
              "escribir archivos"))
    general.add_argument(
        "-v", "--verbose", action="store_true",
        help="salida detallada (nivel DEBUG)")
    general.add_argument(
        "--version", action="version",
        version=f"{config.APP_NAME} {config.VERSION}",
        help="muestra la versión y sale")
    general.add_argument(
        "-h", "--help", action="help",
        help="muestra esta ayuda y sale")
    return parser
