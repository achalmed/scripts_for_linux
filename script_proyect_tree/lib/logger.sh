#!/usr/bin/env bash
# =============================================================================
# lib/logger.sh — Sistema de logging centralizado
# =============================================================================
# All user-facing output goes through these functions.
# stderr is used for WARN/ERROR so stdout stays pipe-safe.
# Colors are suppressed automatically when stdout is not a TTY
# or when --no-color is active.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# _setup_colors()
# Initializes color variables based on terminal capability and --no-color flag.
# Called once at startup — avoids tput calls on every log line.
_setup_colors() {
    if [[ "${NO_COLOR}" == "true" ]] || [[ ! -t 1 ]]; then
        CLR_RESET="" CLR_BOLD="" CLR_DIM=""
        CLR_INFO="" CLR_WARN="" CLR_ERROR="" CLR_OK="" CLR_ACCENT=""
    else
        CLR_RESET="\e[0m"
        CLR_BOLD="\e[1m"
        CLR_DIM="\e[2m"
        CLR_INFO="\e[36m"       # cyan
        CLR_WARN="\e[33m"       # yellow
        CLR_ERROR="\e[31m"      # red
        CLR_OK="\e[32m"         # green
        CLR_ACCENT="\e[35m"     # magenta
    fi
}

log_info() {
    printf "${CLR_INFO}[INFO]${CLR_RESET}  %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

log_ok() {
    printf "${CLR_OK}[OK]${CLR_RESET}    %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

log_warn() {
    printf "${CLR_WARN}[WARN]${CLR_RESET}  %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >&2
}

log_error() {
    printf "${CLR_ERROR}[ERROR]${CLR_RESET} %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >&2
}

# log_verbose()
# Only prints when --verbose is active.
# Used for diagnostic detail that would clutter normal operation.
log_verbose() {
    if [[ "${VERBOSE}" == "true" ]]; then
        printf "${CLR_DIM}[DEBUG]${CLR_RESET} %s - %s\n" \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
    fi
}

log_section() {
    printf "\n${CLR_BOLD}${CLR_ACCENT}══ %s ══${CLR_RESET}\n" "$1"
}
