#!/usr/bin/env bash
# =============================================================================
# install.sh — Instalador de git-sync
# =============================================================================
# Copia los scripts a un directorio de instalación, ajusta repos-config.yml,
# detecta repos existentes y opcionalmente agrega aliases al shell.
#
# BUG CORREGIDO:
#   Bug 5 - El original usaba 'sed -i.bak' que en macOS (BSD sed) requiere
#   que el argumento de extensión sea parte del flag (-i '' en vez de -i.bak).
#   Ahora se usa una función portable que detecta el SO y usa la sintaxis
#   correcta para cada variante de sed.
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

_ok()   { echo -e "${GREEN}✓${NC}  $*"; }
_warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
_err()  { echo -e "${RED}✗${NC}  $*"; }
_info() { echo -e "${BLUE}▶${NC}  $*"; }

echo -e "${BLUE}${BOLD}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║            Instalador de git-sync v2.0                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

ask() {
    local prompt="$1" default="$2" response
    read -r -p "$(echo -e "${YELLOW}${prompt}${NC}") [${default}]: " response
    echo "${response:-$default}"
}

detect_shell() {
    [[ -n "${ZSH_VERSION:-}" ]] && echo "zsh" || echo "bash"
}

# BUG 5 CORREGIDO: sed -i portátil para Linux (GNU) y macOS (BSD)
sed_inplace() {
    local expression="$1" file="$2"
    if sed --version 2>/dev/null | grep -q GNU; then
        sed -i -E "$expression" "$file"
    else
        # macOS BSD sed: -i requiere argumento de extensión (puede ser vacío)
        sed -i '' -E "$expression" "$file"
    fi
}

# ─── Paso 1: configuración inicial ───────────────────────────────────────────
echo -e "${BLUE}[1/5]${NC} Configuración inicial"
echo ""

INSTALL_DIR="$(ask "¿Dónde instalar los scripts?" "$HOME/bin/git-sync")"
REPOS_DIR="$(ask "¿Dónde están tus repositorios?" "$HOME/Documents")"

# ─── Paso 2: crear directorio ────────────────────────────────────────────────
echo ""
echo -e "${BLUE}[2/5]${NC} Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR"
_ok "Directorio: $INSTALL_DIR"

# ─── Paso 3: copiar archivos ─────────────────────────────────────────────────
echo ""
echo -e "${BLUE}[3/5]${NC} Copiando archivos..."

copy_script() {
    local f="$1" exec="$2"
    if [[ -f "${SCRIPT_DIR}/${f}" ]]; then
        cp "${SCRIPT_DIR}/${f}" "${INSTALL_DIR}/"
        [[ "$exec" == "true" ]] && chmod +x "${INSTALL_DIR}/${f}"
        _ok "$f copiado"
    else
        _err "$f no encontrado junto al instalador, se omite"
    fi
}

copy_script "sync.sh"   "true"
copy_script "status.sh" "true"
copy_script "README.md" "false"

# Copiar lib/ completo
if [[ -d "${SCRIPT_DIR}/lib" ]]; then
    mkdir -p "${INSTALL_DIR}/lib"
    cp "${SCRIPT_DIR}/lib/"*.sh "${INSTALL_DIR}/lib/"
    _ok "lib/ copiada (módulos)"
else
    _err "Directorio lib/ no encontrado: los scripts no funcionarán sin los módulos"
fi

# repos-config.yml: no sobrescribir si ya existe (proteger ediciones manuales)
if [[ -f "${INSTALL_DIR}/repos-config.yml" ]]; then
    _warn "Ya existe repos-config.yml en el destino, no se sobrescribe"
elif [[ -f "${SCRIPT_DIR}/repos-config.yml" ]]; then
    cp "${SCRIPT_DIR}/repos-config.yml" "${INSTALL_DIR}/"
    _ok "repos-config.yml copiado"
else
    _err "repos-config.yml no encontrado"
fi

# ─── Paso 4: configurar base_directory ───────────────────────────────────────
echo ""
echo -e "${BLUE}[4/5]${NC} Configurando directorio base..."

CONFIG_PATH="${INSTALL_DIR}/repos-config.yml"
if [[ -f "$CONFIG_PATH" ]]; then
    sed_inplace "s|^base_directory:.*|base_directory: ${REPOS_DIR}|" "$CONFIG_PATH"
    _ok "base_directory configurado: $REPOS_DIR"

    # Detectar repos existentes y comparar con los del config
    if [[ -d "$REPOS_DIR" ]]; then
        local_repos=()
        for dir in "$REPOS_DIR"/*; do
            [[ -d "${dir}/.git" ]] && local_repos+=("$(basename "$dir")")
        done

        if [[ "${#local_repos[@]}" -gt 0 ]]; then
            _ok "Repositorios Git detectados en $REPOS_DIR: ${#local_repos[@]}"
            for repo in "${local_repos[@]}"; do
                if grep -q "name: ${repo}$" "$CONFIG_PATH" 2>/dev/null; then
                    echo "     - ${repo} (ya está en repos-config.yml)"
                else
                    echo -e "     - ${repo} ${YELLOW}(NO está en repos-config.yml, agrégalo manualmente)${NC}"
                fi
            done
        else
            _warn "No se detectaron repositorios Git en $REPOS_DIR"
        fi
    else
        _warn "El directorio $REPOS_DIR no existe todavía"
    fi
fi

# ─── Paso 5: aliases opcionales ──────────────────────────────────────────────
echo ""
echo -e "${BLUE}[5/5]${NC} Configuración de aliases (opcional)"
echo ""

SHELL_TYPE="$(detect_shell)"
SHELL_RC="$HOME/.${SHELL_TYPE}rc"

if [[ -f "$SHELL_RC" ]]; then
    SETUP_ALIASES="$(ask "¿Agregar aliases a $SHELL_RC?" "s")"

    if [[ "$SETUP_ALIASES" =~ ^[sS]$ ]]; then
        if ! grep -q "# git-sync aliases" "$SHELL_RC" 2>/dev/null; then
            cat >> "$SHELL_RC" << EOF

# git-sync aliases — Edison Achalma
alias gsync='${INSTALL_DIR}/sync.sh'
alias gstatus='${INSTALL_DIR}/status.sh'
gsyncm() {
    "${INSTALL_DIR}/sync.sh" -m "\$1"
}
EOF
            _ok "Aliases agregados a $SHELL_RC"
            _warn "Ejecuta: source $SHELL_RC"
        else
            _warn "Los aliases ya existen en $SHELL_RC"
        fi
    fi
fi

# ─── Resumen ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║              ¡Instalación completada!                   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${BLUE}Ubicación:${NC} $INSTALL_DIR"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo "  1. Revisa $INSTALL_DIR/repos-config.yml y ajusta los repos"
echo "  2. Prueba:      $INSTALL_DIR/status.sh"
echo "  3. Verifica:    $INSTALL_DIR/sync.sh --check"
echo "  4. Sincroniza:  $INSTALL_DIR/sync.sh -m \"tu mensaje\""
[[ -f "$SHELL_RC" ]] && echo "  5. Si agregaste aliases: source $SHELL_RC"
echo ""
echo "Documentación: $INSTALL_DIR/README.md"
echo ""
