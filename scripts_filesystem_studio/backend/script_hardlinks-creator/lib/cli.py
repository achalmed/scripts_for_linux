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

  # Modo batch: procesar una lista de nombres (uno por línea, '#' comenta)
  python main.py --batch archivos.txt

  # Batch simulado y sin confirmaciones
  python main.py --batch archivos.txt --dry-run
  python main.py --batch archivos.txt --auto

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

    # Un target obligatorio: un nombre suelto O un listado batch, nunca ambos.
    target = parser.add_mutually_exclusive_group(required=True)

    target.add_argument(
        "filename",
        nargs="?",
        help="Nombre exacto del archivo a buscar (ej. '_metadata.yml', '.editorconfig')",
    )

    target.add_argument(
        "--batch",
        "-b",
        metavar="FILE",
        help=(
            "Archivo de texto con un nombre por línea. Se ignoran líneas vacías, "
            "espacios sobrantes y líneas que comienzan con '#'"
        ),
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
