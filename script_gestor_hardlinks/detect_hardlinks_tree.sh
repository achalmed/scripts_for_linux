#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                  DETECTOR Y VISUALIZADOR DE ENLACES DUROS                    ║
# ║                                                                              ║
# ║  Busca archivos con enlaces duros y los muestra en estructura de árbol      ║
# ║  con información detallada sobre inodos, tamaño y número de enlaces.        ║
# ║                                                                              ║
# ║  Autor: Edison Achalma                                                       ║
# ║  Email: achalmaedison@gmail.com                                              ║
# ║  Versión: 2.0                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ============================================
# CONFIGURACIÓN DE COLORES
# ============================================
# Definir colores para una salida más atractiva
if [[ -t 1 ]]; then
    # Terminal soporta colores
    BOLD='\033[1m'
    RESET='\033[0m'
    
    # Colores básicos
    BLACK='\033[0;30m'
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    WHITE='\033[0;37m'
    GRAY='\033[0;90m'
    
    # Colores brillantes
    BRIGHT_RED='\033[0;91m'
    BRIGHT_GREEN='\033[0;92m'
    BRIGHT_YELLOW='\033[0;93m'
    BRIGHT_BLUE='\033[0;94m'
    BRIGHT_MAGENTA='\033[0;95m'
    BRIGHT_CYAN='\033[0;96m'
    BRIGHT_WHITE='\033[0;97m'
    
    # Combinaciones útiles
    HEADER="${BOLD}${BRIGHT_BLUE}"
    SUCCESS="${BOLD}${BRIGHT_GREEN}"
    WARNING="${BOLD}${BRIGHT_YELLOW}"
    ERROR="${BOLD}${BRIGHT_RED}"
    INFO="${BRIGHT_CYAN}"
    DIM="${GRAY}"
else
    # Terminal no soporta colores
    BOLD=''
    RESET=''
    BLACK=''
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    MAGENTA=''
    CYAN=''
    WHITE=''
    GRAY=''
    BRIGHT_RED=''
    BRIGHT_GREEN=''
    BRIGHT_YELLOW=''
    BRIGHT_BLUE=''
    BRIGHT_MAGENTA=''
    BRIGHT_CYAN=''
    BRIGHT_WHITE=''
    HEADER=''
    SUCCESS=''
    WARNING=''
    ERROR=''
    INFO=''
    DIM=''
fi

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

print_header() {
    local text="$1"
    local width=80
    
    echo -e "\n${HEADER}╔$(printf '═%.0s' $(seq 1 $((width - 2))))╗${RESET}"
    local padding=$(( (width - ${#text} - 2) / 2 ))
    printf "${HEADER}║%*s${BOLD}%s%*s║${RESET}\n" $padding "" "$text" $((width - ${#text} - padding - 2)) ""
    echo -e "${HEADER}╚$(printf '═%.0s' $(seq 1 $((width - 2))))╝${RESET}\n"
}

print_box() {
    local label="$1"
    local value="$2"
    local icon="$3"
    echo -e "${INFO}${icon} ${label}:${RESET} ${BOLD}${value}${RESET}"
}

print_separator() {
    local char="${1:-━}"
    echo -e "\n${DIM}$(printf "${char}%.0s" $(seq 1 80))${RESET}\n"
}

print_success() {
    echo -e "${SUCCESS}✓${RESET} $1"
}

print_warning() {
    echo -e "${WARNING}⚠${RESET} $1"
}

print_error() {
    echo -e "${ERROR}✗${RESET} $1" >&2
}

print_info() {
    echo -e "${INFO}ℹ${RESET} $1"
}

format_size() {
    local size=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0
    
    while (( $(echo "$size >= 1024" | bc -l) )) && (( unit < 4 )); do
        size=$(echo "scale=2; $size / 1024" | bc)
        ((unit++))
    done
    
    printf "%.2f %s" "$size" "${units[$unit]}"
}

show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    
    printf "\r${INFO}Progreso: [${RESET}"
    printf "${SUCCESS}%${filled}s${RESET}" | tr ' ' '█'
    printf "%$((width - filled))s" | tr ' ' '░'
    printf "${INFO}] %3d%% (%d/%d)${RESET}" "$percentage" "$current" "$total"
}

# ============================================
# CONFIGURACIÓN: Directorio de trabajo
# Por defecto usa el directorio actual, pero puedes especificar uno diferente
# Uso: ./script.sh [directorio]
# Ejemplo: ./script.sh /home/usuario/documentos
# ============================================

if [ -z "$1" ]; then
    # Si no se proporciona argumento, usar el directorio actual
    DIRECTORY=$(pwd)
    print_info "Usando directorio actual: ${BOLD}${DIRECTORY}${RESET}"
else
    # Si se proporciona un argumento, usarlo como directorio de trabajo
    DIRECTORY="$1"
    print_info "Usando directorio especificado: ${BOLD}${DIRECTORY}${RESET}"
fi

# ============================================
# VALIDACIÓN DEL DIRECTORIO
# ============================================

# Verificar que el directorio existe y es accesible
if [ ! -d "$DIRECTORY" ]; then
    print_error "No se puede acceder al directorio '${DIRECTORY}'"
    echo -e "${DIM}Verifica que:${RESET}"
    echo -e "${DIM}  • La ruta sea correcta${RESET}"
    echo -e "${DIM}  • Tengas permisos de lectura${RESET}"
    echo -e "${DIM}  • El directorio exista${RESET}"
    exit 1
fi

# ============================================
# PREPARACIÓN DE ARCHIVOS TEMPORALES
# ============================================

# Crear archivo temporal para almacenar información de inodos
# Los inodos son identificadores únicos de archivos en el sistema
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# ============================================
# BÚSQUEDA DE ENLACES DUROS
# ============================================

print_header "DETECTOR DE ENLACES DUROS - ANÁLISIS"

print_box "Directorio" "$DIRECTORY" "📁"
echo ""

echo -e "${INFO}🔍 Escaneando directorio en busca de enlaces duros...${RESET}"

# Contar archivos totales para mostrar progreso
if command -v pv &> /dev/null; then
    # Si pv está disponible, usarlo para mostrar progreso
    find "$DIRECTORY" -type f -links +1 -exec stat --format="%i %n" {} + 2>/dev/null | pv -l -s $(find "$DIRECTORY" -type f -links +1 2>/dev/null | wc -l) > "$TEMP_FILE"
else
    # Sin pv, solo mostrar mensaje
    find "$DIRECTORY" -type f -links +1 -exec stat --format="%i %n" {} + 2>/dev/null > "$TEMP_FILE"
    echo -e "${SUCCESS}✓${RESET} Escaneo completado"
fi

# ============================================
# PROCESAMIENTO DE DATOS
# ============================================

# Crear un array asociativo para agrupar archivos por inodo
# Un mismo inodo agrupa todos los enlaces duros del mismo archivo
declare -A inodes
declare -A inode_sizes
declare -A inode_links

# Leer el archivo temporal línea por línea
while IFS=' ' read -r inode file; do
    if [ -n "$inode" ] && [ -n "$file" ]; then
        inodes["$inode"]+="$file;"
        
        # Obtener tamaño y número de enlaces solo una vez por inodo
        if [ -z "${inode_sizes[$inode]}" ]; then
            inode_sizes["$inode"]=$(stat -c%s "$file" 2>/dev/null || echo "0")
            inode_links["$inode"]=$(stat -c%h "$file" 2>/dev/null || echo "0")
        fi
    fi
done < "$TEMP_FILE"

# ============================================
# PRESENTACIÓN DE RESULTADOS
# ============================================

print_separator
print_header "ÁRBOL DE ARCHIVOS CON ENLACES DUROS"

print_box "Directorio analizado" "$DIRECTORY" "📂"
print_box "Total de conjuntos encontrados" "${#inodes[@]}" "🔗"

if [ ${#inodes[@]} -eq 0 ]; then
    echo ""
    print_success "No se encontraron archivos con enlaces duros en este directorio"
    print_info "Esto significa que no hay archivos enlazados físicamente"
    echo ""
    exit 0
fi

echo ""
print_info "A continuación se muestran todos los conjuntos de archivos enlazados:"

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
    
    # Recopilar todas las rutas relativas
    for file in "${file_array[@]}"; do
        if [ -n "$file" ]; then
            local rel_path=$(realpath --relative-to="$DIRECTORY" "$file" 2>/dev/null || echo "$file")
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
                    indent="${indent}${DIM}│   ${RESET}"
                done
                
                echo -e "${indent}${BRIGHT_BLUE}├──${RESET} ${BOLD}${CYAN}${path_components[$i]}/${RESET}"
            fi
        done
        
        # Mostrar el archivo con indentación apropiada
        local file_indent=""
        for ((i=0; i<${#path_components[@]}; i++)); do
            file_indent="${file_indent}${DIM}│   ${RESET}"
        done
        
        echo -e "${file_indent}${BRIGHT_GREEN}└──${RESET} ${path_components[${#path_components[@]}-1]}"
    done
}

# ============================================
# MOSTRAR CADA CONJUNTO DE ENLACES DUROS
# ============================================

contador=1
total_space_used=0
total_space_saved=0

for inode in "${!inodes[@]}"; do
    files=${inodes[$inode]}
    IFS=';' read -ra file_array <<< "$files"
    
    link_count=${inode_links[$inode]}
    file_size_bytes=${inode_sizes[$inode]}
    file_size=$(format_size "$file_size_bytes")
    
    # Calcular espacio usado y ahorrado
    total_space_used=$((total_space_used + file_size_bytes))
    total_space_saved=$((total_space_saved + file_size_bytes * (link_count - 1)))
    
    print_separator "─"
    
    echo -e "${HEADER}Conjunto #${contador}${RESET}"
    echo -e "${DIM}  Inodo: ${RESET}${inode}"
    echo -e "${DIM}  Enlaces: ${RESET}${BOLD}${link_count}${RESET}"
    echo -e "${DIM}  Tamaño por enlace: ${RESET}${BOLD}${file_size}${RESET}"
    echo -e "${DIM}  Espacio ahorrado: ${RESET}${SUCCESS}$(format_size $((file_size_bytes * (link_count - 1))))${RESET}"
    echo ""
    
    print_hierarchical_tree "$files"
    echo -e "${DIM}└──${RESET}"
    echo ""
    
    ((contador++))
done

# ============================================
# RESUMEN FINAL
# ============================================

print_separator
print_header "RESUMEN DE ANÁLISIS"

echo -e "${HEADER}╠$(printf '═%.0s' $(seq 1 78))╣${RESET}"
echo -e "${HEADER}║${RESET}  ${SUCCESS}📊 Estadísticas de Enlaces:${RESET}$(printf ' %.0s' $(seq 1 48))${HEADER}║${RESET}"
echo -e "${HEADER}║${RESET}     • Conjuntos encontrados: ${BOLD}${#inodes[@]}${RESET}$(printf ' %.0s' $(seq 1 $((51 - ${#inodes[@]} / 10))))${HEADER}║${RESET}"
echo -e "${HEADER}║${RESET}     • Espacio en disco usado: ${BOLD}$(format_size $total_space_used)${RESET}$(printf ' %.0s' $(seq 1 $((46 - ${#total_space_used} / 10))))${HEADER}║${RESET}"
echo -e "${HEADER}║${RESET}     • Espacio ahorrado: ${SUCCESS}${BOLD}$(format_size $total_space_saved)${RESET}$(printf ' %.0s' $(seq 1 $((50 - ${#total_space_saved} / 10))))${HEADER}║${RESET}"
echo -e "${HEADER}╚$(printf '═%.0s' $(seq 1 78))╝${RESET}"

# ============================================
# GUÍA DE USO
# ============================================

echo ""
print_header "GUÍA DE GESTIÓN DE ENLACES DUROS"

echo -e "${BOLD}${BRIGHT_CYAN}📖 ¿Qué son los enlaces duros?${RESET}"
echo -e "${DIM}   Son múltiples nombres para el mismo archivo físico.${RESET}"
echo -e "${DIM}   Todos comparten el mismo contenido y espacio en disco.${RESET}"
echo ""

echo -e "${BOLD}${BRIGHT_CYAN}🔧 Operaciones disponibles:${RESET}"
echo ""

echo -e "${SUCCESS}   • Eliminar un enlace:${RESET}"
echo -e "${DIM}     ${BOLD}rm /ruta/completa/archivo${RESET}"
echo -e "${DIM}     (El archivo permanece mientras exista al menos un enlace)${RESET}"
echo ""

echo -e "${SUCCESS}   • Mover un enlace:${RESET}"
echo -e "${DIM}     ${BOLD}mv /ruta/completa/archivo /nueva/ruta/${RESET}"
echo -e "${DIM}     (Los demás enlaces no se ven afectados)${RESET}"
echo ""

echo -e "${SUCCESS}   • Crear un nuevo enlace duro:${RESET}"
echo -e "${DIM}     ${BOLD}ln /archivo/existente /nueva/ubicación/nombre${RESET}"
echo ""

echo -e "${SUCCESS}   • Ver información de enlaces:${RESET}"
echo -e "${DIM}     ${BOLD}ls -li /ruta/archivo${RESET}"
echo -e "${DIM}     (La primera columna muestra el número de inodo)${RESET}"
echo ""

echo -e "${SUCCESS}   • Verificar si dos archivos son hard links:${RESET}"
echo -e "${DIM}     ${BOLD}stat -c '%i' archivo1 archivo2${RESET}"
echo -e "${DIM}     (Si los inodos son iguales, son hard links)${RESET}"
echo ""

echo -e "${WARNING}⚠️  IMPORTANTE:${RESET}"
echo -e "${DIM}   • Modificar el contenido afecta a TODOS los enlaces${RESET}"
echo -e "${DIM}   • El archivo se elimina solo cuando se borran TODOS los enlaces${RESET}"
echo -e "${DIM}   • Los enlaces duros no funcionan entre diferentes sistemas de archivos${RESET}"
echo -e "${DIM}   • No se pueden crear enlaces duros de directorios${RESET}"
echo ""

echo -e "${BOLD}${BRIGHT_CYAN}📝 Uso del script:${RESET}"
echo -e "${DIM}   ${BOLD}$0${RESET} ${DIM}[directorio]${RESET}"
echo -e "${DIM}   Ejemplo: ${BOLD}$0 /home/usuario/documentos${RESET}"
echo ""

echo -e "${BOLD}${BRIGHT_CYAN}🔗 Scripts relacionados:${RESET}"
echo -e "${DIM}   • ${BOLD}create_hardlinks.py${RESET}${DIM} - Crear enlaces duros automáticamente${RESET}"
echo -e "${DIM}   • ${BOLD}unlink_hardlinks.py${RESET}${DIM} - Deshacer enlaces duros${RESET}"
echo ""

print_success "Análisis completado exitosamente"
echo ""

exit 0