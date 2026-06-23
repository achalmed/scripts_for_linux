#!/usr/bin/env bash
# =============================================================================
#  lib/summary.sh — Resumen final del backup
# =============================================================================
#
#  Genera el informe de cierre con estadísticas de la sesión,
#  estado actual del disco externo, y ejecuta el comando post-backup
#  si el usuario lo definió con --post-cmd.
# =============================================================================

# ── show_summary() ────────────────────────────────────────────────────────────
# Imprime el resumen completo de la sesión de backup al finalizar.
# Muestra contadores de todas las categorías y estado del disco.
#
# Arguments:
#   $1 - Número de carpetas procesadas
#   $2 - Ruta al disco externo (para df)
#   $3 - Modo simulación (true/false)
#   $4 - Archivo de log (ruta o cadena vacía)
show_summary() {
    local folders_count="$1"
    local disk_path="$2"
    local simulate="${3:-false}"
    local log_file="${4:-}"

    echo ""
    log_separator "═" 70
    log_title "  RESUMEN DEL BACKUP"
    log_separator "═" 70
    echo ""

    log_ok    "  ✓ Archivos nuevos copiados:      ${STATS_COPIED}"
    log_ok    "  ✓ Archivos actualizados:         ${STATS_UPDATED}"
    log_info  "  → Archivos omitidos:             ${STATS_SKIPPED}"

    if [ "${STATS_ORPHANS}" -gt 0 ]; then
        log_warn "  ⚠  Huérfanos encontrados:         ${STATS_ORPHANS}"
    fi

    if [ "${STATS_DELETED}" -gt 0 ]; then
        log_action "  ✗ Elementos eliminados del disco: ${STATS_DELETED}"
    fi

    echo ""
    log_info  "  Carpetas procesadas:             ${folders_count}"
    log_info  "  Tiempo total:                    $(elapsed_time)"

    if [ "${simulate}" = true ]; then
        echo ""
        log_warn "  ⚠  MODO SIMULACIÓN ACTIVO — No se realizaron cambios reales"
    fi

    if [ -n "${log_file}" ]; then
        echo ""
        log_info "  Log guardado en: ${log_file}"
    fi

    echo ""
    log_separator "═" 70

    # Estado del disco externo post-backup
    if [ -d "${disk_path}" ]; then
        echo ""
        log_title "  Estado del disco tras el backup:"
        df -h "${disk_path}" | tail -1 | awk '{
            printf "    Usado: %s / Total: %s  |  Libre: %s (%s)\n", $3, $2, $4, $5
        }'
    fi

    echo ""
}

# ── run_post_command() ────────────────────────────────────────────────────────
# Ejecuta el comando definido por el usuario con --post-cmd al finalizar.
# Útil para notificaciones de escritorio, scripts de limpieza, etc.
#
# Arguments:
#   $1 - Comando a ejecutar (cadena o vacía)
#   $2 - Modo simulación (true/false)
run_post_command() {
    local cmd="$1"
    local simulate="${2:-false}"

    [ -z "${cmd}" ] && return 0

    if [ "${simulate}" = true ]; then
        log_info "[SIMULACIÓN] Se ejecutaría post-cmd: ${cmd}"
        return 0
    fi

    log_info "Ejecutando comando post-backup: ${cmd}"
    if eval "${cmd}"; then
        log_ok "Post-cmd completado correctamente."
    else
        log_warn "Post-cmd retornó código de error (el backup fue exitoso de todas formas)."
    fi
}

# ── print_config_banner() ─────────────────────────────────────────────────────
# Imprime el banner de configuración antes de pedir confirmación.
# Da al usuario una vista clara de lo que va a pasar.
#
# Arguments:
#   $1  - Ruta de origen
#   $2  - Ruta de destino
#   $3  - Perfil activo
#   $4  - Número de carpetas
#   $5  - OPT_SIMULATE
#   $6  - OPT_FORCE
#   $7  - OPT_DELETE_ALL
#   $8  - OPT_NO_CHECKSUM
#   $9  - OPT_COMPRESS
#   $10 - OPT_SINGLE_FOLDER (o vacío)
print_config_banner() {
    local src="$1"
    local dest="$2"
    local profile="$3"
    local folder_count="$4"
    local simulate="$5"
    local force="$6"
    local delete_all="$7"
    local no_checksum="$8"
    local compress="$9"
    local single_folder="${10:-}"

    echo ""
    log_title "  Configuración del backup:"
    log_separator
    log_info  "  Perfil:          ${profile}"
    log_info  "  Origen:          ${src}"
    log_info  "  Destino:         ${dest}"

    if [ -n "${single_folder}" ]; then
        log_info "  Carpeta única:   ${single_folder}"
    else
        log_info "  Carpetas:        ${folder_count}"
    fi

    log_info  "  Simulación:      ${simulate}"
    log_info  "  Forzar cambios:  ${force}"
    log_info  "  Borrar huérf.:   ${delete_all}"
    log_info  "  Modo rápido:     ${no_checksum} (sin checksum)"
    log_info  "  Compresión:      ${compress}"
    echo ""
}
