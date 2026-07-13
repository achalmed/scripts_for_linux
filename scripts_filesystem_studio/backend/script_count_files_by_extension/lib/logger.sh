#!/usr/bin/env bash
# =============================================================================
# lib/logger.sh — Sistema de logging centralizado
# =============================================================================
# Toda la salida hacia el usuario pasa por estas funciones.
# WARN/ERROR van a stderr para que stdout se pueda redirigir sin ruido.
# Los colores se desactivan solos cuando stdout no es una TTY o con --no-color.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# _setup_colors()
# Inicializa las variables de color según la capacidad de la terminal
# y el flag --no-color. Se llama una sola vez al inicio.
_setup_colors() {
    if [[ "${OPT_NO_COLOR}" == "true" ]] || [[ ! -t 1 ]]; then
        CLR_RESET="" CLR_BOLD="" CLR_DIM=""
        CLR_INFO="" CLR_WARN="" CLR_ERROR="" CLR_OK="" CLR_ACCENT=""
    else
        CLR_RESET="\e[0m"
        CLR_BOLD="\e[1m"
        CLR_DIM="\e[2m"
        CLR_INFO="\e[36m"       # cyan
        CLR_WARN="\e[33m"       # amarillo
        CLR_ERROR="\e[31m"      # rojo
        CLR_OK="\e[32m"         # verde
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
# Solo imprime con --verbose activo; detalle diagnóstico que estorbaría
# en una ejecución normal.
log_verbose() {
    if [[ "${OPT_VERBOSE}" == "true" ]]; then
        printf "${CLR_DIM}[DEBUG]${CLR_RESET} %s - %s\n" \
            "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
    fi
}

log_section() {
    printf "\n${CLR_BOLD}${CLR_ACCENT}══ %s ══${CLR_RESET}\n" "$1"
}
