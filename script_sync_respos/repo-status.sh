#!/bin/bash

# Script para generar reporte del estado de todos los repositorios
# Útil para verificar qué repos necesitan atención

# Configuración
BASE_DIR="$HOME/Documents/publicaciones"
REPOS=(
    "actus-mercator"
    "aequilibria"
    "axiomata"
    "chaska"
    "dialectica-y-mercado"
    "epsilon-y-beta"
    "methodica"
    "numerus-scriptum"
    "optimums"
    "pecunia-fluxus"
    "res-publica"
    "website-achalma"
)

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Función para obtener info del repo
get_repo_info() {
    local repo_path="$1"
    local repo_name="$2"
    
    cd "$repo_path" 2>/dev/null || return 1
    
    # Información básica
    local branch=$(git branch --show-current 2>/dev/null)
    local remote=$(git remote get-url origin 2>/dev/null)
    local last_commit=$(git log -1 --format="%h - %s (%cr)" 2>/dev/null)
    
    # Estado
    local status=""
    local color=""
    
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        status="CAMBIOS SIN COMMIT"
        color="$RED"
    elif [ "$(git log origin/$branch..$branch 2>/dev/null | wc -l)" -gt 0 ]; then
        status="COMMITS SIN PUSH"
        color="$YELLOW"
    elif [ "$(git log $branch..origin/$branch 2>/dev/null | wc -l)" -gt 0 ]; then
        status="COMMITS REMOTOS (PULL NECESARIO)"
        color="$CYAN"
    else
        status="SINCRONIZADO"
        color="$GREEN"
    fi
    
    # Estadísticas
    local uncommitted=$(git status --short 2>/dev/null | wc -l)
    local unpushed=$(git log origin/$branch..$branch --oneline 2>/dev/null | wc -l)
    local behind=$(git log $branch..origin/$branch --oneline 2>/dev/null | wc -l)
    
    echo "$repo_name|$branch|$status|$color|$uncommitted|$unpushed|$behind|$last_commit"
}

# Encabezado
clear
echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║           REPORTE DE ESTADO DE REPOSITORIOS GIT                   ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Directorio base:${NC} $BASE_DIR"
echo -e "${BLUE}Fecha:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BLUE}Repositorios analizados:${NC} ${#REPOS[@]}"
echo ""

# Recopilar información
declare -a repo_data
total=0
clean=0
dirty=0
behind_count=0

for repo in "${REPOS[@]}"; do
    repo_path="$BASE_DIR/$repo"
    
    if [ -d "$repo_path/.git" ]; then
        info=$(get_repo_info "$repo_path" "$repo")
        repo_data+=("$info")
        ((total++))
        
        status=$(echo "$info" | cut -d'|' -f3)
        if [ "$status" = "SINCRONIZADO" ]; then
            ((clean++))
        else
            ((dirty++))
        fi
        
        behind=$(echo "$info" | cut -d'|' -f7)
        if [ "$behind" -gt 0 ]; then
            ((behind_count++))
        fi
    fi
done

# Resumen
echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}RESUMEN GENERAL${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}Limpios:${NC}        $clean"
echo -e "${YELLOW}Con cambios:${NC}    $dirty"
echo -e "${CYAN}Detrás de origin:${NC} $behind_count"
echo ""

# Tabla de repositorios
echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}ESTADO DETALLADO${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo ""

printf "${BOLD}%-25s %-15s %-25s %s${NC}\n" "REPOSITORIO" "RAMA" "ESTADO" "CAMBIOS"
echo "────────────────────────────────────────────────────────────────────"

for info in "${repo_data[@]}"; do
    IFS='|' read -r name branch status color uncommitted unpushed behind last_commit <<< "$info"
    
    # Construir string de cambios
    changes=""
    [ "$uncommitted" -gt 0 ] && changes+="📝$uncommitted "
    [ "$unpushed" -gt 0 ] && changes+="⬆️$unpushed "
    [ "$behind" -gt 0 ] && changes+="⬇️$behind "
    [ -z "$changes" ] && changes="✓"
    
    printf "%-25s %-15s ${color}%-25s${NC} %s\n" \
        "${name:0:24}" \
        "${branch:0:14}" \
        "${status:0:24}" \
        "$changes"
done

echo ""

# Detalles de repos con problemas
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
        
        echo -e "${BOLD}${color}▶ $name${NC}"
        echo -e "  Rama: $branch"
        echo -e "  Estado: ${color}$status${NC}"
        [ "$uncommitted" -gt 0 ] && echo -e "  ${YELLOW}Archivos sin commit: $uncommitted${NC}"
        [ "$unpushed" -gt 0 ] && echo -e "  ${YELLOW}Commits sin push: $unpushed${NC}"
        [ "$behind" -gt 0 ] && echo -e "  ${CYAN}Commits detrás de origin: $behind${NC}"
        echo -e "  Último commit: $last_commit"
        echo ""
    fi
done

# Leyenda
echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}LEYENDA${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo -e "📝  Archivos modificados sin commit"
echo -e "⬆️  Commits locales sin push"
echo -e "⬇️  Commits remotos (necesita pull)"
echo -e "✓  Sincronizado correctamente"
echo ""

# Sugerencias
if [ "$dirty" -gt 0 ] || [ "$behind_count" -gt 0 ]; then
    echo "════════════════════════════════════════════════════════════════════"
    echo -e "${BOLD}ACCIONES SUGERIDAS${NC}"
    echo "════════════════════════════════════════════════════════════════════"
    
    if [ "$behind_count" -gt 0 ]; then
        echo -e "${CYAN}1. Actualizar desde remoto:${NC}"
        echo "   cd $BASE_DIR && for repo in */; do cd \"\$repo\" && git pull && cd ..; done"
        echo ""
    fi
    
    if [ "$dirty" -gt 0 ]; then
        echo -e "${YELLOW}2. Sincronizar cambios locales:${NC}"
        echo "   ./quick-sync.sh \"update: sincronización $(date +%Y-%m-%d)\""
        echo ""
        echo -e "${YELLOW}3. O sincronizar manualmente cada repo:${NC}"
        for info in "${repo_data[@]}"; do
            IFS='|' read -r name branch status color uncommitted unpushed behind last_commit <<< "$info"
            if [ "$uncommitted" -gt 0 ] || [ "$unpushed" -gt 0 ]; then
                echo "   cd $BASE_DIR/$name && git add -A && git commit -m 'update' && git push"
            fi
        done
    fi
    echo ""
fi

# Estadísticas de commits (últimos 7 días)
echo "════════════════════════════════════════════════════════════════════"
echo -e "${BOLD}ACTIVIDAD RECIENTE (últimos 7 días)${NC}"
echo "════════════════════════════════════════════════════════════════════"
echo ""

total_commits=0
for repo in "${REPOS[@]}"; do
    repo_path="$BASE_DIR/$repo"
    if [ -d "$repo_path/.git" ]; then
        commits=$(cd "$repo_path" && git log --since="7 days ago" --oneline 2>/dev/null | wc -l)
        if [ "$commits" -gt 0 ]; then
            printf "%-25s %3d commits\n" "$repo" "$commits"
            ((total_commits += commits))
        fi
    fi
done

echo ""
echo -e "${BOLD}Total de commits en la semana: $total_commits${NC}"
echo ""
