#!/bin/bash

################################################################################
# PDF Compressor - Script de Prueba
# Prueba todos los métodos de compresión en un PDF
# Autor: Edison Achalma
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo.pdf>"
    echo ""
    echo "Este script prueba todos los métodos de compresión disponibles"
    echo "en un PDF para que puedas comparar resultados."
    exit 1
fi

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: El archivo '$INPUT_FILE' no existe${NC}"
    exit 1
fi

if [[ "$INPUT_FILE" != *.pdf ]]; then
    echo -e "${RED}Error: El archivo debe ser un PDF${NC}"
    exit 1
fi

# Función para obtener tamaño
get_size() {
    stat -c%s "$1" 2>/dev/null || echo 0
}

# Función para formatear tamaño
format_size() {
    local size=$1
    if [ $size -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $size/1024}")KB"
    elif [ $size -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $size/1048576}")MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $size/1073741824}")GB"
    fi
}

ORIGINAL_SIZE=$(get_size "$INPUT_FILE")
ORIGINAL_FMT=$(format_size $ORIGINAL_SIZE)

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PDF Compressor - Test de Métodos${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Archivo:         ${CYAN}$(basename "$INPUT_FILE")${NC}"
echo -e "Tamaño original: ${CYAN}$ORIGINAL_FMT${NC}"
echo ""
echo -e "${YELLOW}Probando todos los métodos de compresión...${NC}"
echo ""

# Crear directorio temporal
TEST_DIR=$(mktemp -d /tmp/pdf_test_XXXXXX)

# Array de métodos
METHODS=("screen" "ebook" "printer" "prepress")
declare -A RESULTS

echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"

# Probar cada método
for METHOD in "${METHODS[@]}"; do
    echo -ne "${YELLOW}Probando método '$METHOD'...${NC} "
    
    OUTPUT="$TEST_DIR/${METHOD}_compressed.pdf"
    
    # Comprimir
    gs -sDEVICE=pdfwrite \
       -dCompatibilityLevel=1.4 \
       -dPDFSETTINGS="/$METHOD" \
       -dNOPAUSE \
       -dQUIET \
       -dBATCH \
       -sOutputFile="$OUTPUT" \
       "$INPUT_FILE" 2>/dev/null
    
    if [ $? -eq 0 ] && [ -f "$OUTPUT" ]; then
        SIZE=$(get_size "$OUTPUT")
        RESULTS[$METHOD]=$SIZE
        REDUCTION=$((100 - (SIZE * 100 / ORIGINAL_SIZE)))
        echo -e "${GREEN}✓ OK${NC} - $(format_size $SIZE) (${REDUCTION}% reducción)"
    else
        echo -e "${RED}✗ FALLÓ${NC}"
        RESULTS[$METHOD]=0
    fi
done

echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"

# Probar OCR si está disponible
if command -v ocrmypdf &> /dev/null; then
    echo -ne "${YELLOW}Probando método 'ocr'...${NC} "
    OUTPUT="$TEST_DIR/ocr_compressed.pdf"
    
    ocrmypdf --optimize 3 \
             --output-type pdf \
             --skip-text \
             --tesseract-timeout=0 \
             --quiet \
             "$INPUT_FILE" "$OUTPUT" 2>/dev/null
    
    if [ $? -eq 0 ] && [ -f "$OUTPUT" ]; then
        SIZE=$(get_size "$OUTPUT")
        RESULTS["ocr"]=$SIZE
        REDUCTION=$((100 - (SIZE * 100 / ORIGINAL_SIZE)))
        echo -e "${GREEN}✓ OK${NC} - $(format_size $SIZE) (${REDUCTION}% reducción)"
    else
        echo -e "${RED}✗ FALLÓ${NC}"
        RESULTS["ocr"]=0
    fi
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
else
    echo -e "${YELLOW}Nota: ocrmypdf no está instalado, omitiendo método 'ocr'${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
fi

echo ""
echo -e "${GREEN}Resumen de Resultados${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

printf "%-12s | %-12s | %-12s | %s\n" "Método" "Tamaño" "Reducción" "Recomendación"
echo "──────────────────────────────────────────────────────────────"

# Encontrar el mejor método
BEST_METHOD=""
BEST_SIZE=999999999999

for METHOD in "${!RESULTS[@]}"; do
    SIZE=${RESULTS[$METHOD]}
    
    if [ $SIZE -gt 0 ]; then
        SIZE_FMT=$(format_size $SIZE)
        REDUCTION=$((100 - (SIZE * 100 / ORIGINAL_SIZE)))
        
        # Determinar recomendación
        RECOMMENDATION=""
        case $METHOD in
            screen)
                RECOMMENDATION="Web/Email"
                ;;
            ebook)
                RECOMMENDATION="Lectura digital ⭐"
                ;;
            printer)
                RECOMMENDATION="Imprimir"
                ;;
            prepress)
                RECOMMENDATION="Impresión pro"
                ;;
            ocr)
                RECOMMENDATION="Escaneados ⭐"
                ;;
        esac
        
        printf "%-12s | %-12s | %10s%% | %s\n" "$METHOD" "$SIZE_FMT" "$REDUCTION" "$RECOMMENDATION"
        
        # Actualizar mejor método
        if [ $SIZE -lt $BEST_SIZE ]; then
            BEST_SIZE=$SIZE
            BEST_METHOD=$METHOD
        fi
    fi
done

echo ""
echo -e "${GREEN}Mejor compresión: ${CYAN}$BEST_METHOD${NC} - $(format_size $BEST_SIZE) ($(((100 - (BEST_SIZE * 100 / ORIGINAL_SIZE))))% reducción)"
echo ""

# Recomendación personalizada
echo -e "${CYAN}Recomendación según uso:${NC}"
echo ""
echo "  • Para lectura en pantalla/tablet:"
echo "    ${YELLOW}./compress_pdf.sh -m ebook \"$INPUT_FILE\"${NC}"
echo ""
echo "  • Para compartir online (máxima compresión):"
echo "    ${YELLOW}./compress_pdf.sh -m screen \"$INPUT_FILE\"${NC}"
echo ""
echo "  • Para imprimir:"
echo "    ${YELLOW}./compress_pdf.sh -m printer \"$INPUT_FILE\"${NC}"
echo ""

if command -v ocrmypdf &> /dev/null; then
    echo "  • Si es un PDF escaneado:"
    echo "    ${YELLOW}./compress_pdf.sh -m ocr \"$INPUT_FILE\"${NC}"
    echo ""
fi

# Limpiar
rm -rf "$TEST_DIR"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
