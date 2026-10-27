#!/usr/bin/env bash
# scripts-linux/script_alerta_ram/lib/logger.sh — envoltorio: el logger vive en core/shell-lib/logger.sh; aquí solo lo propio de esta suite.
_core_d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; while [ "$_core_d" != / ] && [ ! -f "$_core_d/core/shell-lib/logger.sh" ]; do _core_d="$(dirname "$_core_d")"; done
[ -f "$_core_d/core/shell-lib/logger.sh" ] || { echo "[ERROR] no encuentro core/shell-lib/logger.sh subiendo desde ${BASH_SOURCE[0]}" >&2; exit 1; }
source "$_core_d/core/shell-lib/logger.sh"; unset _core_d

# propio de la suite: sin archivo de log; bajo systemd la salida va al journal (journalctl --user -u alerta-ram)
logger_init() {
    LOG_VERBOSE="${1:-false}"
    LOG_FILE=""
    return 0
}
