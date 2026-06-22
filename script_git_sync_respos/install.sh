#!/bin/bash
#
# install.sh — Instalador de git-sync (sync.sh + status.sh)
#
# Copia los scripts a un directorio de instalación, detecta tus repos
# existentes para pre-llenar repos-config.yml, y opcionalmente agrega
# alias a tu shell.

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Instalador de git-sync                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Función para preguntar al usuario
ask() {
    local prompt="$1"
    local default="$2"
    local response
    read -r -p "$(echo -e "${YELLOW}${prompt}${NC}") [${default}]: " response
    echo "${response:-$default}"
}

# Función para detectar shell
detect_shell() {
    if [ -n "${ZSH_VERSION:-}" ]; then
        echo "zsh"
    else
        echo "bash"
    fi
}

# ---------- Paso 1: configuración inicial ----------
echo -e "${BLUE}[1/5]${NC} Configuración inicial"
echo ""

INSTALL_DIR="$(ask "¿Dónde instalar los scripts?" "$HOME/bin/git-sync")"
REPOS_DIR="$(ask "¿Dónde están tus repositorios?" "$HOME/Documents/publicaciones")"

# ---------- Paso 2: crear directorio ----------
echo ""
echo -e "${BLUE}[2/5]${NC} Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓${NC} Directorio creado: $INSTALL_DIR"

# ---------- Paso 3: copiar archivos ----------
echo ""
echo -e "${BLUE}[3/5]${NC} Copiando archivos..."

CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"

copy_file() {
    local filename="$1"
    local make_exec="$2"
    if [ -f "$CURRENT_DIR/$filename" ]; then
        cp "$CURRENT_DIR/$filename" "$INSTALL_DIR/"
        [ "$make_exec" = "true" ] && chmod +x "$INSTALL_DIR/$filename"
        echo -e "${GREEN}✓${NC} $filename copiado"
    else
        echo -e "${RED}✗${NC} $filename no encontrado junto al instalador, se omite"
    fi
}

copy_file "sync.sh" "true"
copy_file "status.sh" "true"
copy_file "README.md" "false"

# repos-config.yml: si ya existe uno instalado, no lo sobrescribimos (para no
# perder ediciones manuales previas del usuario)
if [ -f "$INSTALL_DIR/repos-config.yml" ]; then
    echo -e "${YELLOW}⚠${NC}  Ya existe repos-config.yml en el destino, no se sobrescribe"
elif [ -f "$CURRENT_DIR/repos-config.yml" ]; then
    cp "$CURRENT_DIR/repos-config.yml" "$INSTALL_DIR/"
    echo -e "${GREEN}✓${NC} repos-config.yml copiado"
else
    echo -e "${RED}✗${NC} repos-config.yml no encontrado"
fi

# ---------- Paso 4: configurar base_directory en repos-config.yml ----------
echo ""
echo -e "${BLUE}[4/5]${NC} Configurando directorio base..."

CONFIG_PATH="$INSTALL_DIR/repos-config.yml"
if [ -f "$CONFIG_PATH" ]; then
    # Normalizar REPOS_DIR a forma con ~ si corresponde, o ruta absoluta
    sed -i.bak -E "s|^base_directory:.*|base_directory: ${REPOS_DIR}|" "$CONFIG_PATH"
    rm -f "${CONFIG_PATH}.bak"
    echo -e "${GREEN}✓${NC} base_directory configurado: $REPOS_DIR"
fi

# Detectar repos existentes y avisar si hay diferencias con el config
if [ -d "$REPOS_DIR" ]; then
    DETECTED=()
    for dir in "$REPOS_DIR"/*; do
        [ -d "$dir/.git" ] && DETECTED+=("$(basename "$dir")")
    done

    if [ "${#DETECTED[@]}" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Repositorios Git detectados en $REPOS_DIR: ${#DETECTED[@]}"
        for repo in "${DETECTED[@]}"; do
            if grep -q "name: $repo$" "$CONFIG_PATH" 2>/dev/null; then
                echo "    - $repo (ya está en repos-config.yml)"
            else
                echo -e "    - $repo ${YELLOW}(NO está en repos-config.yml, agrégalo manualmente)${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠${NC}  No se detectaron repositorios Git en $REPOS_DIR"
    fi
else
    echo -e "${YELLOW}⚠${NC}  El directorio $REPOS_DIR no existe todavía"
fi

# ---------- Paso 5: aliases opcionales ----------
echo ""
echo -e "${BLUE}[5/5]${NC} Configuración de aliases (opcional)"
echo ""

SHELL_TYPE="$(detect_shell)"
SHELL_RC="$HOME/.${SHELL_TYPE}rc"

if [ -f "$SHELL_RC" ]; then
    SETUP_ALIASES="$(ask "¿Agregar aliases a $SHELL_RC?" "s")"

    if [[ "$SETUP_ALIASES" =~ ^[sS]$ ]]; then
        if ! grep -q "# git-sync aliases" "$SHELL_RC" 2>/dev/null; then
            cat >> "$SHELL_RC" << EOF

# git-sync aliases - Edison Achalma
alias gsync='$INSTALL_DIR/sync.sh'
alias gstatus='$INSTALL_DIR/status.sh'
gsyncm() {
    "$INSTALL_DIR/sync.sh" -m "\$1"
}
EOF
            echo -e "${GREEN}✓${NC} Aliases agregados a $SHELL_RC"
            echo -e "${YELLOW}ℹ${NC}  Ejecuta: source $SHELL_RC"
        else
            echo -e "${YELLOW}⚠${NC}  Los aliases ya existen en $SHELL_RC"
        fi
    fi
fi

# ---------- Resumen ----------
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ¡Instalación completada!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Ubicación:${NC} $INSTALL_DIR"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo "  1. Revisa $INSTALL_DIR/repos-config.yml y ajusta tus repos"
echo "  2. Prueba:  $INSTALL_DIR/status.sh"
echo "  3. Sincroniza: $INSTALL_DIR/sync.sh -c    (modo verificación primero)"
echo "  4. Si agregaste aliases: source $SHELL_RC"
echo ""
echo -e "${BLUE}Uso rápido:${NC}"
echo "  $INSTALL_DIR/status.sh                          # Ver estado de todos los repos"
echo "  $INSTALL_DIR/sync.sh                             # Sincronizar todos"
echo "  $INSTALL_DIR/sync.sh -m \"mensaje\"               # Con mensaje personalizado"
echo "  $INSTALL_DIR/sync.sh -h                          # Ver todas las opciones"
echo ""
echo "Documentación completa en: $INSTALL_DIR/README.md"
echo ""
