#!/bin/bash
#
# sync.sh — Sincronización de múltiples repositorios Git en uno solo.
#
# Reemplaza el antiguo trío sync-repos.sh / sync-repos.py / quick-sync.sh
# por un único script bash, sin dependencias externas (sin Python, sin PyYAML).
#
# Lee la lista de repos desde repos-config.yml (mismo directorio que este script,
# salvo que se indique otro archivo con --config).
#
# Autor: Edison Achalma (achalmed)

set -uo pipefail

# ---------- Ubicación de este script (para encontrar repos-config.yml junto a él) ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/repos-config.yml"

# ---------- Colores ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------- Valores por defecto ----------
COMMIT_MSG=""
SELECTED_REPOS=""
CHECK_ONLY=false
VERBOSE=false
NO_PULL=false

show_help() {
cat << EOF
Uso: $(basename "$0") [OPCIONES]

Sincroniza (git pull + add + commit + push) todos los repositorios
definidos en repos-config.yml, o un subconjunto de ellos.

Opciones:
  -m, --message "texto"      Mensaje de commit. Si no se indica, se usa
                              default_commit_message del archivo de config.
  -r, --repos "a,b,c"        Sincronizar solo estos repos (nombres separados
                              por coma). Si no se indica, se procesan todos
                              los repos con enabled: true.
  -c, --check                Solo mostrar qué cambió, sin hacer commit ni push.
  -v, --verbose               Modo detallado (muestra git status, salida de pull/push).
  -n, --no-pull               No hacer 'git pull' antes de sincronizar.
      --config RUTA           Usar un archivo de configuración distinto a
                               repos-config.yml (por defecto, el que está
                               junto a este script).
  -h, --help                  Mostrar esta ayuda.

Ejemplos:
  $(basename "$0")
      Sincroniza todos los repos habilitados con el mensaje por defecto.

  $(basename "$0") -m "feat: nuevo artículo sobre inflación"
      Sincroniza todos, con mensaje personalizado.

  $(basename "$0") -r "axiomata,chaska" -m "docs: actualizar índices"
      Sincroniza solo esos dos repos.

  $(basename "$0") -c
      Solo revisa qué repos tienen cambios pendientes, sin tocar nada.

  $(basename "$0") -v -m "chore: actualizar scripts"
      Sincroniza todos en modo verbose (muestra detalle de cada paso).
EOF
}

# ---------- Parseo de argumentos ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--message)   COMMIT_MSG="$2"; shift 2 ;;
        -r|--repos)     SELECTED_REPOS="$2"; shift 2 ;;
        -c|--check)     CHECK_ONLY=true; shift ;;
        -v|--verbose)   VERBOSE=true; shift ;;
        -n|--no-pull)   NO_PULL=true; shift ;;
        --config)       CONFIG_FILE="$2"; shift 2 ;;
        -h|--help)      show_help; exit 0 ;;
        *) print_error "Opción desconocida: $1"; show_help; exit 1 ;;
    esac
done

# ---------- Validar config ----------
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "No se encontró el archivo de configuración: $CONFIG_FILE"
    print_info  "Crea uno junto a este script, o indica la ruta con --config"
    exit 1
fi

# ---------- Parser YAML ligero ----------
# Diseñado específicamente para la estructura de repos-config.yml:
#   base_directory: ...
#   repositories:
#     - name: ...
#       branch: ...
#       enabled: true|false
#   default_commit_message: "..."
# No es un parser YAML genérico; si cambias la estructura del archivo,
# revisa estas funciones.

yaml_base_directory() {
    grep -E '^base_directory:' "$CONFIG_FILE" | sed -E 's/^base_directory:[[:space:]]*//' | sed -E 's/[[:space:]]*$//'
}

yaml_default_message() {
    grep -E '^default_commit_message:' "$CONFIG_FILE" \
        | sed -E 's/^default_commit_message:[[:space:]]*"?//' \
        | sed -E 's/"?[[:space:]]*$//'
}

# Imprime una línea "name|branch|enabled" por cada repo
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
BASE_DIR="${BASE_DIR/#\~/$HOME}"   # expandir ~ manualmente, sin depender de eval

if [ -z "$BASE_DIR" ]; then
    print_error "base_directory no está definido en $CONFIG_FILE"
    exit 1
fi

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="$(yaml_default_message)"
    [ -z "$COMMIT_MSG" ] && COMMIT_MSG="update: sincronización automática de contenidos"
fi

# ---------- Filtrar repos a procesar ----------
mapfile -t ALL_REPO_LINES < <(yaml_repos)

if [ "${#ALL_REPO_LINES[@]}" -eq 0 ]; then
    print_error "No se encontró ningún repositorio en $CONFIG_FILE"
    exit 1
fi

declare -a TARGET_REPOS  # cada elemento: "name|branch"

if [ -n "$SELECTED_REPOS" ]; then
    IFS=',' read -ra WANTED <<< "$SELECTED_REPOS"
    for w in "${WANTED[@]}"; do
        w="$(echo "$w" | xargs)"
        found=false
        for line in "${ALL_REPO_LINES[@]}"; do
            name="${line%%|*}"
            rest="${line#*|}"
            branch="${rest%%|*}"
            if [ "$name" = "$w" ]; then
                TARGET_REPOS+=("${name}|${branch}")
                found=true
                break
            fi
        done
        [ "$found" = false ] && print_warning "Repo '$w' no está en $CONFIG_FILE, se omite"
    done
else
    for line in "${ALL_REPO_LINES[@]}"; do
        name="${line%%|*}"
        rest="${line#*|}"
        branch="${rest%%|*}"
        enabled="${rest##*|}"
        if [ "$enabled" = "true" ]; then
            TARGET_REPOS+=("${name}|${branch}")
        fi
    done
fi

if [ "${#TARGET_REPOS[@]}" -eq 0 ]; then
    print_error "No hay repositorios para procesar (revisa -r o los 'enabled: true' en el config)"
    exit 1
fi

# ---------- Procesar un repo ----------
process_repo() {
    local name="$1"
    local branch="$2"
    local repo_path="${BASE_DIR}/${name}"

    echo ""
    echo "=========================================="
    print_info "Procesando: ${YELLOW}${name}${NC}"
    echo "=========================================="

    if [ ! -d "$repo_path" ]; then
        print_error "Directorio no encontrado: $repo_path"
        return 2
    fi

    if [ ! -d "${repo_path}/.git" ]; then
        print_error "No es un repositorio Git: $repo_path"
        return 2
    fi

    pushd "$repo_path" > /dev/null || return 2

    local current_branch
    current_branch="$(git branch --show-current 2>/dev/null)"
    if [ "$current_branch" != "$branch" ]; then
        print_warning "Rama actual: '${current_branch}', esperada: '${branch}' (continúo en la actual)"
    fi

    if [ "$NO_PULL" = false ] && [ "$CHECK_ONLY" = false ]; then
        print_info "Actualizando desde remoto (git pull)..."
        local pull_err
        pull_err="$(mktemp)"
        if [ "$VERBOSE" = true ]; then
            if ! git pull 2>"$pull_err"; then
                cat "$pull_err" >&2
                print_error "git pull falló en ${name}. Resuélvelo manualmente (puede haber ramas divergentes) y vuelve a intentar."
                rm -f "$pull_err"
                popd > /dev/null || true
                return 2
            fi
        else
            if ! git pull -q 2>"$pull_err"; then
                print_error "git pull falló en ${name}: $(cat "$pull_err" | head -3 | tr '\n' ' ')"
                print_info "Sugerencia: entra al repo y ejecuta 'git pull' manualmente para ver el detalle y resolverlo."
                rm -f "$pull_err"
                popd > /dev/null || true
                return 2
            fi
        fi
        rm -f "$pull_err"
    fi

    if git diff-index --quiet HEAD -- 2>/dev/null; then
        print_warning "Sin cambios en ${name}"
        popd > /dev/null || true
        return 1
    fi

    print_info "Cambios detectados en ${name}"
    [ "$VERBOSE" = true ] && git status --short

    if [ "$CHECK_ONLY" = true ]; then
        git status --short
        popd > /dev/null || true
        return 1
    fi

    print_info "Agregando cambios..."
    if ! git add -A; then
        print_error "Falló 'git add' en ${name}"
        popd > /dev/null || true
        return 2
    fi

    print_info "Creando commit: '${COMMIT_MSG}'"
    if ! git commit -m "$COMMIT_MSG" -q; then
        print_error "Falló 'git commit' en ${name}"
        popd > /dev/null || true
        return 2
    fi

    print_info "Enviando cambios (git push)..."
    if [ "$VERBOSE" = true ]; then
        git push
        push_status=$?
    else
        git push -q
        push_status=$?
    fi

    popd > /dev/null || true

    if [ "$push_status" -eq 0 ]; then
        print_success "${name} sincronizado correctamente"
        return 0
    else
        print_error "Falló 'git push' en ${name}"
        return 2
    fi
}

# ---------- Encabezado ----------
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        SINCRONIZACIÓN DE REPOSITORIOS GIT                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_info "Directorio base: $BASE_DIR"
print_info "Repositorios a procesar: ${#TARGET_REPOS[@]}"
[ "$CHECK_ONLY" = true ] && print_warning "Modo verificación (no se hará commit ni push)"
[ "$NO_PULL" = true ] && print_info "Pull deshabilitado (--no-pull)"
[ "$CHECK_ONLY" = false ] && print_info "Mensaje de commit: $COMMIT_MSG"

SUCCESS_COUNT=0
NO_CHANGES_COUNT=0
ERROR_COUNT=0

for entry in "${TARGET_REPOS[@]}"; do
    name="${entry%%|*}"
    branch="${entry##*|}"

    process_repo "$name" "$branch"
    result=$?

    case $result in
        0) ((SUCCESS_COUNT++)) ;;
        1) ((NO_CHANGES_COUNT++)) ;;
        2) ((ERROR_COUNT++)) ;;
    esac
done

echo ""
echo "=========================================="
echo "          RESUMEN DE SINCRONIZACIÓN"
echo "=========================================="
print_success "Sincronizados: $SUCCESS_COUNT"
print_warning "Sin cambios: $NO_CHANGES_COUNT"
print_error   "Errores: $ERROR_COUNT"
echo "=========================================="
echo ""

[ "$ERROR_COUNT" -gt 0 ] && exit 1
exit 0
