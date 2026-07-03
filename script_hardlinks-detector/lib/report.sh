#!/usr/bin/env bash
# lib/report.sh — Markdown audit report generator for hardlinks-detector.
#
# NEW FEATURE: --report writes an executive audit report to
# reports/hardlinks-report.md inside the project directory. The file is
# always overwritten on purpose — version history is delegated to Git,
# so consecutive runs can be compared with `git diff`.
#
# Single responsibility: transform the INODE_* globals populated by
# scanner.sh into a Markdown document. This module never re-scans the
# filesystem; it only reuses data already in memory.
#
# Depends on: lib/renderer.sh (_build_tree_paths) and lib/ui.sh (format_size).
# Each _report_* function renders exactly one section to stdout;
# generate_report() assembles them and redirects to the report file.

# ---------------------------------------------------------------------------
# Module-level cache (populated once by _report_build_cache)
# Avoids recomputing relative paths for every section of the report.
# ---------------------------------------------------------------------------
declare -A REPORT_REL_PATHS    # inode → newline-separated sorted relative paths
declare -A REPORT_MAIN_FILE    # inode → representative (first) relative path
declare -A REPORT_PATH_COUNT   # inode → number of paths found inside the scan
REPORT_SORTED_INODES=()        # inodes ordered by representative path

# Aggregate stats (computed once by _report_compute_stats)
REPORT_TOTAL_LINKS=0           # sum of nlinks over all groups
REPORT_TOTAL_FILES=0           # total hardlinked paths found in the tree
REPORT_EXTERNAL_GROUPS=0       # groups with links outside the scanned tree
REPORT_ZERO_SIZE_GROUPS=0      # groups whose file size is 0 bytes
REPORT_CRITICAL_COUNT=0        # groups with nlinks >= CRITICAL_LINKS_THRESHOLD

# Fixed category order so the report layout is stable across runs
readonly -a REPORT_CATEGORIES=(
    "SCSS" "JavaScript" "HTML" "YAML" "Markdown" "QMD" "Lua" "Scripts" "Otros"
)

# ---------------------------------------------------------------------------
# _md_escape()
# Escapes pipe characters so file names cannot break Markdown tables.
# Arguments: $1 - raw text
# ---------------------------------------------------------------------------
_md_escape() {
    printf '%s' "${1//|/\\|}"
}

# ---------------------------------------------------------------------------
# _category_of()
# Maps a file path to a report category based on its extension.
# Arguments: $1 - file path
# Outputs: category name (one of REPORT_CATEGORIES)
# ---------------------------------------------------------------------------
_category_of() {
    local name="${1##*/}"
    local ext="${name##*.}"
    [[ "$name" == "$ext" ]] && ext=""   # file without extension

    case "${ext,,}" in
        scss|sass)              echo "SCSS" ;;
        js|mjs|cjs|jsx|ts|tsx)  echo "JavaScript" ;;
        html|htm)               echo "HTML" ;;
        yml|yaml)               echo "YAML" ;;
        md|markdown)            echo "Markdown" ;;
        qmd)                    echo "QMD" ;;
        lua)                    echo "Lua" ;;
        sh|bash|zsh|py|pl|rb)   echo "Scripts" ;;
        *)                      echo "Otros" ;;
    esac
}

# ---------------------------------------------------------------------------
# _detect_os()
# Returns a human-readable OS name without touching the scanned tree.
# Arguments: none
# ---------------------------------------------------------------------------
_detect_os() {
    local pretty=""
    if [[ -r /etc/os-release ]]; then
        # Parse instead of sourcing: os-release defines VERSION, which would
        # collide with our readonly VERSION constant from config.sh
        pretty="$(sed -n 's/^PRETTY_NAME="\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' /etc/os-release)"
    fi
    printf '%s' "${pretty:-$(uname -sr)}"
}

# ---------------------------------------------------------------------------
# _report_build_cache()
# Fills the REPORT_* cache arrays from the INODE_* globals. Inodes are
# ordered by representative path (not by hash order) so the report is
# deterministic and Git diffs between runs stay meaningful.
# Arguments: $1 - base directory
# ---------------------------------------------------------------------------
_report_build_cache() {
    local base_dir="$1"
    local inode rel_paths
    REPORT_SORTED_INODES=()

    for inode in "${!INODE_FILES[@]}"; do
        rel_paths="$(_build_tree_paths "$base_dir" "${INODE_FILES[$inode]}")"
        REPORT_REL_PATHS["$inode"]="$rel_paths"
        REPORT_MAIN_FILE["$inode"]="${rel_paths%%$'\n'*}"
        REPORT_PATH_COUNT["$inode"]="$(printf '%s\n' "$rel_paths" | grep -c .)"
    done

    while IFS=$'\t' read -r _ inode; do
        REPORT_SORTED_INODES+=("$inode")
    done < <(
        for inode in "${!INODE_FILES[@]}"; do
            printf '%s\t%s\n' "${REPORT_MAIN_FILE[$inode]}" "$inode"
        done | sort
    )
}

# ---------------------------------------------------------------------------
# _report_compute_stats()
# Computes the aggregate REPORT_* counters used by several sections.
# Arguments: none (reads the cache and INODE_* globals)
# ---------------------------------------------------------------------------
_report_compute_stats() {
    local inode nlinks count
    REPORT_TOTAL_LINKS=0
    REPORT_TOTAL_FILES=0
    REPORT_EXTERNAL_GROUPS=0
    REPORT_ZERO_SIZE_GROUPS=0
    REPORT_CRITICAL_COUNT=0

    for inode in "${REPORT_SORTED_INODES[@]}"; do
        nlinks="${INODE_LINKS[$inode]}"
        count="${REPORT_PATH_COUNT[$inode]}"
        REPORT_TOTAL_LINKS=$(( REPORT_TOTAL_LINKS + nlinks ))
        REPORT_TOTAL_FILES=$(( REPORT_TOTAL_FILES + count ))
        (( count < nlinks )) && REPORT_EXTERNAL_GROUPS=$(( REPORT_EXTERNAL_GROUPS + 1 ))
        (( INODE_SIZE[$inode] == 0 )) && REPORT_ZERO_SIZE_GROUPS=$(( REPORT_ZERO_SIZE_GROUPS + 1 ))
        (( nlinks >= CRITICAL_LINKS_THRESHOLD )) && REPORT_CRITICAL_COUNT=$(( REPORT_CRITICAL_COUNT + 1 ))
    done
    return 0
}

# ---------------------------------------------------------------------------
# _group_status()
# Status label for one group: OK when every hard link of the inode was
# found inside the scanned tree, Parcial when some live outside it.
# Arguments: $1 - inode
# ---------------------------------------------------------------------------
_group_status() {
    local inode="$1"
    if (( REPORT_PATH_COUNT[$inode] < INODE_LINKS[$inode] )); then
        echo "⚠️ Parcial"
    else
        echo "✅ OK"
    fi
}

# ---------------------------------------------------------------------------
# _group_notes()
# Observation text for one group (external links, or em-dash if clean).
# Arguments: $1 - inode
# ---------------------------------------------------------------------------
_group_notes() {
    local inode="$1"
    local outside=$(( INODE_LINKS[$inode] - REPORT_PATH_COUNT[$inode] ))
    if (( outside > 0 )); then
        echo "${outside} enlace(s) fuera del directorio analizado"
    else
        echo "—"
    fi
}

# ---------------------------------------------------------------------------
# _group_saved()
# Human-readable space saved by one group: size × (nlinks − 1).
# Arguments: $1 - inode
# ---------------------------------------------------------------------------
_group_saved() {
    local inode="$1"
    format_size $(( INODE_SIZE[$inode] * (INODE_LINKS[$inode] - 1) ))
}

# ---------------------------------------------------------------------------
# Section: header with run metadata
# Arguments: $1 - base directory
# ---------------------------------------------------------------------------
_report_metadata() {
    local base_dir="$1"
    cat << EOF
# Reporte de Auditoría — Hard Links

- **Fecha:** $(date '+%Y-%m-%d')
- **Hora:** $(date '+%H:%M:%S')
- **Directorio analizado:** \`${base_dir}\`
- **Tiempo de ejecución:** ${SCAN_DURATION:-0} s
- **Versión:** hardlinks-detector ${VERSION}
- **Sistema operativo:** $(_detect_os)

> Línea base del sistema de hard links. Este archivo se sobrescribe en cada
> ejecución; usa \`git diff\` para comparar con ejecuciones anteriores.
EOF
}

# ---------------------------------------------------------------------------
# Section: executive summary table
# ---------------------------------------------------------------------------
_report_executive_summary() {
    cat << EOF

## Resumen Ejecutivo

| Indicador | Valor |
| --- | ---: |
| Conjuntos de hard links | ${#REPORT_SORTED_INODES[@]} |
| Hard links (suma de enlaces) | ${REPORT_TOTAL_LINKS} |
| Archivos encontrados en el árbol | ${REPORT_TOTAL_FILES} |
| Espacio usado | $(format_size "$TOTAL_SPACE_USED") |
| Espacio ahorrado | $(format_size "$TOTAL_SPACE_SAVED") |
EOF
}

# ---------------------------------------------------------------------------
# Section: general health status derived from the computed stats
# ---------------------------------------------------------------------------
_report_general_status() {
    printf '\n## Estado General\n\n'

    if (( ${#REPORT_SORTED_INODES[@]} == 0 )); then
        printf -- '- ℹ️ No se encontraron conjuntos de hard links en el directorio analizado.\n'
        return 0
    fi

    if (( REPORT_EXTERNAL_GROUPS == 0 )); then
        printf -- '- ✅ Todos los conjuntos están completos dentro del directorio analizado.\n'
    else
        printf -- '- ⚠️ %d conjunto(s) tienen enlaces fuera del directorio analizado.\n' \
            "$REPORT_EXTERNAL_GROUPS"
    fi

    if (( REPORT_ZERO_SIZE_GROUPS == 0 )); then
        printf -- '- ✅ No se detectaron conjuntos con tamaño 0 bytes.\n'
    else
        printf -- '- ⚠️ %d conjunto(s) tienen tamaño 0 bytes (revisar).\n' \
            "$REPORT_ZERO_SIZE_GROUPS"
    fi

    printf -- '- ℹ️ %d archivo(s) crítico(s) con %d o más enlaces.\n' \
        "$REPORT_CRITICAL_COUNT" "$CRITICAL_LINKS_THRESHOLD"
}

# ---------------------------------------------------------------------------
# Section: full inventory — one row per inode group, none omitted
# ---------------------------------------------------------------------------
_report_inventory() {
    printf '\n## Inventario Completo\n\n'

    if (( ${#REPORT_SORTED_INODES[@]} == 0 )); then
        printf 'Sin conjuntos que inventariar.\n'
        return 0
    fi

    printf '| # | Archivo | Tipo | Inodo | Links | Tamaño | Ahorro | Estado | Observaciones |\n'
    printf '| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |\n'

    local inode num=1
    for inode in "${REPORT_SORTED_INODES[@]}"; do
        printf '| %d | `%s` | %s | %s | %s | %s | %s | %s | %s |\n' \
            "$num" \
            "$(_md_escape "${REPORT_MAIN_FILE[$inode]}")" \
            "$(_category_of "${REPORT_MAIN_FILE[$inode]}")" \
            "$inode" \
            "${INODE_LINKS[$inode]}" \
            "$(format_size "${INODE_SIZE[$inode]}")" \
            "$(_group_saved "$inode")" \
            "$(_group_status "$inode")" \
            "$(_group_notes "$inode")"
        (( num++ ))
    done
}

# ---------------------------------------------------------------------------
# Section: groups organized by file category, one table per category
# ---------------------------------------------------------------------------
_report_categories() {
    printf '\n## Agrupación por categorías\n'

    if (( ${#REPORT_SORTED_INODES[@]} == 0 )); then
        printf '\nSin conjuntos que agrupar.\n'
        return 0
    fi

    local category inode printed_header
    for category in "${REPORT_CATEGORIES[@]}"; do
        printed_header=false
        for inode in "${REPORT_SORTED_INODES[@]}"; do
            [[ "$(_category_of "${REPORT_MAIN_FILE[$inode]}")" != "$category" ]] && continue

            if [[ "$printed_header" == "false" ]]; then
                printf '\n### %s\n\n' "$category"
                printf '| Archivo | Inodo | Links | Tamaño | Ahorro |\n'
                printf '| --- | --- | ---: | ---: | ---: |\n'
                printed_header=true
            fi
            printf '| `%s` | %s | %s | %s | %s |\n' \
                "$(_md_escape "${REPORT_MAIN_FILE[$inode]}")" \
                "$inode" \
                "${INODE_LINKS[$inode]}" \
                "$(format_size "${INODE_SIZE[$inode]}")" \
                "$(_group_saved "$inode")"
        done
    done
}

# ---------------------------------------------------------------------------
# Section: top shared files, ordered by link count (descending)
# ---------------------------------------------------------------------------
_report_top_shared() {
    printf '\n## Top archivos más compartidos\n\n'

    if (( ${#REPORT_SORTED_INODES[@]} == 0 )); then
        printf 'Sin conjuntos que ordenar.\n'
        return 0
    fi

    printf '| Posición | Archivo | Links | Tamaño | Ahorro |\n'
    printf '| ---: | --- | ---: | ---: | ---: |\n'

    local inode rank=1
    # Stable sort (-s) keeps path order on ties → deterministic Git diffs
    while IFS=$'\t' read -r _ inode; do
        printf '| %d | `%s` | %s | %s | %s |\n' \
            "$rank" \
            "$(_md_escape "${REPORT_MAIN_FILE[$inode]}")" \
            "${INODE_LINKS[$inode]}" \
            "$(format_size "${INODE_SIZE[$inode]}")" \
            "$(_group_saved "$inode")"
        (( rank++ ))
    done < <(
        for inode in "${REPORT_SORTED_INODES[@]}"; do
            printf '%s\t%s\n' "${INODE_LINKS[$inode]}" "$inode"
        done | sort -s -k1,1nr | head -n "$TOP_SHARED_LIMIT"
    )
}

# ---------------------------------------------------------------------------
# Section: critical files — inferred automatically from the link count
# ---------------------------------------------------------------------------
_report_critical_files() {
    printf '\n## Archivos críticos\n\n'
    printf 'Archivos con **%d o más enlaces**: modificar su contenido afecta a todas sus copias.\n\n' \
        "$CRITICAL_LINKS_THRESHOLD"

    if (( REPORT_CRITICAL_COUNT == 0 )); then
        printf 'No se detectaron archivos críticos con el umbral actual.\n'
        return 0
    fi

    printf '| Archivo | Inodo | Links | Impacto de una modificación |\n'
    printf '| --- | --- | ---: | --- |\n'

    local inode
    for inode in "${REPORT_SORTED_INODES[@]}"; do
        (( INODE_LINKS[$inode] < CRITICAL_LINKS_THRESHOLD )) && continue
        printf '| `%s` | %s | %s | Afecta a %s ubicaciones |\n' \
            "$(_md_escape "${REPORT_MAIN_FILE[$inode]}")" \
            "$inode" \
            "${INODE_LINKS[$inode]}" \
            "${INODE_LINKS[$inode]}"
    done
}

# ---------------------------------------------------------------------------
# Section: per-directory summary (first path component = project)
# Savings are counted where they materialize: size × (copies_in_dir − 1).
# ---------------------------------------------------------------------------
_report_directory_summary() {
    printf '\n## Resumen por directorios\n\n'

    if (( ${#REPORT_SORTED_INODES[@]} == 0 )); then
        printf 'Sin directorios que resumir.\n'
        return 0
    fi

    local inode rel top size
    local -A dir_files=() dir_saved=()
    local -A group_count

    for inode in "${REPORT_SORTED_INODES[@]}"; do
        size="${INODE_SIZE[$inode]}"
        group_count=()
        while IFS= read -r rel; do
            [[ -z "$rel" ]] && continue
            top="${rel%%/*}"
            [[ "$top" == "$rel" ]] && top="(raíz)"
            dir_files["$top"]=$(( ${dir_files["$top"]:-0} + 1 ))
            group_count["$top"]=$(( ${group_count["$top"]:-0} + 1 ))
        done <<< "${REPORT_REL_PATHS[$inode]}"

        for top in "${!group_count[@]}"; do
            if (( group_count["$top"] > 1 )); then
                dir_saved["$top"]=$(( ${dir_saved["$top"]:-0} + size * (group_count["$top"] - 1) ))
            fi
        done
    done

    printf '| Proyecto | Archivos compartidos | Espacio ahorrado |\n'
    printf '| --- | ---: | ---: |\n'

    local dir
    while IFS= read -r dir; do
        printf '| `%s` | %d | %s |\n' \
            "$(_md_escape "$dir")" \
            "${dir_files[$dir]}" \
            "$(format_size "${dir_saved[$dir]:-0}")"
    done < <(printf '%s\n' "${!dir_files[@]}" | sort)

    printf '\n> El ahorro se atribuye al directorio donde existen copias duplicadas\n'
    printf '> del mismo inodo (tamaño × copias adicionales dentro del directorio).\n'
}

# ---------------------------------------------------------------------------
# Section: audit checklist, designed to compare future runs
# ---------------------------------------------------------------------------
_report_checklist() {
    local complete_mark="x" zero_mark="x"
    (( REPORT_EXTERNAL_GROUPS > 0 )) && complete_mark=" "
    (( REPORT_ZERO_SIZE_GROUPS > 0 )) && zero_mark=" "

    cat << EOF

## Checklist de auditoría

- [x] Escaneo completado (${#REPORT_SORTED_INODES[@]} conjunto(s) inventariado(s))
- [${complete_mark}] Todos los conjuntos están completos dentro del directorio analizado
- [${zero_mark}] Ningún conjunto con tamaño 0 bytes
- [ ] Comparado con la ejecución anterior: \`git diff -- ${REPORT_DIR_NAME}/${REPORT_FILE_NAME}\`
- [ ] Revisados los conjuntos marcados como «Parcial» (si existen)
- [ ] Verificado que los archivos críticos siguen sincronizados
EOF
}

# ---------------------------------------------------------------------------
# Section: useful commands for manual verification
# Arguments: $1 - base directory
# ---------------------------------------------------------------------------
_report_useful_commands() {
    local base_dir="$1"
    cat << EOF

## Comandos útiles

\`\`\`bash
# Ver inodo, tamaño y número de enlaces de un archivo
stat -c '%i %s %h %n' archivo

# Localizar todos los enlaces de un inodo específico
find '${base_dir}' -inum INODO

# Localizar todos los enlaces del mismo archivo físico
find '${base_dir}' -samefile archivo

# Listar todos los archivos con más de un hard link
find '${base_dir}' -type f -links +1
\`\`\`
EOF
}

# ---------------------------------------------------------------------------
# Section: auto-generated conclusion
# ---------------------------------------------------------------------------
_report_conclusion() {
    printf '\n## Conclusión\n\n'

    if (( ${#REPORT_SORTED_INODES[@]} == 0 )); then
        printf 'No se detectaron hard links en el directorio analizado. '
        printf 'Usa `%s` para crear hard links entre archivos idénticos.\n' \
            "$COMPANION_TOOL"
        return 0
    fi

    printf 'El análisis identificó **%d conjunto(s)** de hard links que agrupan ' \
        "${#REPORT_SORTED_INODES[@]}"
    printf '**%d archivo(s)**, con un ahorro total de **%s** en disco.\n\n' \
        "$REPORT_TOTAL_FILES" "$(format_size "$TOTAL_SPACE_SAVED")"

    if (( REPORT_EXTERNAL_GROUPS == 0 && REPORT_ZERO_SIZE_GROUPS == 0 )); then
        printf 'No se detectaron inconsistencias: el sistema de hard links se encuentra en buen estado.\n'
    else
        printf 'Se detectaron puntos de atención: %d conjunto(s) con enlaces externos y %d con tamaño 0.\n' \
            "$REPORT_EXTERNAL_GROUPS" "$REPORT_ZERO_SIZE_GROUPS"
        printf 'Revisa la columna «Observaciones» del inventario antes de la próxima ejecución.\n'
    fi
}

# ---------------------------------------------------------------------------
# generate_report()
# Public entry point called by main.sh when --report is set.
# Builds the cache, computes stats, and writes all sections to the
# fixed report path, overwriting the previous file (Git keeps history).
# Arguments: $1 - base directory that was scanned
# ---------------------------------------------------------------------------
generate_report() {
    local base_dir="$1"
    local report_dir="${SCRIPT_DIR}/${REPORT_DIR_NAME}"
    local report_file="${report_dir}/${REPORT_FILE_NAME}"

    if ! mkdir -p "$report_dir"; then
        log_error "No se pudo crear la carpeta de reportes: '${report_dir}'"
        return 1
    fi

    log_debug "Generando reporte de auditoría en '${report_file}'…"
    _report_build_cache "$base_dir"
    _report_compute_stats

    {
        _report_metadata "$base_dir"
        _report_executive_summary
        _report_general_status
        _report_inventory
        _report_categories
        _report_top_shared
        _report_critical_files
        _report_directory_summary
        _report_checklist
        _report_useful_commands "$base_dir"
        _report_conclusion
    } > "$report_file"

    log_info "Reporte de auditoría generado: ${report_file}"
    print_success "Reporte Markdown actualizado — compara con: git diff -- ${REPORT_DIR_NAME}/${REPORT_FILE_NAME}"
}
