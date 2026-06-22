#!/usr/bin/env bash
# =============================================================================
# lib/stats.sh — Estadísticas, resumen y listado de proyectos
# =============================================================================
# All reporting functions that don't write structure files live here.
# Keeping them separate from generator.sh means the reporting logic
# can evolve independently (e.g. adding JSON output for stats).
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# show_disk_stats()
# Prints a formatted table of disk usage per project.
# du is called per project rather than recursively so the table
# stays readable even with hundreds of projects.
#
# Arguments:
#   $@ - list of absolute project directory paths
show_disk_stats() {
    local -a paths=("$@")

    log_section "Estadísticas de disco"
    printf "\n%-50s %10s %8s\n" "Proyecto" "Tamaño" "Archivos"
    printf "%-50s %10s %8s\n" \
        "$(printf '─%.0s' {1..50})" \
        "$(printf '─%.0s' {1..10})" \
        "$(printf '─%.0s' {1..8})"

    for project_path in "${paths[@]}"; do
        [[ ! -d "${project_path}" ]] && continue
        local name
        name="$(basename "${project_path}")"
        local size
        size="$(du -sh "${project_path}" 2>/dev/null | cut -f1)"
        local file_count
        file_count="$(find "${project_path}" -type f 2>/dev/null | wc -l)"
        printf "%-50s %10s %8s\n" "${name}" "${size}" "${file_count}"
    done
    printf "\n"
}

# show_summary()
# Lists each processed project with a checkmark indicating whether
# the output file exists. In dry-run mode shows a [dry-run] label instead.
#
# Arguments:
#   $@ - list of absolute project directory paths
show_summary() {
    local -a paths=("$@")
    local count="${#paths[@]}"

    log_section "Resumen de proyectos procesados"
    printf "\n  Total: %d proyecto(s)\n\n" "${count}"

    for project_path in "${paths[@]}"; do
        local name
        name="$(basename "${project_path}")"
        local out_file="${project_path}/${OUTPUT_FILENAME}"
        local exists_mark

        if [[ "${DRY_RUN}" == "true" ]]; then
            exists_mark="${CLR_DIM}[dry-run]${CLR_RESET}"
        elif [[ -f "${out_file}" ]]; then
            exists_mark="${CLR_OK}✓${CLR_RESET}"
        else
            exists_mark="${CLR_WARN}✗${CLR_RESET}"
        fi

        printf "  %b  %-45s → %s\n" \
            "${exists_mark}" "${name}" "${out_file}"
    done
    printf "\n"
}

# list_all_projects()
# Enumerates every detected project grouped by type and prints to stdout.
# Exits after printing — intended for --list mode only.
#
# Arguments: none
list_all_projects() {
    log_section "Proyectos detectados en ${PROJECTS_ROOT}"

    for group_key in pub scripts campustex website; do
        local pattern="${PROJECT_GROUPS[${group_key}]}"
        local found=()
        while IFS= read -r dir; do
            found+=("$(basename "${dir}")")
        done < <(find_projects_by_pattern "${pattern}")

        if [[ ${#found[@]} -gt 0 ]]; then
            printf "\n  ${CLR_BOLD}%-12s${CLR_RESET} (%d)\n" \
                "[${group_key}]" "${#found[@]}"
            for name in "${found[@]}"; do
                printf "    • %s\n" "${name}"
            done
        else
            printf "\n  ${CLR_DIM}[%-10s]  (ninguno encontrado)${CLR_RESET}\n" \
                "${group_key}"
        fi
    done
    printf "\n"
}
