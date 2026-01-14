#!/bin/bash

################################################################################
# Instalador de PDF Compressor v2.0
# Autor: Edison Achalma
# Descripción: Script de instalación para Arch Linux
################################################################################

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Ubicación fija recomendada
INSTALL_DIR="$HOME/Documents/scripts/scripts_for_linux/script_compress_pdf"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PDF Compressor v2.0 - Instalador${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Verificar si se está ejecutando en Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo -e "${YELLOW}Advertencia: Este script está diseñado para Arch Linux${NC}"
    echo -e "${YELLOW}Puede funcionar en otras distribuciones con ajustes${NC}"
    echo ""
    read -p "¿Deseas continuar de todos modos? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${RED}Instalación cancelada${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}Verificando dependencias...${NC}"
echo ""

# Verificar e instalar Ghostscript
if ! command -v gs &> /dev/null; then
    echo -e "${YELLOW}Ghostscript no está instalado${NC}"
    read -p "¿Deseas instalar Ghostscript ahora? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${BLUE}Instalando Ghostscript...${NC}"
        sudo pacman -S --noconfirm ghostscript
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Ghostscript instalado correctamente${NC}"
        else
            echo -e "${RED}✗ Error al instalar Ghostscript${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Ghostscript es necesario para el funcionamiento del script${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ghostscript ya está instalado${NC}"
fi

# Verificar ocrmypdf (opcional)
if ! command -v ocrmypdf &> /dev/null; then
    echo -e "${YELLOW}ocrmypdf no está instalado (opcional)${NC}"
    read -p "¿Deseas instalar ocrmypdf para optimizar PDFs escaneados? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${BLUE}Instalando ocrmypdf...${NC}"
        sudo pacman -S --noconfirm ocrmypdf
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ ocrmypdf instalado correctamente${NC}"
        else
            echo -e "${YELLOW}⚠ No se pudo instalar ocrmypdf (puedes continuar sin él)${NC}"
        fi
    fi
else
    echo -e "${GREEN}✓ ocrmypdf ya está instalado${NC}"
fi

echo ""
echo -e "${CYAN}Selecciona el tipo de instalación:${NC}"
echo ""
echo "1. Instalación en carpeta fija (recomendado)"
echo "   └─ Ubicación: $INSTALL_DIR"
echo "   └─ Incluye wrapper global para ejecutar desde cualquier lugar"
echo ""
echo "2. Instalación global directa"
echo "   └─ Copia el script a /usr/local/bin"
echo ""
echo "3. Solo preparar archivos (sin instalar wrapper)"
echo ""
read -p "Selecciona una opción (1/2/3): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        echo -e "${BLUE}Instalando en carpeta fija...${NC}"
        
        # Crear directorio si no existe
        mkdir -p "$INSTALL_DIR"
        
        # Copiar archivos
        cp compress_pdf.sh "$INSTALL_DIR/"
        cp README.md "$INSTALL_DIR/"
        cp LICENSE "$INSTALL_DIR/"
        
        # Dar permisos
        chmod +x "$INSTALL_DIR/compress_pdf.sh"
        
        # Actualizar pdf-compress con la ruta correcta
        sed -i "s|^SCRIPT_DIR=.*|SCRIPT_DIR=\"$INSTALL_DIR\"|" pdf-compress
        
        # Instalar wrapper globalmente
        echo -e "${BLUE}Instalando wrapper global...${NC}"
        sudo cp pdf-compress /usr/local/bin/
        sudo chmod +x /usr/local/bin/pdf-compress
        
        echo -e "${GREEN}✓ Instalación completada exitosamente${NC}"
        echo ""
        echo -e "${CYAN}Archivos instalados en:${NC}"
        echo "  $INSTALL_DIR/compress_pdf.sh"
        echo "  $INSTALL_DIR/README.md"
        echo "  $INSTALL_DIR/LICENSE"
        echo ""
        echo -e "${CYAN}Wrapper instalado en:${NC}"
        echo "  /usr/local/bin/pdf-compress"
        echo ""
        echo -e "${GREEN}Puedes ejecutar desde cualquier lugar con:${NC}"
        echo "  pdf-compress -r ~/Documents/biblioteca"
        echo ""
        echo -e "${GREEN}O directamente:${NC}"
        echo "  cd $INSTALL_DIR"
        echo "  ./compress_pdf.sh -r ~/Documents/biblioteca"
        ;;
        
    2)
        echo -e "${BLUE}Instalando globalmente...${NC}"
        sudo cp compress_pdf.sh /usr/local/bin/compress-pdf
        sudo chmod +x /usr/local/bin/compress-pdf
        echo -e "${GREEN}✓ Script instalado globalmente${NC}"
        echo -e "${YELLOW}Puedes ejecutarlo con: compress-pdf${NC}"
        ;;
        
    3)
        echo -e "${BLUE}Preparando archivos...${NC}"
        chmod +x compress_pdf.sh
        echo -e "${GREEN}✓ Archivos preparados${NC}"
        echo -e "${YELLOW}Puedes ejecutarlo con: ./compress_pdf.sh${NC}"
        ;;
        
    *)
        echo -e "${RED}Opción no válida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}¡Instalación completada!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

if [[ $REPLY == "1" ]] || [[ $REPLY == "2" ]]; then
    echo -e "${CYAN}Ejemplos de uso:${NC}"
    echo ""
    if [[ $REPLY == "1" ]]; then
        echo "  # Comprimir un archivo"
        echo "  pdf-compress ~/Documents/libro.pdf"
        echo ""
        echo "  # Comprimir recursivamente con método ebook"
        echo "  pdf-compress -m ebook -r ~/Documents/biblioteca"
        echo ""
        echo "  # Máxima compresión"
        echo "  pdf-compress -m screen ~/Documents/presentacion.pdf"
        echo ""
        echo "  # Para PDFs escaneados"
        echo "  pdf-compress -m ocr -r ~/Documents/escaneados"
    else
        echo "  compress-pdf ~/Documents/libro.pdf"
        echo "  compress-pdf -m ebook -r ~/Documents/biblioteca"
        echo "  compress-pdf -m screen ~/Documents/presentacion.pdf"
    fi
fi

echo ""
echo -e "${CYAN}Para ver la ayuda completa:${NC}"
if [[ $REPLY == "1" ]]; then
    echo "  pdf-compress --help"
elif [[ $REPLY == "2" ]]; then
    echo "  compress-pdf --help"
else
    echo "  ./compress_pdf.sh --help"
fi

echo ""
echo -e "${CYAN}Para más información, consulta el README.md${NC}"
echo ""

# Mostrar estadísticas de prueba si existen PDFs en el directorio actual
pdf_count=$(find . -maxdepth 1 -name "*.pdf" 2>/dev/null | wc -l)
if [ $pdf_count -gt 0 ]; then
    echo -e "${YELLOW}Encontré $pdf_count PDF(s) en el directorio actual.${NC}"
    echo -e "${YELLOW}¿Quieres probar el script ahora? (esto es solo una sugerencia)${NC}"
fi

echo ""