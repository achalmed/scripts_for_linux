#!/usr/bin/env bash
# =============================================================================
# lib/tree_utils.sh — Utilidades de generación de árboles de directorios
# =============================================================================
# Builds exclusion patterns and runs tree in the requested output format.
# All format-specific logic lives here so generate_project_structure()
# in generator.sh stays format-agnostic.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# build_exclude_pattern()
# Combines default + user-supplied exclusions into a single pipe-separated
# string suitable for `tree -I "pattern"`.
# Centralizing this avoids exclusion lists scattered across the codebase.
#
# Arguments: none
# Stdout   : pipe-separated pattern string
build_exclude_pattern() {
    local -a all_dirs=("${DEFAULT_EXCLUDE_DIRS[@]}" "${EXTRA_EXCLUDE_DIRS[@]}")
    local -a all_files=("${DEFAULT_EXCLUDE_FILES[@]}" "${EXTRA_EXCLUDE_FILES[@]}")
    local pattern
    pattern="$(IFS="|"; echo "${all_dirs[*]}|${all_files[*]}")"
    echo "${pattern}"
}

# build_meta_flags()
# Returns the extra flags for file metadata, or empty string if --no-meta.
# Keeping this as a function makes it easy to add more conditions later.
#
# Arguments: none
# Stdout   : flag string (e.g. "-h -D") or empty
build_meta_flags() {
    if [[ "${NO_META}" == "true" ]]; then
        echo ""
    else
        echo "${META_FLAGS}"
    fi
}

# build_tree_header()
# Writes a descriptive header block for the top of txt output files.
# Documenting when and how a snapshot was taken avoids confusion during diffs.
#
# Arguments:
#   $1 - absolute path to the project directory
# Stdout   : multi-line header string
build_tree_header() {
    local project_path="$1"
    local project_name
    project_name="$(basename "${project_path}")"

    cat << EOF
# ============================================================
# Proyecto : ${project_name}
# Ruta     : ${project_path}
# Generado : $(date '+%Y-%m-%d %H:%M:%S')
# Script   : ${SCRIPT_NAME} v${SCRIPT_VERSION}
# Profund. : ${DEPTH} niveles
# Formato  : ${FORMAT}
# Excluye  : $(build_exclude_pattern | tr '|' ' ')
# ============================================================

EOF
}

# run_tree_txt()
# Runs tree in plain text mode for a project directory.
#
# Arguments:
#   $1 - absolute path to the project directory
# Stdout   : tree plain-text output
run_tree_txt() {
    local project_path="$1"
    local exclude_pattern
    exclude_pattern="$(build_exclude_pattern)"
    local meta_flags
    meta_flags="$(build_meta_flags)"

    # shellcheck disable=SC2086
    # meta_flags is intentionally unquoted — it expands to multiple flags
    tree -L "${DEPTH}" \
         --charset UTF-8 \
         -I "${exclude_pattern}" \
         ${meta_flags} \
         "${project_path}" 2>/dev/null
}

# run_tree_json()
# Runs tree in JSON mode. Useful for downstream processing with jq.
# Requires tree >= 1.8 for clean JSON output.
#
# Arguments:
#   $1 - absolute path to the project directory
# Stdout   : JSON tree output
run_tree_json() {
    local project_path="$1"
    local exclude_pattern
    exclude_pattern="$(build_exclude_pattern)"

    tree -L "${DEPTH}" \
         -J \
         -I "${exclude_pattern}" \
         "${project_path}" 2>/dev/null
}

# run_tree_markdown()
# Generates a Markdown document with the tree embedded in a fenced code block.
# Produces a file ready to paste into a project README or wiki.
#
# Arguments:
#   $1 - absolute path to the project directory
# Stdout   : Markdown document string
run_tree_markdown() {
    local project_path="$1"
    local project_name
    project_name="$(basename "${project_path}")"
    local exclude_pattern
    exclude_pattern="$(build_exclude_pattern)"
    local meta_flags
    meta_flags="$(build_meta_flags)"

    cat << EOF
# Estructura: ${project_name}

> Generado el $(date '+%Y-%m-%d %H:%M:%S') con \`${SCRIPT_NAME} v${SCRIPT_VERSION}\`
> Profundidad: ${DEPTH} niveles

\`\`\`
EOF
    # shellcheck disable=SC2086
    tree -L "${DEPTH}" \
         --charset UTF-8 \
         -I "${exclude_pattern}" \
         ${meta_flags} \
         "${project_path}" 2>/dev/null
    echo '```'
}
