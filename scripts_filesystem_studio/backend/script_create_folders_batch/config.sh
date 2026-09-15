#!/usr/bin/env bash
# =============================================================================
# config.sh — Configuración de create_folders_batch
# =============================================================================
# Todos los valores editables por el usuario viven aquí, incluida la lista
# predefinida de carpetas que se usa cuando no se pasa -f/--file.
#
# =============================================================================

readonly SCRIPT_NAME="create-folders-batch"
readonly SCRIPT_VERSION="2.0.0"

# Directorio base por defecto donde se crean las carpetas
readonly DEFAULT_BASE_DIR="."

# Cuántas carpetas mostrar en la vista previa antes de truncar con "... y N más"
readonly PREVIEW_MAX_ITEMS=10

# Lista predefinida de carpetas (una por línea).
# Se usa solo cuando no se proporciona un archivo con -f/--file.
readonly PREDEFINED_FOLDERS='2022-07-131-01-02-manipulacion-de-datos
2022-07-132-01-03-visualizacion-de-datos
2022-07-133-01-04-modelo-de-machine-learning-i-analisis-exploratorio
2022-07-134-01-05-modelo-de-machine-learning-ii-modelo-de-clasificacion
2022-07-135-01-06-modelo-de-machine-learning-iii-modelo-de-regresion
2022-07-136-01-07-modelo-de-machine-learning-iv-tex-mining'
