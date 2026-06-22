#!/usr/bin/env bash
# =============================================================================
# lib/cli.sh — Interfaz de línea de comandos
# =============================================================================
# Parses all CLI flags into global variables declared in config.sh.
# Centralizing argument parsing here keeps main.sh clean and makes
# adding new flags a one-file change.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# show_help()
# Prints full usage information to stdout and returns.
# Callers are responsible for exiting with the appropriate code.
show_help() {
    cat << EOF
${CLR_BOLD}Uso:${CLR_RESET} ${SCRIPT_NAME} [OPCIONES]

${CLR_BOLD}Descripción:${CLR_RESET}
  Genera y actualiza archivos '${OUTPUT_FILENAME}' con la estructura de
  directorios de los proyectos en ${PROJECTS_ROOT}.

${CLR_BOLD}Opciones de selección:${CLR_RESET}
  -t, --target TARGET     Qué actualizar (default: all)
                          Valores: all | pub | scripts | campustex | website
                                   | <nombre-exacto-del-proyecto>
  -L, --depth N           Profundidad del árbol (default: ${DEFAULT_DEPTH})

${CLR_BOLD}Opciones de exclusión:${CLR_RESET}
  -X, --exclude-dir DIR   Excluir carpeta adicional (repetible)
  -x, --exclude-file PAT  Excluir patrón de archivo adicional (repetible)

${CLR_BOLD}Opciones de formato:${CLR_RESET}
  -f, --format FORMAT     Formato de salida: txt | md | json (default: txt)
      --no-meta           Omitir tamaños y fechas del árbol

${CLR_BOLD}Opciones de información:${CLR_RESET}
  -l, --list              Listar todos los proyectos detectados y salir
  -s, --summary           Mostrar resumen de proyectos al finalizar
      --stats             Mostrar solo estadísticas (sin generar archivos)

${CLR_BOLD}Opciones generales:${CLR_RESET}
  -v, --verbose           Mostrar información de depuración
      --dry-run           Simular sin escribir ningún archivo
      --no-color          Deshabilitar colores
      --version           Mostrar versión
  -h, --help              Mostrar esta ayuda

${CLR_BOLD}Ejemplos:${CLR_RESET}
  # Actualizar todos los proyectos
  ${SCRIPT_NAME}

  # Actualizar solo las publicaciones
  ${SCRIPT_NAME} --target pub

  # Actualizar un proyecto específico
  ${SCRIPT_NAME} --target pub_numerus-scriptum

  # Ver estructura sin guardar nada
  ${SCRIPT_NAME} --target pub_numerus-scriptum --dry-run --verbose

  # Formato Markdown con profundidad 4
  ${SCRIPT_NAME} --target website --format md --depth 4

  # Excluir carpetas adicionales en esta ejecución
  ${SCRIPT_NAME} --target pub --exclude-dir "data" --exclude-dir "raw"

  # Listar proyectos detectados
  ${SCRIPT_NAME} --list

  # Ver estadísticas de disco sin tocar archivos
  ${SCRIPT_NAME} --stats --target campustex

EOF
}

# _parse_target()
# Extracts and validates the --target / -t flag value.
# Separated to keep parse_arguments() under 30 lines.
#
# Arguments:
#   $1 - the value following --target
_parse_target() {
    [[ -z "${1:-}" ]] && { log_error "--target requiere un valor."; exit 2; }
    TARGET="$1"
}

# _parse_depth()
# Extracts and validates the --depth / -L flag value.
# Rejects non-integer values immediately rather than letting tree fail later.
#
# Arguments:
#   $1 - the value following --depth
_parse_depth() {
    [[ -z "${1:-}" ]] && { log_error "--depth requiere un valor numérico."; exit 2; }
    if ! [[ "$1" =~ ^[0-9]+$ ]]; then
        log_error "--depth debe ser un número entero positivo."
        exit 2
    fi
    DEPTH="$1"
}

# _parse_format()
# Extracts and validates the --format / -f flag value.
# Allowlist approach — rejects anything not explicitly supported.
#
# Arguments:
#   $1 - the value following --format
_parse_format() {
    [[ -z "${1:-}" ]] && { log_error "--format requiere un valor."; exit 2; }
    case "$1" in
        txt|md|json) FORMAT="$1" ;;
        *) log_error "Formato inválido: '$1'. Usa: txt | md | json"; exit 2 ;;
    esac
}

# parse_arguments()
# Reads all CLI flags and populates the global variables in config.sh.
# Type validation happens here; semantic validation is in validator.sh.
#
# Arguments:
#   $@ - all arguments passed to the script
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target|-t)      _parse_target  "${2:-}"; shift 2 ;;
            --depth|-L)       _parse_depth   "${2:-}"; shift 2 ;;
            --format|-f)      _parse_format  "${2:-}"; shift 2 ;;
            --exclude-dir|-X)
                [[ -z "${2:-}" ]] && { log_error "--exclude-dir requiere un valor."; exit 2; }
                EXTRA_EXCLUDE_DIRS+=("$2"); shift 2 ;;
            --exclude-file|-x)
                [[ -z "${2:-}" ]] && { log_error "--exclude-file requiere un valor."; exit 2; }
                EXTRA_EXCLUDE_FILES+=("$2"); shift 2 ;;
            --no-meta)      NO_META=true;        shift ;;
            --list|-l)      LIST_PROJECTS=true;  shift ;;
            --summary|-s)   SHOW_SUMMARY=true;   shift ;;
            --stats)        STATS_ONLY=true;     shift ;;
            --verbose|-v)   VERBOSE=true;        shift ;;
            --dry-run)      DRY_RUN=true;        shift ;;
            --no-color)     NO_COLOR=true;       shift ;;
            --version)      echo "${SCRIPT_NAME} v${SCRIPT_VERSION}"; exit 0 ;;
            --help|-h)      show_help; exit 0 ;;
            *)
                log_error "Argumento desconocido: '$1'"
                printf "Usa '%s --help' para ver las opciones disponibles.\n" \
                    "${SCRIPT_NAME}" >&2
                exit 2 ;;
        esac
    done
}
