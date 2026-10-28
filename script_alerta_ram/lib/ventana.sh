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
# Arguments: $1 - prefijo del título de la ventana.
encima_activar() {
    local titulo="$1" id
    [ "${VENTANA_ENCIMA}" = true ] || return 0
    command -v busctl &>/dev/null || return 0
    ENCIMA_SCRIPT="alerta-ram-encima-${BASHPID}"
    ENCIMA_ARCHIVO="${XDG_RUNTIME_DIR:-/tmp}/${ENCIMA_SCRIPT}.js"
    # el título va dentro de una cadena de JavaScript: sin comillas ni barras
    sed "s|@TITULO@|${titulo//[\"\\|]/}|g" "${SCRIPT_DIR}/kwin/encima.js.in" > "$ENCIMA_ARCHIVO"
    id="$(busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
        loadScript ss "$ENCIMA_ARCHIVO" "$ENCIMA_SCRIPT" 2>/dev/null | awk '{print $2}')"
    if [ -z "$id" ] || [ "$id" -lt 0 ] \
       || ! busctl --user call org.kde.KWin "/Scripting/Script${id}" org.kde.kwin.Script run &>/dev/null; then
        log_warn "no pude pedir a KWin que ponga la lista encima; se abre igual."
        encima_desactivar
    fi
    return 0
}

# --- encima_desactivar() ---------------------------------------------------
encima_desactivar() {
    if [ -n "$ENCIMA_SCRIPT" ]; then
        busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
            unloadScript s "$ENCIMA_SCRIPT" &>/dev/null || true
        rm -f "$ENCIMA_ARCHIVO"
        ENCIMA_SCRIPT=""; ENCIMA_ARCHIVO=""
    fi
    return 0
}
