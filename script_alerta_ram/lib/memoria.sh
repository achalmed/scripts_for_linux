#!/usr/bin/env bash
# =============================================================================
#  lib/memoria.sh — Lectura de la RAM y de qué apps la usan
# =============================================================================
#
#  Una «app» es una unidad app-*.scope o app-*.service de app.slice: Plasma 6
#  lanza cada aplicación en la suya, con todos sus procesos (las pestañas de un
#  navegador incluidas). Su RAM es la del cgroup (MemoryCurrent). Lo que corre
#  fuera (servicios del sistema, contenedores) se resume como «fuera de tus apps».
# =============================================================================

# --- ram_pct() -------------------------------------------------------------
# Outputs (stdout): % de RAM usada, entero, según (MemTotal - MemAvailable).
ram_pct() {
    awk '/^MemTotal:/ {t=$2} /^MemAvailable:/ {a=$2} END {printf "%d", (t-a)*100/t}' /proc/meminfo
}

# --- ram_usada_mb() --------------------------------------------------------
ram_usada_mb() {
    awk '/^MemTotal:/ {t=$2} /^MemAvailable:/ {a=$2} END {printf "%d", (t-a)/1024}' /proc/meminfo
}

# --- id_app() --------------------------------------------------------------
# Arguments: $1 - unidad (app-com.anthropic.Claude-3256.scope,
# app-claude\x2ddesktop@autostart.service). Outputs: el id de la app.
id_app() {
    local id
    id="$(printf '%b' "$1")"          # \x2d → -
    id="${id#app-}"
    id="${id#flatpak-}"               # el sandbox de una app Flatpak: app-flatpak-<id>-<n>.scope
    case "$id" in
        *.scope)   id="${id%.scope}"; id="${id%-*}" ;;   # app-<id>-<aleatorio>.scope
        *.service) id="${id%.service}"; id="${id%@*}" ;; # app-<id>@<instancia>.service
    esac
    echo "$id"
}

# --- nombre_app() ----------------------------------------------------------
# Arguments: $1 - id de la app. Outputs: Name= de su .desktop o, si no hay, el
# último tramo del id.
nombre_app() {
    local id="$1" dir archivo nombre=""
    local dirs="${XDG_DATA_HOME:-$HOME/.local/share}:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}:/var/lib/flatpak/exports/share"
    IFS=: read -ra lista <<<"$dirs"
    for dir in "${lista[@]}"; do
        archivo="${dir}/applications/${id}.desktop"
        if [ -f "$archivo" ]; then
            nombre="$(awk -F= '/^Name=/ {print $2; exit}' "$archivo")"
            [ -n "$nombre" ] && break
        fi
    done
    echo "${nombre:-${id##*.}}"
}

# --- apps_abiertas() -------------------------------------------------------
# Outputs (stdout): «MB|unidades|nombre» por app, de mayor a menor RAM. Las
# unidades de una misma app (un Flatpak tiene su sandbox y su lanzador) se suman
# y van juntas, separadas por espacio. Respeta APPS_MIN_MB y EXCLUIR_CIERRE.
apps_abiertas() {
    local unidades=() mb unidad id grupo patron excluida
    mapfile -t unidades < <(systemctl --user list-units --type=scope,service --state=running \
        --no-legend --plain 'app-*' 2>/dev/null | awk '{print $1}')
    [ "${#unidades[@]}" -gt 0 ] || return 0
    systemctl --user show -p Id,MemoryCurrent "${unidades[@]}" 2>/dev/null \
        | awk -F= '/^Id=/ {id=$2} /^MemoryCurrent=/ {m=$2}
                   /^$/ {if (id != "" && m ~ /^[0-9]+$/) printf "%d|%s\n", m/1048576, id; id=""; m=""}
                   END  {if (id != "" && m ~ /^[0-9]+$/) printf "%d|%s\n", m/1048576, id}' \
        | while IFS='|' read -r mb unidad; do
            printf '%s|%s|%s\n' "$mb" "$unidad" "$(id_app "$unidad")"
        done \
        | awk -F'|' '{m[$3]+=$1; u[$3]=(u[$3] == "" ? $2 : u[$3] " " $2)}
                     END {for (i in m) printf "%d|%s|%s\n", m[i], u[i], i}' \
        | sort -t'|' -k1,1 -rn \
        | while IFS='|' read -r mb grupo id; do
            [ "$mb" -ge "${APPS_MIN_MB}" ] || continue
            excluida=0
            for patron in "${EXCLUIR_CIERRE[@]}"; do
                # shellcheck disable=SC2053  # el patrón es un glob a propósito
                if [[ "$id" == $patron ]]; then excluida=1; break; fi
            done
            if [ "$excluida" -eq 0 ]; then
                printf '%s|%s|%s\n' "$mb" "$grupo" "$(nombre_app "$id")"
            fi
        done
    return 0
}

# --- formato_gb() ----------------------------------------------------------
formato_gb() { awk -v m="$1" 'BEGIN {printf "%.1f GB", m/1024}'; }

# --- top_apps() ------------------------------------------------------------
# Outputs (stdout): las TOP_APPS apps que más usan y, aparte, lo que queda
# fuera de ellas (sistema, contenedores), para que no sorprenda el total.
top_apps() {
    local apps suma=0 mb nombre fuera n=0
    apps="$(apps_abiertas)"
    while IFS='|' read -r mb _ nombre; do
        [ -n "$mb" ] || continue
        suma=$(( suma + mb ))
        if [ "$n" -lt "${TOP_APPS}" ]; then
            printf '• %s: %s\n' "$nombre" "$(formato_gb "$mb")"
            n=$(( n + 1 ))
        fi
    done <<<"$apps"
    fuera=$(( $(ram_usada_mb) - suma ))
    if [ "$fuera" -gt 512 ]; then
        printf '• fuera de tus apps (sistema, contenedores): %s\n' "$(formato_gb "$fuera")"
    fi
    return 0
}
