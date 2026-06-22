#!/usr/bin/env bash
# =============================================================================
# lib/config.sh
# -----------------------------------------------------------------------------
# Parseo del archivo repos-config.yml y exposición de variables globales.
# Todos los demás módulos leen la configuración desde aquí.
# No depende de ningún otro módulo de lib/.
#
# Variables exportadas tras llamar a config_load():
#   BASE_DIR               Ruta absoluta del directorio base de repos
#   DEFAULT_COMMIT_MSG     Mensaje de commit por defecto
#   ALL_REPO_LINES[]       Array "name|branch|enabled" por repositorio
# =============================================================================

[[ -n "${_CONFIG_LOADED:-}" ]] && return 0
readonly _CONFIG_LOADED=1

# =============================================================================
# PARSEO YAML LIGERO
# Diseñado específicamente para la estructura de repos-config.yml.
# No es un parser YAML genérico: solo maneja los campos documentados.
# =============================================================================

# Imprime el valor de base_directory
_config_parse_base_dir() {
    grep -E '^base_directory:' "$1" \
        | sed -E 's/^base_directory:[[:space:]]*//' \
        | sed -E 's/[[:space:]]*$//'
}

# Imprime el valor de default_commit_message
_config_parse_default_msg() {
    grep -E '^default_commit_message:' "$1" \
        | sed -E 's/^default_commit_message:[[:space:]]*"?//' \
        | sed -E 's/"?[[:space:]]*$//'
}

# Imprime una línea "name|branch|enabled" por repositorio
_config_parse_repos() {
    awk '
        /^  - name:/ {
            if (name != "") print name "|" branch "|" enabled
            name = $0
            sub(/^  - name:[[:space:]]*/, "", name)
            gsub(/[[:space:]]+$/, "", name)
            branch  = "main"
            enabled = "true"
            next
        }
        /^    branch:/ {
            branch = $0
            sub(/^    branch:[[:space:]]*/, "", branch)
            gsub(/[[:space:]]+$/, "", branch)
            next
        }
        /^    enabled:/ {
            enabled = $0
            sub(/^    enabled:[[:space:]]*/, "", enabled)
            gsub(/[[:space:]]+$/, "", enabled)
            next
        }
        END { if (name != "") print name "|" branch "|" enabled }
    ' "$1"
}

# =============================================================================
# config_load CONFIG_FILE
#   Carga el archivo de configuración y exporta las variables globales.
#   Retorna 1 si el archivo no existe o está incompleto.
# =============================================================================
config_load() {
    local config_file="$1"

    if [[ ! -f "$config_file" ]]; then
        log_error "Archivo de configuración no encontrado: $config_file"
        log_info  "Crea uno con: $(basename "$0") --init-config"
        return 1
    fi

    BASE_DIR="$(_config_parse_base_dir "$config_file")"
    BASE_DIR="${BASE_DIR/#\~/$HOME}"   # expandir ~ sin depender de eval

    if [[ -z "$BASE_DIR" ]]; then
        log_error "base_directory no definido en $config_file"
        return 1
    fi

    DEFAULT_COMMIT_MSG="$(_config_parse_default_msg "$config_file")"
    [[ -z "$DEFAULT_COMMIT_MSG" ]] && \
        DEFAULT_COMMIT_MSG="update: sincronización automática de contenidos"

    mapfile -t ALL_REPO_LINES < <(_config_parse_repos "$config_file")

    if [[ "${#ALL_REPO_LINES[@]}" -eq 0 ]]; then
        log_error "No se encontraron repositorios en $config_file"
        return 1
    fi

    return 0
}

# =============================================================================
# config_get_enabled_repos [selected_csv]
#   Imprime array de "name|branch" para repos habilitados.
#   Si se pasa selected_csv ("a,b,c"), filtra solo esos nombres.
# =============================================================================
config_get_enabled_repos() {
    local selected_csv="${1:-}"
    local -a wanted=()

    if [[ -n "$selected_csv" ]]; then
        IFS=',' read -ra wanted <<< "$selected_csv"
        # Limpiar espacios
        for i in "${!wanted[@]}"; do
            wanted[$i]="$(echo "${wanted[$i]}" | xargs)"
        done
    fi

    for line in "${ALL_REPO_LINES[@]}"; do
        local name branch enabled
        name="${line%%|*}"
        local rest="${line#*|}"
        branch="${rest%%|*}"
        enabled="${rest##*|}"

        if [[ "${#wanted[@]}" -gt 0 ]]; then
            local found=false
            for w in "${wanted[@]}"; do
                [[ "$name" == "$w" ]] && { found=true; break; }
            done
            $found && echo "${name}|${branch}"
        else
            [[ "$enabled" == "true" ]] && echo "${name}|${branch}"
        fi
    done
}

# =============================================================================
# config_validate_repo_names CONFIG_FILE BASE_DIR
#   Advierte si algún repo habilitado no existe como carpeta .git en BASE_DIR.
# =============================================================================
config_validate_repo_names() {
    local config_file="$1"
    local base="$2"
    local issues=0

    for line in "${ALL_REPO_LINES[@]}"; do
        local name enabled
        name="${line%%|*}"
        enabled="${line##*|}"
        [[ "$enabled" != "true" ]] && continue

        local repo_path="${base}/${name}"
        if [[ ! -d "${repo_path}/.git" ]]; then
            log_warn "Repo '${name}' habilitado pero no encontrado como repo Git en: ${repo_path}"
            ((issues++)) || true
        fi
    done

    return $((issues > 0 ? 1 : 0))
}
