#!/usr/bin/env bash
# =============================================================================
# main.sh — Project Structure Manager (punto de entrada)
# =============================================================================
# Orchestrator: sources all modules, then runs the generation pipeline.
# This file intentionally contains NO business logic — each responsibility
# lives in its own module under lib/.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# Requires: tree >= 1.7, bash >= 5.0, Kubuntu/Debian
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Module loading
# Resolve the script's real directory so sourcing works regardless of where
# the user calls the script from (absolute path, relative path, symlink, etc.)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

# shellcheck source=lib/logger.sh
source "${SCRIPT_DIR}/lib/logger.sh"

# shellcheck source=lib/validator.sh
source "${SCRIPT_DIR}/lib/validator.sh"

# shellcheck source=lib/cli.sh
source "${SCRIPT_DIR}/lib/cli.sh"

# shellcheck source=lib/tree_utils.sh
source "${SCRIPT_DIR}/lib/tree_utils.sh"

# shellcheck source=lib/generator.sh
source "${SCRIPT_DIR}/lib/generator.sh"

# shellcheck source=lib/stats.sh
source "${SCRIPT_DIR}/lib/stats.sh"

# =============================================================================
# MAIN ORCHESTRATOR
# Order of operations: parse → color setup → validate → dispatch → report
# =============================================================================

main() {
    parse_arguments "$@"
    _setup_colors

    printf "\n${CLR_BOLD}%s v%s${CLR_RESET} — Project Structure Manager\n\n" \
        "${SCRIPT_NAME}" "${SCRIPT_VERSION}"

    validate_dependencies
    validate_projects_root
    validate_target "${TARGET}"

    # --list: enumerate projects and exit without generating any files
    if [[ "${LIST_PROJECTS}" == "true" ]]; then
        list_all_projects
        exit 0
    fi

    local -a target_paths=()
    collect_target_paths target_paths

    if [[ ${#target_paths[@]} -eq 0 ]]; then
        log_warn "No se encontraron proyectos para el target '${TARGET}'."
        exit 0
    fi

    _print_run_summary "${target_paths[@]}"

    # --stats: print disk usage and exit without generating any files
    if [[ "${STATS_ONLY}" == "true" ]]; then
        show_disk_stats "${target_paths[@]}"
        exit 0
    fi

    _run_generation_loop "${target_paths[@]}"

    if [[ "${SHOW_SUMMARY}" == "true" ]]; then
        show_disk_stats "${target_paths[@]}"
        show_summary    "${target_paths[@]}"
    fi

    _print_final_status
}

# _print_run_summary()
# Logs the key run parameters before generation starts.
# Separating this from main() keeps main() under 30 lines.
#
# Arguments:
#   $@ - resolved project paths (used only for count)
_print_run_summary() {
    local -a paths=("$@")
    log_info "Target    : ${TARGET}"
    log_info "Proyectos : ${#paths[@]}"
    log_info "Formato   : ${FORMAT}"
    log_info "Profund.  : ${DEPTH}"
    [[ "${DRY_RUN}" == "true" ]] && \
        log_warn "Modo DRY-RUN activo — no se escribirá ningún archivo."
}

# _run_generation_loop()
# Iterates over all target paths, generates each structure file,
# and tracks successes and failures for the final status line.
#
# Arguments:
#   $@ - list of absolute project directory paths
_run_generation_loop() {
    log_section "Generando estructuras"
    local success_count=0
    local fail_count=0

    for project_path in "$@"; do
        if generate_project_structure "${project_path}"; then
            (( success_count++ )) || true
        else
            (( fail_count++ )) || true
        fi
    done

    # Store counts for _print_final_status()
    _GEN_SUCCESS="${success_count}"
    _GEN_FAIL="${fail_count}"
}

# _print_final_status()
# Prints the completion line using counts stored by _run_generation_loop().
_print_final_status() {
    printf "\n"
    log_ok "Completado — OK: ${_GEN_SUCCESS}  Fallidos: ${_GEN_FAIL}"
    [[ "${DRY_RUN}" == "true" ]] && \
        log_warn "Nada fue escrito (--dry-run activo)."
    printf "\n"
}

main "$@"
