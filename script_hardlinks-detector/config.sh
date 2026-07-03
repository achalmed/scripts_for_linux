#!/usr/bin/env bash
# config.sh — Centralized configuration for hardlinks-detector.
#
# All tuneable constants live here. Source this file from every
# other module with: source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

# ---------------------------------------------------------------------------
# VERSION
# ---------------------------------------------------------------------------
readonly VERSION="3.1.0"
readonly AUTHOR="Edison Achalma"
readonly EMAIL="achalmaedison@outlook.com"

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
# AUDIT REPORT (--report)
# The Markdown report is always written to the same fixed path inside the
# project so consecutive runs can be compared with Git. Overwriting the
# previous file is intentional: no timestamps, no automatic history.
# ---------------------------------------------------------------------------
readonly REPORT_DIR_NAME="reports"
readonly REPORT_FILE_NAME="hardlinks-report.md"
readonly CRITICAL_LINKS_THRESHOLD=5   # nlinks needed to flag a file as critical
readonly TOP_SHARED_LIMIT=10          # max rows in the "top shared files" table

# ---------------------------------------------------------------------------
# EXIT CODES (POSIX)
# ---------------------------------------------------------------------------
readonly EXIT_SUCCESS=0
readonly EXIT_ERROR=1
readonly EXIT_BAD_ARGS=2
readonly EXIT_NOT_FOUND=3
readonly EXIT_NO_PERMISSION=4
