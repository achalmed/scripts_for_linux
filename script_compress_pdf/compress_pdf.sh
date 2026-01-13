#!/bin/bash

################################################################################
# PDF Compressor Script for Arch Linux
# Autor: Edison Achalma
# Descripción: Comprime archivos PDF manteniendo alta calidad visual
# Usa Ghostscript para la compresión con diferentes niveles de calidad
################################################################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Función para mostrar uso
show_usage() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}PDF Compressor - Compresor de PDFs de Alta Calidad${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Uso: $0 [OPCIONES] <archivo.pdf> [archivo_salida.pdf]"
    echo ""
    echo "Opciones:"
    echo "  -q, --quality NIVEL    Nivel de calidad (default, high, max, custom)"
    echo "                         default: Compresión balanceada (preprint)"
    echo "                         high:    Alta calidad (printer)"
    echo "                         max:     Máxima calidad, sin pérdidas visibles"
    echo "                         custom:  Configuración personalizada"
    echo "  -d, --dpi DPI          DPI para imágenes (default: 300)"
    echo "  -c, --color-dpi DPI    DPI para imágenes a color (default: 300)"
    echo "  -g, --gray-dpi DPI     DPI para imágenes en escala de grises (default: 300)"
    echo "  -m, --mono-dpi DPI     DPI para imágenes monocromáticas (default: 1200)"
    echo "  -b, --batch            Modo batch: procesa todos los PDFs en el directorio actual"
    echo "  -o, --output-dir DIR   Directorio de salida para modo batch (default: compressed/)"
    echo "  -s, --stats            Muestra estadísticas detalladas de compresión"
    echo "  -h, --help             Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 documento.pdf                           # Compresión con calidad por defecto"
    echo "  $0 -q max documento.pdf                    # Máxima calidad"
    echo "  $0 -q high documento.pdf comprimido.pdf    # Alta calidad con nombre específico"
    echo "  $0 -q custom -d 450 documento.pdf          # Calidad personalizada a 450 DPI"
    echo "  $0 -b -q high                              # Comprimir todos los PDFs del directorio"
    echo "  $0 -b -o /ruta/salida -q max               # Batch con directorio de salida personalizado"
    echo ""
}

# Función para verificar dependencias
check_dependencies() {
    local missing_deps=()
    
    if ! command -v gs &> /dev/null; then
        missing_deps+=("ghostscript")
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

# Función para obtener tamaño de archivo en formato legible
get_file_size() {
    local file=$1
    du -h "$file" | cut -f1
}

# Función para obtener tamaño en bytes
get_file_size_bytes() {
    local file=$1
    stat -c%s "$file"
}

# Función para calcular porcentaje de compresión
calculate_compression() {
    local original=$1
    local compressed=$2
    local original_size=$(get_file_size_bytes "$original")
    local compressed_size=$(get_file_size_bytes "$compressed")
    local reduction=$((100 - (compressed_size * 100 / original_size)))
    echo "$reduction"
}

# Función principal de compresión
compress_pdf() {
    local input_file=$1
    local output_file=$2
    local quality=$3
    local color_dpi=$4
    local gray_dpi=$5
    local mono_dpi=$6
    local show_stats=$7
    
    # Verificar que el archivo existe
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}Error: El archivo '$input_file' no existe${NC}"
        return 1
    fi
    
    # Configurar parámetros según nivel de calidad
    local gs_quality=""
    case $quality in
        default)
            gs_quality="/prepress"
            ;;
        high)
            gs_quality="/printer"
            ;;
        max)
            gs_quality="/printer"
            color_dpi=450
            gray_dpi=450
            mono_dpi=1200
            ;;
        custom)
            gs_quality="/printer"
            ;;
        *)
            echo -e "${RED}Error: Nivel de calidad no válido${NC}"
            return 1
            ;;
    esac
    
    echo -e "${YELLOW}Comprimiendo: ${NC}$input_file"
    echo -e "${YELLOW}Calidad:      ${NC}$quality"
    echo -e "${YELLOW}DPI Color:    ${NC}$color_dpi"
    echo -e "${YELLOW}DPI Grises:   ${NC}$gray_dpi"
    echo -e "${YELLOW}DPI Mono:     ${NC}$mono_dpi"
    echo ""
    
    # Ejecutar Ghostscript
    gs -sDEVICE=pdfwrite \
       -dCompatibilityLevel=1.4 \
       -dPDFSETTINGS=$gs_quality \
       -dNOPAUSE \
       -dQUIET \
       -dBATCH \
       -dDetectDuplicateImages=true \
       -dCompressFonts=true \
       -dColorImageResolution=$color_dpi \
       -dGrayImageResolution=$gray_dpi \
       -dMonoImageResolution=$mono_dpi \
       -dColorImageDownsampleType=/Bicubic \
       -dGrayImageDownsampleType=/Bicubic \
       -dMonoImageDownsampleType=/Bicubic \
       -dOptimize=true \
       -dEmbedAllFonts=true \
       -dSubsetFonts=true \
       -dAutoFilterColorImages=false \
       -dAutoFilterGrayImages=false \
       -dColorImageFilter=/DCTEncode \
       -dGrayImageFilter=/DCTEncode \
       -dJPEGQ=95 \
       -sOutputFile="$output_file" \
       "$input_file"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ Compresión exitosa${NC}"
        
        if [ "$show_stats" = true ]; then
            local original_size=$(get_file_size "$input_file")
            local compressed_size=$(get_file_size "$output_file")
            local reduction=$(calculate_compression "$input_file" "$output_file")
            
            echo ""
            echo -e "${BLUE}═══════════════════════════════════════${NC}"
            echo -e "${GREEN}Estadísticas de Compresión:${NC}"
            echo -e "${BLUE}═══════════════════════════════════════${NC}"
            echo -e "Tamaño original:   $original_size"
            echo -e "Tamaño comprimido: $compressed_size"
            echo -e "Reducción:         ${GREEN}${reduction}%${NC}"
            echo -e "${BLUE}═══════════════════════════════════════${NC}"
            echo ""
        fi
        
        return 0
    else
        echo -e "${RED}✗ Error durante la compresión${NC}"
        return 1
    fi
}

# Variables por defecto
QUALITY="default"
COLOR_DPI=300
GRAY_DPI=300
MONO_DPI=1200
BATCH_MODE=false
OUTPUT_DIR="compressed"
SHOW_STATS=true
INPUT_FILE=""
OUTPUT_FILE=""

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -d|--dpi)
            COLOR_DPI="$2"
            GRAY_DPI="$2"
            shift 2
            ;;
        -c|--color-dpi)
            COLOR_DPI="$2"
            shift 2
            ;;
        -g|--gray-dpi)
            GRAY_DPI="$2"
            shift 2
            ;;
        -m|--mono-dpi)
            MONO_DPI="$2"
            shift 2
            ;;
        -b|--batch)
            BATCH_MODE=true
            shift
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -s|--stats)
            SHOW_STATS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [ -z "$INPUT_FILE" ]; then
                INPUT_FILE="$1"
            elif [ -z "$OUTPUT_FILE" ]; then
                OUTPUT_FILE="$1"
            else
                echo -e "${RED}Error: Argumento no reconocido: $1${NC}"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Verificar dependencias
check_dependencies

# Modo batch
if [ "$BATCH_MODE" = true ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Modo Batch: Procesando todos los PDFs en el directorio actual${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Crear directorio de salida si no existe
    mkdir -p "$OUTPUT_DIR"
    
    # Contador de archivos
    local count=0
    local success=0
    local total_original=0
    local total_compressed=0
    
    # Procesar todos los PDFs
    for pdf in *.pdf; do
        if [ -f "$pdf" ]; then
            count=$((count + 1))
            output_name="${OUTPUT_DIR}/$(basename "${pdf%.pdf}_compressed.pdf")"
            
            echo -e "${YELLOW}[$count] Procesando: $pdf${NC}"
            
            if compress_pdf "$pdf" "$output_name" "$QUALITY" "$COLOR_DPI" "$GRAY_DPI" "$MONO_DPI" false; then
                success=$((success + 1))
                total_original=$((total_original + $(get_file_size_bytes "$pdf")))
                total_compressed=$((total_compressed + $(get_file_size_bytes "$output_name")))
            fi
            echo ""
        fi
    done
    
    # Mostrar resumen
    if [ $count -gt 0 ]; then
        local total_reduction=$((100 - (total_compressed * 100 / total_original)))
        echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}Resumen del Procesamiento Batch:${NC}"
        echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
        echo -e "Total de archivos procesados: $count"
        echo -e "Archivos comprimidos exitosamente: ${GREEN}$success${NC}"
        echo -e "Archivos con errores: ${RED}$((count - success))${NC}"
        echo -e "Reducción total de tamaño: ${GREEN}${total_reduction}%${NC}"
        echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    else
        echo -e "${YELLOW}No se encontraron archivos PDF para procesar${NC}"
    fi
    
    exit 0
fi

# Modo archivo único
if [ -z "$INPUT_FILE" ]; then
    echo -e "${RED}Error: Debes especificar un archivo PDF${NC}"
    echo ""
    show_usage
    exit 1
fi

# Si no se especificó archivo de salida, generarlo automáticamente
if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="${INPUT_FILE%.pdf}_compressed.pdf"
fi

# Comprimir archivo
compress_pdf "$INPUT_FILE" "$OUTPUT_FILE" "$QUALITY" "$COLOR_DPI" "$GRAY_DPI" "$MONO_DPI" "$SHOW_STATS"

exit $?
