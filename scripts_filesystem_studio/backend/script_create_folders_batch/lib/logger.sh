#!/usr/bin/env bash
# scripts_for_linux/scripts_filesystem_studio/backend/script_create_folders_batch/lib/logger.sh — envoltorio (FS2, 2026-09-07): el logger vive en core/shell-lib/logger.sh; aquí solo lo propio de esta suite.
_core_d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; while [ "$_core_d" != / ] && [ ! -f "$_core_d/core/shell-lib/logger.sh" ]; do _core_d="$(dirname "$_core_d")"; done
[ -f "$_core_d/core/shell-lib/logger.sh" ] || { echo "[ERROR] no encuentro core/shell-lib/logger.sh subiendo desde ${BASH_SOURCE[0]}" >&2; exit 1; }
source "$_core_d/core/shell-lib/logger.sh"; unset _core_d

# propio de la suite: _setup_colors se llama tras leer --no-color / --verbose (OPT_NO_COLOR, NO_COLOR, OPT_VERBOSE, VERBOSE)
_setup_colors() {
    if [[ "${OPT_NO_COLOR:-}" == "true" || "${NO_COLOR:-}" == "true" || ! -t 1 ]]; then desactivar_colores; else core_colores; fi
}
