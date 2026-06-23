#!/usr/bin/env bash
# lib/validator.sh — Input and dependency validation for hardlinks-detector.
#
# All environment checks run here before the scan begins so that
# failures are caught early with descriptive messages.

# ---------------------------------------------------------------------------
# validate_directory()
# Ensures the target directory exists and is readable.
# Arguments: $1 - path to validate
# Returns:   0 if valid
# Exits:     EXIT_NOT_FOUND(3) or EXIT_NO_PERMISSION(4) on failure
# ---------------------------------------------------------------------------
validate_directory() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        log_error "No se puede acceder al directorio '${dir}'"
        printf "${GRAY}  Verifica que la ruta sea correcta y el directorio exista.${RESET}\n" >&2
        exit "${EXIT_NOT_FOUND:-3}"
    fi

    if [[ ! -r "$dir" ]]; then
        log_error "Sin permisos de lectura en '${dir}'"
        printf "${GRAY}  Ejecuta: chmod +r '%s'${RESET}\n" "$dir" >&2
        exit "${EXIT_NO_PERMISSION:-4}"
    fi
}

# ---------------------------------------------------------------------------
# validate_output_path()
# Checks that the parent directory of an output file is writable.
# Arguments: $1 - output file path
# Returns:   0 if writable, 1 if not (caller decides whether to exit)
# ---------------------------------------------------------------------------
validate_output_path() {
    local output_file="$1"
    local parent_dir
    parent_dir="$(dirname "$output_file")"

    if [[ ! -w "$parent_dir" ]]; then
        log_error "Sin permisos de escritura en '${parent_dir}' para guardar '${output_file}'"
        return 1
    fi
    return 0
}

# ---------------------------------------------------------------------------
# check_required_tools()
# Verifies that all required external commands are available.
# Exits with EXIT_ERROR(1) listing every missing tool at once
# rather than failing one by one.
# Arguments: none (uses hardcoded list of required tools)
# ---------------------------------------------------------------------------
check_required_tools() {
    local required=("find" "stat" "sort")
    local missing=()

    for tool in "${required[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            missing+=("$tool")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        log_error "Herramientas requeridas no encontradas: ${missing[*]}"
        printf "${GRAY}  Instálalas con: sudo apt install coreutils findutils${RESET}\n" >&2
        exit "${EXIT_ERROR:-1}"
    fi
}
