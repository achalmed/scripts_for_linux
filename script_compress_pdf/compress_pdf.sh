#!/bin/bash

################################################################################
# PDF Compressor Script for Arch Linux
# Autor: Edison Achalma
# Descripción: Comprime PDFs
# Características: Recursivo, guarda en carpeta original, múltiples métodos
################################################################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # Sin color

# Variables globales
TOTAL_ORIGINAL=0
TOTAL_COMPRESSED=0
FILES_PROCESSED=0
FILES_SUCCESS=0
FILES_FAILED=0
FILES_SKIPPED=0

# Función para mostrar uso
show_usage() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}PDF Compressor v2.0${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Uso: $0 [OPCIONES] <directorio_o_archivo>"
    echo ""
    echo "Opciones:"
    echo "  -m, --method MÉTODO    Método de compresión:"
    echo "                         screen:   Máxima compresión (80-95%) - 72 DPI"
    echo "                         ebook:    Alta compresión (60-85%) - 150 DPI [DEFAULT]"
    echo "                         printer:  Buena calidad (40-70%) - 300 DPI"
    echo "                         prepress: Máxima calidad (20-50%) - 300 DPI"
    echo "                         ocr:      Usa ocrmypdf (óptimo para escaneados)"
    echo ""
    echo "  -r, --recursive        Procesa subdirectorios recursivamente"
    echo "  -s, --suffix SUFIJO    Sufijo para archivo comprimido (default: _compressed)"
    echo "  -f, --force            Sobrescribe archivos existentes"
    echo "  -k, --keep-original    Mantiene original si compresión falla o aumenta tamaño"
    echo "  -t, --threshold PCT    Solo comprime si reduce al menos PCT% (default: 5)"
    echo "  -v, --verbose          Modo detallado"
    echo "  -h, --help             Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 /ruta/documento.pdf                    # Comprime un archivo"
    echo "  $0 -r /ruta/carpeta                       # Comprime todos los PDFs recursivamente"
    echo "  $0 -m screen /ruta/carpeta                # Máxima compresión"
    echo "  $0 -m ocr -r ~/Documentos/escaneados     # Usa OCR para escaneados"
    echo "  $0 -m printer -r -t 10 ~/biblioteca      # Solo si reduce >10%"
    echo ""
}

# Función para verificar dependencias
check_dependencies() {
    local missing_deps=()
    
    if ! command -v gs &> /dev/null; then
        missing_deps+=("ghostscript")
    fi
    
    if [ "$METHOD" = "ocr" ] && ! command -v ocrmypdf &> /dev/null; then
        missing_deps+=("ocrmypdf")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Error: Faltan las siguientes dependencias:${NC}"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Instala las dependencias con:"
        echo "  sudo pacman -S ${missing_deps[*]}"
        exit 1
    fi
}

# Función para obtener tamaño en bytes
get_file_size_bytes() {
    stat -c%s "$1" 2>/dev/null || echo 0
}

# Función para formatear tamaño
format_size() {
    local size=$1
    if [ $size -lt 1024 ]; then
        echo "${size}B"
    elif [ $size -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $size/1024}")KB"
    elif [ $size -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $size/1048576}")MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1073741824}")GB"
    fi
}

# Función para calcular porcentaje de reducción
calculate_reduction() {
    local original=$1
    local compressed=$2
    if [ $original -eq 0 ]; then
        echo "0"
        return
    fi
    echo "$((100 - (compressed * 100 / original)))"
}

# Función de compresión con Ghostscript
compress_with_gs() {
    local input="$1"
    local output="$2"
    local quality="$3"
    
    [ "$VERBOSE" = true ] && echo -e "${CYAN}  Usando Ghostscript con calidad: $quality${NC}"
    
    gs -sDEVICE=pdfwrite \
       -dCompatibilityLevel=1.4 \
       -dPDFSETTINGS="$quality" \
       -dNOPAUSE \
       -dQUIET \
       -dBATCH \
       -sOutputFile="$output" \
       "$input" 2>/dev/null
    
    return $?
}

# Función de compresión con ocrmypdf
compress_with_ocr() {
    local input="$1"
    local output="$2"
    
    [ "$VERBOSE" = true ] && echo -e "${CYAN}  Usando ocrmypdf con optimización nivel 3${NC}"
    
    ocrmypdf --optimize 3 \
             --output-type pdf \
             --skip-text \
             --tesseract-timeout=0 \
             --quiet \
             "$input" "$output" 2>/dev/null
    
    return $?
}

# Función principal de compresión
compress_pdf() {
    local input_file="$1"
    local dir_path=$(dirname "$input_file")
    local base_name=$(basename "$input_file" .pdf)
    local output_file="${dir_path}/${base_name}${SUFFIX}.pdf"
    
    # Verificar que el archivo existe y es PDF
    if [ ! -f "$input_file" ]; then
        [ "$VERBOSE" = true ] && echo -e "${RED}  ✗ Archivo no encontrado${NC}"
        return 1
    fi
    
    # Verificar que no es el mismo archivo de salida
    if [[ "$input_file" == *"$SUFFIX.pdf" ]]; then
        [ "$VERBOSE" = true ] && echo -e "${YELLOW}  ⊘ Saltando archivo ya comprimido${NC}"
        FILES_SKIPPED=$((FILES_SKIPPED + 1))
        return 2
    fi
    
    # Verificar si existe el archivo de salida
    if [ -f "$output_file" ] && [ "$FORCE" = false ]; then
        [ "$VERBOSE" = true ] && echo -e "${YELLOW}  ⊘ Ya existe, usa -f para sobrescribir${NC}"
        FILES_SKIPPED=$((FILES_SKIPPED + 1))
        return 2
    fi
    
    local original_size=$(get_file_size_bytes "$input_file")
    
    if [ $original_size -eq 0 ]; then
        [ "$VERBOSE" = true ] && echo -e "${RED}  ✗ Error al leer archivo${NC}"
        return 1
    fi
    
    # Crear archivo temporal
    local temp_output=$(mktemp /tmp/pdf_compress_XXXXXX.pdf)
    
    # Comprimir según método
    local compress_result=0
    case $METHOD in
        screen)
            compress_with_gs "$input_file" "$temp_output" "/screen"
            compress_result=$?
            ;;
        ebook)
            compress_with_gs "$input_file" "$temp_output" "/ebook"
            compress_result=$?
            ;;
        printer)
            compress_with_gs "$input_file" "$temp_output" "/printer"
            compress_result=$?
            ;;
        prepress)
            compress_with_gs "$input_file" "$temp_output" "/prepress"
            compress_result=$?
            ;;
        ocr)
            compress_with_ocr "$input_file" "$temp_output"
            compress_result=$?
            ;;
    esac
    
    # Verificar si la compresión fue exitosa
    if [ $compress_result -ne 0 ] || [ ! -f "$temp_output" ]; then
        rm -f "$temp_output"
        echo -e "${RED}  ✗ Error durante la compresión${NC}"
        FILES_FAILED=$((FILES_FAILED + 1))
        return 1
    fi
    
    local compressed_size=$(get_file_size_bytes "$temp_output")
    
    # Verificar que el archivo comprimido es válido
    if [ $compressed_size -eq 0 ]; then
        rm -f "$temp_output"
        echo -e "${RED}  ✗ Archivo comprimido inválido${NC}"
        FILES_FAILED=$((FILES_FAILED + 1))
        return 1
    fi
    
    local reduction=$(calculate_reduction $original_size $compressed_size)
    
    # Verificar umbral de compresión
    if [ $reduction -lt $THRESHOLD ]; then
        rm -f "$temp_output"
        echo -e "${YELLOW}  ⊘ Reducción insuficiente (${reduction}% < ${THRESHOLD}%)${NC}"
        if [ "$KEEP_ORIGINAL" = true ]; then
            FILES_SKIPPED=$((FILES_SKIPPED + 1))
        else
            FILES_FAILED=$((FILES_FAILED + 1))
        fi
        return 2
    fi
    
    # Mover archivo comprimido a destino final
    mv "$temp_output" "$output_file"
    
    # Actualizar estadísticas
    TOTAL_ORIGINAL=$((TOTAL_ORIGINAL + original_size))
    TOTAL_COMPRESSED=$((TOTAL_COMPRESSED + compressed_size))
    FILES_SUCCESS=$((FILES_SUCCESS + 1))
    
    # Mostrar resultado
    local orig_fmt=$(format_size $original_size)
    local comp_fmt=$(format_size $compressed_size)
    echo -e "${GREEN}  ✓ ${orig_fmt} → ${comp_fmt} (${GREEN}${reduction}%${NC} reducción)"
    
    return 0
}

# Función para procesar un archivo
process_file() {
    local file="$1"
    FILES_PROCESSED=$((FILES_PROCESSED + 1))
    
    echo -e "${BLUE}[$FILES_PROCESSED]${NC} $(basename "$file")"
    compress_pdf "$file"
}

# Función para procesar directorio
process_directory() {
    local dir="$1"
    
    if [ "$RECURSIVE" = true ]; then
        # Procesar recursivamente
        while IFS= read -r -d '' pdf_file; do
            process_file "$pdf_file"
        done < <(find "$dir" -type f -name "*.pdf" ! -name "*$SUFFIX.pdf" -print0)
    else
        # Solo directorio actual
        for pdf_file in "$dir"/*.pdf; do
            if [ -f "$pdf_file" ] && [[ "$pdf_file" != *"$SUFFIX.pdf" ]]; then
                process_file "$pdf_file"
            fi
        done
    fi
}

# Función para mostrar resumen
show_summary() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Resumen del Procesamiento${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "Archivos procesados:        ${BLUE}$FILES_PROCESSED${NC}"
    echo -e "Comprimidos exitosamente:   ${GREEN}$FILES_SUCCESS${NC}"
    echo -e "Saltados:                   ${YELLOW}$FILES_SKIPPED${NC}"
    echo -e "Fallidos:                   ${RED}$FILES_FAILED${NC}"
    
    if [ $TOTAL_ORIGINAL -gt 0 ]; then
        local total_reduction=$(calculate_reduction $TOTAL_ORIGINAL $TOTAL_COMPRESSED)
        local saved=$((TOTAL_ORIGINAL - TOTAL_COMPRESSED))
        echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
        echo -e "Tamaño original total:      $(format_size $TOTAL_ORIGINAL)"
        echo -e "Tamaño comprimido total:    $(format_size $TOTAL_COMPRESSED)"
        echo -e "Espacio ahorrado:           ${GREEN}$(format_size $saved) (${total_reduction}%)${NC}"
    fi
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

# Variables por defecto
METHOD="ebook"
RECURSIVE=false
SUFFIX="_compressed"
FORCE=false
KEEP_ORIGINAL=true
THRESHOLD=5
VERBOSE=false
TARGET=""

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--method)
            METHOD="$2"
            shift 2
            ;;
        -r|--recursive)
            RECURSIVE=true
            shift
            ;;
        -s|--suffix)
            SUFFIX="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -k|--keep-original)
            KEEP_ORIGINAL=true
            shift
            ;;
        -t|--threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# Verificar que se proporcionó un objetivo
if [ -z "$TARGET" ]; then
    echo -e "${RED}Error: Debes especificar un archivo o directorio${NC}"
    echo ""
    show_usage
    exit 1
fi

# Verificar que el objetivo existe
if [ ! -e "$TARGET" ]; then
    echo -e "${RED}Error: '$TARGET' no existe${NC}"
    exit 1
fi

# Validar método
case $METHOD in
    screen|ebook|printer|prepress|ocr)
        ;;
    *)
        echo -e "${RED}Error: Método no válido: $METHOD${NC}"
        echo "Métodos válidos: screen, ebook, printer, prepress, ocr"
        exit 1
        ;;
esac

# Verificar dependencias
check_dependencies

# Mostrar banner inicial
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PDF Compressor v2.0 - Compresión Real${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "Método:      ${CYAN}$METHOD${NC}"
echo -e "Recursivo:   $([ "$RECURSIVE" = true ] && echo "${GREEN}Sí${NC}" || echo "${YELLOW}No${NC}")"
echo -e "Umbral:      ${CYAN}${THRESHOLD}%${NC}"
echo -e "Objetivo:    ${CYAN}$TARGET${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Procesar según tipo de objetivo
if [ -f "$TARGET" ]; then
    # Es un archivo
    if [[ "$TARGET" != *.pdf ]]; then
        echo -e "${RED}Error: El archivo debe ser un PDF${NC}"
        exit 1
    fi
    process_file "$TARGET"
elif [ -d "$TARGET" ]; then
    # Es un directorio
    process_directory "$TARGET"
else
    echo -e "${RED}Error: '$TARGET' no es un archivo ni directorio válido${NC}"
    exit 1
fi

# Mostrar resumen
show_summary

# Código de salida
if [ $FILES_FAILED -gt 0 ]; then
    exit 1
elif [ $FILES_SUCCESS -eq 0 ]; then
    exit 2
else
    exit 0
fi