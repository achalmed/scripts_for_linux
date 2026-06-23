"""
lib/cli.py — CLI argument parsing for hardlinks-creator.

Centralizing argument definitions here keeps main.py minimal
and makes it trivial to add new flags without touching business logic.
"""

import argparse
from config import VERSION


def build_parser() -> argparse.ArgumentParser:
    """
    Defines all CLI arguments and flags.

    Returns:
        Configured ArgumentParser ready for parse_args().
    """
    parser = argparse.ArgumentParser(
        prog="hardlinks-creator",
        description=(
            "Busca archivos con el mismo nombre, los agrupa por contenido idéntico "
            "(SHA-256) y crea hard links para eliminar duplicados sin perder datos."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Enlazar todos los _metadata.yml con mismo contenido
  python main.py _metadata.yml

  # Simular sin hacer cambios
  python main.py _metadata.yml --dry-run

  # Modo automático (sin confirmación interactiva)
  python main.py _metadata.yml --auto

  # Directorio personalizado
  python main.py _quarto.yml --directory ~/Documents

  # Excluir carpetas adicionales
  python main.py .editorconfig --exclude build dist temp

  # Exportar reporte JSON
  python main.py _metadata.yml --report-json /tmp/report.json

  # Sin colores (para logs, CI/CD)
  python main.py _metadata.yml --no-color
        """,
    )

    parser.add_argument(
        "filename",
        help="Nombre exacto del archivo a buscar (ej. '_metadata.yml', '.editorconfig')",
    )

    parser.add_argument(
        "--directory",
        "-d",
        metavar="DIR",
        help="Directorio raíz donde buscar (sobreescribe DEFAULT_DIRECTORY en config.py)",
    )

    parser.add_argument(
        "--exclude",
        nargs="*",
        metavar="DIR",
        help="Carpetas adicionales a excluir (se suman a las predefinidas en config.py)",
    )

    parser.add_argument(
        "--replace-exclude",
        nargs="*",
        metavar="DIR",
        help="Reemplaza completamente la lista de exclusiones predefinida",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Crear todos los grupos sin confirmación interactiva",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular la operación sin realizar cambios en disco",
    )

    parser.add_argument(
        "--report-json",
        metavar="FILE",
        help="Guardar un reporte JSON de la operación en la ruta indicada",
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Desactivar colores ANSI en la salida"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar mensajes de depuración adicionales",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    return parser
