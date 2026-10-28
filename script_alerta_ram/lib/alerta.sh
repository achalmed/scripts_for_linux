#!/usr/bin/env bash
# =============================================================================
#  lib/alerta.sh — Niveles, sonido, notificación y el bucle de vigilancia
# =============================================================================

# Nivel elegido por elegir_nivel()
NIVEL_DESDE=0; NIVEL_SONIDO=""; NIVEL_URGENCIA=""; NIVEL_REPETIR=0; NIVEL_ACCION="-"

# --- elegir_nivel() --------------------------------------------------------
# Arguments: $1 - % de RAM. Fija NIVEL_* con el primer nivel cuyo «desde» se
# alcanza (NIVELES va de mayor a menor). Returns: 1 si está bajo UMBRAL.
elegir_nivel() {
    local pct="$1" nivel desde
    for nivel in "${NIVELES[@]}"; do
        IFS='|' read -r desde NIVEL_SONIDO NIVEL_URGENCIA NIVEL_REPETIR NIVEL_ACCION <<<"$nivel"
        if [ "$pct" -ge "$desde" ]; then
            NIVEL_DESDE="$desde"
            return 0
        fi
    done
    return 1
}

# --- volumen_para() --------------------------------------------------------
# Arguments: $1 - % de RAM, $2 - escalón (avisos ya dados en este episodio).
# Outputs: volumen; base lineal de VOL_MIN (UMBRAL) a VOL_MAX (VOL_TOPE_PCT)
# más VOL_PASO por escalón, sin pasar de VOL_MAX.
volumen_para() {
    local pct="$1" escalon="${2:-0}" vol
    vol=$(( VOL_MIN + (pct - UMBRAL) * (VOL_MAX - VOL_MIN) / (VOL_TOPE_PCT - UMBRAL) + escalon * VOL_PASO ))
    if [ "$vol" -gt "$VOL_MAX" ]; then vol="$VOL_MAX"; fi
    if [ "$vol" -lt "$VOL_MIN" ]; then vol="$VOL_MIN"; fi
    echo "$vol"
}

# --- veces_para() ----------------------------------------------------------
# Arguments: $1 - escalón. Outputs: cuántas veces seguidas suena (1, 1, 2, 2, 3…).
veces_para() {
    local veces=$(( 1 + ${1:-0} / 2 ))
    if [ "$veces" -gt "$SONIDO_VECES_MAX" ]; then veces="$SONIDO_VECES_MAX"; fi
    echo "$veces"
}

# --- sonar() ---------------------------------------------------------------
# Arguments: $1 - archivo en DIR_SONIDOS, $2 - volumen (%), $3 - veces.
# paplay usa 0–65536 = 0–100 %; no toca el volumen del sistema. En segundo plano
# para no frenar la medición.
sonar() {
    local archivo="${DIR_SONIDOS}/$1" vol=$(( $2 * 65536 / 100 )) veces="${3:-1}"
    (
        for (( i = 0; i < veces; i++ )); do
            paplay --volume="$vol" "$archivo"
        done
    ) &>/dev/null &
    return 0
}

# --- notificar() -----------------------------------------------------------
# Arguments: $1 - id a reemplazar (0 = nueva), $2 - urgencia, $3 - icono,
# $4 - título, $5 - cuerpo. Outputs: el id (para reemplazarla en vez de apilar
# otra). Sin sesión gráfica falla en silencio y devuelve 0.
notificar() {
    local duracion=()
    [ "$2" = normal ] && duracion=(-t "${NOTIF_DURACION_MS}")
    notify-send -p -r "$1" -a "${NOMBRE_APP}" -u "$2" "${duracion[@]}" -i "$3" "$4" "$5" 2>/dev/null || echo 0
}

# --- primer_nivel_cierre() -------------------------------------------------
# Outputs: el % del nivel más bajo con acción «cerrar» (NIVELES va de mayor a menor).
primer_nivel_cierre() {
    local nivel desde accion primero=""
    for nivel in "${NIVELES[@]}"; do
        IFS='|' read -r desde _ _ _ accion <<<"$nivel"
        if [ "$accion" = cerrar ]; then primero="$desde"; fi
    done
    echo "${primero:-100}"
}

# --- cierre_libre() ----------------------------------------------------------
# Arguments: $1 - pid de la última lista. Returns: 0 si no hay una abierta.
# 0 es «nunca se abrió»: kill -0 0 apunta al propio grupo de procesos y siempre acierta.
cierre_libre() {
    [ "$1" -eq 0 ] || ! kill -0 "$1" 2>/dev/null
}

# --- vigilar() -------------------------------------------------------------
# Bucle del servicio. Avisa al cruzar UMBRAL; cada repetición sin que la RAM
# baje sube un escalón (más volumen, más veces) y al subir de nivel suena ya.
# Abre la lista de apps al llegar a un nivel «cerrar» o si la RAM sube de golpe
# (SUBIDA_RAPIDA); si la descartas, no la reabre hasta CIERRE_ESPERA salvo que
# la RAM llegue a un nivel «cerrar» más alto. Al bajar de REARME avisa «normal».
vigilar() {
    local pct previo=0 ahora vol veces cuerpo activo=0 ultimo=0 id=0 escalon=0 desde_previo=0
    local motivo nivel_cierre sonido_rapido cierre_pid=0 cierre_ultimo=0 cierre_desde=0
    IFS='|' read -r _ sonido_rapido _ _ _ <<<"${NIVELES[0]}"
    log_info "vigilando la RAM cada ${INTERVALO} s (aviso desde ${UMBRAL}%, lista desde $(primer_nivel_cierre)% o si sube ${SUBIDA_RAPIDA} puntos de golpe, rearme bajo ${REARME}%)"
    while true; do
        pct=$(ram_pct)
        ahora=$(date +%s)
        motivo=""; nivel_cierre=0
        if elegir_nivel "$pct"; then
            # al subir de nivel suena ya, sin esperar el NIVEL_REPETIR del nivel anterior
            if [ "$activo" -eq 0 ] || [ "$NIVEL_DESDE" -gt "$desde_previo" ] \
               || [ $(( ahora - ultimo )) -ge "$NIVEL_REPETIR" ]; then
                vol=$(volumen_para "$pct" "$escalon")
                veces=$(veces_para "$escalon")
                sonar "$NIVEL_SONIDO" "$vol" "$veces"
                cuerpo="Las que más usan:"$'\n'"$(top_apps)"
                [ "$NIVEL_ACCION" = cerrar ] || cuerpo+=$'\n'"Al $(primer_nivel_cierre)% se abre la lista para cerrar apps."
                id=$(notificar "$id" "$NIVEL_URGENCIA" dialog-warning "RAM al ${pct}%" "$cuerpo")
                if [ "$activo" -eq 0 ] || [ "$NIVEL_DESDE" -ne "$desde_previo" ]; then
                    log_warn "RAM al ${pct}%: aviso ${NIVEL_URGENCIA} (${NIVEL_SONIDO})"
                fi
                desde_previo="$NIVEL_DESDE"
                log_debug "aviso ${escalon}: ${pct}% · ${NIVEL_SONIDO} ×${veces} · volumen ${vol}%"
                activo=1; ultimo="$ahora"; escalon=$(( escalon + 1 ))
            fi
            if [ "$NIVEL_ACCION" = cerrar ]; then
                motivo="RAM al ${pct}%"; nivel_cierre="$NIVEL_DESDE"
            fi
        elif [ "$activo" -eq 1 ] && [ "$pct" -lt "$REARME" ]; then
            notificar "$id" normal dialog-information "RAM normal (${pct}%)" "Ya bajó del ${REARME}%." >/dev/null
            log_ok "RAM normal (${pct}%)"
            activo=0; id=0; escalon=0; desde_previo=0; cierre_ultimo=0; cierre_desde=0
        fi
        if [ -z "$motivo" ] && [ "$previo" -gt 0 ] && [ "$pct" -ge "${SUBIDA_DESDE}" ] \
           && [ $(( pct - previo )) -ge "${SUBIDA_RAPIDA}" ]; then
            motivo="la RAM subió de ${previo}% a ${pct}% en ${INTERVALO} s"
        fi
        if [ -n "$motivo" ] && cierre_libre "$cierre_pid" \
           && { [ $(( ahora - cierre_ultimo )) -ge "${CIERRE_ESPERA}" ] || [ "$nivel_cierre" -gt "$cierre_desde" ]; }; then
            log_warn "${motivo}: abro la lista para cerrar apps"
            if [ "$nivel_cierre" -eq 0 ]; then sonar "$sonido_rapido" "$VOL_MAX" 1; fi
            abrir_cierre "$pct" &
            cierre_pid=$!; cierre_ultimo="$ahora"; cierre_desde="$nivel_cierre"
        fi
        previo="$pct"
        sleep "${INTERVALO}"
    done
}

# --- mostrar_estado() ------------------------------------------------------
mostrar_estado() {
    local pct activo mb nombre
    pct=$(ram_pct)
    activo=$(systemctl --user is-active "${UNIDAD}" 2>/dev/null || true)
    log_section "Alerta de RAM"
    log_summary_row "RAM usada" "${pct}% ($(formato_gb "$(ram_usada_mb)"))"
    if elegir_nivel "$pct"; then
        log_summary_row "Nivel" "${NIVEL_URGENCIA} · ${NIVEL_SONIDO} · volumen $(volumen_para "$pct")%"
    else
        log_summary_row "Nivel" "sin aviso (empieza en ${UMBRAL}%)"
    fi
    log_summary_row "Servicio ${UNIDAD}" "${activo:-desconocido}"
    log_plain ""
    log_plain "Tus apps abiertas (las que «cerrar» ofrecería):"
    while IFS='|' read -r mb _ nombre; do
        if [ -n "$mb" ]; then printf '  %-30s %s\n' "$nombre" "$(formato_gb "$mb")"; fi
    done < <(apps_abiertas)
    log_plain ""
    top_apps | grep 'fuera de tus apps' || true
    if ! swapon --noheadings 2>/dev/null | grep -q .; then
        log_plain ""
        log_warn "no hay swap: si la RAM se llena, el kernel cierra procesos sin aviso."
    fi
    return 0
}

# --- probar_niveles() ------------------------------------------------------
# Hace sonar cada nivel de menor a mayor y, en el más alto, el escalamiento
# completo (escalones 0, 2 y 4), para calibrar el volumen.
probar_niveles() {
    local i nivel desde vol veces escalon
    log_section "Prueba de sonidos"
    for (( i = ${#NIVELES[@]} - 1; i >= 0; i-- )); do
        IFS='|' read -r desde NIVEL_SONIDO NIVEL_URGENCIA _ _ <<<"${NIVELES[$i]}"
        for escalon in 0 2 4; do
            [ "$i" -eq 0 ] || [ "$escalon" -eq 0 ] || continue
            vol=$(volumen_para "$desde" "$escalon")
            veces=$(veces_para "$escalon")
            log_info "${desde}% · escalón ${escalon} → ${NIVEL_SONIDO} ×${veces} a ${vol}% (${NIVEL_URGENCIA})"
            sonar "$NIVEL_SONIDO" "$vol" "$veces"
            sleep $(( 2 * veces + 1 ))
        done
    done
    notificar 0 normal dialog-warning "Alerta de RAM (prueba)" "Así se verá el aviso. Las que más usan:"$'\n'"$(top_apps)" >/dev/null
    log_ok "prueba terminada (la lista de cierre se prueba con: main.sh cerrar)"
    return 0
}
