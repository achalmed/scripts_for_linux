#!/usr/bin/env bash
# =============================================================================
# lib/validator.sh — Validación de entradas y del entorno
# =============================================================================
# Precondiciones (directorio base, archivo de entrada) y la regla de
# seguridad sobre nombres de carpeta: nunca escribir fuera del directorio
# base, aunque el archivo de lista contenga rutas maliciosas o erróneas.
#
# =============================================================================

# validate_base_dir()
# Comprueba (o crea, previa confirmación) el directorio base y lo
# normaliza a ruta absoluta.
validate_base_dir() {
    OPT_BASE_DIR="${OPT_BASE_DIR/#\~/$HOME}"

    if [[ ! -d "${OPT_BASE_DIR}" ]]; then
        log_warn "El directorio base '${OPT_BASE_DIR}' no existe."
        if ! confirm_action "¿Desea crearlo?"; then
            log_error "Operación cancelada: no existe el directorio base."
            exit 3
        fi
        if ! mkdir -p "${OPT_BASE_DIR}"; then
            log_error "No se pudo crear el directorio base '${OPT_BASE_DIR}'."
            exit 4
        fi
        log_ok "Directorio base creado: ${OPT_BASE_DIR}"
    fi

    if [[ ! -w "${OPT_BASE_DIR}" ]]; then
        log_error "Sin permisos de escritura en '${OPT_BASE_DIR}'."
        exit 4
    fi

    OPT_BASE_DIR="$(cd "${OPT_BASE_DIR}" && pwd)"
    log_verbose "Directorio base: ${OPT_BASE_DIR}"
}

# validate_input_file()
# Solo aplica cuando el usuario pasó -f/--file.
validate_input_file() {
    if [[ -n "${OPT_INPUT_FILE}" ]] && [[ ! -f "${OPT_INPUT_FILE}" ]]; then
        log_error "El archivo '${OPT_INPUT_FILE}' no existe."
        exit 3
    fi
    if [[ -n "${OPT_INPUT_FILE}" ]] && [[ ! -r "${OPT_INPUT_FILE}" ]]; then
        log_error "Sin permisos de lectura sobre '${OPT_INPUT_FILE}'."
        exit 4
    fi
}

# is_safe_folder_name()
# Rechaza nombres que escaparían del directorio base: rutas absolutas
# y cualquier componente "..". Sin esta comprobación, una línea como
# "../../otro" en el archivo de lista escribiría fuera del destino.
#
# Arguments:
#   $1 - nombre de carpeta ya sanitizado
#
# Returns:
#   0 si es seguro, 1 si debe rechazarse
is_safe_folder_name() {
    local folder_name="$1"
    [[ "${folder_name}" == /* ]] && return 1
    [[ "${folder_name}" == ".." ]] && return 1
    [[ "${folder_name}" == ../* ]] && return 1
    [[ "${folder_name}" == */../* ]] && return 1
    [[ "${folder_name}" == */.. ]] && return 1
    return 0
}

# confirm_action()
# Confirmación interactiva unificada. Con --yes o --dry-run no pregunta;
# sin TTY disponible aborta con instrucción clara en vez de colgarse.
#
# Arguments:
#   $1 - pregunta a mostrar
#
# Returns:
#   0 si el usuario acepta, 1 si rechaza
confirm_action() {
    local question="$1"
    if [[ "${OPT_ASSUME_YES}" == "true" ]] || [[ "${OPT_DRY_RUN}" == "true" ]]; then
        return 0
    fi
    if [[ ! -t 0 ]]; then
        log_error "No hay terminal interactiva; use --yes para omitir la confirmación."
        exit 2
    fi
    local reply
    read -r -p "${question} (s/N): " reply
    [[ "${reply}" =~ ^[sS]$ ]]
}
