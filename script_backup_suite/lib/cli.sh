#!/usr/bin/env bash
# =============================================================================
#  lib/cli.sh — Interfaz de línea de comandos
# =============================================================================
#
#  Define y parsea todos los flags del script.
#  Centralizar el CLI aquí mantiene main.sh limpio y hace que agregar
#  nuevos flags sea trivial sin tocar la lógica de negocio.
#
#  FLAGS IMPLEMENTADOS:
#    Básicos  : --help, --version, --simulate, --verbose, --log
#    Perfil   : --profile <nombre|list>
#    Selección: --src, --dest, --folder
#    Rsync    : --force, --delete-all, --fast, --compress, --no-checksum
#    Avanzados: --no-confirm, --post-cmd
# =============================================================================

# ── Variables de estado (sobreescritas por parsear_args) ─────────────────────
# Se inicializan con los defaults de config.sh
OPT_VERBOSE=false
OPT_SIMULATE=false
OPT_LOG=false
OPT_FORCE=false
OPT_DELETE_ALL=false
OPT_COMPRESS=false
OPT_NO_CHECKSUM=false
OPT_NO_CONFIRM=false
OPT_PROFILE=""
OPT_CUSTOM_SRC=""
OPT_CUSTOM_DEST=""
OPT_SINGLE_FOLDER=""
OPT_POST_CMD=""

# ── show_help() ───────────────────────────────────────────────────────────────
# Muestra la ayuda completa del script con colores si el terminal los soporta.
# Usa variables de color del logger (ya inicializadas cuando se llama esto).
show_help() {
    cat <<EOF
${CLR_BOLD}${CLR_BLUE}
╔══════════════════════════════════════════════════════════════════════╗
║           BACKUP SUITE — Sincronización Inteligente de Backup        ║
║           Compatible: Kubuntu / Ubuntu / Arch / Archcraft            ║
╚══════════════════════════════════════════════════════════════════════╝
${CLR_RESET}
${CLR_BOLD}USO:${CLR_RESET}
    $(basename "$0") [OPCIONES]

${CLR_BOLD}OPCIONES GENERALES:${CLR_RESET}
    -h, --help              Muestra esta ayuda y sale
        --version           Muestra la versión del script
    -v, --verbose           Modo detallado (lista cada archivo procesado)
    -s, --simulate          Simulación: muestra qué haría sin ejecutar nada
    -l, --log               Guarda log completo en: ${LOG_FILE}
        --no-confirm        No pide confirmación inicial (útil en scripts)

${CLR_BOLD}PERFILES DE BACKUP:${CLR_RESET}
    -p, --profile <nombre>  Selecciona un perfil de backup predefinido
        --profile list      Lista todos los perfiles disponibles

    Perfiles disponibles:
      home   (default) Carpetas de usuario principales
      docs             Solo Documents — backup rápido de trabajo activo
      full             Todo el home excepto exclusiones globales
      custom           Usar --src y --dest para origen/destino libre

${CLR_BOLD}SELECCIÓN PERSONALIZADA:${CLR_RESET}
        --src <ruta>        Carpeta de origen (reemplaza la del perfil)
        --dest <ruta>       Carpeta de destino (reemplaza la del perfil)
    -F, --folder <nombre>   Respalda UNA sola carpeta del perfil activo

${CLR_BOLD}CONTROL DE SINCRONIZACIÓN:${CLR_RESET}
    -f, --force             Sobreescribe archivos modificados sin preguntar
    -d, --delete-all        Elimina huérfanos del disco sin preguntar
        --fast              Usa fecha/tamaño en vez de checksum (más rápido)
        --compress          Activa compresión rsync (útil para red, no para USB)
        --post-cmd <cmd>    Ejecuta un comando al finalizar el backup

${CLR_BOLD}EJEMPLOS:${CLR_RESET}
    # Backup interactivo con perfil por defecto
    $(basename "$0")

    # Backup silencioso con log (ideal para cron/systemd)
    $(basename "$0") --profile home --force --delete-all --log --no-confirm

    # Ver qué cambiaría sin tocar nada
    $(basename "$0") --simulate --verbose

    # Backup rápido solo de Documents
    $(basename "$0") --profile docs

    # Respaldar una sola carpeta
    $(basename "$0") --folder Documents

    # Origen y destino personalizados
    $(basename "$0") --profile custom --src /home/user/Proyectos --dest /mnt/backup/Proyectos

    # Backup con comando post-proceso (notificación de escritorio)
    $(basename "$0") --log --post-cmd "notify-send 'Backup' 'Completado'"

${CLR_BOLD}ORIGEN DEFAULT:${CLR_RESET}  ${HOME_DIR}/
${CLR_BOLD}DESTINO DEFAULT:${CLR_RESET} (detectado automáticamente en /media o /run/media)

EOF
}

# ── show_version() ────────────────────────────────────────────────────────────
show_version() {
    echo "backup-suite v3.0.0"
    echo "Compatible con Kubuntu, Ubuntu, Arch Linux, Archcraft"
    echo "Autor: achalmaedison"
}

# ── show_profiles() ───────────────────────────────────────────────────────────
# Lista los perfiles disponibles con descripción y carpetas incluidas.
show_profiles() {
    echo ""
    log_title "Perfiles de backup disponibles:"
    log_separator
    echo ""
    echo -e "${CLR_BOLD}  home${CLR_RESET} (default)"
    echo "    Carpetas: ${PROFILE_HOME_FOLDERS[*]}"
    echo ""
    echo -e "${CLR_BOLD}  docs${CLR_RESET}"
    echo "    Carpetas: ${PROFILE_DOCS_FOLDERS[*]}"
    echo "    Uso: backup rápido de trabajo activo diario"
    echo ""
    echo -e "${CLR_BOLD}  full${CLR_RESET}"
    echo "    Carpetas: Todo el home excepto exclusiones globales"
    echo ""
    echo -e "${CLR_BOLD}  custom${CLR_RESET}"
    echo "    Requiere: --src <ruta_origen> --dest <ruta_destino>"
    echo "    Uso: origen y destino completamente libres"
    echo ""
}

# ── parse_args() ──────────────────────────────────────────────────────────────
# Parsea todos los argumentos de la línea de comandos.
# Usa un bucle while con case para soportar flags cortos y largos.
# Valida combinaciones inválidas antes de retornar.
#
# Arguments:
#   $@ - Todos los argumentos pasados al script
#
# Returns:
#   0 en éxito
#   exit 2 si los argumentos son inválidos
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            -v|--verbose)
                OPT_VERBOSE=true
                shift
                ;;
            -s|--simulate)
                OPT_SIMULATE=true
                shift
                ;;
            -l|--log)
                OPT_LOG=true
                shift
                ;;
            --no-confirm)
                OPT_NO_CONFIRM=true
                shift
                ;;
            -p|--profile)
                if [ -z "${2:-}" ]; then
                    log_error "--profile requiere un nombre de perfil (o 'list')"
                    exit 2
                fi
                if [ "$2" = "list" ]; then
                    show_profiles
                    exit 0
                fi
                OPT_PROFILE="$2"
                shift 2
                ;;
            --src)
                if [ -z "${2:-}" ]; then
                    log_error "--src requiere una ruta de origen"
                    exit 2
                fi
                OPT_CUSTOM_SRC="$2"
                shift 2
                ;;
            --dest)
                if [ -z "${2:-}" ]; then
                    log_error "--dest requiere una ruta de destino"
                    exit 2
                fi
                OPT_CUSTOM_DEST="$2"
                shift 2
                ;;
            -F|--folder)
                if [ -z "${2:-}" ]; then
                    log_error "--folder requiere el nombre de una carpeta"
                    exit 2
                fi
                OPT_SINGLE_FOLDER="$2"
                shift 2
                ;;
            -f|--force)
                OPT_FORCE=true
                shift
                ;;
            -d|--delete-all)
                OPT_DELETE_ALL=true
                shift
                ;;
            --fast)
                OPT_NO_CHECKSUM=true
                shift
                ;;
            --compress)
                OPT_COMPRESS=true
                shift
                ;;
            --post-cmd)
                if [ -z "${2:-}" ]; then
                    log_error "--post-cmd requiere un comando"
                    exit 2
                fi
                OPT_POST_CMD="$2"
                shift 2
                ;;
            *)
                log_error "Argumento desconocido: '$1'"
                log_error "Usa --help para ver las opciones disponibles."
                exit 2
                ;;
        esac
    done

    # Validar combinaciones de flags
    _validate_flag_combinations
}

# ── _validate_flag_combinations() ────────────────────────────────────────────
# Detecta combinaciones de flags contradictorias o incompletas.
# Separado de parse_args() para mantener la función de parseo limpia.
_validate_flag_combinations() {
    # custom profile requiere --src y --dest
    if [ "${OPT_PROFILE}" = "custom" ]; then
        if [ -z "${OPT_CUSTOM_SRC}" ] || [ -z "${OPT_CUSTOM_DEST}" ]; then
            log_error "El perfil 'custom' requiere --src <origen> y --dest <destino>"
            exit 2
        fi
    fi

    # --src sin --dest o viceversa
    if [ -n "${OPT_CUSTOM_SRC}" ] && [ -z "${OPT_CUSTOM_DEST}" ]; then
        log_error "--src requiere también --dest"
        exit 2
    fi
    if [ -n "${OPT_CUSTOM_DEST}" ] && [ -z "${OPT_CUSTOM_SRC}" ]; then
        log_error "--dest requiere también --src"
        exit 2
    fi

    # Si hay --src/--dest, forzar perfil custom
    if [ -n "${OPT_CUSTOM_SRC}" ] && [ -n "${OPT_CUSTOM_DEST}" ]; then
        OPT_PROFILE="custom"
    fi

    # --force y --simulate son contradictorios (simulate tiene precedencia)
    if [ "${OPT_FORCE}" = true ] && [ "${OPT_SIMULATE}" = true ]; then
        log_warn "--force ignorado en modo --simulate"
        OPT_FORCE=false
    fi

    # Aplicar profile default si no se especificó
    if [ -z "${OPT_PROFILE}" ]; then
        OPT_PROFILE="${DEFAULT_PROFILE}"
    fi
}
