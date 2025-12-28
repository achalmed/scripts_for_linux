#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GESTOR DE HARD LINKS - CREADOR                            ║
║                                                                              ║
║  Busca archivos con el mismo nombre y crea hard links agrupando por         ║
║  contenido idéntico. Soporta múltiples grupos para archivos con mismo       ║
║  nombre pero diferente contenido.                                           ║
║                                                                              ║
║  Autor: Edison Achalma                                                       ║
║  Email: achalmaedison@gmail.com                                              ║
║  Versión: 2.0                                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple

# =============================================================================
# CONFIGURACIÓN DE COLORES ANSI
# =============================================================================
class Colors:
    """Códigos de color ANSI para terminal."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Colores adicionales
    GRAY = '\033[90m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_RED = '\033[91m'

# =============================================================================
# CONFIGURACIÓN MANUAL DEL DIRECTORIO
# =============================================================================
# IMPORTANTE: Modifica esta línea para especificar tu directorio
# Si está en None, usará el directorio padre del script
MANUAL_DIRECTORY = "/home/achalmaedison/Documents/publicaciones/"

# =============================================================================
# LISTA DE CARPETAS A EXCLUIR POR DEFECTO
# =============================================================================
EXCLUDED_DIRS = [
    "_extensions",
    "_freeze",
    "_partials",
    ".idea",
    ".github",
    ".obsidian",
    ".git",
    ".vscode",
    ".quarto",
    "_site",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    # Añade más carpetas aquí si es necesario:
    # "node_modules",
    # "dist",
    # "temp",
    # "build",
]

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def print_header(text: str, char: str = "═") -> None:
    """Imprime un encabezado formateado."""
    width = 80
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}{'╔' + char * (width - 2) + '╗'}{Colors.ENDC}")
    padding = (width - len(text) - 2) // 2
    print(f"{Colors.BOLD}{Colors.OKBLUE}║{' ' * padding}{text}{' ' * (width - len(text) - padding - 2)}║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}{'╚' + char * (width - 2) + '╝'}{Colors.ENDC}\n")

def print_separator(char: str = "━") -> None:
    """Imprime un separador."""
    print(f"\n{Colors.GRAY}{char * 80}{Colors.ENDC}\n")

def print_box_info(label: str, value: str, icon: str = "📋") -> None:
    """Imprime información en formato de caja."""
    print(f"{Colors.OKCYAN}{icon} {label}:{Colors.ENDC} {Colors.BOLD}{value}{Colors.ENDC}")

def print_success(text: str) -> None:
    """Imprime mensaje de éxito."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Imprime mensaje de advertencia."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Imprime mensaje de error."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str) -> None:
    """Imprime mensaje informativo."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_skip(text: str) -> None:
    """Imprime mensaje de omisión."""
    print(f"{Colors.GRAY}⏭️  {text}{Colors.ENDC}")

def format_size(size_bytes: int) -> str:
    """Formatea el tamaño de archivo de forma legible."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def calculate_file_hash(filepath: str) -> Optional[str]:
    """
    Calcula el hash SHA-256 de un archivo.
    
    Args:
        filepath: Ruta completa del archivo
        
    Returns:
        str: Hash SHA-256 en formato hexadecimal, o None si hay error
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except OSError as e:
        print_error(f"Error al calcular hash para {filepath}: {e}")
        return None

def get_inode(filepath: str) -> Optional[int]:
    """
    Obtiene el número de inodo de un archivo.
    
    Args:
        filepath: Ruta completa del archivo
        
    Returns:
        int: Número de inodo, o None si hay error
    """
    try:
        return os.stat(filepath).st_ino
    except OSError as e:
        print_error(f"Error al obtener inodo para {filepath}: {e}")
        return None

def get_file_size(filepath: str) -> Optional[int]:
    """
    Obtiene el tamaño de un archivo.
    
    Args:
        filepath: Ruta completa del archivo
        
    Returns:
        int: Tamaño en bytes, o None si hay error
    """
    try:
        return os.stat(filepath).st_size
    except OSError as e:
        print_error(f"Error al obtener tamaño para {filepath}: {e}")
        return None

def get_relative_path(filepath: str, base_dir: str) -> str:
    """Obtiene la ruta relativa de un archivo respecto a un directorio base."""
    try:
        return os.path.relpath(filepath, base_dir)
    except ValueError:
        return filepath

# =============================================================================
# FUNCIÓN PRINCIPAL DE CREACIÓN DE HARD LINKS
# =============================================================================

def create_hardlinks(search_dir: str, filename: str, exclude_dirs: List[str], 
                    auto_mode: bool = False, dry_run: bool = False) -> Dict[str, int]:
    """
    Busca archivos con nombre exacto y los agrupa por contenido (hash).
    Para cada grupo, ofrece crear hard links al primer archivo del grupo.
    
    Args:
        search_dir: Directorio raíz donde buscar
        filename: Nombre exacto del archivo a buscar
        exclude_dirs: Lista de carpetas a excluir
        auto_mode: Si es True, crea todos los grupos sin preguntar
        dry_run: Si es True, solo simula sin hacer cambios
        
    Returns:
        Dict con estadísticas de la operación
    """
    # Normalizar rutas de carpetas excluidas
    exclude_dirs = set(os.path.normpath(os.path.join(search_dir, d)) for d in exclude_dirs)
    
    # Diccionario para agrupar archivos por hash
    hash_groups: Dict[str, List[str]] = defaultdict(list)
    
    # Estadísticas
    stats = {
        'total_files': 0,
        'groups_found': 0,
        'groups_created': 0,
        'groups_skipped': 0,
        'links_created': 0,
        'files_skipped': 0,
        'errors': 0
    }
    
    print_header("GESTOR DE HARD LINKS - ANÁLISIS COMPLETO")
    
    print_box_info("Directorio", search_dir, "📁")
    print_box_info("Archivo buscado", filename, "🔎")
    if exclude_dirs:
        excluded_names = [os.path.basename(d) for d in exclude_dirs]
        print_box_info("Excluyendo", ", ".join(excluded_names), "🚫")
    if dry_run:
        print_warning("MODO SIMULACIÓN: No se realizarán cambios reales")
    
    print_separator()
    print(f"{Colors.OKCYAN}🔍 Escaneando directorio...{Colors.ENDC}\n")
    
    # Fase 1: Recopilar todos los archivos y calcular hashes
    for root, dirs, files in os.walk(search_dir, topdown=True):
        # Excluir directorios
        dirs[:] = [d for d in dirs if os.path.normpath(os.path.join(root, d)) not in exclude_dirs]
        
        if filename in files:
            filepath = os.path.join(root, filename)
            stats['total_files'] += 1
            
            file_hash = calculate_file_hash(filepath)
            if file_hash is None:
                stats['errors'] += 1
                continue
            
            hash_groups[file_hash].append(filepath)
    
    # Verificar si se encontraron archivos
    if stats['total_files'] == 0:
        print_warning(f"No se encontraron archivos con el nombre '{filename}'")
        return stats
    
    print_success(f"Se encontraron {stats['total_files']} archivo(s) con el nombre '{filename}'")
    
    # Contar grupos (excluyendo grupos con un solo archivo)
    groups_with_multiple_files = [group for group in hash_groups.values() if len(group) > 1]
    stats['groups_found'] = len(groups_with_multiple_files)
    
    if stats['groups_found'] == 0:
        print_info("Todos los archivos tienen contenido único, no hay candidatos para hard links")
        return stats
    
    print_success(f"Se encontraron {stats['groups_found']} grupo(s) de archivos con contenido idéntico\n")
    
    # Fase 2: Procesar cada grupo
    group_number = 1
    for file_hash, file_list in hash_groups.items():
        if len(file_list) < 2:
            continue  # Saltar grupos con un solo archivo
        
        print_separator()
        print(f"{Colors.BOLD}{Colors.LIGHT_BLUE}🔍 GRUPO #{group_number}{Colors.ENDC} - {Colors.GRAY}Hash: {file_hash[:16]}...{Colors.ENDC}\n")
        
        # Verificar inodos para determinar qué archivos ya están enlazados
        inodes = {}
        for filepath in file_list:
            inode = get_inode(filepath)
            if inode is not None:
                inodes[filepath] = inode
        
        # Agrupar por inodo
        inode_groups = defaultdict(list)
        for filepath, inode in inodes.items():
            inode_groups[inode].append(filepath)
        
        # Seleccionar archivo fuente (el primero del primer grupo de inodos)
        source_inode = list(inode_groups.keys())[0]
        source_path = inode_groups[source_inode][0]
        
        # Obtener tamaño del archivo
        file_size = get_file_size(source_path)
        size_str = format_size(file_size) if file_size is not None else "desconocido"
        
        print(f"{Colors.OKGREEN}📌 Archivo fuente:{Colors.ENDC} {Colors.BOLD}{get_relative_path(source_path, search_dir)}{Colors.ENDC}")
        print(f"{Colors.GRAY}   Tamaño: {size_str} | Inodo: {source_inode}{Colors.ENDC}\n")
        
        # Archivos que ya son hard links del fuente
        already_linked = [f for f in inode_groups[source_inode] if f != source_path]
        
        # Archivos candidatos para crear hard links
        candidates = [f for f in file_list if f not in inode_groups[source_inode]]
        
        if already_linked:
            print(f"{Colors.GRAY}⏭️  Archivos ya enlazados ({len(already_linked)}):{Colors.ENDC}")
            for filepath in already_linked:
                print(f"{Colors.GRAY}   • {get_relative_path(filepath, search_dir)}{Colors.ENDC}")
            print()
        
        if not candidates:
            print_info("Todos los archivos de este grupo ya están enlazados")
            stats['files_skipped'] += len(already_linked)
            group_number += 1
            continue
        
        print(f"{Colors.OKCYAN}📋 Archivos a enlazar ({len(candidates)}):{Colors.ENDC}")
        for i, filepath in enumerate(candidates, 1):
            print(f"{Colors.OKCYAN}   {i}. {get_relative_path(filepath, search_dir)}{Colors.ENDC}")
        print()
        
        # Preguntar confirmación (a menos que sea modo automático)
        if not auto_mode and not dry_run:
            response = input(f"{Colors.BOLD}¿Crear hard links para este grupo? [S/n]: {Colors.ENDC}").strip().lower()
            if response in ['n', 'no']:
                print_warning("Grupo omitido por el usuario")
                stats['groups_skipped'] += 1
                group_number += 1
                continue
        
        # Crear hard links
        if dry_run:
            print_info(f"[SIMULACIÓN] Se crearían {len(candidates)} hard link(s)")
            stats['links_created'] += len(candidates)
            stats['groups_created'] += 1
        else:
            success_count = 0
            for filepath in candidates:
                try:
                    os.remove(filepath)
                    os.link(source_path, filepath)
                    print_success(f"Hard link creado: {get_relative_path(filepath, search_dir)}")
                    success_count += 1
                except OSError as e:
                    print_error(f"Error al crear hard link para {get_relative_path(filepath, search_dir)}: {e}")
                    stats['errors'] += 1
            
            stats['links_created'] += success_count
            if success_count > 0:
                stats['groups_created'] += 1
        
        stats['files_skipped'] += len(already_linked)
        group_number += 1
    
    return stats

def print_summary(stats: Dict[str, int]) -> None:
    """Imprime un resumen de las operaciones realizadas."""
    print_separator()
    print_header("RESUMEN DE OPERACIONES")
    
    print(f"{Colors.BOLD}{Colors.OKBLUE}╠{'═' * 78}╣{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}  {Colors.OKGREEN}✅ Grupos creados:{Colors.ENDC} {Colors.BOLD}{stats['groups_created']}{Colors.ENDC}" + " " * (67 - len(str(stats['groups_created']))) + f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}  {Colors.OKCYAN}📝 Hard links creados:{Colors.ENDC} {Colors.BOLD}{stats['links_created']}{Colors.ENDC}" + " " * (61 - len(str(stats['links_created']))) + f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}  {Colors.GRAY}⏭️  Archivos omitidos:{Colors.ENDC} {Colors.BOLD}{stats['files_skipped']}{Colors.ENDC} (ya eran hard links)" + " " * (37 - len(str(stats['files_skipped']))) + f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}  {Colors.WARNING}⚠️  Grupos omitidos:{Colors.ENDC} {Colors.BOLD}{stats['groups_skipped']}{Colors.ENDC}" + " " * (59 - len(str(stats['groups_skipped']))) + f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}")
    if stats['errors'] > 0:
        print(f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}  {Colors.FAIL}❌ Errores:{Colors.ENDC} {Colors.BOLD}{stats['errors']}{Colors.ENDC}" + " " * (67 - len(str(stats['errors']))) + f"{Colors.BOLD}{Colors.OKBLUE}║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}╚{'═' * 78}╝{Colors.ENDC}")
    
    # Mensaje final
    if stats['groups_created'] > 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✨ ¡Proceso completado exitosamente!{Colors.ENDC}")
        print(f"{Colors.GRAY}   Usa 'detect_hardlinks_tree.sh' para verificar los enlaces creados{Colors.ENDC}\n")
    elif stats['groups_skipped'] > 0:
        print(f"\n{Colors.WARNING}ℹ️  Proceso completado sin crear enlaces (grupos omitidos por el usuario){Colors.ENDC}\n")
    else:
        print(f"\n{Colors.OKCYAN}ℹ️  No se requirieron cambios{Colors.ENDC}\n")

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Función principal que maneja argumentos y ejecuta el script."""
    parser = argparse.ArgumentParser(
        description="Busca archivos por nombre exacto y crea hard links agrupando por contenido idéntico.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BOLD}Ejemplos de uso:{Colors.ENDC}
  {Colors.OKCYAN}# Modo interactivo (pregunta para cada grupo){Colors.ENDC}
  python create_hardlinks.py _metadata.yml
  
  {Colors.OKCYAN}# Modo automático (crea todos los grupos sin preguntar){Colors.ENDC}
  python create_hardlinks.py _metadata.yml --auto
  
  {Colors.OKCYAN}# Modo simulación (no hace cambios reales){Colors.ENDC}
  python create_hardlinks.py _metadata.yml --dry-run
  
  {Colors.OKCYAN}# Con exclusiones personalizadas{Colors.ENDC}
  python create_hardlinks.py documento.py --exclude temp build dist
        """
    )
    
    parser.add_argument("filename", 
                       help="Nombre exacto del archivo a buscar (ej. '_metadata.yml', 'config.py')")
    parser.add_argument("--exclude", nargs="*", default=None,
                       help="Carpetas a excluir (adicionales o reemplazo de las predefinidas)")
    parser.add_argument("--auto", action="store_true",
                       help="Modo automático: crear todos los grupos sin preguntar")
    parser.add_argument("--dry-run", action="store_true",
                       help="Modo simulación: mostrar qué se haría sin hacer cambios")
    parser.add_argument("--no-color", action="store_true",
                       help="Desactivar colores en la salida")
    
    args = parser.parse_args()
    
    # Desactivar colores si se solicita
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('__'):
                setattr(Colors, attr, '')
    
    # Determinar directorios a excluir
    if args.exclude is not None:
        exclude_dirs = args.exclude
    else:
        exclude_dirs = EXCLUDED_DIRS
    
    # Determinar el directorio de búsqueda
    if MANUAL_DIRECTORY is not None:
        search_dir = os.path.abspath(MANUAL_DIRECTORY)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_dir = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Verificar que el directorio existe
    if not os.path.isdir(search_dir):
        print_error(f"El directorio '{search_dir}' no existe.")
        sys.exit(1)
    
    # Ejecutar creación de hard links
    try:
        stats = create_hardlinks(search_dir, args.filename, exclude_dirs, 
                                args.auto, args.dry_run)
        print_summary(stats)
        
        # Código de salida basado en resultados
        if stats['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Operación cancelada por el usuario{Colors.ENDC}\n")
        sys.exit(130)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()