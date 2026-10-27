#!/usr/bin/env bash
# =============================================================================
#  lib/servicio.sh — Instalar y desinstalar el servicio systemd de usuario
# =============================================================================
#
#  La unidad se renderiza desde systemd/<UNIDAD>.in sustituyendo @SUITE@ por la
#  ruta real de la suite (la carpeta de inicio no se escribe en el repo). Sin
#  --aplicar solo se informa lo que se haría.
# =============================================================================

# --- carpeta_unidades() ----------------------------------------------------
carpeta_unidades() {
    echo "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
}

# --- instalar_servicio() ---------------------------------------------------
# Arguments: $1 - aplicar (true/false).
instalar_servicio() {
    local aplicar="$1" destino
    destino="$(carpeta_unidades)/${UNIDAD}"
    log_section "Instalar ${UNIDAD}"
    if [ "$aplicar" != true ]; then
        log_info "simulación: escribiría ${destino} y haría «systemctl --user enable --now ${UNIDAD}»."
        log_plain ""
        sed "s|@SUITE@|${SCRIPT_DIR}|g" "${SCRIPT_DIR}/systemd/${UNIDAD}.in"
        log_plain ""
        log_info "para hacerlo: main.sh instalar --aplicar"
        return 0
    fi
    mkdir -p "$(dirname "$destino")"
    sed "s|@SUITE@|${SCRIPT_DIR}|g" "${SCRIPT_DIR}/systemd/${UNIDAD}.in" > "$destino"
    systemctl --user daemon-reload
    systemctl --user enable --now "${UNIDAD}"
    systemctl --user restart "${UNIDAD}"   # si ya corría, toma la config.sh nueva
    log_ok "instalado y activo: ${destino}"
    return 0
}

# --- desinstalar_servicio() ------------------------------------------------
# Arguments: $1 - aplicar (true/false).
desinstalar_servicio() {
    local aplicar="$1" destino
    destino="$(carpeta_unidades)/${UNIDAD}"
    log_section "Desinstalar ${UNIDAD}"
    if [ ! -f "$destino" ]; then
        log_skip "no está instalado (${destino} no existe)."
        return 0
    fi
    if [ "$aplicar" != true ]; then
        log_info "simulación: detendría ${UNIDAD} y borraría ${destino}. Para hacerlo: main.sh desinstalar --aplicar"
        return 0
    fi
    systemctl --user disable --now "${UNIDAD}" || true
    rm -f "$destino"
    systemctl --user daemon-reload
    log_ok "desinstalado"
    return 0
}
