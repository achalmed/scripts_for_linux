#!/usr/bin/env bash
# =============================================================================
# lib/scanner.sh — Escaneo del directorio en una sola pasada
# =============================================================================
# Recorre el árbol UNA vez con find -printf (tamaño + nombre) y acumula
# conteo y bytes por extensión en arrays asociativos. La versión 1.x
# relanzaba find + un stat por archivo POR CADA extensión (O(N×M));
# esta pasada única es O(N) y no ejecuta ningún proceso por archivo.
#
# =============================================================================

# Resultados del escaneo, consumidos por lib/renderer.sh
declare -gA EXT_COUNTS=()   # extensión -> cantidad de archivos
declare -gA EXT_SIZES=()    # extensión -> bytes acumulados
declare -g  TOTAL_FILES=0
declare -g  TOTAL_SIZE=0
declare -g  TOTAL_DIRS=0

# extract_extension()
# Normaliza la extensión de un nombre de archivo a minúsculas.
# Los archivos sin punto, y los dotfiles tipo ".bashrc" (cuyo único punto
# es el inicial), se agrupan bajo NO_EXTENSION_LABEL: en la v1.x ".bashrc"
# se contaba erróneamente como extensión "bashrc".
#
# Arguments:
#   $1 - nombre de archivo (sin ruta)
#
# Returns:
#   Imprime la extensión normalizada en stdout.
extract_extension() {
    local filename="${1,,}"
    local base_without_leading_dot="${filename#.}"

    if [[ "${base_without_leading_dot}" != *.* ]]; then
        printf '%s' "${NO_EXTENSION_LABEL}"
    else
        printf '%s' "${filename##*.}"
    fi
}

# scan_directory()
# Llena EXT_COUNTS / EXT_SIZES / TOTAL_* leyendo registros "tamaño\tnombre"
# separados por NUL, seguro ante nombres con espacios o saltos de línea.
#
# Arguments:
#   $1 - directorio raíz (ya validado y absoluto)
scan_directory() {
    local root_dir="$1"
    local record file_size file_name extension

    while IFS='' read -r -d '' record; do
        file_size="${record%%$'\t'*}"
        file_name="${record#*$'\t'}"
        extension="$(extract_extension "${file_name}")"

        EXT_COUNTS["${extension}"]=$(( ${EXT_COUNTS["${extension}"]:-0} + 1 ))
        EXT_SIZES["${extension}"]=$(( ${EXT_SIZES["${extension}"]:-0} + file_size ))
        TOTAL_FILES=$(( TOTAL_FILES + 1 ))
        TOTAL_SIZE=$(( TOTAL_SIZE + file_size ))
    done < <(find "${root_dir}" -type f -printf '%s\t%f\0')

    # Conteo de directorios con -printf '.' para no depender de nombres
    # (un "| wc -l" clásico se rompe con saltos de línea en rutas)
    TOTAL_DIRS="$(find "${root_dir}" -mindepth 1 -type d -printf '.' | wc -c)"
}

# sorted_extension_rows()
# Emite filas "cantidad<TAB>extensión<TAB>bytes" ordenadas por cantidad
# descendente, listas para que el renderer las formatee.
sorted_extension_rows() {
    local extension
    for extension in "${!EXT_COUNTS[@]}"; do
        printf '%d\t%s\t%d\n' \
            "${EXT_COUNTS[${extension}]}" "${extension}" "${EXT_SIZES[${extension}]}"
    done | sort -t $'\t' -k1,1nr -k2,2
}
