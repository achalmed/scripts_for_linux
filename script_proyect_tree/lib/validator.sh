#!/usr/bin/env bash
# =============================================================================
# lib/validator.sh — Validación de dependencias, rutas y argumentos
# =============================================================================
# All checks run before any tree call is made.
# Failing fast here gives the user a clear, actionable message
# instead of a cryptic error mid-execution.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# validate_dependencies()
# Ensures every external program the script relies on is available.
# Exits with code 5 so callers can distinguish a missing dependency
# from a logic error (code 1) or bad arguments (code 2).
#
# Arguments: none
# Returns  : 0 if all deps found; exits 5 otherwise
validate_dependencies() {
    local missing=0
    for cmd in tree find date du; do
        if ! command -v "${cmd}" &>/dev/null; then
            log_error "Dependencia no encontrada: '${cmd}'"
            missing=1
        fi
    done

    if [[ ${missing} -eq 1 ]]; then
        log_error "Instala las dependencias faltantes y vuelve a intentarlo."
        log_info  "  sudo apt install tree"
        exit 5
    fi
}

# validate_projects_root()
# Confirms PROJECTS_ROOT exists before any work starts.
# A missing root is a configuration error, not a user error.
#
# Arguments: none
# Returns  : 0 if dir exists; exits 3 otherwise
validate_projects_root() {
    if [[ ! -d "${PROJECTS_ROOT}" ]]; then
        log_error "El directorio raíz de proyectos no existe: '${PROJECTS_ROOT}'"
        exit 3
    fi
}

# validate_target()
# Checks that the --target value refers to a known group or a real directory.
# Semantic validation is separated from argument parsing to keep cli.sh lean.
#
# Arguments:
#   $1 - target string provided by the user
# Returns  : 0 if valid; exits 2 otherwise
validate_target() {
    local t="$1"

    # "all" is always valid
    [[ "${t}" == "all" ]] && return 0

    # Known group keys are always valid
    [[ -v PROJECT_GROUPS["${t}"] ]] && return 0

    # Accept exact directory names that actually exist under PROJECTS_ROOT
    if [[ -d "${PROJECTS_ROOT}/${t}" ]]; then
        return 0
    fi

    log_error "Target desconocido: '${t}'"
    log_info  "Usa un grupo (pub, scripts, campustex, website) o el nombre exacto de un proyecto."
    exit 2
}
