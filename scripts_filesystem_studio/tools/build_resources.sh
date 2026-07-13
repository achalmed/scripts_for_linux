#!/usr/bin/env bash
# Compila resources/resources.qrc a resources_rc.py (opcional: sin él,
# los iconos se cargan directamente del disco).
set -euo pipefail
cd "$(dirname "$0")/.."
pyside6-rcc resources/resources.qrc -o resources_rc.py
echo "resources_rc.py generado."
