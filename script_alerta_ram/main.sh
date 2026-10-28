#!/usr/bin/env bash
# =============================================================================
#  main.sh — Alerta de RAM
# =============================================================================
#
#  Punto de entrada. Su único rol es orquestar los módulos de lib/:
#    1. Cargar configuración y módulos
#    2. Parsear argumentos CLI
#    3. Inicializar logger
#    4. Validar dependencias según el subcomando
#    5. Ejecutar el subcomando (vigilar · estado · probar · cerrar · instalar · desinstalar)
#
#  La lógica de negocio vive en lib/. main.sh no debería superar ~120 líneas.
# =============================================================================

set -euo pipefail

# --- Directorio del script (funciona desde cualquier CWD) ------------------
# readlink -f: llamado desde el enlace ~/.local/bin/alerta-ram, la suite está donde apunta el enlace.
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# --- Cargar configuración y módulos en orden de dependencia ----------------
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/lib/logger.sh"
source "${SCRIPT_DIR}/lib/validator.sh"
source "${SCRIPT_DIR}/lib/cli.sh"
source "${SCRIPT_DIR}/lib/memoria.sh"
source "${SCRIPT_DIR}/lib/alerta.sh"
source "${SCRIPT_DIR}/lib/ventana.sh"
source "${SCRIPT_DIR}/lib/cierre.sh"
source "${SCRIPT_DIR}/lib/servicio.sh"

# --- main() ----------------------------------------------------------------
main() {
    # --- FASE 1: Parsear argumentos ----------------------------------------
    parse_args "$@"

    # --- FASE 2: Inicializar logger ----------------------------------------
    logger_init "${OPT_VERBOSE}"

    # --- FASE 3: Validar lo que el subcomando necesita ---------------------
    validate_meminfo
    case "${OPT_SUBCOMANDO}" in
        vigilar|probar) validate_sonido_y_avisos ;;
        cerrar)         validate_cierre ;;
        instalar)       validate_plantilla_unidad ;;
    esac

    # --- FASE 4: Ejecutar ---------------------------------------------------
    case "${OPT_SUBCOMANDO}" in
        vigilar)     validate_cierre; vigilar ;;
        estado)      mostrar_estado ;;
        probar)      probar_niveles ;;
        cerrar)      abrir_cierre "$(ram_pct)" ;;
        instalar)    instalar_servicio "${OPT_APLICAR}" ;;
        desinstalar) desinstalar_servicio "${OPT_APLICAR}" ;;
    esac
    return 0
}

main "$@"
