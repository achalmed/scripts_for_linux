"""CLI argument parsing for dni-a-copia.

Defines every flag in one place; main.py only consumes the parsed
namespace. Help texts are in Spanish (user-facing), per repo convention.
"""
from __future__ import annotations

import argparse

import config

_EPILOG = """\
Ejemplos:
  # Reproducir la copia por defecto (DNI 28250954) -> Word en la carpeta del DNI
  python3 main.py

  # Cualquier DNI: anverso + reverso, indicando salida y nombre base
  python3 main.py --front frente.jpg --back reverso.jpg \\
      --output-dir ~/copias --name dni_juan

  # Generar tambien el PDF, listo para imprimir a tamano real
  python3 main.py --to-pdf

  # Alta resolucion (por defecto 600 dpi con restauracion) a otra resolucion
  python3 main.py --dpi 450 --to-pdf

  # Sin restauracion (acabado anterior, mas rapido)
  python3 main.py --no-enhance

  # Guardar ademas las PNG de cada cara (anverso/reverso) junto al Word
  python3 main.py --save-caras

  # Simulacion: ver que se generaria sin escribir nada
  python3 main.py --dry-run --verbose
"""


def build_argument_parser() -> argparse.ArgumentParser:
    """Builds the full parser: input images + output/render/general flags."""
    parser = argparse.ArgumentParser(
        prog=config.APP_NAME,
        description=("Arma una copia limpia, a tamano real, del anverso y "
                     "reverso de un DNI (endereza, recorta, blanquea el fondo, "
                     "corrige color y centra ambas caras en A4) como Word y, "
                     "opcionalmente, PDF."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # re-declared below so the help text is in Spanish
    )

    io_group = parser.add_argument_group("Entrada y salida")
    io_group.add_argument(
        "--front", default=config.DEFAULT_FRONT, metavar="IMG",
        help="imagen del anverso (por defecto: la del DNI 28250954)")
    io_group.add_argument(
        "--back", default=config.DEFAULT_BACK, metavar="IMG",
        help="imagen del reverso (por defecto: la del DNI 28250954)")
    io_group.add_argument(
        "-o", "--output-dir", default=config.DEFAULT_OUTPUT_DIR, metavar="DIR",
        help="directorio donde dejar el Word/PDF (por defecto: %(default)s)")
    io_group.add_argument(
        "-n", "--name", default=config.DEFAULT_NAME, metavar="NOMBRE",
        help="nombre base de los archivos de salida (por defecto: %(default)s)")

    render_group = parser.add_argument_group("Render")
    render_group.add_argument(
        "--dpi", type=int, default=config.DEFAULT_DPI, metavar="N",
        help="resolucion de las imagenes (por defecto: %(default)s)")
    render_group.add_argument(
        "--to-pdf", action="store_true", default=config.DEFAULT_TO_PDF,
        help="ademas del Word, exporta a PDF con LibreOffice")
    render_group.add_argument(
        "--no-enhance", action="store_false", dest="enhance",
        default=config.DEFAULT_ENHANCE,
        help="desactiva la restauracion (de-JPEG/denoise/realce hi-res)")
    render_group.add_argument(
        "--rotate", choices=config.ROTATE_CHOICES, default=config.DEFAULT_ROTATE,
        metavar="MODO",
        help="orientacion de las caras: auto (def.) o grados CCW 0/90/180/270")
    render_group.add_argument(
        "--no-perspective", action="store_false", dest="perspective",
        default=config.DEFAULT_PERSPECTIVE,
        help="desactiva la correccion de perspectiva (keystone)")
    render_group.add_argument(
        "--pre-cropped", action="store_true", dest="pre_cropped",
        default=config.DEFAULT_PRE_CROPPED,
        help="la imagen ya es el DNI recortado y plano (DNIe/escaneo): omite "
             "deteccion, perspectiva, recorte y balance de color")
    render_group.add_argument(
        "--grayscale", "--bn", action="store_true", dest="grayscale",
        default=config.DEFAULT_GRAYSCALE,
        help="salida en blanco y negro (escala de grises)")
    render_group.add_argument(
        "--save-caras", action="store_true", default=config.DEFAULT_SAVE_FACES,
        help="guarda tambien las PNG de cada cara junto al Word")

    general_group = parser.add_argument_group("Generales")
    general_group.add_argument(
        "-d", "--dry-run", action="store_true",
        help="simula: muestra que se generaria sin escribir nada")
    general_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="salida detallada (nivel DEBUG)")
    general_group.add_argument(
        "--version", action="version",
        version=f"{config.APP_NAME} {config.VERSION}",
        help="muestra la version y sale")
    general_group.add_argument(
        "-h", "--help", action="help",
        help="muestra esta ayuda y sale")
    return parser
