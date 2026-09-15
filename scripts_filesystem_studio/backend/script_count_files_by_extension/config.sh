#!/usr/bin/env bash
# =============================================================================
# config.sh — Configuración de count_files_by_extension
# =============================================================================
# Todos los valores editables por el usuario viven aquí; los módulos de lib/
# nunca llevan rutas ni números mágicos hardcodeados.
#
# =============================================================================

readonly SCRIPT_NAME="count-files-by-extension"
readonly SCRIPT_VERSION="2.0.0"

# Directorio analizado cuando no se pasa uno como argumento
readonly DEFAULT_DIRECTORY="${HOME}/Documents/biblioteca"

# Cuántas extensiones mostrar en el ranking "top"
readonly DEFAULT_TOP_COUNT=5

# Ancho máximo (en caracteres) de la barra de porcentaje del ranking
readonly BAR_MAX_WIDTH=50

# Etiqueta usada para agrupar archivos que no tienen extensión
readonly NO_EXTENSION_LABEL="sin_extension"
