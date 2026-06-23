#!/usr/bin/env bash
# config.sh — Centralized configuration for hardlinks-detector.
#
# All tuneable constants live here. Source this file from every
# other module with: source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

# ---------------------------------------------------------------------------
# VERSION
# ---------------------------------------------------------------------------
readonly VERSION="3.0.0"
readonly AUTHOR="Edison Achalma"
readonly EMAIL="achalmaedison@gmail.com"

# ---------------------------------------------------------------------------
# DISPLAY
# Terminal width used for box-drawing. 80 is safe for almost all terminals.
# ---------------------------------------------------------------------------
readonly TERM_WIDTH=80

# ---------------------------------------------------------------------------
# COMPANION TOOL
# Referenced in summary and help text to keep the two projects linked.
# ---------------------------------------------------------------------------
readonly COMPANION_TOOL="hardlinks-creator"

# ---------------------------------------------------------------------------
# OUTPUT FORMATS
# Supported values: "tree" | "csv" | "json"
# Can be overridden at runtime with --format FLAG.
# ---------------------------------------------------------------------------
readonly DEFAULT_FORMAT="tree"

# ---------------------------------------------------------------------------
# EXIT CODES (POSIX)
# ---------------------------------------------------------------------------
readonly EXIT_SUCCESS=0
readonly EXIT_ERROR=1
readonly EXIT_BAD_ARGS=2
readonly EXIT_NOT_FOUND=3
readonly EXIT_NO_PERMISSION=4
