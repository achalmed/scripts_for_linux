#!/bin/bash

################################################################################
# Script: create_folders_batch.sh
# Descripción: Crea múltiples carpetas de forma masiva desde una lista
#              predefinida o desde un archivo externo.
# Autor: Edison Achalma
# Fecha: 2024
# Uso: ./create_folders_batch.sh [opciones]
#      ./create_folders_batch.sh -f archivo.txt
#      ./create_folders_batch.sh -p /ruta/destino
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
# CONFIGURACIÓN PREDETERMINADA
################################################################################

# Directorio donde se crearán las carpetas (por defecto: directorio actual)
BASE_DIR="."

# Archivo de entrada con lista de carpetas (opcional)
INPUT_FILE=""

# Modo verbose (mostrar más detalles)
VERBOSE=false

# Modo dry-run (simular sin crear)
DRY_RUN=false

################################################################################
# LISTA PREDEFINIDA DE CARPETAS
################################################################################
# Puedes editar esta lista directamente en el script
# o proporcionar un archivo externo con la opción -f

PREDEFINED_FOLDERS=$(cat <<EOF
2022-07-131-01-02-manipulacion-de-datos
2022-07-132-01-03-visualizacion-de-datos
2022-07-133-01-04-modelo-de-machine-learning-i-analisis-exploratorio
2022-07-134-01-05-modelo-de-machine-learning-ii-modelo-de-clasificacion
2022-07-135-01-06-modelo-de-machine-learning-iii-modelo-de-regresion
2022-07-136-01-07-modelo-de-machine-learning-iv-tex-mining
EOF
)

################################################################################
# FUNCIONES DE LOGGING
################################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

################################################################################
# FUNCIONES DE AYUDA Y VALIDACIÓN
################################################################################

show_help() {
    cat << EOF
${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}
${CYAN}║${NC}     ${MAGENTA}CREADOR MASIVO DE CARPETAS${NC}                                     ${CYAN}║${NC}
${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}

Uso: $0 [opciones]

${YELLOW}OPCIONES:${NC}
  -f <archivo>      Leer nombres de carpetas desde un archivo
  -p <ruta>         Directorio base donde crear las carpetas (default: .)
  -v, --verbose     Modo detallado (muestra más información)
  -d, --dry-run     Simular creación sin crear carpetas realmente
  -h, --help        Mostrar esta ayuda

${YELLOW}EJEMPLOS:${NC}
  # Usar lista predefinida en el directorio actual
  $0

  # Leer carpetas desde un archivo
  $0 -f lista_carpetas.txt

  # Crear en un directorio específico
  $0 -p /home/usuario/proyectos

  # Modo dry-run (simular)
  $0 -d -f carpetas.txt

  # Modo verbose con archivo personalizado
  $0 -v -f mis_carpetas.txt -p /tmp/nuevas_carpetas

${YELLOW}FORMATO DEL ARCHIVO:${NC}
  El archivo debe contener un nombre de carpeta por línea:
  
  carpeta-uno
  carpeta-dos
  carpeta-tres/subcarpeta
  
  Las líneas vacías y las que comienzan con # son ignoradas.

${YELLOW}NOTAS:${NC}
  • Si no se especifica -f, usa la lista predefinida en el script
  • Soporta creación de subcarpetas con rutas (ej: carpeta/subcarpeta)
  • Verifica duplicados antes de crear
  • Nombres de carpetas pueden contener espacios si están en archivo

EOF
}

# Validar directorio base
validate_base_dir() {
    # Expandir tilde si existe
    BASE_DIR="${BASE_DIR/#\~/$HOME}"
    
    if [ ! -d "$BASE_DIR" ]; then
        log_error "El directorio base '$BASE_DIR' no existe"
        read -p "¿Desea crear el directorio? (s/N): " create_dir
        if [[ "$create_dir" =~ ^[sS]$ ]]; then
            mkdir -p "$BASE_DIR"
            log_success "Directorio base creado: $BASE_DIR"
        else
            exit 1
        fi
    fi
    
    # Convertir a ruta absoluta
    BASE_DIR=$(cd "$BASE_DIR" && pwd)
    log_verbose "Directorio base: $BASE_DIR"
}

# Validar archivo de entrada
validate_input_file() {
    if [ -n "$INPUT_FILE" ] && [ ! -f "$INPUT_FILE" ]; then
        log_error "El archivo '$INPUT_FILE' no existe"
        exit 1
    fi
}

################################################################################
# FUNCIONES DE PROCESAMIENTO
################################################################################

# Leer carpetas desde archivo o usar lista predefinida
get_folders_list() {
    if [ -n "$INPUT_FILE" ]; then
        log_info "Leyendo carpetas desde: ${BLUE}$INPUT_FILE${NC}"
        # Leer archivo, ignorar líneas vacías y comentarios
        grep -v '^\s*$' "$INPUT_FILE" | grep -v '^\s*#'
    else
        log_info "Usando lista predefinida de carpetas"
        echo "$PREDEFINED_FOLDERS"
    fi
}

# Sanitizar nombre de carpeta
sanitize_folder_name() {
    local name="$1"
    # Eliminar espacios al inicio y final
    name=$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    # Reemplazar caracteres problemáticos (opcional, comentar si no se desea)
    # name=$(echo "$name" | tr -d '\r')
    echo "$name"
}

# Crear una carpeta individual
create_single_folder() {
    local folder_name="$1"
    local full_path="$BASE_DIR/$folder_name"
    
    # Sanitizar el nombre
    folder_name=$(sanitize_folder_name "$folder_name")
    
    # Ignorar líneas vacías
    if [ -z "$folder_name" ]; then
        return
    fi
    
    log_verbose "Procesando: $folder_name"
    
    # Verificar si ya existe
    if [ -d "$full_path" ]; then
        log_warning "Ya existe: ${YELLOW}$folder_name${NC}"
        return 1
    fi
    
    # Modo dry-run
    if [ "$DRY_RUN" = true ]; then
        echo -e "${CYAN}[DRY-RUN]${NC} Se crearía: $folder_name"
        return 0
    fi
    
    # Crear carpeta (con -p para crear subdirectorios si es necesario)
    if mkdir -p "$full_path" 2>/dev/null; then
        log_success "Creada: ${GREEN}$folder_name${NC}"
        return 0
    else
        log_error "Error al crear: ${RED}$folder_name${NC}"
        return 1
    fi
}

# Mostrar resumen de carpetas a crear
show_preview() {
    local folders_list="$1"
    local count=$(echo "$folders_list" | wc -l | tr -d ' ')
    
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${MAGENTA}VISTA PREVIA${NC}                                                    ${CYAN}║${NC}"
    echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"
    printf "${CYAN}║${NC}  ${GREEN}Directorio destino:${NC}   %-43s ${CYAN}║${NC}\n" "$BASE_DIR"
    printf "${CYAN}║${NC}  ${GREEN}Total de carpetas:${NC}    %-43s ${CYAN}║${NC}\n" "$count"
    echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}Carpetas a crear:${NC}                                              ${CYAN}║${NC}"
    
    # Mostrar primeras 10 carpetas
    local display_count=0
    while IFS= read -r folder; do
        folder=$(sanitize_folder_name "$folder")
        [ -z "$folder" ] && continue
        
        if [ $display_count -lt 10 ]; then
            printf "${CYAN}║${NC}    • %-60s ${CYAN}║${NC}\n" "$folder"
            ((display_count++))
        fi
    done <<< "$folders_list"
    
    if [ $count -gt 10 ]; then
        printf "${CYAN}║${NC}    ${YELLOW}... y %d carpetas más${NC}%40s ${CYAN}║${NC}\n" $((count - 10)) ""
    fi
    
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

################################################################################
# FUNCIÓN PRINCIPAL
################################################################################

main() {
    # Validaciones
    validate_base_dir
    validate_input_file
    
    # Obtener lista de carpetas
    local folders_list=$(get_folders_list)
    
    # Mostrar vista previa
    show_preview "$folders_list"
    
    # Confirmar en modo normal (no dry-run)
    if [ "$DRY_RUN" = false ]; then
        read -p "¿Desea continuar con la creación? (s/N): " confirm
        if [[ ! "$confirm" =~ ^[sS]$ ]]; then
            log_warning "Operación cancelada por el usuario"
            exit 0
        fi
    fi
    
    echo ""
    log_info "Iniciando creación de carpetas..."
    echo ""
    
    # Contadores
    local created=0
    local existed=0
    local failed=0
    
    # Procesar cada carpeta
    while IFS= read -r folder; do
        folder=$(sanitize_folder_name "$folder")
        [ -z "$folder" ] && continue
        
        if create_single_folder "$folder"; then
            ((created++))
        else
            if [ -d "$BASE_DIR/$folder" ]; then
                ((existed++))
            else
                ((failed++))
            fi
        fi
    done <<< "$folders_list"
    
    # Mostrar resumen final
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${MAGENTA}RESUMEN FINAL${NC}                                                  ${CYAN}║${NC}"
    echo -e "${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"
    printf "${CYAN}║${NC}  ${GREEN}✓ Carpetas creadas:${NC}     %-41s ${CYAN}║${NC}\n" "$created"
    printf "${CYAN}║${NC}  ${YELLOW}⚠ Ya existían:${NC}          %-41s ${CYAN}║${NC}\n" "$existed"
    printf "${CYAN}║${NC}  ${RED}✗ Errores:${NC}              %-41s ${CYAN}║${NC}\n" "$failed"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_info "Modo DRY-RUN: No se creó ninguna carpeta realmente"
    elif [ $failed -eq 0 ]; then
        log_success "Proceso completado exitosamente"
    else
        log_warning "Proceso completado con algunos errores"
        exit 1
    fi
}

################################################################################
# PROCESAMIENTO DE ARGUMENTOS
################################################################################

# Procesar opciones de línea de comandos
while getopts "f:p:vdh-:" opt; do
    case $opt in
        f) INPUT_FILE="$OPTARG" ;;
        p) BASE_DIR="$OPTARG" ;;
        v) VERBOSE=true ;;
        d) DRY_RUN=true ;;
        h) show_help; exit 0 ;;
        -)
            case "$OPTARG" in
                help) show_help; exit 0 ;;
                verbose) VERBOSE=true ;;
                dry-run) DRY_RUN=true ;;
                *) log_error "Opción inválida: --$OPTARG"; exit 1 ;;
            esac
            ;;
        \?) log_error "Opción inválida: -$OPTARG"; exit 1 ;;
    esac
done

# Ejecutar función principal
main
