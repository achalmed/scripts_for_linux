#!/usr/bin/env bash
# =============================================================================
#  lib/ventana.sh — Poner la lista para cerrar apps encima de las demás ventanas
# =============================================================================
#
#  kdialog no tiene opción «siempre encima» y en Wayland una app no puede
#  ponerse delante por su cuenta. Mientras la lista está abierta se carga en
#  KWin (por D-Bus) el script kwin/encima.js.in, que espera a que aparezca la
#  ventana, la deja encima y le da el foco; al cerrarse la lista se descarga.
#  No se toca la configuración de KWin. Si algo falla, la lista se abre igual.
# =============================================================================

ENCIMA_SCRIPT=""   # nombre con que se cargó en KWin ("" = no cargado)
ENCIMA_ARCHIVO=""

# --- encima_activar() ------------------------------------------------------
# Arguments: $1 - prefijo del título de la ventana, $2 - su clase en KWin
# (resourceClass: org.kde.kdialog, o el id que fija lib/lista_viva.py).
encima_activar() {
    local titulo="$1" clase="${2:-org.kde.kdialog}" id
    [ "${VENTANA_ENCIMA}" = true ] || return 0
    command -v busctl &>/dev/null || return 0
    ENCIMA_SCRIPT="alerta-ram-encima-${BASHPID}"
    ENCIMA_ARCHIVO="${XDG_RUNTIME_DIR:-/tmp}/${ENCIMA_SCRIPT}.js"
    # van dentro de cadenas de JavaScript: sin comillas ni barras
    sed -e "s|@TITULO@|${titulo//[\"\\|]/}|g" -e "s|@CLASE@|${clase//[\"\\|]/}|g" \
        "${SCRIPT_DIR}/kwin/encima.js.in" > "$ENCIMA_ARCHIVO"
    id="$(busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
        loadScript ss "$ENCIMA_ARCHIVO" "$ENCIMA_SCRIPT" 2>/dev/null | awk '{print $2}')"
    if [ -z "$id" ] || [ "$id" -lt 0 ] \
       || ! busctl --user call org.kde.KWin "/Scripting/Script${id}" org.kde.kwin.Script run &>/dev/null; then
        log_warn "no pude pedir a KWin que ponga la lista encima; se abre igual."
        encima_desactivar
        return 0
    fi
    # si matan la lista abierta (systemctl restart, Ctrl+C) el script no debe quedar cargado en KWin
    trap 'encima_desactivar' EXIT
    trap 'encima_desactivar; exit 143' TERM INT HUP
    return 0
}

# --- encima_desactivar() ---------------------------------------------------
encima_desactivar() {
    if [ -n "$ENCIMA_SCRIPT" ]; then
        busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
            unloadScript s "$ENCIMA_SCRIPT" &>/dev/null || true
        rm -f "$ENCIMA_ARCHIVO"
        ENCIMA_SCRIPT=""; ENCIMA_ARCHIVO=""
        trap - EXIT TERM INT HUP
    fi
    return 0
}
