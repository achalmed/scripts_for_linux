#!/usr/bin/env bash
# =============================================================================
# lib/cli.sh — Parseo de argumentos
# =============================================================================
# Define y llena las variables OPT_* que el resto de módulos consumen.
# El directorio se acepta como argumento posicional para mantener
# compatibilidad con la versión 1.x del script.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# parse_arguments()
# Rellena las variables globales OPT_* a partir de "$@".
# Sale con código 2 ante opciones desconocidas (error de uso).
#
# Arguments:
#   $@ - argumentos crudos de línea de comandos
parse_arguments() {
    OPT_DIRECTORY="${DEFAULT_DIRECTORY}"
    OPT_TOP="${DEFAULT_TOP_COUNT}"
    OPT_VERBOSE="false"
    OPT_NO_COLOR="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)     show_help; exit 0 ;;
            --version)     printf '%s %s\n' "${SCRIPT_NAME}" "${SCRIPT_VERSION}"; exit 0 ;;
            -v|--verbose)  OPT_VERBOSE="true"; shift ;;
            --no-color)    OPT_NO_COLOR="true"; shift ;;
            -t|--top)      _require_option_value "$1" "${2:-}"; OPT_TOP="$2"; shift 2 ;;
            -*)
                printf 'Opción desconocida: %s\n' "$1" >&2
                show_help >&2
                exit 2
                ;;
            *)             OPT_DIRECTORY="$1"; shift ;;
        esac
    done

    # Expandir "~" manualmente: cuando llega entre comillas la shell no lo hace
    OPT_DIRECTORY="${OPT_DIRECTORY/#\~/$HOME}"
}

# _require_option_value()
# Garantiza que una opción que espera valor realmente lo recibió,
# para fallar con un mensaje claro en vez de un error de bash.
#
# Arguments:
#   $1 - nombre de la opción (para el mensaje de error)
#   $2 - valor recibido (posiblemente vacío)
_require_option_value() {
    if [[ -z "$2" ]]; then
        printf 'La opción %s requiere un valor\n' "$1" >&2
        exit 2
    fi
}

show_help() {
    cat << EOF
Uso: $(basename "$0") [OPCIONES] [directorio]

Analiza recursivamente un directorio y cuenta los archivos agrupados
por extensión, mostrando cantidad y tamaño total por cada una.

Argumentos:
  directorio          Directorio a analizar
                      (por defecto: ${DEFAULT_DIRECTORY})

Opciones:
  -t, --top N         Cuántas extensiones mostrar en el ranking (default: ${DEFAULT_TOP_COUNT})
  -v, --verbose       Mostrar información de diagnóstico
      --no-color      Desactivar colores en la salida
      --version       Mostrar versión
  -h, --help          Mostrar esta ayuda

Ejemplos:
  $(basename "$0")                        # usa el directorio por defecto
  $(basename "$0") ~/Documents            # analiza ~/Documents
  $(basename "$0") -t 10 /ruta/proyecto   # ranking con 10 extensiones
EOF
}
