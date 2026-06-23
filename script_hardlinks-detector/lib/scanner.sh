#!/usr/bin/env bash
# lib/scanner.sh — Hard link discovery for hardlinks-detector.
#
# Uses `find -links +1` to locate all files with more than one
# hard link, then groups them by inode using an associative array.
# The data is stored in module-level globals that renderer.sh reads.

# ---------------------------------------------------------------------------
# Module-level storage (populated by scan_hardlinks, read by renderers)
# ---------------------------------------------------------------------------
declare -A INODE_FILES    # inode → semicolon-separated file paths
declare -A INODE_SIZE     # inode → file size in bytes
declare -A INODE_LINKS    # inode → number of hard links (nlink)
TOTAL_SPACE_USED=0
TOTAL_SPACE_SAVED=0

# ---------------------------------------------------------------------------
# scan_hardlinks()
# Populates the INODE_* globals by scanning the given directory.
#
# Strategy: `find -links +1 -exec stat --format="%i %s %h %n"` outputs
# inode, size, nlink, name in a single pass — one stat call per file
# rather than two (one for inode, one for size) as in the original.
#
# Arguments:
#   $1 - directory to scan
#   $2 - minimum link count filter (default: 2, from MIN_LINKS)
# ---------------------------------------------------------------------------
scan_hardlinks() {
    local dir="$1"
    local min_links="${2:-2}"
    local tmp_file
    tmp_file=$(mktemp)
    # Ensure temp file is removed even if the script is interrupted
    trap "rm -f '$tmp_file'" RETURN

    log_debug "Iniciando escaneo en '${dir}' (min-links=${min_links})…"

    # Single find+stat pass: inode size nlink fullpath
    find "$dir" -type f -links +"$((min_links - 1))" \
        -exec stat --format="%i %s %h %n" {} + 2>/dev/null \
        > "$tmp_file"

    if [[ ! -s "$tmp_file" ]]; then
        log_debug "No se encontraron archivos con hard links."
        return 0
    fi

    # Parse the temp file into associative arrays
    local inode size nlinks filepath
    while IFS=' ' read -r inode size nlinks filepath; do
        [[ -z "$inode" || -z "$filepath" ]] && continue

        INODE_FILES["$inode"]+="${filepath};"

        # Only store size/nlinks once per inode (first occurrence)
        if [[ -z "${INODE_SIZE[$inode]+set}" ]]; then
            INODE_SIZE["$inode"]="$size"
            INODE_LINKS["$inode"]="$nlinks"
            TOTAL_SPACE_USED=$(( TOTAL_SPACE_USED + size ))
            TOTAL_SPACE_SAVED=$(( TOTAL_SPACE_SAVED + size * (nlinks - 1) ))
        fi
    done < "$tmp_file"

    log_debug "Escaneo completado: ${#INODE_FILES[@]} grupo(s) encontrado(s)."
}

# ---------------------------------------------------------------------------
# apply_inode_filter()
# Removes all inode groups from INODE_FILES except the requested one.
# Called after scan_hardlinks when --filter-inode is set.
#
# Arguments: $1 - inode number to keep
# ---------------------------------------------------------------------------
apply_inode_filter() {
    local target_inode="$1"
    local all_inodes=("${!INODE_FILES[@]}")

    for inode in "${all_inodes[@]}"; do
        if [[ "$inode" != "$target_inode" ]]; then
            unset "INODE_FILES[$inode]"
            unset "INODE_SIZE[$inode]"
            unset "INODE_LINKS[$inode]"
        fi
    done

    if [[ -z "${INODE_FILES[$target_inode]+set}" ]]; then
        log_warn "Inodo '${target_inode}' no encontrado en '${DIRECTORY}'."
    fi
}
