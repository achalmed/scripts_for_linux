#!/usr/bin/env bash
# =============================================================================
# lib/renderer.sh — Presentación de resultados
# =============================================================================
# Tabla por extensión, ranking top-N con barras y estadísticas generales.
# Este módulo solo lee los datos que dejó lib/scanner.sh; no escanea nada.
#
# =============================================================================

# format_size()
# Convierte bytes a una unidad legible (B/KB/MB/GB).
# awk se usa porque bash no tiene aritmética de punto flotante.
#
# Arguments:
#   $1 - tamaño en bytes
format_size() {
    local bytes="${1:-0}"
    if   (( bytes < 1024 ));       then printf '%dB' "${bytes}"
    elif (( bytes < 1048576 ));    then awk -v b="${bytes}" 'BEGIN {printf "%.2fKB", b/1024}'
    elif (( bytes < 1073741824 )); then awk -v b="${bytes}" 'BEGIN {printf "%.2fMB", b/1048576}'
    else                                awk -v b="${bytes}" 'BEGIN {printf "%.2fGB", b/1073741824}'
    fi
}

# render_extension_table()
# Tabla completa: una fila por extensión con cantidad y tamaño acumulado.
render_extension_table() {
    log_section "Archivos por extensión"
    printf "${CLR_BOLD}%-22s %12s %16s${CLR_RESET}\n" "EXTENSIÓN" "CANTIDAD" "TAMAÑO TOTAL"

    local count extension bytes
    while IFS=$'\t' read -r count extension bytes; do
        printf "${CLR_OK}%-22s${CLR_RESET} %12s %16s\n" \
            ".${extension}" "${count}" "$(format_size "${bytes}")"
    done < <(sorted_extension_rows)
}

# render_top_extensions()
# Ranking de las OPT_TOP extensiones más frecuentes con barra de porcentaje.
render_top_extensions() {
    log_section "Top ${OPT_TOP} extensiones más comunes"

    local count extension bytes percentage bar_length bar
    while IFS=$'\t' read -r count extension bytes; do
        percentage="$(awk -v c="${count}" -v t="${TOTAL_FILES}" \
            'BEGIN {printf "%.1f", (c/t)*100}')"
        # La barra escala el porcentaje al ancho configurado; awk de nuevo
        # porque percentage es decimal y $(( )) solo maneja enteros
        bar_length="$(awk -v p="${percentage}" -v w="${BAR_MAX_WIDTH}" \
            'BEGIN {printf "%d", (p*w)/100}')"
        bar="$(printf "%${bar_length}s" '' | tr ' ' '█')"

        printf "  ${CLR_OK}%-16s${CLR_RESET} %6s [${CLR_INFO}%-${BAR_MAX_WIDTH}s${CLR_RESET}] ${CLR_WARN}%5s%%${CLR_RESET}\n" \
            ".${extension}" "${count}" "${bar}" "${percentage}"
    done < <(sorted_extension_rows | head -n "${OPT_TOP}")
}

# render_statistics()
# Resumen global: totales de archivos, directorios y tamaño.
render_statistics() {
    log_section "Estadísticas generales"
    printf "  %-24s %s\n" "Total de archivos:"     "${TOTAL_FILES}"
    printf "  %-24s %s\n" "Total de directorios:"  "${TOTAL_DIRS}"
    printf "  %-24s %s\n" "Tamaño total:"          "$(format_size "${TOTAL_SIZE}")"
    printf "  %-24s %s\n" "Ruta analizada:"        "${OPT_DIRECTORY}"
    printf '\n'
}
