#!/usr/bin/env bash
# lib/cli.sh — CLI argument parsing for hardlinks-detector.
#
# Centralizing argument logic here keeps main.sh minimal.
# All parsed values are written into global variables that
# main.sh reads after calling parse_arguments().

# ---------------------------------------------------------------------------
# Default values — defined here so they're findable in one place
# ---------------------------------------------------------------------------
DIRECTORY=""        # resolved in main.sh from $1 or pwd
FORMAT="tree"       # tree | csv | json
OUTPUT_FILE=""      # empty = stdout only
VERBOSE=false
NO_COLOR=false
FILTER_INODE=""     # NEW: filter output to a single inode group
MIN_LINKS=2         # NEW: only show groups with at least N hard links

# ---------------------------------------------------------------------------
# show_help()
# Prints usage information to stdout.
# ---------------------------------------------------------------------------
show_help() {
    cat << EOF
${BOLD}Uso:${RESET}
  $(basename "$0") [DIRECTORIO] [OPCIONES]

${BOLD}Descripción:${RESET}
  Detecta y visualiza todos los hard links en un árbol de directorios.
  Proyecto complementario de ${CYAN}hardlinks-creator${RESET}.

${BOLD}Argumentos:${RESET}
  DIRECTORIO            Directorio raíz a analizar (por defecto: directorio actual)

${BOLD}Opciones:${RESET}
  -f, --format FORMAT   Formato de salida: tree (defecto), csv, json
  -o, --output FILE     Guardar salida en un archivo (además de mostrar en consola)
      --min-links N     Mostrar solo grupos con al menos N enlaces (defecto: 2)
      --filter-inode N  Mostrar solo el grupo con el inodo indicado
      --no-color        Desactivar colores ANSI
  -v, --verbose         Mostrar mensajes de depuración
      --version         Mostrar versión
  -h, --help            Mostrar esta ayuda

${BOLD}Ejemplos:${RESET}
  # Analizar directorio actual en árbol
  $(basename "$0")

  # Analizar directorio específico
  $(basename "$0") ~/Documents

  # Exportar como JSON
  $(basename "$0") ~/Documents --format json --output report.json

  # Exportar como CSV
  $(basename "$0") ~/Documents --format csv --output links.csv

  # Solo grupos con 5 o más enlaces
  $(basename "$0") ~/Documents --min-links 5

  # Ver un inodo específico
  $(basename "$0") ~/Documents --filter-inode 14820714

${BOLD}Herramienta complementaria:${RESET}
  ${CYAN}hardlinks-creator${RESET} — crea hard links entre archivos con contenido idéntico

EOF
}

# ---------------------------------------------------------------------------
# parse_arguments()
# Parses $@ and writes results into the global variables above.
# Arguments: $@ - all CLI arguments passed to main.sh
# ---------------------------------------------------------------------------
parse_arguments() {
    # The first positional argument (if not a flag) is the directory
    if [[ $# -gt 0 && "$1" != -* ]]; then
        DIRECTORY="$1"
        shift
    fi

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--format)
                FORMAT="$2"
                if [[ ! "$FORMAT" =~ ^(tree|csv|json)$ ]]; then
                    log_error "Formato inválido: '${FORMAT}'. Use: tree, csv, json"
                    exit "${EXIT_BAD_ARGS:-2}"
                fi
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --min-links)
                MIN_LINKS="$2"
                if ! [[ "$MIN_LINKS" =~ ^[0-9]+$ ]] || (( MIN_LINKS < 2 )); then
                    log_error "--min-links debe ser un entero >= 2"
                    exit "${EXIT_BAD_ARGS:-2}"
                fi
                shift 2
                ;;
            --filter-inode)
                FILTER_INODE="$2"
                shift 2
                ;;
            --no-color)
                NO_COLOR=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --version)
                printf "hardlinks-detector %s\n" "${VERSION:-3.0.0}"
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Argumento desconocido: '$1'"
                show_help
                exit "${EXIT_BAD_ARGS:-2}"
                ;;
        esac
    done
}
