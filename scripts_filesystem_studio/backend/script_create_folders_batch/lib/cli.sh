#!/usr/bin/env bash
# =============================================================================
# lib/cli.sh — Parseo de argumentos
# =============================================================================
# Mantiene compatibilidad total con las flags cortas de la v1.x
# (-f, -p, -v, -d, -h) y añade sus variantes largas.
#
# =============================================================================

# parse_arguments()
# Rellena las variables globales OPT_* a partir de "$@".
# Sale con código 2 ante opciones desconocidas (error de uso).
parse_arguments() {
    OPT_BASE_DIR="${DEFAULT_BASE_DIR}"
    OPT_INPUT_FILE=""
    OPT_VERBOSE="false"
    OPT_DRY_RUN="false"
    OPT_ASSUME_YES="false"
    OPT_NO_COLOR="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--file)     _require_option_value "$1" "${2:-}"; OPT_INPUT_FILE="$2"; shift 2 ;;
            -p|--path)     _require_option_value "$1" "${2:-}"; OPT_BASE_DIR="$2"; shift 2 ;;
            -v|--verbose)  OPT_VERBOSE="true"; shift ;;
            -d|--dry-run)  OPT_DRY_RUN="true"; shift ;;
            -y|--yes)      OPT_ASSUME_YES="true"; shift ;;
            --no-color)    OPT_NO_COLOR="true"; shift ;;
            --version)     printf '%s %s\n' "${SCRIPT_NAME}" "${SCRIPT_VERSION}"; exit 0 ;;
            -h|--help)     show_help; exit 0 ;;
            *)
                printf 'Opción desconocida: %s\n' "$1" >&2
                show_help >&2
                exit 2
                ;;
        esac
    done
}

# _require_option_value()
# Falla con mensaje claro si una opción que espera valor no lo recibió.
#
# Arguments:
#   $1 - nombre de la opción
#   $2 - valor recibido (posiblemente vacío)
_require_option_value() {
    if [[ -z "$2" ]]; then
        printf 'La opción %s requiere un valor\n' "$1" >&2
        exit 2
    fi
}

show_help() {
    cat << EOF
Uso: $(basename "$0") [OPCIONES]

Crea múltiples carpetas de forma masiva desde una lista predefinida
(editable en config.sh) o desde un archivo externo.

Opciones:
  -f, --file ARCHIVO   Leer nombres de carpetas desde un archivo
  -p, --path RUTA      Directorio base donde crear las carpetas (default: .)
  -d, --dry-run        Simular sin crear carpetas realmente
  -y, --yes            No pedir confirmación interactiva
  -v, --verbose        Mostrar información detallada
      --no-color       Desactivar colores
      --version        Mostrar versión
  -h, --help           Mostrar esta ayuda

Formato del archivo (-f):
  Un nombre de carpeta por línea. Las líneas vacías y las que comienzan
  con # se ignoran. Se admiten subcarpetas relativas (carpeta/subcarpeta);
  se rechazan rutas absolutas y componentes ".." por seguridad.

Ejemplos:
  $(basename "$0")                          # lista predefinida, directorio actual
  $(basename "$0") -f lista.txt             # leer desde archivo
  $(basename "$0") -p ~/proyectos -f l.txt  # crear en otro directorio
  $(basename "$0") -d -f lista.txt          # simular (dry-run)
  $(basename "$0") -y -f lista.txt          # sin confirmación (cron/scripts)
EOF
}
