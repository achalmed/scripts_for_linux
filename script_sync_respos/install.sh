#!/bin/bash

# Script de instalación automática
# Instala y configura los scripts de sincronización de Git

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Instalador de Scripts de Sincronización Git          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Función para preguntar al usuario
ask() {
    local prompt="$1"
    local default="$2"
    local response
    
    read -p "$(echo -e ${YELLOW}${prompt}${NC}) [${default}]: " response
    echo "${response:-$default}"
}

# Función para detectar shell
detect_shell() {
    if [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    else
        echo "bash"
    fi
}

# Paso 1: Configuración inicial
echo -e "${BLUE}[1/6]${NC} Configuración inicial"
echo ""

INSTALL_DIR=$(ask "¿Dónde instalar los scripts?" "$HOME/bin/git-sync")
REPOS_DIR=$(ask "¿Dónde están tus repositorios?" "$HOME/Projects")

# Paso 2: Crear directorio
echo ""
echo -e "${BLUE}[2/6]${NC} Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓${NC} Directorio creado: $INSTALL_DIR"

# Paso 3: Copiar archivos
echo ""
echo -e "${BLUE}[3/6]${NC} Copiando archivos..."

# Verificar que existan los archivos en el directorio actual
CURRENT_DIR=$(dirname "$0")

if [ -f "$CURRENT_DIR/sync-repos.sh" ]; then
    cp "$CURRENT_DIR/sync-repos.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/sync-repos.sh"
    echo -e "${GREEN}✓${NC} sync-repos.sh copiado"
else
    echo -e "${RED}✗${NC} sync-repos.sh no encontrado"
fi

if [ -f "$CURRENT_DIR/sync-repos.py" ]; then
    cp "$CURRENT_DIR/sync-repos.py" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/sync-repos.py"
    echo -e "${GREEN}✓${NC} sync-repos.py copiado"
else
    echo -e "${RED}✗${NC} sync-repos.py no encontrado"
fi

if [ -f "$CURRENT_DIR/quick-sync.sh" ]; then
    cp "$CURRENT_DIR/quick-sync.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/quick-sync.sh"
    echo -e "${GREEN}✓${NC} quick-sync.sh copiado"
else
    echo -e "${RED}✗${NC} quick-sync.sh no encontrado"
fi

if [ -f "$CURRENT_DIR/repos-config.yml" ]; then
    cp "$CURRENT_DIR/repos-config.yml" "$INSTALL_DIR/"
    echo -e "${GREEN}✓${NC} repos-config.yml copiado"
else
    echo -e "${RED}✗${NC} repos-config.yml no encontrado"
fi

if [ -f "$CURRENT_DIR/README.md" ]; then
    cp "$CURRENT_DIR/README.md" "$INSTALL_DIR/"
    echo -e "${GREEN}✓${NC} README.md copiado"
fi

# Paso 4: Configurar BASE_DIR en los scripts
echo ""
echo -e "${BLUE}[4/6]${NC} Configurando rutas..."

# Actualizar BASE_DIR en sync-repos.sh
if [ -f "$INSTALL_DIR/sync-repos.sh" ]; then
    sed -i.bak "s|BASE_DIR=\"\$HOME/Projects\"|BASE_DIR=\"$REPOS_DIR\"|g" "$INSTALL_DIR/sync-repos.sh"
    rm -f "$INSTALL_DIR/sync-repos.sh.bak"
    echo -e "${GREEN}✓${NC} sync-repos.sh configurado"
fi

# Actualizar BASE_DIR en quick-sync.sh
if [ -f "$INSTALL_DIR/quick-sync.sh" ]; then
    sed -i.bak "s|BASE_DIR=\"\$HOME/Projects\"|BASE_DIR=\"$REPOS_DIR\"|g" "$INSTALL_DIR/quick-sync.sh"
    rm -f "$INSTALL_DIR/quick-sync.sh.bak"
    echo -e "${GREEN}✓${NC} quick-sync.sh configurado"
fi

# Actualizar base_directory en repos-config.yml
if [ -f "$INSTALL_DIR/repos-config.yml" ]; then
    sed -i.bak "s|base_directory: ~/Projects|base_directory: $REPOS_DIR|g" "$INSTALL_DIR/repos-config.yml"
    rm -f "$INSTALL_DIR/repos-config.yml.bak"
    echo -e "${GREEN}✓${NC} repos-config.yml configurado"
fi

# Paso 5: Detectar repositorios automáticamente
echo ""
echo -e "${BLUE}[5/6]${NC} Detectando repositorios..."

if [ -d "$REPOS_DIR" ]; then
    DETECTED_REPOS=()
    for dir in "$REPOS_DIR"/*; do
        if [ -d "$dir/.git" ]; then
            repo_name=$(basename "$dir")
            DETECTED_REPOS+=("$repo_name")
        fi
    done
    
    if [ ${#DETECTED_REPOS[@]} -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Repositorios detectados: ${#DETECTED_REPOS[@]}"
        for repo in "${DETECTED_REPOS[@]}"; do
            echo "  - $repo"
        done
        
        UPDATE_CONFIG=$(ask "¿Actualizar repos-config.yml con estos repositorios?" "s")
        
        if [[ "$UPDATE_CONFIG" =~ ^[sS]$ ]]; then
            # Crear nueva sección de repositorios
            REPOS_SECTION="repositories:"
            for repo in "${DETECTED_REPOS[@]}"; do
                REPOS_SECTION="$REPOS_SECTION
  - name: $repo
    branch: main
    enabled: true"
            done
            
            # Actualizar archivo (esto es simplificado, en producción sería más robusto)
            echo -e "${YELLOW}⚠${NC}  Actualiza manualmente repos-config.yml con tus repositorios"
        fi
    else
        echo -e "${YELLOW}⚠${NC}  No se detectaron repositorios Git en $REPOS_DIR"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Directorio no encontrado: $REPOS_DIR"
fi

# Paso 6: Configurar aliases
echo ""
echo -e "${BLUE}[6/6]${NC} Configuración de aliases (opcional)"
echo ""

SHELL_TYPE=$(detect_shell)
SHELL_RC="$HOME/.${SHELL_TYPE}rc"

if [ -f "$SHELL_RC" ]; then
    SETUP_ALIASES=$(ask "¿Agregar aliases a $SHELL_RC?" "s")
    
    if [[ "$SETUP_ALIASES" =~ ^[sS]$ ]]; then
        # Verificar si los aliases ya existen
        if ! grep -q "# Git Sync Scripts" "$SHELL_RC"; then
            cat >> "$SHELL_RC" << EOF

# Git Sync Scripts - Edison Achalma
alias gsync='$INSTALL_DIR/quick-sync.sh'
alias gsync-check='$INSTALL_DIR/sync-repos.sh -c'
alias gsync-all='$INSTALL_DIR/sync-repos.py -v'
gsyncm() {
    $INSTALL_DIR/quick-sync.sh "\$1"
}

EOF
            echo -e "${GREEN}✓${NC} Aliases agregados a $SHELL_RC"
            echo -e "${YELLOW}ℹ${NC}  Ejecuta: source $SHELL_RC"
        else
            echo -e "${YELLOW}⚠${NC}  Los aliases ya existen en $SHELL_RC"
        fi
    fi
fi

# Paso 7: Instalar dependencias de Python (opcional)
echo ""
INSTALL_PYTHON=$(ask "¿Instalar dependencias de Python (PyYAML)?" "s")

if [[ "$INSTALL_PYTHON" =~ ^[sS]$ ]]; then
    if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
        PIP_CMD=$(command -v pip3 || command -v pip)
        echo "Instalando PyYAML..."
        $PIP_CMD install pyyaml --break-system-packages 2>/dev/null || $PIP_CMD install pyyaml
        echo -e "${GREEN}✓${NC} PyYAML instalado"
    else
        echo -e "${YELLOW}⚠${NC}  pip no encontrado, instala PyYAML manualmente si deseas usar sync-repos.py"
    fi
fi

# Resumen final
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ¡Instalación Completada!                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Ubicación:${NC} $INSTALL_DIR"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo "  1. Edita $INSTALL_DIR/repos-config.yml con tus repositorios"
echo "  2. Prueba: cd $INSTALL_DIR && ./quick-sync.sh"
echo "  3. Si agregaste aliases: source $SHELL_RC"
echo "  4. Lee el README.md para más información"
echo ""
echo -e "${BLUE}Uso rápido:${NC}"
echo "  $INSTALL_DIR/quick-sync.sh                    # Sincronización rápida"
echo "  $INSTALL_DIR/sync-repos.sh -h                 # Ver opciones"
echo "  $INSTALL_DIR/sync-repos.py -v                 # Python con verbose"
echo ""
echo -e "${BLUE}Con aliases (después de source):${NC}"
echo "  gsync                                          # Sincronización rápida"
echo "  gsyncm \"tu mensaje\"                           # Con mensaje"
echo "  gsync-check                                    # Solo verificar"
echo ""
echo "Documentación completa en: $INSTALL_DIR/README.md"
echo ""
