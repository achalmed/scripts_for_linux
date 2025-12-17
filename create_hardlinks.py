import os
import argparse
import hashlib
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN MANUAL DEL DIRECTORIO
# =============================================================================
# IMPORTANTE: Descomenta y modifica la siguiente línea para especificar tu directorio manualmente
# Si está comentada (con #), el script usará el directorio padre del script
# Ejemplos:
#   MANUAL_DIRECTORY = "/home/usuario/mi_proyecto"
#   MANUAL_DIRECTORY = r"C:\Users\Edison\Documentos\proyecto"
#   MANUAL_DIRECTORY = None  # Usar directorio padre del script (comportamiento predeterminado)

MANUAL_DIRECTORY = "/home/achalmaedison/Documents/publicaciones/"  # <-- MODIFICA ESTA LÍNEA con tu ruta o déjala en None

# =============================================================================
# INSTRUCCIONES DE USO
# =============================================================================
# Uso básico:
#   python create_hardlinks.py _contenido-inicio.qmd
#   python create_hardlinks.py documento.py
# 
# Con exclusiones personalizadas:
#   python create_hardlinks.py documento.py --exclude temp build
# =============================================================================

# Lista de carpetas a excluir por defecto (puedes añadir más aquí)
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
    # Añade más carpetas aquí si es necesario:
    # "node_modules",
    # "dist",
    # "temp",
    # "build",
]


def calculate_file_hash(filepath):
    """
    Calcula el hash SHA-256 de un archivo para verificar su contenido.
    
    Args:
        filepath: Ruta completa del archivo
        
    Returns:
        str: Hash SHA-256 en formato hexadecimal, o None si hay error
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Leer el archivo en fragmentos de 4KB para manejar archivos grandes eficientemente
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except OSError as e:
        print(f"❌ Error al calcular hash para {filepath}: {e}")
        return None


def get_inode(filepath):
    """
    Obtiene el número de inodo de un archivo.
    Los hard links comparten el mismo inodo.
    
    Args:
        filepath: Ruta completa del archivo
        
    Returns:
        int: Número de inodo, o None si hay error
    """
    try:
        return os.stat(filepath).st_ino
    except OSError as e:
        print(f"❌ Error al obtener inodo para {filepath}: {e}")
        return None


def create_hardlinks(search_dir, filename, exclude_dirs):
    """
    Busca archivos con nombre exacto recursivamente y reemplaza los encontrados 
    con hard links al primer archivo encontrado (fuente principal), si:
    - Los hash coinciden (mismo contenido)
    - Los inodos difieren (no son ya hard links)
    
    Excluye las carpetas especificadas en exclude_dirs.
    
    Args:
        search_dir: Directorio raíz donde buscar
        filename: Nombre exacto del archivo a buscar
        exclude_dirs: Lista de carpetas a excluir
    """
    # Normalizar rutas de carpetas excluidas para comparación precisa
    exclude_dirs = set(os.path.normpath(os.path.join(search_dir, d)) for d in exclude_dirs)
    
    # Variables para el archivo fuente principal
    source_path = None
    source_hash = None
    source_inode = None
    
    print(f"\n🔍 Iniciando búsqueda recursiva de '{filename}'...\n")
    
    # Recorrer recursivamente el directorio de búsqueda
    for root, dirs, files in os.walk(search_dir, topdown=True):
        # Excluir directorios especificados (modifica dirs in-place)
        dirs[:] = [d for d in dirs if os.path.normpath(os.path.join(root, d)) not in exclude_dirs]
        
        # Buscar archivos que coincidan exactamente con el nombre
        if filename in files:
            current_path = os.path.join(root, filename)
            
            try:
                # Si no tenemos un archivo fuente principal, usar el primero encontrado
                if source_path is None:
                    source_path = current_path
                    source_hash = calculate_file_hash(source_path)
                    source_inode = get_inode(source_path)
                    
                    if source_hash is None or source_inode is None:
                        print(f"❌ No se puede usar {source_path} como fuente principal: Error al obtener hash o inodo.")
                        return
                    
                    print(f"📌 Archivo fuente principal: {source_path}")
                    print(f"   Hash: {source_hash[:16]}...")
                    print(f"   Inodo: {source_inode}\n")
                    continue
                
                # Verificar inodo del archivo actual
                current_inode = get_inode(current_path)
                if current_inode is None:
                    print(f"❌ No se puede procesar {current_path}: Error al obtener inodo.")
                    continue
                
                # Si tienen el mismo inodo, ya es un hard link
                if current_inode == source_inode:
                    print(f"⏭️  Omitiendo {current_path}")
                    print(f"   → Ya es un hard link del archivo fuente (inodo: {current_inode})")
                    continue
                
                # Comparar hash para verificar si el contenido es idéntico
                current_hash = calculate_file_hash(current_path)
                if current_hash is None:
                    print(f"❌ No se puede procesar {current_path}: Error al calcular hash.")
                    continue
                
                if current_hash != source_hash:
                    print(f"⚠️  Advertencia: {current_path}")
                    print(f"   → Contenido diferente detectado (hash no coincide), omitiendo reemplazo.")
                    continue
                
                # Reemplazar el archivo actual con un hard link al archivo fuente
                os.remove(current_path)
                os.link(source_path, current_path)
                print(f"✅ Hard link creado: {current_path}")
                print(f"   → Enlazado a: {source_path}")
            
            except OSError as e:
                print(f"❌ Error al crear hard link para {current_path}: {e}")
    
    print(f"\n✨ Proceso completado.\n")


def main():
    """Función principal que maneja argumentos y ejecuta el script."""
    parser = argparse.ArgumentParser(
        description="Busca archivos por nombre exacto y reemplaza con hard links al primer archivo encontrado.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python create_hardlinks.py _contenido-inicio.qmd
  python create_hardlinks.py documento.py --exclude temp build dist
        """
    )
    parser.add_argument("filename", 
                       help="Nombre exacto del archivo a buscar (ej. '_contenido-final.qmd', 'documento.py')")
    parser.add_argument("--exclude", nargs="*", default=EXCLUDED_DIRS, 
                       help="Carpetas a excluir (adicionales a las predefinidas)")
    
    args = parser.parse_args()
    
    # Determinar el directorio de búsqueda
    if MANUAL_DIRECTORY is not None:
        # Usar directorio especificado manualmente
        search_dir = os.path.abspath(MANUAL_DIRECTORY)
        print(f"📁 Usando directorio manual especificado: {search_dir}")
    else:
        # Usar directorio padre del script (comportamiento predeterminado)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_dir = os.path.abspath(os.path.join(script_dir, ".."))
        print(f"📁 Usando directorio padre del script: {search_dir}")
    
    # Verificar que el directorio existe
    if not os.path.isdir(search_dir):
        print(f"❌ Error: El directorio '{search_dir}' no existe.")
        return
    
    print(f"🔎 Buscando archivo: '{args.filename}'")
    if args.exclude:
        print(f"🚫 Excluyendo carpetas: {', '.join(args.exclude)}")
    
    create_hardlinks(search_dir, args.filename, args.exclude)


if __name__ == "__main__":
    main()
