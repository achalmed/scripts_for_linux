#!/usr/bin/env bash
# =============================================================================
# config.sh — Configuración central
# =============================================================================
# Single source of truth for every constant and mutable runtime variable.
# All other modules source this file; nothing is hardcoded elsewhere.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_VERSION="2.0.0"
readonly PROJECTS_ROOT="${HOME}/Documents"

# Output file name written inside each project directory
readonly OUTPUT_FILENAME="estructura.txt"

# Groups: each key maps to a glob pattern used by find.
# Add new groups here — collect_target_paths() picks them up automatically.
declare -A PROJECT_GROUPS=(
    [pub]="pub_*"
    [scripts]="scripts_*"
    [campustex]="CampusTeX-*"
    [website]="website-achalma"
)

# Folders excluded from every tree call.
# Covers Quarto artifacts, Python cache, LaTeX aux, Node, git internals,
# and OS metadata — none of these belong in a project snapshot.
DEFAULT_EXCLUDE_DIRS=(
    "_extensions" "_freeze" "_partials" "_site" "site_libs"
    "build" "__pycache__" "log" "output" "temp"
    ".git" ".quarto" "node_modules"
    ".Rproj.user" "index_cache"
    "__MACOSX"
)

# File patterns excluded by default (LaTeX aux, Python bytecode, OS junk).
DEFAULT_EXCLUDE_FILES=(
    "*.aux" "*.log" "*.out" "*.toc"
    "*.bbl" "*.blg" "*.synctex.gz"
    "*.fff" "*.ttt" "*.fls" "*.fdb_latexmk"
    "*.pyc" "*.pyo" "*.egg-info"
    "*.ipynb_checkpoints"
    ".DS_Store" "Thumbs.db" ".Rhistory" ".RData"
    "${OUTPUT_FILENAME}"    # never include the output file in its own tree
)

# Tree depth for full structure snapshots.
# Deeper = more detail; shallower = cleaner overview.
DEFAULT_DEPTH=6

# Extra metadata flags appended to tree (suppressed via --no-meta).
# -h = human-readable sizes  |  -D = last modification date
META_FLAGS="-h -D"

# ---------------------------------------------------------------------------
# Runtime state — all values set here are overridden by parse_arguments()
# ---------------------------------------------------------------------------
VERBOSE=false
DRY_RUN=false
NO_META=false
NO_COLOR=false
FORMAT="txt"        # txt | md | json
TARGET="all"        # all | pub | scripts | campustex | website | <name>
EXTRA_EXCLUDE_DIRS=()
EXTRA_EXCLUDE_FILES=()
DEPTH="${DEFAULT_DEPTH}"
SHOW_SUMMARY=false
LIST_PROJECTS=false
STATS_ONLY=false
