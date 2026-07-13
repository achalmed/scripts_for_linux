#!/usr/bin/env bash
# =============================================================================
# main.sh — Contador de archivos por extensión (punto de entrada)
# =============================================================================
# Orquestador: carga config y módulos, luego ejecuta el pipeline.
# Este archivo NO contiene lógica de negocio; cada responsabilidad
# vive en su propio módulo bajo lib/.
#
# Flujo: parse args → colores → validar → escanear → renderizar
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# Requires: bash >= 4.0, GNU findutils, awk
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
# shellcheck source=lib/scanner.sh
source "${SCRIPT_DIR}/lib/scanner.sh"
# shellcheck source=lib/renderer.sh
source "${SCRIPT_DIR}/lib/renderer.sh"

main() {
    parse_arguments "$@"
    _setup_colors

    printf "\n${CLR_BOLD}%s v%s${CLR_RESET} — Análisis de archivos por extensión\n\n" \
        "${SCRIPT_NAME}" "${SCRIPT_VERSION}"

    validate_dependencies
    validate_top_option
    validate_directory

    log_info "Analizando directorio: ${OPT_DIRECTORY}"
    scan_directory "${OPT_DIRECTORY}"

    if (( TOTAL_FILES == 0 )); then
        log_warn "No se encontraron archivos en el directorio especificado."
        exit 0
    fi

    log_info "Se escanearon ${TOTAL_FILES} archivo(s)."

    render_extension_table
    render_top_extensions
    render_statistics

    log_ok "Análisis completado exitosamente."
}

main "$@"
