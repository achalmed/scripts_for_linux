#!/usr/bin/env bash
# =============================================================================
# lib/validator.sh — Validación de dependencias y entradas
# =============================================================================
# Todas las precondiciones se comprueban aquí, antes de ejecutar cualquier
# lógica, para fallar temprano con mensajes claros y códigos de salida
# estándar (2 uso, 3 no encontrado, 4 permisos, 5 dependencia faltante).
#
# =============================================================================

# validate_dependencies()
# El escáner depende de find con -printf (GNU findutils); se comprueba
# explícitamente porque en sistemas BSD find no soporta esa opción.
validate_dependencies() {
    if ! command -v find > /dev/null 2>&1; then
        log_error "Falta el comando 'find' (GNU findutils)."
        exit 5
    fi
    if ! find /dev/null -printf '' > /dev/null 2>&1; then
        log_error "Este 'find' no soporta -printf (se requiere GNU findutils)."
        exit 5
    fi
}

# validate_top_option()
# --top debe ser un entero positivo; cualquier otra cosa es error de uso.
validate_top_option() {
    if ! [[ "${OPT_TOP}" =~ ^[1-9][0-9]*$ ]]; then
        log_error "El valor de --top debe ser un entero positivo (recibido: '${OPT_TOP}')."
        exit 2
    fi
}

# validate_directory()
# Comprueba existencia y permisos de lectura, y normaliza OPT_DIRECTORY
# a ruta absoluta para que los mensajes sean inequívocos.
validate_directory() {
    if [[ ! -d "${OPT_DIRECTORY}" ]]; then
        log_error "El directorio '${OPT_DIRECTORY}' no existe."
        exit 3
    fi
    if [[ ! -r "${OPT_DIRECTORY}" ]] || [[ ! -x "${OPT_DIRECTORY}" ]]; then
        log_error "Sin permisos de lectura sobre '${OPT_DIRECTORY}'."
        exit 4
    fi
    OPT_DIRECTORY="$(cd "${OPT_DIRECTORY}" && pwd)"
    log_verbose "Directorio normalizado: ${OPT_DIRECTORY}"
}
