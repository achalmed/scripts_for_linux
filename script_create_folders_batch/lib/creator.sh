#!/usr/bin/env bash
# =============================================================================
# lib/creator.sh — Creación de carpetas y contadores de resultado
# =============================================================================
# Cada carpeta termina en exactamente uno de estos contadores globales,
# que lib/ui.sh muestra en el resumen final:
#   COUNT_CREATED  - creadas (o "se crearían" en dry-run)
#   COUNT_EXISTED  - ya existían
#   COUNT_REJECTED - nombres inseguros rechazados por el validador
#   COUNT_FAILED   - mkdir falló (permisos, FS de solo lectura, etc.)
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

declare -g COUNT_CREATED=0
declare -g COUNT_EXISTED=0
declare -g COUNT_REJECTED=0
declare -g COUNT_FAILED=0

# Códigos de retorno internos de create_single_folder(); distinguen
# "ya existía" de "falló", cosa que la v1.x mezclaba en un mismo status
readonly RESULT_CREATED=0
readonly RESULT_FAILED=1
readonly RESULT_EXISTED=2
readonly RESULT_REJECTED=3

# create_single_folder()
# Crea una carpeta (o simula en dry-run). El nombre debe llegar YA
# saneado; la ruta completa se construye después del saneo — la v1.x
# la construía antes y verificaba/creaba rutas con espacios o \r finales.
#
# Arguments:
#   $1 - nombre de carpeta saneado y no vacío
#
# Returns:
#   Uno de los códigos RESULT_* de arriba.
create_single_folder() {
    local folder_name="$1"
    local full_path="${OPT_BASE_DIR}/${folder_name}"

    if ! is_safe_folder_name "${folder_name}"; then
        log_warn "Rechazada (ruta insegura): ${folder_name}"
        return "${RESULT_REJECTED}"
    fi

    if [[ -d "${full_path}" ]]; then
        log_warn "Ya existe: ${folder_name}"
        return "${RESULT_EXISTED}"
    fi

    if [[ "${OPT_DRY_RUN}" == "true" ]]; then
        printf "${CLR_INFO}[DRY-RUN]${CLR_RESET} Se crearía: %s\n" "${folder_name}"
        return "${RESULT_CREATED}"
    fi

    # -p crea subdirectorios intermedios (soporte de "carpeta/subcarpeta")
    if mkdir -p "${full_path}"; then
        log_ok "Creada: ${folder_name}"
        return "${RESULT_CREATED}"
    fi
    log_error "Error al crear: ${folder_name}"
    return "${RESULT_FAILED}"
}

# process_folders_list()
# Recorre la lista completa acumulando resultados en los contadores.
#
# Arguments:
#   $1 - lista de carpetas (una por línea, cruda)
process_folders_list() {
    local folders_list="$1"
    local raw_line folder_name result

    while IFS='' read -r raw_line; do
        folder_name="$(sanitize_folder_name "${raw_line}")"
        [[ -z "${folder_name}" ]] && continue
        log_verbose "Procesando: ${folder_name}"

        # set -e no debe abortar el lote entero por una carpeta fallida
        result=0
        create_single_folder "${folder_name}" || result=$?

        case "${result}" in
            "${RESULT_CREATED}")  COUNT_CREATED=$((COUNT_CREATED + 1)) ;;
            "${RESULT_EXISTED}")  COUNT_EXISTED=$((COUNT_EXISTED + 1)) ;;
            "${RESULT_REJECTED}") COUNT_REJECTED=$((COUNT_REJECTED + 1)) ;;
            *)                    COUNT_FAILED=$((COUNT_FAILED + 1)) ;;
        esac
    done <<< "${folders_list}"
}
