#!/bin/bash
#
# status.sh — Reporte de estado de todos los repositorios Git configurados.
#
# Lee la misma lista de repos que sync.sh desde repos-config.yml,
# así que nunca se desincronizan entre sí.
#
# Autor: Edison Achalma (achalmed)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/repos-config.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

show_help() {
cat << EOF
Uso: $(basename "$0") [OPCIONES]

Muestra el estado de todos los repositorios definidos en repos-config.yml:
cambios sin commit, commits sin push, y commits remotos pendientes de pull.

Opciones:
      --config RUTA    Usar un archivo de configuración distinto a
                        repos-config.yml (por defecto, el que está junto
                        a este script, el mismo que usa sync.sh).
  -h, --help            Mostrar esta ayuda.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config) CONFIG_FILE="$2"; shift 2 ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Opción desconocida: $1"; show_help; exit 1 ;;
    esac
done

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} No se encontró el archivo de configuración: $CONFIG_FILE"
    exit 1
fi

# ---------- Parser YAML ligero (idéntico al de sync.sh) ----------
yaml_base_directory() {
    grep -E '^base_directory:' "$CONFIG_FILE" | sed -E 's/^base_directory:[[:space:]]*//' | sed -E 's/[[:space:]]*$//'
}

yaml_repos() {
    awk '
        /^  - name:/ {
            if (name != "") print name "|" branch "|" enabled
            name=$0; sub(/^  - name:[[:space:]]*/, "", name); gsub(/[[:space:]]+$/, "", name)
            branch="main"; enabled="true"
            next
        }
        /^    branch:/ {
            branch=$0; sub(/^    branch:[[:space:]]*/, "", branch); gsub(/[[:space:]]+$/, "", branch)
            next
        }
        /^    enabled:/ {
            enabled=$0; sub(/^    enabled:[[:space:]]*/, "", enabled); gsub(/[[:space:]]+$/, "", enabled)
            next
        }
        END {
            if (name != "") print name "|" branch "|" enabled
        }
    ' "$CONFIG_FILE"
}

BASE_DIR="$(yaml_base_directory)"
BASE_DIR="${BASE_DIR/#\~/$HOME}"

if [ -z "$BASE_DIR" ]; then
    echo -e "${RED}[ERROR]${NC} base_directory no está definido en $CONFIG_FILE"
    exit 1
fi

mapfile -t ALL_REPO_LINES < <(yaml_repos)

declare -a REPOS=()
for line in "${ALL_REPO_LINES[@]}"; do
    name="${line%%|*}"
    rest="${line#*|}"
    enabled="${rest##*|}"
    [ "$enabled" = "true" ] && REPOS+=("$name")
done

if [ "${#REPOS[@]}" -eq 0 ]; then
    echo -e "${RED}[ERROR]${NC} No hay repositorios habilitados en $CONFIG_FILE"
    exit 1
fi

# ---------- Obtener info de un repo ----------
get_repo_info() {
    local repo_path="$1"
    local repo_name="$2"

    cd "$repo_path" 2>/dev/null || return 1

    local branch remote last_commit
    branch="$(git branch --show-current 2>/dev/null)"
    last_commit="$(git log -1 --format="%h - %s (%cr)" 2>/dev/null)"

    local uncommitted unpushed behind
    uncommitted="$(git status --short 2>/dev/null | wc -l)"

    # Si no hay upstream configurado, estos comandos fallan silenciosamente -> 0
    unpushed="$(git log "origin/${branch}..${branch}" --oneline 2>/dev/null | wc -l)"
    behind="$(git log "${branch}..origin/${branch}" --oneline 2>/dev/null | wc -l)"

    local status color
    if [ "$uncommitted" -gt 0 ]; then
        status="CAMBIOS SIN COMMIT"; color="$RED"
    elif [ "$unpushed" -gt 0 ]; then
        status="COMMITS SIN PUSH"; color="$YELLOW"
    elif [ "$behind" -gt 0 ]; then
        status="COMMITS REMOTOS (PULL NECESARIO)"; color="$CYAN"
    else
        status="SINCRONIZADO"; color="$GREEN"
    fi

    echo "${repo_name}|${branch}|${status}|${color}|${uncommitted}|${unpushed}|${behind}|${last_commit}"
}

clear
echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║           REPORTE DE ESTADO DE REPOSITORIOS GIT                   ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Directorio base:${NC} $BASE_DIR"
echo -e "${BLUE}Fecha:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BLUE}Repositorios analizados:${NC} ${#REPOS[@]}"
echo ""

declare -a repo_data
total=0
clean=0
dirty=0
behind_count=0

for repo in "${REPOS[@]}"; do
    repo_path="${BASE_DIR}/${repo}"

    if [ -d "${repo_path}/.git" ]; then
        info="$(get_repo_info "$repo_path" "$repo")"
        repo_data+=("$info")
        ((total++))

        status="$(echo "$info" | cut -d'|' -f3)"
        if [ "$status" = "SINCRONIZADO" ]; then
            ((clean++))
        else
            ((dirty++))
        fi

        behind="$(echo "$info" | cut -d'|' -f7)"
        [ "$behind" -gt 0 ] && ((behind_count++))
    else
        echo -e "${YELLOW}[AVISO]${NC} ${repo}: no encontrado o no es repo Git (${repo_path})"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}RESUMEN GENERAL${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}Sincronizados:${NC}    $clean"
echo -e "${YELLOW}Con cambios:${NC}      $dirty"
echo -e "${CYAN}Detrás de origin:${NC} $behind_count"
echo ""

echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}ESTADO DETALLADO${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo ""

printf "${BOLD}%-25s %-15s %-30s %s${NC}\n" "REPOSITORIO" "RAMA" "ESTADO" "CAMBIOS"
echo "────────────────────────────────────────────────────────────────────"

for info in "${repo_data[@]}"; do
    IFS='|' read -r name branch status color uncommitted unpushed behind last_commit <<< "$info"

    changes=""
    [ "$uncommitted" -gt 0 ] && changes+="M:${uncommitted} "
    [ "$unpushed" -gt 0 ] && changes+="↑${unpushed} "
    [ "$behind" -gt 0 ] && changes+="↓${behind} "
    [ -z "$changes" ] && changes="✓"

    printf "%-25s %-15s ${color}%-30s${NC} %s\n" \
        "${name:0:24}" "${branch:0:14}" "${status:0:29}" "$changes"
done

echo ""

needs_attention=false
for info in "${repo_data[@]}"; do
    IFS='|' read -r name branch status color uncommitted unpushed behind last_commit <<< "$info"

    if [ "$status" != "SINCRONIZADO" ]; then
        if [ "$needs_attention" = false ]; then
            echo "════════════════════════════════════════════════════════════════════"
            echo -e "${BOLD}REPOSITORIOS QUE NECESITAN ATENCIÓN${NC}"
            echo "════════════════════════════════════════════════════════════════════"
            echo ""
            needs_attention=true
        fi

        echo -e "${BOLD}${color}▶ ${name}${NC}"
        echo -e "  Rama: ${branch}"
        echo -e "  Estado: ${color}${status}${NC}"
        [ "$uncommitted" -gt 0 ] && echo -e "  ${YELLOW}Archivos sin commit: ${uncommitted}${NC}"
        [ "$unpushed" -gt 0 ] && echo -e "  ${YELLOW}Commits sin push: ${unpushed}${NC}"
        [ "$behind" -gt 0 ] && echo -e "  ${CYAN}Commits detrás de origin: ${behind}${NC}"
        echo -e "  Último commit: ${last_commit}"
        echo ""
    fi
done

echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}LEYENDA${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo -e "M:n  Archivos modificados sin commit"
echo -e "↑n   Commits locales sin push"
echo -e "↓n   Commits remotos (necesita pull)"
echo -e "✓    Sincronizado correctamente"
echo ""

if [ "$dirty" -gt 0 ] || [ "$behind_count" -gt 0 ]; then
    echo "════════════════════════════════════════════════════════════════════"
    echo -e "${BOLD}ACCIONES SUGERIDAS${NC}"
    echo "════════════════════════════════════════════════════════════════════"

    if [ "$behind_count" -gt 0 ]; then
        echo -e "${CYAN}- Hay repos detrás de origin. Para actualizarlos:${NC}"
        echo "    ${SCRIPT_DIR}/sync.sh -n -c   # revisar primero"
        echo ""
    fi

    if [ "$dirty" -gt 0 ]; then
        echo -e "${YELLOW}- Hay repos con cambios pendientes. Para sincronizarlos:${NC}"
        echo "    ${SCRIPT_DIR}/sync.sh -m \"tu mensaje aquí\""
        echo ""
    fi
fi

echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}ACTIVIDAD RECIENTE (últimos 7 días)${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo ""

total_commits=0
for repo in "${REPOS[@]}"; do
    repo_path="${BASE_DIR}/${repo}"
    if [ -d "${repo_path}/.git" ]; then
        commits="$(cd "$repo_path" && git log --since="7 days ago" --oneline 2>/dev/null | wc -l)"
        if [ "$commits" -gt 0 ]; then
            printf "%-25s %3d commits\n" "$repo" "$commits"
            ((total_commits += commits))
        fi
    fi
done

echo ""
echo -e "${BOLD}Total de commits en la semana: ${total_commits}${NC}"
echo ""
