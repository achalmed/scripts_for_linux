#!/usr/bin/env bash
# =============================================================================
# main.sh — Creador masivo de carpetas (punto de entrada)
# =============================================================================
# Orquestador: carga config y módulos, luego ejecuta el pipeline.
# Este archivo NO contiene lógica de negocio; cada responsabilidad
# vive en su propio módulo bajo lib/.
#
# Flujo: parse args → colores → validar → leer lista → vista previa
#        → confirmar → crear → resumen
#
# Depende de: bash >= 4.0
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
# shellcheck source=lib/reader.sh
source "${SCRIPT_DIR}/lib/reader.sh"
# shellcheck source=lib/creator.sh
source "${SCRIPT_DIR}/lib/creator.sh"
# shellcheck source=lib/ui.sh
source "${SCRIPT_DIR}/lib/ui.sh"

main() {
    parse_arguments "$@"
    _setup_colors

    printf "\n${CLR_BOLD}%s v%s${CLR_RESET} — Creador masivo de carpetas\n\n" \
        "${SCRIPT_NAME}" "${SCRIPT_VERSION}"

    validate_base_dir
    validate_input_file

    local folders_list
    folders_list="$(get_folders_list)"

    show_preview "${folders_list}"

    if (( PREVIEW_TOTAL == 0 )); then
        log_warn "La lista no contiene ninguna carpeta que crear."
        exit 0
    fi

    if ! confirm_action "¿Desea continuar con la creación?"; then
        log_warn "Operación cancelada por el usuario."
        exit 0
    fi

    [[ "${OPT_DRY_RUN}" == "true" ]] && \
        log_warn "Modo DRY-RUN activo — no se creará ninguna carpeta."
    log_info "Procesando lista de carpetas..."
    printf '\n'

    process_folders_list "${folders_list}"
    show_final_summary

    if (( COUNT_FAILED > 0 )); then
        log_warn "Proceso completado con errores."
        exit 1
    fi
    log_ok "Proceso completado exitosamente."
}

main "$@"
