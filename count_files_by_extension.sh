#!/bin/bash

################################################################################
# Script: count_files_by_extension.sh
# Descripción: Analiza recursivamente un directorio y cuenta los archivos
#              agrupados por extensión, mostrando estadísticas detalladas.
# Autor: Edison Achalma
# Fecha: 2024
# Uso: ./count_files_by_extension.sh [directorio]
#      Si no se especifica, usa ~/Documents/biblioteca por defecto
################################################################################

################################################################################
# COLORES PARA MENSAJES
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # Sin color

################################################################################
# CONFIGURACIÓN
################################################################################

# Directorio a analizar (por defecto ~/Documents/biblioteca)
# Se puede pasar como argumento: ./script.sh /ruta/al/directorio
DIRECTORY="${1:-~/Documents/biblioteca}"

# Expandir la tilde (~) a la ruta completa del home
DIRECTORY="${DIRECTORY/#\~/$HOME}"

# Archivo temporal para almacenar las extensiones
TEMP_FILE=$(mktemp)

################################################################################
# FUNCIONES
################################################################################

# Función para mostrar mensajes con formato
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[ADVERTENCIA]${NC} $1"
}

# Función para limpiar archivos temporales al salir
cleanup() {
    rm -f "$TEMP_FILE"
}

# Registrar la función de limpieza para que se ejecute al salir
trap cleanup EXIT

# Función para validar el directorio
validate_directory() {
    if [ ! -d "$DIRECTORY" ]; then
        log_error "El directorio '$DIRECTORY' no existe."
        echo ""
        echo "Uso: $0 [directorio]"
        echo "Ejemplo: $0 ~/Documents"
        exit 1
    fi
    
    # Convertir a ruta absoluta
    DIRECTORY=$(cd "$DIRECTORY" && pwd)
}

# Función para formatear tamaños de archivo
format_size() {
    local size=$1
    if [ $size -lt 1024 ]; then
        echo "${size}B"
    elif [ $size -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1024}")KB"
    elif [ $size -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1048576}")MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1073741824}")GB"
    fi
}

# Función para obtener el tamaño total de archivos por extensión
get_size_by_extension() {
    local ext="$1"
    local total_size=0
    
    if [ "$ext" = "sin_extension" ]; then
        # Buscar archivos sin extensión
        while IFS= read -r file; do
            if [ -f "$file" ]; then
                size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
                total_size=$((total_size + size))
            fi
        done < <(find "$DIRECTORY" -type f ! -name "*.*")
    else
        # Buscar archivos con extensión específica
        while IFS= read -r file; do
            if [ -f "$file" ]; then
                size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
                total_size=$((total_size + size))
            fi
        done < <(find "$DIRECTORY" -type f -iname "*.$ext")
    fi
    
    echo "$total_size"
}

# Función para mostrar el encabezado
show_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}     ${MAGENTA}ANÁLISIS DE ARCHIVOS POR EXTENSIÓN${NC}                           ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Función para contar y clasificar archivos
count_files() {
    log_info "Analizando directorio: ${BLUE}$DIRECTORY${NC}"
    echo ""
    
    # Contar total de archivos primero
    local total_files=$(find "$DIRECTORY" -type f | wc -l)
    
    if [ $total_files -eq 0 ]; then
        log_warning "No se encontraron archivos en el directorio especificado"
        exit 0
    fi
    
    log_info "Escaneando ${YELLOW}$total_files${NC} archivo(s)..."
    echo ""
    
    # Procesar cada archivo y extraer su extensión
    find "$DIRECTORY" -type f | while read -r file; do
        # Extraer solo el nombre del archivo (sin la ruta)
        filename=$(basename "$file")
        
        # Extraer la extensión del archivo (en minúsculas)
        extension=$(echo "${filename##*.}" | tr '[:upper:]' '[:lower:]')
        
        # Si no tiene extensión (el nombre es igual a la "extensión")
        if [ "$extension" = "$filename" ]; then
            extension="sin_extension"
        fi
        
        echo "$extension" >> "$TEMP_FILE"
    done
    
    # Ordenar, contar y mostrar resultados
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    printf "${YELLOW}%-20s %15s %18s${NC}\n" "EXTENSIÓN" "CANTIDAD" "TAMAÑO TOTAL"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    
    # Procesar y mostrar cada extensión con su conteo y tamaño
    sort "$TEMP_FILE" | uniq -c | sort -rn | while read count ext; do
        # Calcular tamaño total para esta extensión
        total_size=$(get_size_by_extension "$ext")
        size_formatted=$(format_size $total_size)
        
        # Formatear la salida con colores
        printf "${GREEN}%-20s${NC} %15s %18s\n" ".$ext" "$count" "$size_formatted"
    done
    
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
}

# Función para mostrar estadísticas adicionales
show_statistics() {
    local total=$(find "$DIRECTORY" -type f | wc -l)
    local total_dirs=$(find "$DIRECTORY" -type d | wc -l)
    local total_size=0
    
    # Calcular tamaño total del directorio
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            total_size=$((total_size + size))
        fi
    done < <(find "$DIRECTORY" -type f)
    
    local size_formatted=$(format_size $total_size)
    
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${MAGENTA}ESTADÍSTICAS GENERALES${NC}                                          ${CYAN}║${NC}"
    echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"
    printf "${CYAN}║${NC}  ${GREEN}Total de archivos:${NC}      %-40s ${CYAN}║${NC}\n" "$total"
    printf "${CYAN}║${NC}  ${GREEN}Total de directorios:${NC}   %-40s ${CYAN}║${NC}\n" "$((total_dirs - 1))"
    printf "${CYAN}║${NC}  ${GREEN}Tamaño total:${NC}           %-40s ${CYAN}║${NC}\n" "$size_formatted"
    printf "${CYAN}║${NC}  ${GREEN}Ruta analizada:${NC}         %-40s ${CYAN}║${NC}\n" "$(basename "$DIRECTORY")"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Función para mostrar las extensiones más comunes
show_top_extensions() {
    echo ""
    log_info "Top 5 extensiones más comunes:"
    echo ""
    
    sort "$TEMP_FILE" | uniq -c | sort -rn | head -n 5 | while read count ext; do
        # Calcular porcentaje
        total=$(wc -l < "$TEMP_FILE")
        percentage=$(awk "BEGIN {printf \"%.1f\", ($count/$total)*100}")
        
        # Crear barra de progreso visual
        bar_length=$((percentage / 2))
        bar=$(printf "%${bar_length}s" | tr ' ' '█')
        
        printf "  ${GREEN}%-15s${NC} %5s archivos [${CYAN}%-50s${NC}] ${YELLOW}%5s%%${NC}\n" \
               ".$ext" "$count" "$bar" "$percentage"
    done
    
    echo ""
}

################################################################################
# FUNCIÓN PRINCIPAL
################################################################################

main() {
    # Validar directorio
    validate_directory
    
    # Mostrar encabezado
    show_header
    
    # Contar y clasificar archivos
    count_files
    
    # Mostrar extensiones más comunes
    show_top_extensions
    
    # Mostrar estadísticas generales
    show_statistics
    
    log_info "Análisis completado exitosamente"
}

################################################################################
# AYUDA
################################################################################

# Mostrar ayuda si se solicita
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Uso: $0 [directorio]"
    echo ""
    echo "Analiza recursivamente un directorio y cuenta los archivos por extensión."
    echo ""
    echo "Argumentos:"
    echo "  directorio    Directorio a analizar (por defecto: ~/Documents/biblioteca)"
    echo ""
    echo "Opciones:"
    echo "  -h, --help    Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                      # Usa el directorio por defecto"
    echo "  $0 ~/Documents          # Analiza ~/Documents"
    echo "  $0 /home/user/proyectos # Analiza un directorio específico"
    echo ""
    exit 0
fi

# Ejecutar función principal
main
