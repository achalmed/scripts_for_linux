#!/usr/bin/env bash
# =============================================================================
#  lib/validator.sh — Dependencias y entorno
# =============================================================================
#
#  Falla rápido si falta algo que el subcomando necesita (exit 5 = dependencia).
# =============================================================================

# --- validate_meminfo() ----------------------------------------------------
# Sin MemAvailable (kernel < 3.14) el porcentaje no se puede calcular bien.
validate_meminfo() {
    if ! grep -q '^MemAvailable:' /proc/meminfo 2>/dev/null; then
        log_error "/proc/meminfo no tiene MemAvailable: esta suite necesita Linux 3.14 o posterior."
        exit 5
    fi
    return 0
}

# --- validate_sonido_y_avisos() --------------------------------------------
# paplay (PulseAudio o PipeWire) y notify-send son obligatorios; cada sonido
# de NIVELES debe existir en DIR_SONIDOS.
validate_sonido_y_avisos() {
    local falta=0 bin nivel sonido
    for bin in paplay notify-send ps; do
        if ! command -v "$bin" &>/dev/null; then
            log_error "falta «$bin» en PATH."
            falta=1
        fi
    done
    for nivel in "${NIVELES[@]}"; do
        IFS='|' read -r _ sonido _ _ _ <<<"$nivel"
        if [ ! -f "${DIR_SONIDOS}/${sonido}" ]; then
            log_error "no existe el sonido ${DIR_SONIDOS}/${sonido} (revisa NIVELES en config.sh)."
            falta=1
        fi
    done
    [ "$falta" -eq 0 ] || exit 5
    return 0
}

# --- validate_plantilla_unidad() -------------------------------------------
validate_plantilla_unidad() {
    if [ ! -f "${SCRIPT_DIR}/systemd/${UNIDAD}.in" ]; then
        log_error "falta la plantilla systemd/${UNIDAD}.in"
        exit 5
    fi
    if ! command -v systemctl &>/dev/null; then
        log_error "falta systemctl: el servicio solo se instala con systemd."
        exit 5
    fi
    return 0
}

# --- validate_cierre() -----------------------------------------------------
# MODO_CIERRE=lista necesita PyQt6 en LISTA_PYTHON (lista viva) o kdialog;
# ventanas, busctl. Si falta, avisa y sigue: la alarma sonora no depende de esto.
validate_cierre() {
    local bin=kdialog
    [ "${MODO_CIERRE}" = ventanas ] && bin=busctl
    if [ "${MODO_CIERRE}" != ventanas ] && lista_viva_disponible; then return 0; fi
    if [ "${MODO_CIERRE}" != ventanas ] && [ "${LISTA_VIVA}" = true ]; then
        log_warn "${LISTA_PYTHON} no tiene PyQt6 (python3-pyqt6): la lista no se actualizará sola; uso kdialog."
    fi
    if ! command -v "$bin" &>/dev/null; then
        log_warn "falta «${bin}»: sin él no se podrá mostrar la lista para cerrar apps (MODO_CIERRE=${MODO_CIERRE})."
    fi
    return 0
}
