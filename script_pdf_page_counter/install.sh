#!/bin/bash

# Script de instalación rápida para PDF Page Counter
# Autor: Edison Achalma

echo "📦 Instalador de PDF Page Counter"
echo "=================================="
echo ""

# Verificar Python
echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado."
    echo "Por favor, instala Python 3 primero."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION encontrado"
echo ""

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip3 install PyPDF2 openpyxl --break-system-packages

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas correctamente"
else
    echo "⚠️  Hubo problemas instalando dependencias"
    echo "Intenta manualmente: pip3 install PyPDF2 openpyxl"
fi
echo ""

# Dar permisos de ejecución
echo "🔐 Configurando permisos..."
chmod +x pdf_page_counter.py
echo "✅ Permisos configurados"
echo ""

# Probar instalación
echo "🧪 Probando instalación..."
python3 -c "import PyPDF2; import openpyxl; print('✅ Todas las bibliotecas funcionan correctamente')"
echo ""

# Mostrar ayuda
echo "📖 Instalación completada!"
echo ""
echo "Uso básico:"
echo "  python3 pdf_page_counter.py _site"
echo ""
echo "Para ver todas las opciones:"
echo "  python3 pdf_page_counter.py --help"
echo ""
echo "Para más información, consulta README.md"
echo ""
echo "✨ ¡Listo para usar!"
