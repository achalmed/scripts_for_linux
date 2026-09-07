#!/usr/bin/env bash
# scripts_for_linux/scripts_git_studio/backend/script_git_sync_respos/lib/logging.sh — envoltorio (FS2, 2026-09-07): el logger vive en core/shell-lib/logger.sh; aquí solo lo propio de esta suite.
_core_d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; while [ "$_core_d" != / ] && [ ! -f "$_core_d/core/shell-lib/logger.sh" ]; do _core_d="$(dirname "$_core_d")"; done
[ -f "$_core_d/core/shell-lib/logger.sh" ] || { echo "[ERROR] no encuentro core/shell-lib/logger.sh subiendo desde ${BASH_SOURCE[0]}" >&2; exit 1; }
[[ -n "${_LOGGING_LOADED:-}" ]] && return 0
readonly _LOGGING_LOADED=1
source "$_core_d/core/shell-lib/logger.sh"; unset _core_d

# propio de git_sync: cuadros de paso, cabecera y resumen (con los colores del núcleo)
_C_RED="$CORE_C_RED"; _C_GREEN="$CORE_C_GREEN"; _C_YELLOW="$CORE_C_YELLOW"; _C_BLUE="$CORE_C_BLUE"; _C_BOLD="$CORE_C_BOLD"; _C_NC="$CORE_C_RESET"
log_step() {
    echo ""; echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo -e "${_C_BOLD}  $*${_C_NC}"; echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
}
log_header() {
    echo ""; echo -e "${_C_BLUE}${_C_BOLD}╔════════════════════════════════════════════════════════╗${_C_NC}"
    printf "${_C_BLUE}${_C_BOLD}║  %-52s  ║${_C_NC}\n" "$*"
    echo -e "${_C_BLUE}${_C_BOLD}╚════════════════════════════════════════════════════════╝${_C_NC}"; echo ""
}
log_summary() {
    local ok="$1" skipped="$2" errors="$3" label="${4:-RESUMEN}"
    echo ""; echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo -e "${_C_BOLD}  $label${_C_NC}"; echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"
    echo -e "  ${_C_GREEN}✓  Completados:  $ok${_C_NC}"; echo -e "  ${_C_YELLOW}⊘  Sin cambios: $skipped${_C_NC}"; echo -e "  ${_C_RED}✗  Errores:     $errors${_C_NC}"
    echo -e "${_C_BOLD}══════════════════════════════════════════════════════════${_C_NC}"; echo ""
}
