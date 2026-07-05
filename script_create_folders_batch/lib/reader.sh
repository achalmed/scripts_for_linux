#!/usr/bin/env bash
# =============================================================================
# lib/reader.sh — Lectura y saneamiento de la lista de carpetas
# =============================================================================
# Origen de datos único: archivo externo (-f) o lista predefinida de
# config.sh. Los mensajes de log van a stderr para que NUNCA se mezclen
# con la lista que se emite por stdout.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# get_folders_list()
# Emite por stdout un nombre de carpeta por línea, ya filtrado de
# líneas vacías y comentarios (#).
get_folders_list() {
    if [[ -n "${OPT_INPUT_FILE}" ]]; then
        log_info "Leyendo carpetas desde: ${OPT_INPUT_FILE}" >&2
        # grep devuelve 1 cuando no hay coincidencias; con pipefail eso
        # abortaría el script ante un archivo de solo comentarios,
        # por eso el "|| true"
        grep -v '^[[:space:]]*$' "${OPT_INPUT_FILE}" | grep -v '^[[:space:]]*#' || true
    else
        log_info "Usando lista predefinida de carpetas (config.sh)" >&2
        printf '%s\n' "${PREDEFINED_FOLDERS}"
    fi
}

# sanitize_folder_name()
# Normaliza una línea cruda: quita retornos de carro (\r de archivos
# creados en Windows) y espacios al inicio/final. La v1.x no quitaba
# el \r y creaba carpetas con un retorno de carro invisible en el nombre.
#
# Arguments:
#   $1 - línea cruda del archivo o de la lista predefinida
#
# Returns:
#   Imprime el nombre saneado en stdout (vacío si la línea no tenía contenido).
sanitize_folder_name() {
    local raw_name="$1"
    raw_name="${raw_name//$'\r'/}"
    raw_name="${raw_name#"${raw_name%%[![:space:]]*}"}"   # ltrim
    raw_name="${raw_name%"${raw_name##*[![:space:]]}"}"   # rtrim
    printf '%s' "${raw_name}"
}
