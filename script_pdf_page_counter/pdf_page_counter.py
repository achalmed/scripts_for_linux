#!/usr/bin/env python3
"""
Script para contar páginas de archivos PDF de forma recursiva
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import argparse

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Error: PyPDF2 no está instalado.")
    print("Por favor, instala con: pip install PyPDF2 openpyxl --break-system-packages")
    sys.exit(1)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
except ImportError:
    print("Error: openpyxl no está instalado.")
    print("Por favor, instala con: pip install PyPDF2 openpyxl --break-system-packages")
    sys.exit(1)


def contar_paginas_pdf(ruta_pdf: str) -> int:
    """
    Cuenta el número de páginas de un archivo PDF.
    
    Args:
        ruta_pdf: Ruta al archivo PDF
        
    Returns:
        Número de páginas del PDF, o -1 si hay error
    """
    try:
        reader = PdfReader(ruta_pdf)
        return len(reader.pages)
    except Exception as e:
        print(f"⚠️  Error al leer {ruta_pdf}: {str(e)}")
        return -1


def buscar_pdfs(directorio: str, solo_index: bool = True) -> List[Tuple[str, int]]:
    """
    Busca archivos PDF recursivamente en un directorio.
    
    Args:
        directorio: Directorio raíz donde buscar
        solo_index: Si es True, solo busca archivos llamados 'index.pdf'
        
    Returns:
        Lista de tuplas (ruta_pdf, numero_paginas)
    """
    resultados = []
    directorio_path = Path(directorio)
    
    if not directorio_path.exists():
        print(f"❌ Error: El directorio '{directorio}' no existe.")
        return resultados
    
    print(f"🔍 Buscando PDFs en: {directorio}")
    print(f"📋 Modo: {'Solo index.pdf' if solo_index else 'Todos los PDFs'}")
    print("=" * 70)
    
    # Patrón de búsqueda
    patron = "**/index.pdf" if solo_index else "**/*.pdf"
    
    # Buscar archivos
    for pdf_path in directorio_path.glob(patron):
        if pdf_path.is_file():
            ruta_relativa = str(pdf_path.relative_to(directorio_path))
            paginas = contar_paginas_pdf(str(pdf_path))
            
            if paginas > 0:
                resultados.append((ruta_relativa, paginas))
                print(f"✓ {ruta_relativa}: {paginas} página(s)")
            else:
                resultados.append((ruta_relativa, 0))
                print(f"✗ {ruta_relativa}: Error al leer")
    
    return resultados


def crear_excel(resultados: List[Tuple[str, int]], archivo_salida: str):
    """
    Crea un archivo Excel con los resultados.
    
    Args:
        resultados: Lista de tuplas (ruta_pdf, numero_paginas)
        archivo_salida: Nombre del archivo Excel de salida
    """
    # Crear libro de trabajo
    wb = Workbook()
    ws = wb.active
    ws.title = "Conteo de Páginas"
    
    # Estilos
    header_font = Font(bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Encabezados
    ws['A1'] = "Ruta del Archivo"
    ws['B1'] = "Número de Páginas"
    
    # Aplicar estilos a encabezados
    for cell in ['A1', 'B1']:
        ws[cell].font = header_font
        ws[cell].fill = header_fill
        ws[cell].alignment = header_alignment
    
    # Agregar datos
    for idx, (ruta, paginas) in enumerate(resultados, start=2):
        ws[f'A{idx}'] = ruta
        ws[f'B{idx}'] = paginas
        ws[f'B{idx}'].alignment = Alignment(horizontal="center")
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 80
    ws.column_dimensions['B'].width = 20
    
    # Agregar fila de totales
    fila_total = len(resultados) + 2
    ws[f'A{fila_total}'] = "TOTAL"
    ws[f'A{fila_total}'].font = Font(bold=True)
    ws[f'B{fila_total}'] = f"=SUM(B2:B{fila_total-1})"
    ws[f'B{fila_total}'].font = Font(bold=True)
    ws[f'B{fila_total}'].alignment = Alignment(horizontal="center")
    
    # Guardar archivo
    wb.save(archivo_salida)
    print(f"\n✅ Archivo Excel creado: {archivo_salida}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Contador de páginas PDF recursivo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Contar solo archivos index.pdf en _site
  %(prog)s _site
  
  # Contar todos los PDFs en _site
  %(prog)s _site --todos
  
  # Especificar archivo de salida personalizado
  %(prog)s _site -o reporte_pdfs.xlsx
  
  # Contar PDFs en múltiples directorios
  %(prog)s directorio1 directorio2
        """
    )
    
    parser.add_argument(
        'directorios',
        nargs='+',
        help='Directorio(s) donde buscar archivos PDF'
    )
    
    parser.add_argument(
        '-t', '--todos',
        action='store_true',
        help='Buscar todos los archivos PDF (no solo index.pdf)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='conteo_paginas_pdf.xlsx',
        help='Nombre del archivo Excel de salida (default: conteo_paginas_pdf.xlsx)'
    )
    
    args = parser.parse_args()
    
    print("📊 Contador de Páginas PDF")
    print("=" * 70)
    
    # Procesar cada directorio
    todos_resultados = []
    for directorio in args.directorios:
        resultados = buscar_pdfs(directorio, solo_index=not args.todos)
        todos_resultados.extend(resultados)
        print()
    
    # Verificar si hay resultados
    if not todos_resultados:
        print("⚠️  No se encontraron archivos PDF.")
        return
    
    # Crear reporte
    print("=" * 70)
    print(f"📄 Total de archivos encontrados: {len(todos_resultados)}")
    total_paginas = sum(paginas for _, paginas in todos_resultados)
    print(f"📑 Total de páginas: {total_paginas}")
    print()
    
    # Crear archivo Excel
    crear_excel(todos_resultados, args.output)
    print(f"\n✨ Proceso completado exitosamente!")


if __name__ == "__main__":
    main()
