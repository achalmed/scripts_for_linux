#!/bin/bash

# ============================================
# Script: Detector y Visualizador de Enlaces Duros
# Autor: Edison Achalma
# Descripción: Busca archivos con enlaces duros y los muestra en estructura de árbol
# ============================================

# CONFIGURACIÓN: Directorio de trabajo
# Por defecto usa el directorio actual, pero puedes especificar uno diferente
# Uso: ./script.sh [directorio]
# Ejemplo: ./script.sh /home/usuario/documentos

if [ -z "$1" ]; then
    # Si no se proporciona argumento, usar el directorio actual
    DIRECTORY=$(pwd)
    echo "Usando directorio actual: $DIRECTORY"
else
    # Si se proporciona un argumento, usarlo como directorio de trabajo
    DIRECTORY="$1"
    echo "Usando directorio especificado: $DIRECTORY"
fi

# ============================================
# VALIDACIÓN DEL DIRECTORIO
# ============================================

# Verificar que el directorio existe y es accesible
if [ ! -d "$DIRECTORY" ]; then
    echo "Error: No se puede acceder al directorio '$DIRECTORY'"
    echo "Verifica que:"
    echo "  - La ruta sea correcta"
    echo "  - Tengas permisos de lectura"
    echo "  - El directorio exista"
    exit 1
fi

# ============================================
# PREPARACIÓN DE ARCHIVOS TEMPORALES
# ============================================

# Crear archivo temporal para almacenar información de inodos
# Los inodos son identificadores únicos de archivos en el sistema
TEMP_FILE=$(mktemp)

# ============================================
# BÚSQUEDA DE ENLACES DUROS
# ============================================

echo "Escaneando directorio en busca de enlaces duros..."
echo "Esto puede tardar si hay muchos archivos..."

# Buscar archivos con enlaces duros (más de un enlace) recursivamente
# -type f: solo archivos regulares
# -links +1: archivos con más de un enlace (enlaces duros)
# stat --format="%i %n": muestra inodo y nombre de archivo
find "$DIRECTORY" -type f -links +1 -exec stat --format="%i %n" {} + > "$TEMP_FILE"

# ============================================
# PROCESAMIENTO DE DATOS
# ============================================

# Crear un array asociativo para agrupar archivos por inodo
# Un mismo inodo agrupa todos los enlaces duros del mismo archivo
declare -A inodes

# Leer el archivo temporal línea por línea
while IFS=' ' read -r inode file; do
    # Agrupar archivos por su inodo, separados por punto y coma
    inodes["$inode"]+="$file;"
done < "$TEMP_FILE"

# ============================================
# PRESENTACIÓN DE RESULTADOS
# ============================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Árbol de archivos con enlaces duros                       ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Directorio: $DIRECTORY"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar si se encontraron archivos con enlaces duros
if [ ${#inodes[@]} -eq 0 ]; then
    echo "✓ No se encontraron archivos con enlaces duros en este directorio."
    echo "  Esto significa que no hay archivos duplicados físicamente."
else
    echo "Se encontraron ${#inodes[@]} conjunto(s) de enlaces duros:"
    echo ""
    
    # ============================================
    # FUNCIÓN: Construir árbol jerárquico
    # ============================================
    # Esta función toma una lista de archivos del mismo inodo
    # y los muestra en estructura de árbol
    
    print_hierarchical_tree() {
        local files_string="$1"
        IFS=';' read -ra file_array <<< "$files_string"
        
        # Array para almacenar todas las rutas relativas
        declare -a all_paths
        
        # Recopilar todas las rutas relativas al directorio base
        for file in "${file_array[@]}"; do
            if [ -n "$file" ]; then
                # Convertir a ruta relativa para mejor legibilidad
                local rel_path=$(realpath --relative-to="$DIRECTORY" "$file")
                all_paths+=("$rel_path")
            fi
        done
        
        # Ordenar las rutas alfabéticamente para presentación ordenada
        IFS=$'\n' sorted_paths=($(sort <<<"${all_paths[*]}"))
        unset IFS
        
        # Estructura para evitar imprimir directorios duplicados
        declare -A printed_dirs
        
        # Procesar cada archivo en el conjunto de enlaces
        for path in "${sorted_paths[@]}"; do
            # Dividir la ruta en componentes (directorios y archivo)
            IFS='/' read -ra path_components <<< "$path"
            
            # Construir y mostrar directorios padre si aún no se han mostrado
            local current_path=""
            for ((i=0; i<${#path_components[@]}-1; i++)); do
                if [ $i -eq 0 ]; then
                    current_path="${path_components[$i]}"
                else
                    current_path="$current_path/${path_components[$i]}"
                fi
                
                # Solo mostrar directorio si es la primera vez que aparece
                if [ -z "${printed_dirs[$current_path]}" ]; then
                    printed_dirs["$current_path"]=1
                    
                    # Calcular indentación según profundidad
                    local indent=""
                    for ((j=0; j<=i; j++)); do
                        indent="$indent│   "
                    done
                    
                    # Mostrar directorio con símbolo de carpeta
                    echo "$indent├── ${path_components[$i]}/"
                fi
            done
            
            # Mostrar el archivo con indentación apropiada
            local file_indent=""
            for ((i=0; i<${#path_components[@]}; i++)); do
                file_indent="$file_indent│   "
            done
            
            # Usar símbolo de final de rama para el archivo
            echo "$file_indent└── ${path_components[${#path_components[@]}-1]}"
        done
    }
    
    # ============================================
    # MOSTRAR CADA CONJUNTO DE ENLACES DUROS
    # ============================================
    
    contador=1
    for inode in "${!inodes[@]}"; do
        files=${inodes[$inode]}
        IFS=';' read -ra file_array <<< "$files"
        
        # Obtener el número de enlaces del primer archivo
        link_count=$(ls -l "${file_array[0]}" | awk '{print $2}')
        
        # Obtener tamaño del archivo
        file_size=$(ls -lh "${file_array[0]}" | awk '{print $5}')
        
        echo "─────────────────────────────────────────────────────────────"
        echo "Conjunto #$contador"
        echo "  Inodo: $inode"
        echo "  Enlaces: $link_count"
        echo "  Tamaño: $file_size"
        echo ""
        
        # Mostrar árbol de archivos vinculados
        print_hierarchical_tree "$files"
        echo "└──"
        echo ""
        
        ((contador++))
    done
fi

# ============================================
# LIMPIEZA
# ============================================

# Eliminar archivo temporal
rm "$TEMP_FILE"

# ============================================
# GUÍA DE USO
# ============================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  GUÍA DE GESTIÓN DE ENLACES DUROS                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📖 ¿Qué son los enlaces duros?"
echo "   Son múltiples nombres para el mismo archivo físico."
echo "   Todos comparten el mismo contenido y espacio en disco."
echo ""
echo "🔧 Operaciones disponibles:"
echo ""
echo "   • Eliminar un enlace:"
echo "     rm /ruta/completa/archivo"
echo "     (El archivo permanece mientras exista al menos un enlace)"
echo ""
echo "   • Mover un enlace:"
echo "     mv /ruta/completa/archivo /nueva/ruta/"
echo "     (Los demás enlaces no se ven afectados)"
echo ""
echo "   • Crear un nuevo enlace duro:"
echo "     ln /archivo/existente /nueva/ubicación/nombre"
echo ""
echo "   • Ver información de enlaces:"
echo "     ls -li /ruta/archivo"
echo "     (La primera columna muestra el número de inodo)"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Modificar el contenido afecta a TODOS los enlaces"
echo "   - El archivo se elimina solo cuando se borran TODOS los enlaces"
echo "   - Los enlaces duros no funcionan entre diferentes sistemas de archivos"
echo ""
echo "📝 Para ejecutar en otro directorio:"
echo "   $0 /ruta/al/directorio"
echo ""
