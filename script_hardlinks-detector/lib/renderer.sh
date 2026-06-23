#!/usr/bin/env bash
# lib/renderer.sh — Output renderers for hardlinks-detector.
#
# NEW FEATURE: Three output formats (tree, csv, json).
# Each render_* function reads from the INODE_* globals populated
# by scanner.sh and writes to stdout. The caller (main.sh) handles
# tee-ing to a file when --output is set.

# ---------------------------------------------------------------------------
# _build_tree_paths()
# Converts a semicolon-separated path list into a sorted array of
# relative paths for tree display.
# Arguments:
#   $1 - base directory (for relative path calculation)
#   $2 - semicolon-separated absolute paths
# Outputs: sorted relative paths, one per line
# ---------------------------------------------------------------------------
_build_tree_paths() {
    local base_dir="$1"
    local paths_string="$2"
    local IFS=';'
    local -a paths
    read -ra paths <<< "$paths_string"

    local rel
    for path in "${paths[@]}"; do
        [[ -z "$path" ]] && continue
        # realpath --relative-to gives a clean relative path
        rel=$(realpath --relative-to="$base_dir" "$path" 2>/dev/null || echo "$path")
        echo "$rel"
    done | sort
}

# ---------------------------------------------------------------------------
# _print_tree_group()
# Renders one inode group as a hierarchical tree.
# Arguments:
#   $1 - group number
#   $2 - inode
#   $3 - base directory
# ---------------------------------------------------------------------------
_print_tree_group() {
    local group_num="$1"
    local inode="$2"
    local base_dir="$3"
    local size nlinks size_str saved_str

    size="${INODE_SIZE[$inode]}"
    nlinks="${INODE_LINKS[$inode]}"
    size_str=$(format_size "$size")
    saved_str=$(format_size $(( size * (nlinks - 1) )))

    print_separator ""
    printf "${BOLD}${BLUE}Conjunto #%d${RESET}\n" "$group_num"
    printf "  ${GRAY}Inodo:   ${RESET}%s\n" "$inode"
    printf "  ${GRAY}Enlaces: ${RESET}${BOLD}%s${RESET}\n" "$nlinks"
    printf "  ${GRAY}Tamaño:  ${RESET}${BOLD}%s${RESET}\n" "$size_str"
    printf "  ${GRAY}Ahorrado:${RESET} ${GREEN}${BOLD}%s${RESET}\n\n" "$saved_str"

    # Build and print tree
    local -A printed_dirs
    while IFS= read -r rel_path; do
        IFS='/' read -ra parts <<< "$rel_path"
        local current_path=""

        # Print parent directories (only once each)
        for (( i=0; i < ${#parts[@]} - 1; i++ )); do
            if [[ $i -eq 0 ]]; then
                current_path="${parts[$i]}"
            else
                current_path="${current_path}/${parts[$i]}"
            fi
            if [[ -z "${printed_dirs[$current_path]+set}" ]]; then
                printed_dirs["$current_path"]=1
                local indent=""
                for (( j=0; j <= i; j++ )); do
                    indent+="${GRAY}│   ${RESET}"
                done
                printf "%s${BLUE}${BOLD}├── %s/${RESET}\n" "$indent" "${parts[$i]}"
            fi
        done

        # Print the file itself
        local file_indent=""
        for (( i=0; i < ${#parts[@]}; i++ )); do
            file_indent+="${GRAY}│   ${RESET}"
        done
        printf "%s${GREEN}└── %s${RESET}\n" \
            "$file_indent" "${parts[${#parts[@]}-1]}"

    done < <(_build_tree_paths "$base_dir" "${INODE_FILES[$inode]}")

    printf "${GRAY}└──${RESET}\n"
}

# ---------------------------------------------------------------------------
# render_tree()
# Renders all inode groups in tree format.
# Arguments: $1 - base directory
# ---------------------------------------------------------------------------
render_tree() {
    local base_dir="$1"
    local group_num=1

    print_header "ÁRBOL DE ARCHIVOS CON ENLACES DUROS"
    print_field "📂" "Directorio analizado" "$base_dir"
    print_field "🔗" "Total de conjuntos" "${#INODE_FILES[@]}"
    echo ""

    if (( ${#INODE_FILES[@]} == 0 )); then
        print_success "No se encontraron hard links en este directorio."
        return 0
    fi

    for inode in "${!INODE_FILES[@]}"; do
        _print_tree_group "$group_num" "$inode" "$base_dir"
        (( group_num++ ))
    done
}

# ---------------------------------------------------------------------------
# render_csv()
# NEW FEATURE: Exports data as CSV for spreadsheet import.
# Format: inode,nlinks,size_bytes,relative_path
# Arguments: $1 - base directory
# ---------------------------------------------------------------------------
render_csv() {
    local base_dir="$1"

    printf "inode,nlinks,size_bytes,relative_path\n"

    for inode in "${!INODE_FILES[@]}"; do
        local size="${INODE_SIZE[$inode]}"
        local nlinks="${INODE_LINKS[$inode]}"

        while IFS= read -r rel_path; do
            printf "%s,%s,%s,%s\n" "$inode" "$nlinks" "$size" "$rel_path"
        done < <(_build_tree_paths "$base_dir" "${INODE_FILES[$inode]}")
    done
}

# ---------------------------------------------------------------------------
# render_json()
# NEW FEATURE: Exports data as JSON for consumption by CI tools,
# hardlinks-creator's report system, or custom scripts.
# Arguments: $1 - base directory
# ---------------------------------------------------------------------------
render_json() {
    local base_dir="$1"
    local first_group=true

    printf '{\n'
    printf '  "tool": "hardlinks-detector",\n'
    printf '  "version": "%s",\n' "${VERSION:-3.0.0}"
    printf '  "timestamp": "%s",\n' "$(date --iso-8601=seconds)"
    printf '  "directory": "%s",\n' "$base_dir"
    printf '  "total_groups": %d,\n' "${#INODE_FILES[@]}"
    printf '  "total_space_saved_bytes": %d,\n' "$TOTAL_SPACE_SAVED"
    printf '  "groups": [\n'

    for inode in "${!INODE_FILES[@]}"; do
        local size="${INODE_SIZE[$inode]}"
        local nlinks="${INODE_LINKS[$inode]}"

        [[ "$first_group" == "true" ]] && first_group=false || printf ',\n'

        printf '    {\n'
        printf '      "inode": %s,\n' "$inode"
        printf '      "nlinks": %s,\n' "$nlinks"
        printf '      "size_bytes": %s,\n' "$size"
        printf '      "files": [\n'

        local first_file=true
        while IFS= read -r rel_path; do
            [[ "$first_file" == "true" ]] && first_file=false || printf ',\n'
            printf '        "%s"' "$rel_path"
        done < <(_build_tree_paths "$base_dir" "${INODE_FILES[$inode]}")

        printf '\n      ]\n'
        printf '    }'
    done

    printf '\n  ]\n}\n'
}
