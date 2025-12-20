#!/bin/bash

# Script simplificado para sincronización rápida
# Uso: ./quick-sync.sh [mensaje]

# Configuración rápida - MODIFICA ESTAS RUTAS
BASE_DIR="$HOME/Documents/publicaciones"  # Cambia esto a tu directorio

# Repositorios a sincronizar
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
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Mensaje de commit
MSG="${1:-update: sincronización automática}"

echo -e "${BLUE}Sincronizando ${#REPOS[@]} repositorios...${NC}"
echo "Mensaje: $MSG"
echo ""

SUCCESS=0
FAILED=0

for repo in "${REPOS[@]}"; do
    cd "$BASE_DIR/$repo" 2>/dev/null || continue
    
    # Verificar cambios
    if ! git diff-index --quiet HEAD --; then
        echo -e "${BLUE}→ $repo${NC}"
        git add -A
        git commit -m "$MSG" -q
        git push -q
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC}"
            ((SUCCESS++))
        else
            echo "  ✗"
            ((FAILED++))
        fi
    fi
done

echo ""
echo "Completado: $SUCCESS exitosos, $FAILED fallidos"
