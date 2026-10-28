#!/usr/bin/env bash
# =============================================================================
#  lib/cierre.sh — Mostrar las apps abiertas para cerrarlas
# =============================================================================
#
#  MODO_CIERRE=lista: una ventana (kdialog) con cada app y su RAM; las marcadas
#  se cierran con «systemctl --user stop» de sus unidades, que manda SIGTERM a
#  todos sus procesos a la vez (la app puede guardar antes de salir).
#  MODO_CIERRE=ventanas: la Vista general de KWin, por D-Bus.
#  Marcar en la ventana es la confirmación: no se cierra nada sin marcarlo.
# =============================================================================

# --- abrir_cierre() --------------------------------------------------------
# Arguments: $1 - % de RAM (para el texto). Bloquea hasta que se responde:
# vigilar() la llama en segundo plano.
abrir_cierre() {
    case "${MODO_CIERRE}" in
        ventanas) abrir_vista_general ;;
        *)        abrir_lista_cierre "$1" ;;
    esac
    return 0
}

# --- abrir_vista_general() -------------------------------------------------
abrir_vista_general() {
    busctl --user call org.kde.kglobalaccel /component/kwin \
        org.kde.kglobalaccel.Component invokeShortcut s Overview &>/dev/null \
        || log_warn "no pude abrir la Vista general de KWin."
    return 0
}

# --- abrir_lista_cierre() --------------------------------------------------
abrir_lista_cierre() {
    local pct="$1" unidades=() args=() mb unidad nombre i=0 elegidos sel cerradas=() rc=0
    while IFS='|' read -r mb unidad nombre; do
        [ -n "$mb" ] || continue
        i=$(( i + 1 ))
        unidades[i]="$unidad"
        # etiqueta = índice: los nombres de unidad llevan escapes (\x2d) que no conviene pasar por kdialog
        args+=("$i" "${nombre} — $(formato_gb "$mb")" off)
    done < <(apps_abiertas)

    if [ "$i" -eq 0 ]; then
        log_info "no hay apps propias que cerrar (la RAM la usan el sistema o contenedores)."
        return 0
    fi

    encima_activar "${NOMBRE_APP}:"
    elegidos="$(kdialog --title "${NOMBRE_APP}: RAM al ${pct}%" \
        --ok-label "Cerrar las marcadas" --cancel-label "Ahora no" --separate-output \
        --checklist "La RAM está al ${pct}%. Marca las apps que quieres cerrar:" \
        "${args[@]}" 2>/dev/null)" || rc=$?
    encima_desactivar
    if [ "$rc" -ne 0 ]; then
        log_info "lista de cierre descartada."
        return 0
    fi

    while read -r sel; do
        [ -n "$sel" ] || continue
        # shellcheck disable=SC2086  # varias unidades de la misma app, separadas por espacio
        if systemctl --user stop --no-block ${unidades[sel]} 2>/dev/null; then
            cerradas+=("${args[(sel - 1) * 3 + 1]%% — *}")
        else
            log_warn "no pude cerrar ${unidades[sel]}"
        fi
    done <<<"$elegidos"

    if [ "${#cerradas[@]}" -gt 0 ]; then
        log_ok "cerrando: ${cerradas[*]}"
        notificar 0 normal dialog-information "Cerrando apps" "$(printf '• %s\n' "${cerradas[@]}")" >/dev/null
    fi
    return 0
}
