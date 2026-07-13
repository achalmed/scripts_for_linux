#!/usr/bin/env bash
# =============================================================================
# lib/status_reporter.sh
# -----------------------------------------------------------------------------
# Recolección y presentación del estado de todos los repositorios.
#
# BUGS CORREGIDOS:
#   Bug 2 - El original comparaba git log origin/branch..branch sin hacer
#            fetch previo. Si el último fetch fue hace días, los contadores
#            "commits remotos" eran siempre 0 aunque hubiera commits nuevos
#            en GitHub/GitLab. Ahora status_collect_repo hace fetch --quiet
#            antes de calcular behind/ahead.
#
#   Bug 3 - La variable 'remote' se declaraba con 'local' en get_repo_info
#            pero nunca se asignaba ni usaba (residuo de código anterior).
#            Eliminada para evitar confusión.
# =============================================================================

[[ -n "${_STATUS_REPORTER_LOADED:-}" ]] && return 0
readonly _STATUS_REPORTER_LOADED=1

# Códigos de estado (orden de prioridad, mayor a menor)
readonly STATUS_UNCOMMITTED="CAMBIOS SIN COMMIT"
readonly STATUS_UNPUSHED="COMMITS SIN PUSH"
readonly STATUS_BEHIND="COMMITS REMOTOS (PULL NECESARIO)"
readonly STATUS_DIVERGED="DIVERGIDO (PULL + PUSH)"
readonly STATUS_CLEAN="SINCRONIZADO"

# =============================================================================
# status_collect_repo REPO_PATH REPO_NAME
#   Recolecta toda la información de estado de un repo y la imprime como
#   una línea de campos separados por | (para procesado posterior).
#
#   Formato: name|branch|status|uncommitted|ahead|behind|last_commit
# =============================================================================
status_collect_repo() {
    local repo_path="$1"
    local repo_name="$2"

    if ! git_is_repo "$repo_path"; then
        echo "${repo_name}|?|NO_ES_REPO|0|0|0|(no es un repo Git)"
        return
    fi

    cd "$repo_path" 2>/dev/null || {
        echo "${repo_name}|?|ERROR_ACCESO|0|0|0|(no se pudo acceder)"
        return
    }

    local branch
    branch="$(git_current_branch "$repo_path")"

    # CORRECCIÓN Bug 2: hacer fetch antes de calcular behind/ahead
    # El fallo de fetch (sin red) es silencioso; los contadores quedarán en 0
    git_fetch_remote "$repo_path" || true

    local uncommitted ahead behind last_commit
    uncommitted="$(git_count_uncommitted "$repo_path")"
    ahead="$(git_count_ahead "$repo_path" "$branch")"
    behind="$(git_count_behind "$repo_path" "$branch")"
    last_commit="$(git_last_commit_summary "$repo_path")"

    # Determinar estado (orden de prioridad)
    local status
    if [[ "$uncommitted" -gt 0 ]]; then
        status="$STATUS_UNCOMMITTED"
    elif [[ "$ahead" -gt 0 ]] && [[ "$behind" -gt 0 ]]; then
        status="$STATUS_DIVERGED"
    elif [[ "$ahead" -gt 0 ]]; then
        status="$STATUS_UNPUSHED"
    elif [[ "$behind" -gt 0 ]]; then
        status="$STATUS_BEHIND"
    else
        status="$STATUS_CLEAN"
    fi

    echo "${repo_name}|${branch}|${status}|${uncommitted}|${ahead}|${behind}|${last_commit}"
}

# =============================================================================
# status_color_for STATUS
#   Imprime el código de color ANSI para el estado dado.
# =============================================================================
status_color_for() {
    case "$1" in
        "$STATUS_UNCOMMITTED") echo "${_C_RED}" ;;
        "$STATUS_DIVERGED")    echo "${_C_RED}" ;;
        "$STATUS_UNPUSHED")    echo "${_C_YELLOW}" ;;
        "$STATUS_BEHIND")      echo "${_C_CYAN}" ;;
        "$STATUS_CLEAN")       echo "${_C_GREEN}" ;;
        *)                     echo "${_C_NC}" ;;
    esac
}

# =============================================================================
# status_print_table REPO_DATA[]
#   Imprime la tabla formateada de todos los repos.
# =============================================================================
status_print_table() {
    local -a data=("$@")

    echo ""
    printf "${_C_BOLD}%-26s %-16s %-34s %-10s${_C_NC}\n" \
        "REPOSITORIO" "RAMA" "ESTADO" "CAMBIOS"
    echo "────────────────────────────────────────────────────────────────────────────"

    for row in "${data[@]}"; do
        IFS='|' read -r name branch status uncommitted ahead behind _rest <<< "$row"
        local color
        color="$(status_color_for "$status")"

        local changes=""
        [[ "$uncommitted" -gt 0 ]] && changes+="M:${uncommitted} "
        [[ "$ahead"       -gt 0 ]] && changes+="↑${ahead} "
        [[ "$behind"      -gt 0 ]] && changes+="↓${behind} "
        [[ -z "$changes"        ]] && changes="✓"

        printf "%-26s %-16s ${color}%-34s${_C_NC} %s\n" \
            "${name:0:25}" "${branch:0:15}" "${status:0:33}" "${changes}"
    done
}

# =============================================================================
# status_print_attention REPO_DATA[]
#   Imprime el bloque detallado de repos que necesitan atención.
# =============================================================================
status_print_attention() {
    local -a data=("$@")
    local printed_header=false

    for row in "${data[@]}"; do
        IFS='|' read -r name branch status uncommitted ahead behind last_commit <<< "$row"
        [[ "$status" == "$STATUS_CLEAN" ]] && continue

        if ! $printed_header; then
            echo ""
            echo "════════════════════════════════════════════════════════════════════════════"
            echo -e "${_C_BOLD}REPOSITORIOS QUE NECESITAN ATENCIÓN${_C_NC}"
            echo "════════════════════════════════════════════════════════════════════════════"
            printed_header=true
        fi

        local color
        color="$(status_color_for "$status")"
        echo ""
        echo -e "${_C_BOLD}${color}▶ ${name}${_C_NC}"
        echo -e "  Rama:         ${branch}"
        echo -e "  Estado:       ${color}${status}${_C_NC}"
        [[ "$uncommitted" -gt 0 ]] && \
            echo -e "  ${_C_YELLOW}Sin commit:   ${uncommitted} archivos${_C_NC}"
        [[ "$ahead" -gt 0 ]] && \
            echo -e "  ${_C_YELLOW}Sin push:     ${ahead} commits${_C_NC}"
        [[ "$behind" -gt 0 ]] && \
            echo -e "  ${_C_CYAN}Pull needed:  ${behind} commits remotos${_C_NC}"
        echo -e "  Último commit: ${last_commit}"
    done
}

# =============================================================================
# status_print_activity REPOS[] BASE_DIR [DAYS]
#   Imprime el resumen de actividad reciente de todos los repos.
# =============================================================================
status_print_activity() {
    local -a repos=("$@")
    # Los últimos dos parámetros son BASE_DIR y DAYS (convenio de llamada)
    local base_dir="${repos[-2]}"
    local days="${repos[-1]}"
    unset 'repos[-1]' 'repos[-2]'

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    echo -e "${_C_BOLD}ACTIVIDAD RECIENTE (últimos ${days} días)${_C_NC}"
    echo "════════════════════════════════════════════════════════════════════════════"
    echo ""

    local total=0
    for repo in "${repos[@]}"; do
        local name="${repo%%|*}"
        local repo_path="${base_dir}/${name}"
        [[ -d "${repo_path}/.git" ]] || continue
        local count
        count="$(git_recent_commit_count "$repo_path" "$days")"
        if [[ "$count" -gt 0 ]]; then
            printf "  %-26s %3d commits\n" "$name" "$count"
            ((total += count)) || true
        fi
    done

    echo ""
    echo -e "  ${_C_BOLD}Total de commits en ${days} días: ${total}${_C_NC}"
    echo ""
}

# =============================================================================
# status_print_suggestions SCRIPT_DIR DIRTY BEHIND
#   Imprime acciones sugeridas si hay repos con problemas.
# =============================================================================
status_print_suggestions() {
    local script_dir="$1"
    local dirty="$2"
    local behind="$3"

    [[ "$dirty" -eq 0 ]] && [[ "$behind" -eq 0 ]] && return

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    echo -e "${_C_BOLD}ACCIONES SUGERIDAS${_C_NC}"
    echo "════════════════════════════════════════════════════════════════════════════"

    if [[ "$behind" -gt 0 ]]; then
        echo -e "\n  ${_C_CYAN}Repos detrás de origin — para traer cambios remotos:${_C_NC}"
        echo "    ${script_dir}/sync.sh --check     # revisar primero"
        echo "    ${script_dir}/sync.sh              # aplicar pull+push"
    fi

    if [[ "$dirty" -gt 0 ]]; then
        echo -e "\n  ${_C_YELLOW}Repos con cambios pendientes — para sincronizar:${_C_NC}"
        echo "    ${script_dir}/sync.sh -m \"tu mensaje\""
    fi
    echo ""
}
