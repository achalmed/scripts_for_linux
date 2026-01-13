#!/bin/bash

################################################################################
# Instalador de PDF Compressor
# Autor: Edison Achalma
# Descripción: Script de instalación automática para Arch Linux
################################################################################

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PDF Compressor - Instalador${NC}"
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

# Verificar e instalar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"

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

echo ""
echo -e "${YELLOW}Opciones de instalación:${NC}"
echo "1. Instalación local (solo en este directorio)"
echo "2. Instalación global (disponible en todo el sistema)"
echo "3. Ambas (recomendado)"
echo ""
read -p "Selecciona una opción (1/2/3): " -n 1 -r
echo ""

case $REPLY in
    1)
        # Instalación local
        echo -e "${BLUE}Instalando localmente...${NC}"
        chmod +x compress_pdf.sh
        echo -e "${GREEN}✓ Script instalado localmente${NC}"
        echo -e "${YELLOW}Puedes ejecutarlo con: ./compress_pdf.sh${NC}"
        ;;
    2)
        # Instalación global
        echo -e "${BLUE}Instalando globalmente...${NC}"
        sudo cp compress_pdf.sh /usr/local/bin/compress-pdf
        sudo chmod +x /usr/local/bin/compress-pdf
        echo -e "${GREEN}✓ Script instalado globalmente${NC}"
        echo -e "${YELLOW}Puedes ejecutarlo desde cualquier lugar con: compress-pdf${NC}"
        ;;
    3)
        # Ambas
        echo -e "${BLUE}Instalando en ambos modos...${NC}"
        chmod +x compress_pdf.sh
        sudo cp compress_pdf.sh /usr/local/bin/compress-pdf
        sudo chmod +x /usr/local/bin/compress-pdf
        echo -e "${GREEN}✓ Script instalado localmente y globalmente${NC}"
        echo -e "${YELLOW}Puedes ejecutarlo con: ./compress_pdf.sh o compress-pdf${NC}"
        ;;
    *)
        echo -e "${RED}Opción no válida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}¡Instalación completada exitosamente!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Para ver la ayuda completa, ejecuta:"
if [[ $REPLY == "1" ]]; then
    echo "  ./compress_pdf.sh --help"
else
    echo "  compress-pdf --help"
fi
echo ""
echo "Ejemplos de uso:"
if [[ $REPLY == "1" ]]; then
    echo "  ./compress_pdf.sh documento.pdf"
    echo "  ./compress_pdf.sh -q max presentacion.pdf"
    echo "  ./compress_pdf.sh -b -q high"
else
    echo "  compress-pdf documento.pdf"
    echo "  compress-pdf -q max presentacion.pdf"
    echo "  compress-pdf -b -q high"
fi
echo ""
echo "Para más información, consulta el README.md"
echo ""
