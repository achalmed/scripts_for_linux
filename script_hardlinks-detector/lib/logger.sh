#!/usr/bin/env bash
# lib/logger.sh — Centralized logging for hardlinks-detector.
#
# All output goes through these functions so formatting stays
# consistent and can be redirected or silenced from a single place.
#
# Color variables are declared here. Call disable_colors() when
# --no-color is detected to blank them all at once.

# ---------------------------------------------------------------------------
# ANSI COLOR CONSTANTS
# Exported so child modules can reference them after sourcing this file.
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
    BOLD='\033[1m'
    RESET='\033[0m'
    GRAY='\033[0;90m'
    RED='\033[0;91m'
    GREEN='\033[0;92m'
    YELLOW='\033[0;93m'
    BLUE='\033[0;94m'
    CYAN='\033[0;96m'
    WHITE='\033[0;97m'
else
    # Non-interactive terminal (pipe, file redirect) — disable all colors
    BOLD=''; RESET=''; GRAY=''; RED=''; GREEN=''
    YELLOW=''; BLUE=''; CYAN=''; WHITE=''
fi

# ---------------------------------------------------------------------------
# disable_colors()
# Blanks all color variables at runtime (called when --no-color is passed).
# Arguments: none
# ---------------------------------------------------------------------------
disable_colors() {
    BOLD=''; RESET=''; GRAY=''; RED=''; GREEN=''
    YELLOW=''; BLUE=''; CYAN=''; WHITE=''
}

# ---------------------------------------------------------------------------
# Logging functions — all follow the same [LEVEL] timestamp - message format.
# INFO goes to stdout; WARN and ERROR go to stderr.
# ---------------------------------------------------------------------------

# log_info() — informational message
# Arguments: $1 - message
log_info() {
    printf "[${CYAN}INFO${RESET}]  %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

# log_warn() — warning (non-fatal)
# Arguments: $1 - message
log_warn() {
    printf "[${YELLOW}WARN${RESET}]  %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >&2
}

# log_error() — error (typically followed by exit)
# Arguments: $1 - message
log_error() {
    printf "[${RED}ERROR${RESET}] %s - %s\n" \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >&2
}

# log_debug() — only printed when VERBOSE=true
# Arguments: $1 - message
log_debug() {
    if [[ "${VERBOSE:-false}" == "true" ]]; then
        printf "[${GRAY}DEBUG${RESET}] %s - %s\n" \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
    fi
}
