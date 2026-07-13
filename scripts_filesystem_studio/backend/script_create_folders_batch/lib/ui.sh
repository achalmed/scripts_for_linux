#!/usr/bin/env bash
# =============================================================================
# lib/ui.sh — Vista previa y resumen final
# =============================================================================
# Presentación pura: este módulo no crea carpetas ni decide nada,
# solo formatea la información que le pasan main.sh y lib/creator.sh.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# show_preview()
# Muestra destino, total y las primeras PREVIEW_MAX_ITEMS carpetas.
#
# Arguments:
#   $1 - lista de carpetas (una por línea, cruda)
show_preview() {
    local folders_list="$1"
    local raw_line folder_name
    local total=0 displayed=0

    log_section "Vista previa"
    printf "  %-22s %s\n" "Directorio destino:" "${OPT_BASE_DIR}"

    while IFS='' read -r raw_line; do
        folder_name="$(sanitize_folder_name "${raw_line}")"
        [[ -z "${folder_name}" ]] && continue
        total=$((total + 1))
        if (( displayed < PREVIEW_MAX_ITEMS )); then
            printf "    • %s\n" "${folder_name}"
            displayed=$((displayed + 1))
        fi
    done <<< "${folders_list}"

    if (( total > PREVIEW_MAX_ITEMS )); then
        printf "    ${CLR_WARN}... y %d carpeta(s) más${CLR_RESET}\n" $((total - PREVIEW_MAX_ITEMS))
    fi
    printf "  %-22s %s\n\n" "Total de carpetas:" "${total}"

    PREVIEW_TOTAL="${total}"
}

# show_final_summary()
# Resumen con los contadores de lib/creator.sh. En dry-run la etiqueta
# cambia a "se crearían" — la v1.x reportaba "creadas" aun simulando.
show_final_summary() {
    local created_label="Carpetas creadas:"
    [[ "${OPT_DRY_RUN}" == "true" ]] && created_label="Se crearían:"

    log_section "Resumen final"
    printf "  ${CLR_OK}✓ %-20s${CLR_RESET} %s\n" "${created_label}" "${COUNT_CREATED}"
    printf "  ${CLR_WARN}⚠ %-20s${CLR_RESET} %s\n" "Ya existían:" "${COUNT_EXISTED}"
    printf "  ${CLR_WARN}⚠ %-20s${CLR_RESET} %s\n" "Rechazadas:" "${COUNT_REJECTED}"
    printf "  ${CLR_ERROR}✗ %-20s${CLR_RESET} %s\n" "Errores:" "${COUNT_FAILED}"
    printf '\n'

    if [[ "${OPT_DRY_RUN}" == "true" ]]; then
        log_info "Modo DRY-RUN: no se creó ninguna carpeta realmente."
    fi
}
