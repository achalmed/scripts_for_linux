#!/usr/bin/env bash
# =============================================================================
# status.sh — Reporte de estado de todos los repositorios Git configurados
# =============================================================================
# Lee la misma lista de repos que sync.sh desde repos-config.yml,
# así que nunca se desincroniza.
#
# Hace git fetch antes de calcular cuántos commits hay por detrás de origin
# (corrección del bug original donde behind siempre era 0 sin fetch previo).
#
# Autor: Edison Achalma (achalmed)
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cargar módulos
# shellcheck source=lib/logging.sh
source "${SCRIPT_DIR}/lib/logging.sh"
# shellcheck source=lib/config.sh
source "${SCRIPT_DIR}/lib/config.sh"
# shellcheck source=lib/git_ops.sh
source "${SCRIPT_DIR}/lib/git_ops.sh"
# shellcheck source=lib/status_reporter.sh
source "${SCRIPT_DIR}/lib/status_reporter.sh"

CONFIG_FILE="${SCRIPT_DIR}/repos-config.yml"
ACTIVITY_DAYS=7

show_help() {
cat << EOF
Uso: $(basename "$0") [OPCIONES]

Muestra el estado de todos los repositorios definidos en repos-config.yml:
cambios sin commit, commits sin push, commits remotos pendientes de pull,
y actividad reciente.

Hace 'git fetch' antes de comparar con origin para que los contadores
de commits remotos sean siempre precisos.

Opciones:
      --config RUTA    Usar un archivo de configuración distinto.
      --days N         Días de actividad a mostrar (default: 7).
  -h, --help           Mostrar esta ayuda.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config) CONFIG_FILE="$2"; shift 2 ;;
        --days)   ACTIVITY_DAYS="$2"; shift 2 ;;
        -h|--help) show_help; exit 0 ;;
        *) log_error "Opción desconocida: $1"; show_help; exit 1 ;;
    esac
done

config_load "$CONFIG_FILE" || exit 1

# Repos habilitados
declare -a REPOS
mapfile -t REPOS < <(config_get_enabled_repos "")

if [[ "${#REPOS[@]}" -eq 0 ]]; then
    log_error "No hay repositorios habilitados en $CONFIG_FILE"
    exit 1
fi

# ---------- Encabezado ----------
clear
log_header "REPORTE DE ESTADO DE REPOSITORIOS GIT"
log_info "Directorio base: $BASE_DIR"
log_info "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
log_info "Repositorios analizados: ${#REPOS[@]}"
echo ""
log_info "Obteniendo estado actualizado (git fetch por repo)..."
echo ""

# ---------- Recolectar datos ----------
declare -a REPO_DATA=()
total=0 clean=0 dirty=0 behind_total=0

for entry in "${REPOS[@]}"; do
    name="${entry%%|*}"
    repo_path="${BASE_DIR}/${name}"

    if [[ ! -d "$repo_path" ]]; then
        log_warn "No encontrado: ${name} (${repo_path})"
        continue
    fi

    row="$(status_collect_repo "$repo_path" "$name")"
    REPO_DATA+=("$row")
    ((total++)) || true

    status_field="$(echo "$row" | cut -d'|' -f3)"
    behind_field="$(echo "$row" | cut -d'|' -f6)"

    if [[ "$status_field" == "$STATUS_CLEAN" ]]; then
        ((clean++)) || true
    else
        ((dirty++)) || true
    fi
    [[ "$behind_field" -gt 0 ]] && ((behind_total++)) || true
done

# ---------- Resumen global ----------
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${_C_BOLD}RESUMEN GLOBAL${_C_NC}"
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "  ${_C_GREEN}Sincronizados:      $clean${_C_NC}"
echo -e "  ${_C_YELLOW}Con cambios:        $dirty${_C_NC}"
echo -e "  ${_C_CYAN}Detrás de origin:   $behind_total${_C_NC}"

# ---------- Tabla de estado ----------
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${_C_BOLD}ESTADO DETALLADO${_C_NC}"
echo "════════════════════════════════════════════════════════════════════════════"

status_print_table "${REPO_DATA[@]}"

# ---------- Repos que necesitan atención ----------
status_print_attention "${REPO_DATA[@]}"

# ---------- Leyenda ----------
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${_C_BOLD}LEYENDA${_C_NC}"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  M:n  Archivos modificados sin commit"
echo "  ↑n   Commits locales sin push"
echo "  ↓n   Commits remotos (necesita pull)"
echo "  ✓    Sincronizado correctamente"

# ---------- Acciones sugeridas ----------
status_print_suggestions "$SCRIPT_DIR" "$dirty" "$behind_total"

# ---------- Actividad reciente ----------
status_print_activity "${REPOS[@]}" "$BASE_DIR" "$ACTIVITY_DAYS"
