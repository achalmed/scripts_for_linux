#!/usr/bin/env bash
# =============================================================================
# main.sh — Descargador de repos de GitHub (punto de entrada)
# =============================================================================
# Orquestador: carga config y módulos, luego despacha según el modo.
# Este archivo NO contiene lógica de negocio; cada responsabilidad
# vive en su propio módulo bajo lib/.
#
# Flujo: parse args → colores → validar → preparar destino
#        → despachar (single|list|all) → resumen
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# Requires: bash >= 4.3, git; curl y jq solo para el modo "all"
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Carga de módulos
# SCRIPT_DIR se resuelve para que el script funcione desde cualquier CWD
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"
# shellcheck source=lib/logger.sh
source "${SCRIPT_DIR}/lib/logger.sh"
# shellcheck source=lib/cli.sh
source "${SCRIPT_DIR}/lib/cli.sh"
# shellcheck source=lib/validator.sh
source "${SCRIPT_DIR}/lib/validator.sh"
# shellcheck source=lib/github_api.sh
source "${SCRIPT_DIR}/lib/github_api.sh"
# shellcheck source=lib/cloner.sh
source "${SCRIPT_DIR}/lib/cloner.sh"

main() {
    parse_arguments "$@"
    _setup_colors

    printf "\n${CLR_BOLD}%s v%s${CLR_RESET} — Descarga de repos de GitHub\n\n" \
        "${SCRIPT_NAME}" "${SCRIPT_VERSION}"

    validate_options
    validate_dependencies
    prepare_dest_dir
    _print_run_summary

    case "${OPT_MODE}" in
        single) clone_repo "${OPT_REPO_LIST}" ;;
        list)   _clone_repo_list ;;
        all)    _clone_all_repos ;;
    esac

    printf '\n'
    log_ok "Proceso terminado — Descargados: ${COUNT_CLONED}  Omitidos: ${COUNT_SKIPPED}  Fallidos: ${COUNT_FAILED}"
    log_info "Repos en: $(pwd)"
    (( COUNT_FAILED > 0 )) && exit 1
    exit 0
}

# _print_run_summary()
# Muestra los parámetros clave antes de empezar a clonar.
_print_run_summary() {
    log_info "Usuario GitHub : ${OPT_GH_USER}"
    log_info "Destino        : $(pwd)"
    log_info "Profundidad    : ${OPT_DEPTH}"
    log_info "Protocolo      : ${OPT_PROTOCOL}"
    [[ "${OPT_STRIP_GIT}" == "true" ]] && log_info "Modo snapshot  : sin carpeta .git"
    [[ "${OPT_DRY_RUN}" == "true" ]] && \
        log_warn "Modo DRY-RUN activo — no se clonará ningún repo."
    printf '\n'
}

# _clone_repo_list()
# Modo "list": clona los repos indicados en -r, separados por coma.
_clone_repo_list() {
    local -a requested_repos
    IFS=',' read -ra requested_repos <<< "${OPT_REPO_LIST}"

    local repo_name
    for repo_name in "${requested_repos[@]}"; do
        repo_name="${repo_name#"${repo_name%%[![:space:]]*}"}"
        repo_name="${repo_name%"${repo_name##*[![:space:]]}"}"
        [[ -z "${repo_name}" ]] && continue
        clone_repo "${repo_name}"
    done
}

# _clone_all_repos()
# Modo "all": consulta la API, filtra forks y exclusiones, y clona el resto.
_clone_all_repos() {
    log_info "Consultando lista de repos vía API de GitHub..."
    local -a all_repos=()
    mapfile -t all_repos < <(fetch_all_repos)

    if [[ ${#all_repos[@]} -eq 0 ]]; then
        log_error "No se encontraron repos para el usuario '${OPT_GH_USER}'."
        exit 1
    fi

    log_info "Se encontraron ${#all_repos[@]} repos. Iniciando descarga..."
    printf '\n'

    local entry repo_name is_fork
    for entry in "${all_repos[@]}"; do
        repo_name="${entry%%|*}"
        is_fork="${entry##*|}"

        if [[ "${is_fork}" == "true" ]] && [[ "${OPT_INCLUDE_FORKS}" == "false" ]]; then
            log_warn "Omitiendo '${repo_name}' (es un fork; usa -F para incluir forks)."
            COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
            continue
        fi

        if is_excluded_repo "${repo_name}"; then
            log_warn "Omitiendo '${repo_name}' (en lista de exclusión)."
            COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
            continue
        fi

        clone_repo "${repo_name}"
    done
}

main "$@"
