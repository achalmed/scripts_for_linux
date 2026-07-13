#!/usr/bin/env bash
# =============================================================================
# sync.sh — Sincronización de múltiples repositorios Git
# =============================================================================
# Reemplaza el antiguo trío sync-repos.sh / sync-repos.py / quick-sync.sh
# por un único script modular sin dependencias externas.
#
# Lee la lista de repos desde repos-config.yml (mismo directorio que este
# script, salvo que se indique otro con --config).
#
# Uso: ./sync.sh [OPCIONES]
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
# shellcheck source=lib/sync_engine.sh
source "${SCRIPT_DIR}/lib/sync_engine.sh"

# ---------- Valores por defecto ----------
CONFIG_FILE="${SCRIPT_DIR}/repos-config.yml"
COMMIT_MSG=""
SELECTED_REPOS=""
CHECK_ONLY=false
VERBOSE=false
NO_PULL=false

# Exportar para que sync_engine.sh los vea
export CHECK_ONLY VERBOSE NO_PULL

# ---------- Ayuda ----------
show_help() {
cat << EOF
Uso: $(basename "$0") [OPCIONES]

Sincroniza (git pull → add → commit → push) todos los repositorios
definidos en repos-config.yml, o un subconjunto de ellos.

Opciones:
  -m, --message "texto"   Mensaje de commit. Si no se indica, se usa
                           default_commit_message del archivo de config.
  -r, --repos "a,b,c"     Sincronizar solo estos repos (nombres separados
                           por coma). Si no se indica, se procesan todos
                           los repos con enabled: true.
  -c, --check              Solo mostrar qué cambió, sin hacer commit ni push.
                           También detecta commits remotos pendientes de pull
                           (hace fetch primero).
  -v, --verbose            Modo detallado (muestra git status, salida de
                           pull/push en tiempo real).
  -n, --no-pull            No hacer 'git pull' antes de sincronizar.
      --config RUTA        Usar un archivo de configuración distinto.
  -h, --help               Mostrar esta ayuda.

Ejemplos:
  $(basename "$0")
      Sincroniza todos los repos habilitados con el mensaje por defecto.

  $(basename "$0") -m "feat: nuevo artículo sobre inflación"
      Sincroniza todos los repos con mensaje personalizado.

  $(basename "$0") -r "pub_axiomata,pub_chaska" -m "docs: actualizar índices"
      Sincroniza solo esos dos repos.

  $(basename "$0") -c
      Solo revisa qué repos tienen cambios (locales y remotos), sin tocar nada.

  $(basename "$0") -v -m "chore: actualizar scripts"
      Sincroniza en modo verbose, viendo la salida de cada comando git.

  $(basename "$0") -n -m "docs: cambio rápido"
      Sincroniza sin hacer pull primero (útil si sabes que el remoto no cambió).
EOF
}

# ---------- Parseo de argumentos ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--message)  COMMIT_MSG="$2";       shift 2 ;;
        -r|--repos)    SELECTED_REPOS="$2";   shift 2 ;;
        -c|--check)    CHECK_ONLY=true;        shift ;;
        -v|--verbose)  VERBOSE=true;           shift ;;
        -n|--no-pull)  NO_PULL=true;           shift ;;
        --config)      CONFIG_FILE="$2";       shift 2 ;;
        -h|--help)     show_help; exit 0 ;;
        *) log_error "Opción desconocida: $1"; show_help; exit 1 ;;
    esac
done

# ---------- Cargar configuración ----------
config_load "$CONFIG_FILE" || exit 1

# Resolver mensaje de commit
if [[ -z "$COMMIT_MSG" ]]; then
    COMMIT_MSG="$DEFAULT_COMMIT_MSG"
fi
export COMMIT_MSG BASE_DIR

# ---------- Filtrar repos a procesar ----------
declare -a TARGET_REPOS
mapfile -t TARGET_REPOS < <(config_get_enabled_repos "$SELECTED_REPOS")

# Advertir sobre repos pedidos con -r que no existan en el config
if [[ -n "$SELECTED_REPOS" ]]; then
    IFS=',' read -ra wanted_arr <<< "$SELECTED_REPOS"
    for w in "${wanted_arr[@]}"; do
        w="$(echo "$w" | xargs)"
        found=false
        for line in "${ALL_REPO_LINES[@]}"; do
            [[ "${line%%|*}" == "$w" ]] && { found=true; break; }
        done
        $found || log_warn "Repo '$w' no está en $CONFIG_FILE, se omite"
    done
fi

if [[ "${#TARGET_REPOS[@]}" -eq 0 ]]; then
    log_error "No hay repositorios para procesar"
    log_info  "Revisa -r o los 'enabled: true' en $CONFIG_FILE"
    exit 1
fi

# ---------- Encabezado ----------
log_header "SINCRONIZACIÓN DE REPOSITORIOS GIT"
log_info "Directorio base: $BASE_DIR"
log_info "Repositorios a procesar: ${#TARGET_REPOS[@]}"
[[ "$CHECK_ONLY" == "true" ]] && log_warn "Modo verificación (no se hará commit ni push)"
[[ "$NO_PULL"    == "true" ]] && log_info "Pull deshabilitado (--no-pull)"
[[ "$CHECK_ONLY" == "false" ]] && log_info "Mensaje de commit: $COMMIT_MSG"

# ---------- Procesar repos ----------
SUCCESS_COUNT=0
NO_CHANGES_COUNT=0
ERROR_COUNT=0

for entry in "${TARGET_REPOS[@]}"; do
    name="${entry%%|*}"
    branch="${entry##*|}"

    # BUG 4 CORREGIDO: capturar el resultado SIN dejar que pipefail
    # aborte el script si sync_process_repo retorna != 0.
    # Usamos '|| true' para neutralizar set -e/pipefail en la asignación.
    result=0
    sync_process_repo "$name" "$branch" || result=$?

    case $result in
        0) ((SUCCESS_COUNT++))     ;;
        1) ((NO_CHANGES_COUNT++))  ;;
        *) ((ERROR_COUNT++))       ;;
    esac
done

# ---------- Resumen ----------
log_summary "$SUCCESS_COUNT" "$NO_CHANGES_COUNT" "$ERROR_COUNT" \
    "RESUMEN DE SINCRONIZACIÓN"

[[ "$ERROR_COUNT" -gt 0 ]] && exit 1
exit 0
