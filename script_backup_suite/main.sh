#!/usr/bin/env bash
# =============================================================================
#  main.sh — Backup Suite v3.0.0
# =============================================================================
#
#  Punto de entrada del script. Su único rol es orquestar los módulos:
#    1. Cargar configuración y módulos
#    2. Parsear argumentos CLI
#    3. Inicializar logger
#    4. Validar entorno (dependencias, disco, carpetas)
#    5. Construir la lista de carpetas según el perfil
#    6. Confirmar con el usuario (a menos que --no-confirm)
#    7. Ejecutar el backup carpeta por carpeta
#    8. Mostrar resumen y ejecutar post-cmd
#
#  La lógica de negocio vive en lib/. main.sh nunca debería superar
#  ~120 líneas para que el flujo sea legible de un vistazo.
#
#  COMPATIBLE: Kubuntu / Ubuntu / Arch Linux / Archcraft
#  AUTOR     : achalmaedison
#  VERSIÓN   : 3.0.0
# =============================================================================

set -euo pipefail

# ── Directorio del script (funciona aunque se ejecute desde cualquier ruta) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Cargar configuración y módulos en orden de dependencia ───────────────────
# config.sh primero: define las variables que usan todos los demás módulos
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/lib/logger.sh"
source "${SCRIPT_DIR}/lib/validator.sh"
source "${SCRIPT_DIR}/lib/cli.sh"
source "${SCRIPT_DIR}/lib/analyzer.sh"
source "${SCRIPT_DIR}/lib/processor.sh"
source "${SCRIPT_DIR}/lib/summary.sh"

# ── Función principal ─────────────────────────────────────────────────────────
main() {
    # ── Cabecera visual ───────────────────────────────────────────────────────
    clear
    echo ""
    echo -e "${CLR_BOLD}${CLR_BLUE}"
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║          BACKUP SUITE v3.0.0 — Sincronización Inteligente        ║"
    printf "  ║          %-54s║\n" "$(date '+%d/%m/%Y %H:%M:%S')"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${CLR_RESET}"
    echo ""

    # ── FASE 1: Parsear argumentos CLI ───────────────────────────────────────
    parse_args "$@"

    # ── FASE 2: Inicializar logger con las opciones elegidas ─────────────────
    logger_init \
        "${OPT_VERBOSE}" \
        "${OPT_LOG}" \
        "${LOG_FILE}" \
        "${LOG_MAX_BYTES}"

    # ── FASE 3: Advertir si se ejecuta como root ─────────────────────────────
    validate_not_root

    # ── FASE 4: Verificar dependencias ───────────────────────────────────────
    validate_dependencies

    # ── FASE 5: Detectar punto de montaje del disco ───────────────────────────
    local disk_path
    if ! disk_path=$(detect_mount_point "${USUARIO}" "${DISK_LABEL}"); then
        log_error "El disco '${DISK_LABEL}' no está montado."
        log_error "Conecta el disco o monta manualmente con: udisksctl mount -b /dev/sdX1"
        exit 1
    fi

    local dest_base="${disk_path}/${DESTINO_BASE_NAME}"

    validate_disk \
        "${disk_path}" \
        "${dest_base}" \
        "${OPT_SIMULATE}" \
        "${MIN_FREE_BYTES}"

    # ── FASE 6: Construir lista de carpetas según el perfil elegido ───────────
    local carpetas_backup=()
    local src_base="${HOME_DIR}"

    case "${OPT_PROFILE}" in
        home)
            carpetas_backup=("${PROFILE_HOME_FOLDERS[@]}")
            ;;
        docs)
            carpetas_backup=("${PROFILE_DOCS_FOLDERS[@]}")
            ;;
        full)
            # Listar dinámicamente todo el home excepto exclusiones globales
            while IFS= read -r dir; do
                local dirname
                dirname=$(basename "${dir}")
                # Verificar que no está en la lista de exclusiones globales
                local excluded=false
                for excl in "${GLOBAL_EXCLUDE[@]}"; do
                    [ "${dirname}" = "${excl}" ] && excluded=true && break
                done
                [ "${excluded}" = false ] && carpetas_backup+=("${dirname}")
            done < <(find "${HOME_DIR}" -maxdepth 1 -mindepth 1 -type d | sort)
            ;;
        custom)
            # Modo custom: origen y destino completamente libres
            src_base=$(dirname "${OPT_CUSTOM_SRC}")
            local custom_folder
            custom_folder=$(basename "${OPT_CUSTOM_SRC}")
            carpetas_backup=("${custom_folder}")
            dest_base=$(dirname "${OPT_CUSTOM_DEST}")
            ;;
    esac

    # Si se especificó --folder, filtrar a solo esa carpeta
    if [ -n "${OPT_SINGLE_FOLDER}" ]; then
        local found=false
        for f in "${carpetas_backup[@]}"; do
            [ "${f}" = "${OPT_SINGLE_FOLDER}" ] && found=true && break
        done
        if [ "${found}" = true ]; then
            carpetas_backup=("${OPT_SINGLE_FOLDER}")
        else
            # Si no está en el perfil, intentar respaldarla de todas formas
            log_warn "La carpeta '${OPT_SINGLE_FOLDER}' no está en el perfil '${OPT_PROFILE}'."
            log_warn "Se intentará respaldar de todas formas desde: ${src_base}/${OPT_SINGLE_FOLDER}"
            carpetas_backup=("${OPT_SINGLE_FOLDER}")
        fi
    fi

    # Validar que las carpetas de origen existen
    validate_source_folders "${src_base}" carpetas_backup

    if [ "${#carpetas_backup[@]}" -eq 0 ]; then
        log_error "No hay carpetas válidas para respaldar. Abortando."
        exit 1
    fi

    # ── FASE 7: Construir opciones rsync finales ──────────────────────────────
    local rsync_opts="${RSYNC_BASE_OPTS}"

    # Modo rápido: quitar checksum (-c) y usar solo tamaño/fecha
    if [ "${OPT_NO_CHECKSUM}" = true ]; then
        rsync_opts="${rsync_opts//-ahc/-ah}"
        log_warn "Modo --fast activo: comparación por fecha/tamaño (sin checksum)"
    fi

    # Comprimir datos en tránsito (solo útil para rsync sobre red)
    if [ "${OPT_COMPRESS}" = true ]; then
        rsync_opts="${rsync_opts} --compress"
    fi

    # Agregar opciones extra del config (hardlinks, protect-args, etc.)
    for extra in "${RSYNC_EXTRA_OPTS[@]}"; do
        rsync_opts="${rsync_opts} ${extra}"
    done

    # Agregar exclusiones de config (carpetas y patrones)
    local exclude_args
    exclude_args=$(build_rsync_exclude_args)
    rsync_opts="${rsync_opts} ${exclude_args}"

    log_debug "Opciones rsync activas: ${rsync_opts}"

    # ── FASE 8: Mostrar configuración y pedir confirmación ────────────────────
    print_config_banner \
        "${src_base}" \
        "${dest_base}" \
        "${OPT_PROFILE}" \
        "${#carpetas_backup[@]}" \
        "${OPT_SIMULATE}" \
        "${OPT_FORCE}" \
        "${OPT_DELETE_ALL}" \
        "${OPT_NO_CHECKSUM}" \
        "${OPT_COMPRESS}" \
        "${OPT_SINGLE_FOLDER}"

    if [ "${OPT_NO_CONFIRM}" = false ]; then
        local confirm
        read -rp "$(echo -e "${CLR_BOLD}  ¿Iniciar backup? [s/n]: ${CLR_RESET}")" confirm
        confirm=$(echo "${confirm}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
        if [[ ! "${confirm}" =~ ^(s|si|sí|y|yes)$ ]]; then
            log_warn "Backup cancelado por el usuario."
            exit 0
        fi
    fi

    echo ""
    log_separator "═" 70
    log_title "  INICIANDO BACKUP"
    log_separator "═" 70
    echo ""

    # ── FASE 9: Procesar cada carpeta del perfil ──────────────────────────────
    for folder in "${carpetas_backup[@]}"; do
        process_folder \
            "${folder}" \
            "${src_base}" \
            "${dest_base}" \
            "${rsync_opts}"
    done

    # ── FASE 10: Resumen y post-comando ──────────────────────────────────────
    show_summary \
        "${#carpetas_backup[@]}" \
        "${disk_path}" \
        "${OPT_SIMULATE}" \
        "${OPT_LOG:+${LOG_FILE}}"

    run_post_command "${OPT_POST_CMD}" "${OPT_SIMULATE}"
}

# ── Punto de entrada ──────────────────────────────────────────────────────────
main "$@"
