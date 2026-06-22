#!/usr/bin/env bash
# =============================================================================
# lib/generator.sh — Descubrimiento de proyectos y generación de archivos
# =============================================================================
# Responsible for two closely related concerns:
#   1. Discovering which project directories match the active TARGET.
#   2. Generating and atomically writing the structure file for each project.
#
# Keeping discovery and generation together avoids passing large arrays
# between modules while still keeping each function under 30 lines.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# find_projects_by_pattern()
# Returns a sorted list of absolute paths matching a glob pattern
# directly under PROJECTS_ROOT. Only real directories are returned.
#
# Arguments:
#   $1 - glob pattern (e.g. "pub_*")
# Stdout   : one absolute path per line, sorted
find_projects_by_pattern() {
    local pattern="$1"
    find "${PROJECTS_ROOT}" \
         -maxdepth 1 \
         -mindepth 1 \
         -type d \
         -name "${pattern}" \
         | sort
}

# collect_target_paths()
# Resolves TARGET into a deduplicated, sorted list of absolute project paths.
# Using a nameref avoids subshell restrictions on returning arrays.
#
# Arguments:
#   $1 - name of the caller's array variable (nameref)
# Modifies : the caller's array with resolved project paths
collect_target_paths() {
    local -n _result_ref="$1"   # nameref to caller's array

    if [[ "${TARGET}" == "all" ]]; then
        for group_key in "${!PROJECT_GROUPS[@]}"; do
            local pattern="${PROJECT_GROUPS[${group_key}]}"
            while IFS= read -r dir; do
                _result_ref+=("${dir}")
            done < <(find_projects_by_pattern "${pattern}")
        done
    elif [[ -v PROJECT_GROUPS["${TARGET}"] ]]; then
        local pattern="${PROJECT_GROUPS[${TARGET}]}"
        while IFS= read -r dir; do
            _result_ref+=("${dir}")
        done < <(find_projects_by_pattern "${pattern}")
    else
        # Exact project name — already validated by validate_target()
        _result_ref+=("${PROJECTS_ROOT}/${TARGET}")
    fi

    # Sort and deduplicate while preserving natural order
    mapfile -t _result_ref < <(printf '%s\n' "${_result_ref[@]}" | sort -u)
}

# _resolve_output_file()
# Determines the full output file path for a given project and format.
# Extension changes with format; the base name stays canonical for txt.
#
# Arguments:
#   $1 - absolute path to the project directory
# Stdout   : absolute path to the output file
_resolve_output_file() {
    local project_path="$1"
    local ext
    case "${FORMAT}" in
        json) ext="json" ;;
        md)   ext="md"   ;;
        *)    ext="txt"  ;;
    esac

    if [[ "${FORMAT}" == "txt" ]]; then
        echo "${project_path}/${OUTPUT_FILENAME}"
    else
        echo "${project_path}/estructura.${ext}"
    fi
}

# _build_tree_output()
# Assembles the full tree output string for the given project.
# Dispatches to the format-specific runner in tree_utils.sh.
#
# Arguments:
#   $1 - absolute path to the project directory
# Stdout   : complete tree output (header + tree body)
_build_tree_output() {
    local project_path="$1"
    case "${FORMAT}" in
        json) run_tree_json     "${project_path}" ;;
        md)   run_tree_markdown "${project_path}" ;;
        *)    build_tree_header "${project_path}"
              run_tree_txt      "${project_path}" ;;
    esac
}

# _write_structure_file()
# Writes content to disk atomically: temp file first, then mv into place.
# Prevents a partial write from corrupting the existing snapshot.
#
# Arguments:
#   $1 - absolute path of the destination file
#   $2 - content string to write
_write_structure_file() {
    local output_file="$1"
    local content="$2"
    local project_path
    project_path="$(dirname "${output_file}")"

    local tmp_file
    tmp_file="$(mktemp "${project_path}/.estructura_tmp.XXXXXX")"
    printf "%s\n" "${content}" > "${tmp_file}"
    mv "${tmp_file}" "${output_file}"
}

# _print_dry_run_preview()
# In dry-run mode, prints what would be written without touching the disk.
# --verbose shows the first 30 lines of the output for a quick sanity check.
#
# Arguments:
#   $1 - output file path that would be written
#   $2 - content string that would be written
_print_dry_run_preview() {
    local output_file="$1"
    local content="$2"

    log_info "[DRY-RUN] Se escribiría: ${output_file}"
    if [[ "${VERBOSE}" == "true" ]]; then
        echo "──────────────────────────────────────────"
        echo "${content}" | head -30
        echo "  ... (preview truncado a 30 líneas)"
        echo "──────────────────────────────────────────"
    fi
}

# generate_project_structure()
# Orchestrates the full pipeline for one project: validate → build → write.
# Returns 1 if the project directory doesn't exist so main() can count failures.
#
# Arguments:
#   $1 - absolute path to the project directory
# Returns  : 0 on success, 1 if directory not found
generate_project_structure() {
    local project_path="$1"
    local project_name
    project_name="$(basename "${project_path}")"

    if [[ ! -d "${project_path}" ]]; then
        log_warn "Directorio no encontrado, omitiendo: '${project_path}'"
        return 1
    fi

    local output_file
    output_file="$(_resolve_output_file "${project_path}")"

    log_verbose "Procesando: ${project_path}"
    log_verbose "Salida en : ${output_file}"

    # Build in memory — a failure here leaves the existing file intact
    local tree_output
    tree_output="$(_build_tree_output "${project_path}")"

    if [[ "${DRY_RUN}" == "true" ]]; then
        _print_dry_run_preview "${output_file}" "${tree_output}"
        return 0
    fi

    _write_structure_file "${output_file}" "${tree_output}"
    log_ok "Actualizado: ${project_name}/$(basename "${output_file}")"
}
