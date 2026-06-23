#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      HARDLINKS DETECTOR — MAIN                               ║
# ║                                                                              ║
# ║  Detects and visualizes hard links in a directory tree.                      ║
# ║  Companion tool to hardlinks-creator.                                        ║
# ║                                                                              ║
# ║  Author : Edison Achalma <achalmaedison@gmail.com>                           ║
# ║  Version: 3.0.0                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Fail fast: exit on unset variables and pipeline errors.
# 'set -e' is intentionally omitted because find returns non-zero
# on permission errors in subdirectories, which should not abort the scan.
set -uo pipefail

# ---------------------------------------------------------------------------
# Resolve script directory so source paths work regardless of working dir
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/lib/logger.sh"
source "${SCRIPT_DIR}/lib/ui.sh"
source "${SCRIPT_DIR}/lib/validator.sh"
source "${SCRIPT_DIR}/lib/cli.sh"
source "${SCRIPT_DIR}/lib/scanner.sh"
source "${SCRIPT_DIR}/lib/renderer.sh"

# ---------------------------------------------------------------------------
# Phase 0: Parse arguments (must happen before color disable so logger works)
# ---------------------------------------------------------------------------
parse_arguments "$@"

if [[ "$NO_COLOR" == "true" ]]; then
    disable_colors
fi

# ---------------------------------------------------------------------------
# Phase 1: Resolve working directory
# ---------------------------------------------------------------------------
if [[ -z "$DIRECTORY" ]]; then
    DIRECTORY="$(pwd)"
    log_info "Usando directorio actual: ${BOLD}${DIRECTORY}${RESET}"
else
    log_info "Directorio: ${BOLD}${DIRECTORY}${RESET}"
fi

# ---------------------------------------------------------------------------
# Phase 2: Validate inputs and environment
# ---------------------------------------------------------------------------
check_required_tools
validate_directory "$DIRECTORY"

if [[ -n "$OUTPUT_FILE" ]]; then
    validate_output_path "$OUTPUT_FILE" || exit "${EXIT_ERROR}"
fi

# ---------------------------------------------------------------------------
# Phase 3: Scan
# ---------------------------------------------------------------------------
print_header "HARDLINKS DETECTOR — ANÁLISIS"
print_field "📁" "Directorio" "$DIRECTORY"
print_field "🔍" "Formato de salida" "$FORMAT"
[[ -n "$OUTPUT_FILE" ]] && print_field "💾" "Archivo de salida" "$OUTPUT_FILE"
[[ "$MIN_LINKS" -gt 2 ]] && print_field "🔗" "Mínimo de enlaces" "$MIN_LINKS"
echo ""

log_info "Escaneando directorio en busca de hard links…"
scan_hardlinks "$DIRECTORY" "$MIN_LINKS"

# Apply inode filter if requested
if [[ -n "$FILTER_INODE" ]]; then
    log_debug "Filtrando por inodo: ${FILTER_INODE}"
    apply_inode_filter "$FILTER_INODE"
fi

if (( ${#INODE_FILES[@]} == 0 )); then
    print_success "No se encontraron archivos con hard links en '${DIRECTORY}'."
    print_info "Usa '${COMPANION_TOOL}' para crear hard links entre archivos idénticos."
    exit "${EXIT_SUCCESS}"
fi

log_info "${#INODE_FILES[@]} conjunto(s) de hard links encontrado(s)."

# ---------------------------------------------------------------------------
# Phase 4: Render
# ---------------------------------------------------------------------------
_render_output() {
    case "$FORMAT" in
        tree) render_tree "$DIRECTORY" ;;
        csv)  render_csv  "$DIRECTORY" ;;
        json) render_json "$DIRECTORY" ;;
    esac
}

if [[ -n "$OUTPUT_FILE" ]]; then
    # Write to both console and file simultaneously
    _render_output | tee "$OUTPUT_FILE"
    log_info "Salida guardada en: ${OUTPUT_FILE}"
else
    _render_output
fi

# ---------------------------------------------------------------------------
# Phase 5: Summary (only for tree format — csv/json are machine-readable)
# ---------------------------------------------------------------------------
if [[ "$FORMAT" == "tree" ]]; then
    print_separator
    print_summary_box "${#INODE_FILES[@]}" "$TOTAL_SPACE_USED" "$TOTAL_SPACE_SAVED"

    echo ""
    print_header "GUÍA DE GESTIÓN DE HARD LINKS"

    printf "${BOLD}${CYAN}🔗 ¿Qué son los hard links?${RESET}\n"
    printf "${GRAY}   Múltiples nombres para el mismo archivo físico.\n"
    printf "   Todos comparten contenido, inodo y espacio en disco.${RESET}\n\n"

    printf "${GREEN}   • Eliminar un enlace:${RESET}\n"
    printf "${GRAY}     rm /ruta/archivo   (el archivo persiste mientras quede al menos un enlace)${RESET}\n\n"

    printf "${GREEN}   • Crear un nuevo hard link:${RESET}\n"
    printf "${GRAY}     ln /archivo/existente /nueva/ubicacion/nombre${RESET}\n\n"

    printf "${GREEN}   • Verificar si dos archivos son hard links:${RESET}\n"
    printf "${GRAY}     stat -c '%%i' archivo1 archivo2   (inodos iguales = hard links)${RESET}\n\n"

    printf "${YELLOW}   ⚠  Modificar el contenido afecta TODOS los enlaces.${RESET}\n"
    printf "${YELLOW}   ⚠  Los hard links no funcionan entre sistemas de archivos diferentes.${RESET}\n\n"

    printf "${BOLD}${CYAN}🔧 Herramienta complementaria:${RESET}\n"
    printf "${GRAY}   ${CYAN}${COMPANION_TOOL}${RESET}${GRAY} — crea hard links entre archivos con contenido idéntico.${RESET}\n\n"

    printf "${BOLD}${CYAN}📝 Uso:${RESET}\n"
    printf "${GRAY}   %s [DIRECTORIO] [--format tree|csv|json] [--output FILE]${RESET}\n\n" \
        "$(basename "$0")"

    print_success "Análisis completado."
fi

echo ""
exit "${EXIT_SUCCESS}"
