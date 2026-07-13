#!/usr/bin/env bash
# =============================================================================
# lib/logging.sh
# -----------------------------------------------------------------------------
# Sistema de logging centralizado con niveles y colores.
# Todos los demás módulos usan estas funciones en vez de echo directo.
#
# Funciones disponibles:
#   log_info  "mensaje"    → [INFO]    texto azul
#   log_ok    "mensaje"    → [OK]      texto verde
#   log_warn  "mensaje"    → [AVISO]   texto amarillo
#   log_error "mensaje"    → [ERROR]   texto rojo   (→ stderr)
#   log_step  "mensaje"    → ──────    separador de sección
#   log_header "título"    → ╔══╗      cabecera de bloque
# =============================================================================

[[ -n "${_LOGGING_LOADED:-}" ]] && return 0
readonly _LOGGING_LOADED=1

# Colores (se desactivan si la salida no es un TTY)
if [[ -t 1 ]]; then
    _C_RED='\033[0;31m'
    _C_GREEN='\033[0;32m'
    _C_YELLOW='\033[1;33m'
    _C_BLUE='\033[0;34m'
    _C_CYAN='\033[0;36m'
    _C_BOLD='\033[1m'
    _C_NC='\033[0m'
else
    _C_RED="" _C_GREEN="" _C_YELLOW="" _C_BLUE="" _C_CYAN="" _C_BOLD="" _C_NC=""
fi

# Variable global: si está en "true", agrega timestamp a cada línea
LOG_TIMESTAMPS="${LOG_TIMESTAMPS:-false}"

_log_ts() {
    [[ "$LOG_TIMESTAMPS" == "true" ]] && echo -n "[$(date '+%H:%M:%S')] "
}

log_info()  { echo -e "$(_log_ts)${_C_BLUE}[INFO]${_C_NC}  $*"; }
log_ok()    { echo -e "$(_log_ts)${_C_GREEN}[OK]${_C_NC}    $*"; }
log_warn()  { echo -e "$(_log_ts)${_C_YELLOW}[AVISO]${_C_NC} $*"; }
log_error() { echo -e "$(_log_ts)${_C_RED}[ERROR]${_C_NC} $*" >&2; }

log_step() {
    echo ""
    echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo -e "${_C_BOLD}  $*${_C_NC}"
    echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
}

log_header() {
    echo ""
    echo -e "${_C_BLUE}${_C_BOLD}╔════════════════════════════════════════════════════════╗${_C_NC}"
    printf "${_C_BLUE}${_C_BOLD}║  %-52s  ║${_C_NC}\n" "$*"
    echo -e "${_C_BLUE}${_C_BOLD}╚════════════════════════════════════════════════════════╝${_C_NC}"
    echo ""
}

# Resumen final con contadores
log_summary() {
    local ok="$1" skipped="$2" errors="$3" label="${4:-RESUMEN}"
    echo ""
    echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo -e "${_C_BOLD}  $label${_C_NC}"
    echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo -e "  ${_C_GREEN}✓  Completados:  $ok${_C_NC}"
    echo -e "  ${_C_YELLOW}⊘  Sin cambios: $skipped${_C_NC}"
    echo -e "  ${_C_RED}✗  Errores:     $errors${_C_NC}"
    echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo ""
}
