#!/usr/bin/env bash
# =============================================================================
#  lib/processor.sh — Lógica de procesamiento por carpeta
# =============================================================================
#
#  Contiene la lógica principal de backup:
#    - process_folder()     — orquesta los tres pasos (nuevo/mod/huérf)
#    - _handle_new_files()  — copia archivos nuevos con progreso
#    - _handle_modified()   — gestión interactiva de archivos modificados
#    - _handle_orphans()    — gestión interactiva de archivos huérfanos
#
#  Cada función tiene una única responsabilidad siguiendo SRP.
#  Las funciones privadas (prefijo _) son helpers internos del módulo.
# =============================================================================

# ── Contadores globales de estadísticas ──────────────────────────────────────
# Se incrementan durante el procesamiento y se leen en summary.sh
STATS_COPIED=0
STATS_UPDATED=0
STATS_SKIPPED=0
STATS_ORPHANS=0
STATS_DELETED=0
STATS_START_TIME=$(date +%s)

# ── process_folder() ──────────────────────────────────────────────────────────
# Orquesta el backup completo de una carpeta: nuevos → modificados → huérfanos.
# Es el punto de entrada principal desde main.sh para cada carpeta del perfil.
#
# Arguments:
#   $1 - Nombre de la carpeta (relativo al home)
#   $2 - Ruta de origen (home base)
#   $3 - Ruta de destino (base en disco)
#   $4 - Opciones rsync (cadena)
process_folder() {
    local folder="$1"
    local home_path="$2"
    local dest_base="$3"
    local rsync_opts="$4"

    local src="${home_path}/${folder}"
    local dest="${dest_base}/${folder}"

    log_title "╔══ Procesando: ${folder} ══╗"
    log_separator

    # Crear directorio destino si es la primera vez
    if [ ! -d "${dest}" ]; then
        log_info "  Nueva carpeta en disco externo: ${dest}"
        if [ "${OPT_SIMULATE}" = false ]; then
            mkdir -p "${dest}" || {
                log_error "  No se pudo crear: ${dest}"
                return 1
            }
        fi
    fi

    _handle_new_files   "${src}" "${dest}" "${rsync_opts}" "${folder}"
    _handle_modified    "${src}" "${dest}" "${rsync_opts}" "${folder}"
    _handle_orphans     "${src}" "${dest}" "${folder}"

    echo ""
    log_ok "╚══ Finalizado: ${folder} ══╝"
    log_separator
    echo ""
}

# ── _handle_new_files() ───────────────────────────────────────────────────────
# Detecta y copia archivos nuevos (no existen en destino).
# No requiere confirmación: los archivos nuevos siempre se copian.
# Usa pv si está disponible para una barra de progreso visual.
#
# Arguments:
#   $1 - Ruta de origen de la carpeta
#   $2 - Ruta de destino de la carpeta
#   $3 - Opciones rsync
#   $4 - Nombre de la carpeta (para logging)
_handle_new_files() {
    local src="$1"
    local dest="$2"
    local rsync_opts="$3"
    local folder="$4"

    log_info "Paso A: Analizando archivos nuevos..."

    local new_files=()
    while IFS= read -r line; do
        [ -n "${line}" ] && new_files+=("${line}")
    done < <(get_new_files "${src}" "${dest}" "${rsync_opts}")

    if [ "${#new_files[@]}" -eq 0 ]; then
        log_ok "  → Sin archivos nuevos en: ${folder}"
        return 0
    fi

    log_ok "  → ${#new_files[@]} archivo(s) nuevo(s) a copiar"

    if [ "${LOGGER_VERBOSE}" = true ]; then
        for f in "${new_files[@]}"; do
            log_debug "    + ${f}"
        done
    fi

    [ "${OPT_SIMULATE}" = true ] && {
        log_info "  [SIMULACIÓN] Se copiarían ${#new_files[@]} archivo(s) nuevo(s)"
        return 0
    }

    # Calcular tamaño total para la barra de progreso
    local total_bytes=0
    for f in "${new_files[@]}"; do
        local fsize
        fsize=$(stat --printf='%s' "${src}/${f}" 2>/dev/null || echo "0")
        (( total_bytes += fsize ))
    done

    log_info "  Copiando ${#new_files[@]} archivo(s) ($(format_file_size ${total_bytes}))..."

    if command -v pv &>/dev/null; then
        # shellcheck disable=SC2086
        rsync ${rsync_opts} --ignore-existing \
            "${src}/" "${dest}/" 2>/dev/null \
            | pv -l -s "${#new_files[@]}" > /dev/null || true
    else
        # shellcheck disable=SC2086
        rsync ${rsync_opts} --progress --ignore-existing \
            "${src}/" "${dest}/" 2>/dev/null || true
    fi

    (( STATS_COPIED += ${#new_files[@]} ))
    log_ok "  ✓ Copiados: ${#new_files[@]} archivo(s)"
}

# ── _handle_modified() ────────────────────────────────────────────────────────
# Detecta y gestiona archivos cuyos checksums difieren entre origen y destino.
# En modo --force actualiza sin preguntar.
# En modo interactivo pregunta archivo por archivo con opciones detalladas.
#
# Arguments:
#   $1 - Ruta de origen de la carpeta
#   $2 - Ruta de destino de la carpeta
#   $3 - Opciones rsync
#   $4 - Nombre de la carpeta (para logging)
_handle_modified() {
    local src="$1"
    local dest="$2"
    local rsync_opts="$3"
    local folder="$4"

    log_info "Paso B: Analizando archivos modificados..."

    local modified_files=()
    while IFS= read -r line; do
        [ -n "${line}" ] && modified_files+=("${line}")
    done < <(get_modified_files "${src}" "${dest}" "${rsync_opts}")

    if [ "${#modified_files[@]}" -eq 0 ]; then
        log_ok "  → Sin archivos modificados en: ${folder}"
        return 0
    fi

    log_warn "  → ${#modified_files[@]} archivo(s) con cambios detectados"

    # Flag local de carpeta: si usuario elige "todos", aplica al resto del loop
    local force_folder=false

    for file_rel in "${modified_files[@]}"; do
        local file_src="${src}/${file_rel}"
        local file_dest="${dest}/${file_rel}"

        # Si "forzar todos de esta carpeta" fue activado en iteración anterior
        if [ "${force_folder}" = true ]; then
            _sync_single_file "${file_src}" "${file_dest}" "${file_rel}" "${folder}"
            continue
        fi

        echo ""
        log_separator "·" 60
        log_action "  MODIFICADO: ${folder}/${file_rel}"
        log_separator "·" 60

        # Mostrar metadatos del archivo si existe en ambos lados
        if [ -f "${file_src}" ] && [ -f "${file_dest}" ]; then
            local size_src size_dest date_src date_dest
            size_src=$(stat  --printf='%s' "${file_src}"  2>/dev/null || echo "?")
            size_dest=$(stat --printf='%s' "${file_dest}" 2>/dev/null || echo "?")
            date_src=$(stat  --printf='%y' "${file_src}"  2>/dev/null | cut -d'.' -f1)
            date_dest=$(stat --printf='%y' "${file_dest}" 2>/dev/null | cut -d'.' -f1)
            log_info "  Origen (laptop):     ${size_src} bytes  —  ${date_src}"
            log_info "  Destino (disco ext): ${size_dest} bytes  —  ${date_dest}"
        fi

        # Modo --force: actualizar sin preguntar
        if [ "${OPT_FORCE}" = true ]; then
            log_info "  [--force] Actualizando sin preguntar..."
            [ "${OPT_SIMULATE}" = false ] && _sync_single_file \
                "${file_src}" "${file_dest}" "${file_rel}" "${folder}"
            continue
        fi

        # Modo interactivo: preguntar qué hacer
        echo ""
        echo -e "${CLR_BOLD}  ¿Qué deseas hacer con este archivo?${CLR_RESET}"
        echo -e "  ${CLR_GREEN}[s]${CLR_RESET} Actualizar en disco externo (sobrescribir)"
        echo -e "  ${CLR_YELLOW}[v]${CLR_RESET} Ver diferencias primero"
        echo -e "  ${CLR_CYAN}[i]${CLR_RESET} Ignorar (conservar versión del disco)"
        echo -e "  ${CLR_MAGENTA}[t]${CLR_RESET} Actualizar TODOS los modificados de esta carpeta"
        echo -e "  ${CLR_RED}[n]${CLR_RESET} Ignorar TODOS los modificados de esta carpeta"
        echo ""

        local answer
        read -rp "  Tu elección [s/v/i/t/n]: " answer
        answer=$(echo "${answer}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

        case "${answer}" in
            s|si|sí|y|yes)
                [ "${OPT_SIMULATE}" = false ] && \
                    _sync_single_file "${file_src}" "${file_dest}" "${file_rel}" "${folder}"
                ;;
            v|ver)
                show_file_diff "${file_src}" "${file_dest}"
                local answer2
                read -rp "  ¿Actualizar este archivo? [s/n]: " answer2
                answer2=$(echo "${answer2}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
                if [[ "${answer2}" =~ ^(s|si|sí|y|yes)$ ]]; then
                    [ "${OPT_SIMULATE}" = false ] && \
                        _sync_single_file "${file_src}" "${file_dest}" "${file_rel}" "${folder}"
                else
                    log_info "  Omitido: ${file_rel}"
                    (( STATS_SKIPPED++ ))
                fi
                ;;
            i|ignorar)
                log_info "  Omitido: ${file_rel}"
                (( STATS_SKIPPED++ ))
                ;;
            t|todos)
                # Activar flag para el resto del loop de esta carpeta
                force_folder=true
                [ "${OPT_SIMULATE}" = false ] && \
                    _sync_single_file "${file_src}" "${file_dest}" "${file_rel}" "${folder}"
                log_ok "  Modo 'todos' activado para el resto de: ${folder}"
                ;;
            n|no)
                log_info "  Ignorando todos los modificados de: ${folder}"
                # Contar los restantes como omitidos
                (( STATS_SKIPPED++ ))
                return 0
                ;;
            *)
                log_warn "  Opción no reconocida. Omitiendo: ${file_rel}"
                (( STATS_SKIPPED++ ))
                ;;
        esac
    done
}

# ── _handle_orphans() ─────────────────────────────────────────────────────────
# Detecta y gestiona archivos en el disco externo que ya no existen en origen.
# Puede ser: archivos borrados, movidos, o propios del disco.
# En modo --delete-all elimina todos sin preguntar.
# En modo interactivo ofrece: eliminar todos, revisar uno a uno, o conservar.
#
# Arguments:
#   $1 - Ruta de origen de la carpeta
#   $2 - Ruta de destino de la carpeta
#   $3 - Nombre de la carpeta (para logging)
_handle_orphans() {
    local src="$1"
    local dest="$2"
    local folder="$3"

    [ -d "${dest}" ] || return 0

    log_info "Paso C: Buscando archivos huérfanos en disco externo..."

    local orphans=()
    while IFS= read -r line; do
        [ -n "${line}" ] && orphans+=("${line}")
    done < <(get_orphan_files "${src}" "${dest}")

    if [ "${#orphans[@]}" -eq 0 ]; then
        log_ok "  → Sin huérfanos en: ${folder}"
        return 0
    fi

    (( STATS_ORPHANS += ${#orphans[@]} ))
    log_warn "  → ${#orphans[@]} elemento(s) en disco que NO están en origen:"
    echo ""

    for item in "${orphans[@]}"; do
        local item_path="${dest}/${item}"
        local item_type="archivo"
        [ -d "${item_path}" ] && item_type="directorio"
        log_warn "  ⚠  ${item_type}: ${folder}/${item}"

        if [ -f "${item_path}" ]; then
            local item_size item_date
            item_size=$(stat --printf='%s' "${item_path}" 2>/dev/null || echo "?")
            item_date=$(stat --printf='%y' "${item_path}" 2>/dev/null | cut -d'.' -f1)
            log_debug "     Tamaño: ${item_size} bytes | Fecha: ${item_date}"
        fi
    done

    echo ""
    log_warn "  NOTA: Pueden ser archivos eliminados en laptop, movidos, o solo del disco."

    # Modo --delete-all: eliminar todos sin preguntar
    if [ "${OPT_DELETE_ALL}" = true ]; then
        log_action "  [--delete-all] Eliminando todos los huérfanos..."
        for item in "${orphans[@]}"; do
            _delete_orphan "${dest}/${item}" "${folder}/${item}"
        done
        return 0
    fi

    # Modo interactivo
    echo ""
    echo -e "${CLR_BOLD}  ¿Qué deseas hacer con los huérfanos de '${folder}'?${CLR_RESET}"
    echo -e "  ${CLR_RED}[e]${CLR_RESET} Eliminar todos del disco externo (sincronización total)"
    echo -e "  ${CLR_YELLOW}[r]${CLR_RESET} Revisar uno por uno y decidir"
    echo -e "  ${CLR_GREEN}[c]${CLR_RESET} Conservar todos (no eliminar nada)"
    echo ""

    local answer
    read -rp "  Tu elección [e/r/c]: " answer
    answer=$(echo "${answer}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

    case "${answer}" in
        e|eliminar)
            for item in "${orphans[@]}"; do
                _delete_orphan "${dest}/${item}" "${folder}/${item}"
            done
            ;;
        r|revisar)
            for item in "${orphans[@]}"; do
                local item_path="${dest}/${item}"
                echo ""
                log_action "  HUÉRFANO: ${folder}/${item}"
                local answer_item
                read -rp "  ¿Eliminar del disco externo? [s/n]: " answer_item
                answer_item=$(echo "${answer_item}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
                if [[ "${answer_item}" =~ ^(s|si|sí|y|yes)$ ]]; then
                    _delete_orphan "${item_path}" "${folder}/${item}"
                else
                    log_info "  Conservado: ${folder}/${item}"
                fi
            done
            ;;
        c|conservar|n|no|*)
            log_info "  Conservando todos los huérfanos de: ${folder}"
            ;;
    esac
}

# ── _sync_single_file() ───────────────────────────────────────────────────────
# Sincroniza un único archivo de origen a destino usando rsync.
# Extrae como función propia para evitar duplicar la llamada rsync en 3 lugares.
#
# Arguments:
#   $1 - Ruta completa del archivo de origen
#   $2 - Ruta completa del archivo de destino
#   $3 - Ruta relativa del archivo (para logging)
#   $4 - Nombre de la carpeta (para logging)
_sync_single_file() {
    local file_src="$1"
    local file_dest="$2"
    local file_rel="$3"
    local folder="$4"

    # Crear directorio padre si no existe (para archivos en subdirectorios)
    local dest_dir
    dest_dir=$(dirname "${file_dest}")
    [ -d "${dest_dir}" ] || mkdir -p "${dest_dir}"

    if rsync -ahc "${file_src}" "${file_dest}" 2>/dev/null; then
        log_ok "  ✓ Actualizado: ${folder}/${file_rel}"
        (( STATS_UPDATED++ ))
    else
        log_error "  ✗ Error al actualizar: ${folder}/${file_rel}"
    fi
}

# ── _delete_orphan() ──────────────────────────────────────────────────────────
# Elimina un archivo o directorio huérfano del disco externo.
# Separado para evitar duplicación entre modo --delete-all y revisión manual.
#
# Arguments:
#   $1 - Ruta completa del elemento a eliminar
#   $2 - Ruta relativa (para logging)
_delete_orphan() {
    local full_path="$1"
    local display_path="$2"

    if [ "${OPT_SIMULATE}" = true ]; then
        log_info "  [SIMULACIÓN] Se eliminaría: ${display_path}"
        return 0
    fi

    if rm -rf "${full_path}"; then
        log_ok "  ✗ Eliminado: ${display_path}"
        (( STATS_DELETED++ ))
    else
        log_error "  Error al eliminar: ${display_path}"
    fi
}

# ── elapsed_time() ────────────────────────────────────────────────────────────
# Calcula el tiempo transcurrido desde STATS_START_TIME.
#
# Outputs (stdout):
#   Cadena formateada "HHh MMm SSs"
elapsed_time() {
    local seconds=$(( $(date +%s) - STATS_START_TIME ))
    printf '%02dh %02dm %02ds' \
        $(( seconds / 3600 )) \
        $(( (seconds % 3600) / 60 )) \
        $(( seconds % 60 ))
}
