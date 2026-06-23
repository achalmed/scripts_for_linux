#!/usr/bin/env bash
# =============================================================================
#  lib/analyzer.sh — Análisis de cambios entre origen y destino
# =============================================================================
#
#  Contiene las funciones que comparan el origen con el destino para
#  determinar qué archivos son nuevos, cuáles fueron modificados y cuáles
#  son huérfanos (existen en destino pero no en origen).
#
#  Todas las comparaciones usan rsync --dry-run para exactitud,
#  aprovechando la misma lógica que usará la copia real.
# =============================================================================

# ── get_new_files() ───────────────────────────────────────────────────────────
# Obtiene la lista de archivos que existen en origen pero NO en destino.
# Usa rsync --dry-run con --itemize-changes para detectarlos por el código
# '>f+++++++++' que rsync emite para archivos completamente nuevos.
#
# Arguments:
#   $1 - Ruta de origen
#   $2 - Ruta de destino
#   $3 - Opciones rsync base (cadena)
#
# Outputs (stdout):
#   Una ruta relativa por línea (vacío si no hay archivos nuevos)
get_new_files() {
    local src="$1"
    local dest="$2"
    local rsync_opts="$3"

    # shellcheck disable=SC2086
    rsync ${rsync_opts} -n --itemize-changes \
        "${src}/" "${dest}/" 2>/dev/null \
        | grep '^>f+++++++++' \
        | awk '{print $2}' \
        || true
}

# ── get_modified_files() ──────────────────────────────────────────────────────
# Obtiene archivos que existen en ambos lados pero cuyo contenido difiere.
# El código rsync '>f' sin '+++++++++ ' indica un archivo modificado.
#
# Arguments:
#   $1 - Ruta de origen
#   $2 - Ruta de destino
#   $3 - Opciones rsync base (cadena)
#
# Outputs (stdout):
#   Una ruta relativa por línea
get_modified_files() {
    local src="$1"
    local dest="$2"
    local rsync_opts="$3"

    # shellcheck disable=SC2086
    rsync ${rsync_opts} -n --itemize-changes \
        "${src}/" "${dest}/" 2>/dev/null \
        | grep '^>f' \
        | grep -v '+++++++++' \
        | awk '{print $2}' \
        || true
}

# ── get_orphan_files() ────────────────────────────────────────────────────────
# Obtiene archivos que existen en destino pero NO en origen.
# Estos son candidatos para eliminación o conservación.
# Usa comm para comparar los listados de ambos directorios de forma eficiente.
#
# Arguments:
#   $1 - Ruta de origen
#   $2 - Ruta de destino
#
# Outputs (stdout):
#   Una ruta relativa por línea (vacío si no hay huérfanos)
get_orphan_files() {
    local src="$1"
    local dest="$2"

    # Solo buscar huérfanos si el destino ya existe
    [ -d "${dest}" ] || return 0

    local src_list dest_list
    src_list=$(find "${src}/"  -mindepth 1 -printf '%P\n' 2>/dev/null | sort)
    dest_list=$(find "${dest}/" -mindepth 1 -printf '%P\n' 2>/dev/null | sort)

    # comm -13: muestra solo lo que está en destino y NO en origen
    comm -13 <(echo "${src_list}") <(echo "${dest_list}") 2>/dev/null \
        || true
}

# ── show_file_diff() ──────────────────────────────────────────────────────────
# Muestra las diferencias entre la versión de origen y la de destino.
# Para archivos de texto muestra diff unificado (máx. 60 líneas).
# Para archivos binarios muestra metadatos (tamaño, fecha).
#
# Arguments:
#   $1 - Ruta al archivo de origen (versión nueva)
#   $2 - Ruta al archivo de destino (versión en disco externo)
show_file_diff() {
    local file_src="$1"
    local file_dest="$2"

    if ! [ -f "${file_src}" ] || ! [ -f "${file_dest}" ]; then
        log_warn "  No se puede mostrar diff: alguno de los archivos no existe."
        return 0
    fi

    # Determinar si es texto o binario antes de intentar el diff
    if file --brief --mime "${file_src}" 2>/dev/null | grep -q "text"; then
        echo ""
        log_info "  ── Diferencias (origen ← vs → disco externo) ──"

        if [ -n "${DIFF_CMD}" ]; then
            # Cabeceras informativas para el diff
            ${DIFF_CMD} --unified=3 \
                --label "DISCO EXTERNO: $(basename "${file_dest}")" \
                --label "ORIGEN (laptop): $(basename "${file_src}")" \
                "${file_dest}" "${file_src}" 2>/dev/null \
                | head -60 \
                | sed 's/^/    /' \
                || true
        else
            log_warn "  diff no disponible para mostrar diferencias."
        fi
        echo ""
    else
        # Archivo binario: mostrar solo metadatos relevantes
        log_info "  (Archivo binario — se muestran metadatos)"
        local size_src size_dest date_src date_dest
        size_src=$(stat  --printf='%s bytes' "${file_src}"  2>/dev/null || echo "?")
        size_dest=$(stat --printf='%s bytes' "${file_dest}" 2>/dev/null || echo "?")
        date_src=$(stat  --printf='%y' "${file_src}"  2>/dev/null | cut -d'.' -f1)
        date_dest=$(stat --printf='%y' "${file_dest}" 2>/dev/null | cut -d'.' -f1)

        log_info "  Origen (laptop):     ${size_src}  —  ${date_src}"
        log_info "  Destino (disco ext): ${size_dest}  —  ${date_dest}"
    fi
}

# ── format_file_size() ────────────────────────────────────────────────────────
# Convierte bytes a unidad legible (B, KB, MB, GB).
# Usa aritmética de bash pura para evitar dependencia de bc.
#
# Arguments:
#   $1 - Tamaño en bytes (entero)
#
# Outputs (stdout):
#   Tamaño formateado con unidad
format_file_size() {
    local bytes="$1"
    if   [ "${bytes}" -ge 1073741824 ]; then
        awk "BEGIN {printf \"%.2f GB\", ${bytes}/1073741824}"
    elif [ "${bytes}" -ge 1048576 ]; then
        awk "BEGIN {printf \"%.2f MB\", ${bytes}/1048576}"
    elif [ "${bytes}" -ge 1024 ]; then
        awk "BEGIN {printf \"%.2f KB\", ${bytes}/1024}"
    else
        echo "${bytes} B"
    fi
}
