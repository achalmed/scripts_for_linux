#!/usr/bin/env bash
# lib/ui.sh — Terminal UI helpers for hardlinks-detector.
#
# All box-drawing, separators, and status messages live here.
# Business-logic modules must not call printf/echo directly for
# user-facing output — they call these functions instead.

# ---------------------------------------------------------------------------
# print_header()
# Renders a double-line box header centered to TERM_WIDTH.
# Arguments: $1 - text to display
# ---------------------------------------------------------------------------
print_header() {
    local text="$1"
    local width="${TERM_WIDTH:-80}"
    local inner=$((width - 2))
    local bar
    bar=$(printf '═%.0s' $(seq 1 "$inner"))
    local padding=$(( (inner - ${#text}) / 2 ))
    local right=$(( inner - ${#text} - padding ))

    printf "\n${BOLD}${BLUE}╔%s╗${RESET}\n" "$bar"
    printf "${BOLD}${BLUE}║%*s${BOLD}%s%*s║${RESET}\n" \
        "$padding" "" "$text" "$right" ""
    printf "${BOLD}${BLUE}╚%s╝${RESET}\n\n" "$bar"
}

# ---------------------------------------------------------------------------
# print_separator()
# Renders a single-line separator.
# Arguments: $1 - character to use (default: ─)
# ---------------------------------------------------------------------------
print_separator() {
    local char="${1:-─}"
    local width="${TERM_WIDTH:-80}"
    local line=""
    for (( i=0; i<width; i++ )); do
        line+="$char"
    done
    printf "\n%s%s%s\n\n" "$GRAY" "$line" "$RESET"
}

# ---------------------------------------------------------------------------
# print_field()
# Renders a labeled key-value line.
# Arguments: $1 - icon, $2 - label, $3 - value
# ---------------------------------------------------------------------------
print_field() {
    local icon="$1" label="$2" value="$3"
    printf "${CYAN}%s %s:${RESET} ${BOLD}%s${RESET}\n" "$icon" "$label" "$value"
}

# ---------------------------------------------------------------------------
# Status message helpers
# ---------------------------------------------------------------------------
print_success() { printf "${GREEN}✓${RESET} %s\n" "$1"; }
print_warning() { printf "${YELLOW}⚠${RESET} %s\n" "$1"; }
print_error()   { printf "${RED}✗${RESET} %s\n" "$1" >&2; }
print_info()    { printf "${CYAN}ℹ${RESET} %s\n" "$1"; }

# ---------------------------------------------------------------------------
# format_size()
# BUG FIX: original used bc -l in a loop which fails when bc is absent.
# This implementation uses pure bash arithmetic (integer division)
# so no external tools are required.
# Arguments: $1 - size in bytes
# Outputs: human-readable string to stdout
# ---------------------------------------------------------------------------
format_size() {
    local size=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0

    # Integer division in bash — avoids bc dependency entirely
    while (( size >= 1024 && unit < 4 )); do
        size=$(( size / 1024 ))
        (( unit++ ))
    done

    printf "%d %s" "$size" "${units[$unit]}"
}

# ---------------------------------------------------------------------------
# print_summary_box()
# BUG FIX: original used variable-length arithmetic for padding that broke
# for multi-digit counts. This implementation uses printf's %-Ns to pad
# to a fixed column width regardless of value length.
# Arguments:
#   $1 - number of groups found
#   $2 - total space used (bytes)
#   $3 - total space saved (bytes)
# ---------------------------------------------------------------------------
print_summary_box() {
    local groups="$1"
    local space_used
    local space_saved
    space_used=$(format_size "$2")
    space_saved=$(format_size "$3")

    local inner=76
    local bar
    bar=$(printf '═%.0s' $(seq 1 "$inner"))

    printf "\n${BOLD}${BLUE}╔%s╗${RESET}\n" "$bar"
    printf "${BOLD}${BLUE}║${RESET}  ${GREEN}%-40s${RESET}%*s${BOLD}${BLUE}║${RESET}\n" \
        "📊 Estadísticas de enlaces:" $(( inner - 39 )) ""
    printf "${BOLD}${BLUE}║${RESET}     • %-30s ${BOLD}%-10s${RESET}%*s${BOLD}${BLUE}║${RESET}\n" \
        "Conjuntos encontrados:" "$groups" $(( inner - 48 )) ""
    printf "${BOLD}${BLUE}║${RESET}     • %-30s ${BOLD}%-10s${RESET}%*s${BOLD}${BLUE}║${RESET}\n" \
        "Espacio en disco usado:" "$space_used" $(( inner - 48 )) ""
    printf "${BOLD}${BLUE}║${RESET}     • %-30s ${GREEN}${BOLD}%-10s${RESET}%*s${BOLD}${BLUE}║${RESET}\n" \
        "Espacio ahorrado:" "$space_saved" $(( inner - 48 )) ""
    printf "${BOLD}${BLUE}╚%s╝${RESET}\n" "$bar"
}
