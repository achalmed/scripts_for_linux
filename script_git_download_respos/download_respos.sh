#!/usr/bin/env bash
#
# gh-download.sh — Descarga proyectos de GitHub con control de profundidad de commits.
#
# Autor: Edison Achalma (github.com/achalmed)
#
# Casos cubiertos:
#   1) Descargar UN repo con N commits de profundidad (o todo el historial)
#   2) Descargar VARIOS repos específicos (lista separada por comas)
#   3) Descargar TODOS los repos de un usuario/organización de GitHub automáticamente
#   4) Elegir entre clonar con .git (historial git usable) o solo snapshot de archivos
#   5) Elegir protocolo SSH o HTTPS
#   6) Excluir repos por nombre (útil para forks o archivados que no quieres traer)
#
# Requisitos: git, curl, jq
#   Instalar jq si falta:  sudo apt install jq   (Kubuntu/Debian)
#                          sudo pacman -S jq     (Arch)

set -euo pipefail

# ---------- Valores por defecto ----------
GH_USER=""
DEST_DIR="."
DEPTH="1"              # "1" = solo último commit, "0"/"full" = historial completo, N = N commits
PROTOCOL="ssh"          # ssh | https
MODE="all"              # all | list | single
REPO_LIST=""            # repos específicos, separados por coma
EXCLUDE_LIST=""         # repos a excluir, separados por coma
STRIP_GIT="false"       # true = eliminar carpeta .git tras clonar (snapshot puro)
INCLUDE_FORKS="false"   # true = incluir forks al descargar "todos"
BRANCH=""               # rama específica (opcional)
GH_TOKEN="${GITHUB_TOKEN:-}"  # token opcional para repos privados o evitar rate limit

# ---------- Colores para mensajes ----------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ---------- Ayuda ----------
usage() {
cat << EOF
Uso: $0 -u USUARIO [opciones]

Opciones obligatorias:
  -u USUARIO        Usuario u organización de GitHub (ej: achalmed)

Modo de selección de repos (uno de estos):
  -m all            Descargar TODOS los repos públicos del usuario (por defecto)
  -m list -r "a,b,c" Descargar solo los repos listados (separados por coma)
  -m single -r "a"   Descargar un único repo

Control de profundidad:
  -d N               Profundidad de commits a descargar:
                        1        -> solo el último commit (por defecto, más rápido)
                        N        -> los últimos N commits (ej: -d 5)
                        full     -> historial completo (equivale a clone normal)
  -b RAMA            Clonar solo una rama específica (opcional)

Otras opciones:
  -o DIRECTORIO       Carpeta destino donde se crean las subcarpetas de cada repo (por defecto: ./)
  -p ssh|https        Protocolo de clonado (por defecto: ssh)
  -x "repo1,repo2"     Excluir estos repos al usar -m all
  -F                   Incluir forks al usar -m all (por defecto se excluyen)
  -s                   Strip: eliminar carpeta .git al final (solo archivos, sin historial git)
  -t TOKEN             Token de GitHub (opcional; o usa variable de entorno GITHUB_TOKEN)
  -h                   Mostrar esta ayuda

Ejemplos:
  # Descargar todos tus repos, solo el último commit cada uno, vía SSH
  $0 -u achalmed -d 1

  # Descargar todos, últimos 5 commits, en una carpeta específica
  $0 -u achalmed -d 5 -o ~/Documents/github-backup

  # Descargar todo el historial completo de todos los repos
  $0 -u achalmed -d full

  # Descargar solo repos puntuales
  $0 -u achalmed -m list -r "chaska,website-achalma,axiomata" -d 1

  # Descargar un solo repo, snapshot sin .git
  $0 -u achalmed -m single -r "scripts_for_zotero" -d 1 -s

  # Descargar todos excluyendo algunos
  $0 -u achalmed -d 1 -x "Python,CampusTeX-Research"
EOF
exit 1
}

# ---------- Parseo de argumentos ----------
while getopts "u:o:d:p:m:r:x:b:t:Fsh" opt; do
  case "$opt" in
    u) GH_USER="$OPTARG" ;;
    o) DEST_DIR="$OPTARG" ;;
    d) DEPTH="$OPTARG" ;;
    p) PROTOCOL="$OPTARG" ;;
    m) MODE="$OPTARG" ;;
    r) REPO_LIST="$OPTARG" ;;
    x) EXCLUDE_LIST="$OPTARG" ;;
    b) BRANCH="$OPTARG" ;;
    t) GH_TOKEN="$OPTARG" ;;
    F) INCLUDE_FORKS="true" ;;
    s) STRIP_GIT="true" ;;
    h) usage ;;
    *) usage ;;
  esac
done

# ---------- Validaciones ----------
[ -z "$GH_USER" ] && { err "Falta especificar el usuario con -u"; usage; }

for cmd in git curl jq; do
  command -v "$cmd" >/dev/null 2>&1 || { err "Falta el comando '$cmd'. Instálalo antes de continuar."; exit 1; }
done

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

CURL_AUTH=()
if [ -n "$GH_TOKEN" ]; then
  CURL_AUTH=(-H "Authorization: Bearer $GH_TOKEN")
fi

# ---------- Construye flags de git clone según profundidad ----------
build_clone_flags() {
  local flags=()
  if [ "$DEPTH" != "full" ] && [ "$DEPTH" != "0" ]; then
    flags+=(--depth "$DEPTH")
  fi
  if [ -n "$BRANCH" ]; then
    flags+=(--branch "$BRANCH" --single-branch)
  fi
  echo "${flags[@]}"
}

# ---------- Construye la URL de clonado ----------
build_url() {
  local repo="$1"
  if [ "$PROTOCOL" = "ssh" ]; then
    echo "git@github.com:${GH_USER}/${repo}.git"
  else
    echo "https://github.com/${GH_USER}/${repo}.git"
  fi
}

# ---------- Clona un repo individual ----------
clone_repo() {
  local repo="$1"
  local url
  url="$(build_url "$repo")"

  if [ -d "$repo" ]; then
    warn "La carpeta '$repo' ya existe, se omite. (Bórrala o muévela si quieres re-descargarla)"
    return
  fi

  local flags
  read -ra flags <<< "$(build_clone_flags)"

  log "Clonando ${repo} (profundidad: ${DEPTH})..."
  if git clone "${flags[@]}" "$url" "$repo" 2>&1 | sed 's/^/    /'; then
    if [ "$STRIP_GIT" = "true" ]; then
      rm -rf "${repo}/.git"
      ok "${repo} descargado (snapshot sin historial git)"
    else
      ok "${repo} descargado"
    fi
  else
    err "Falló la descarga de ${repo}"
  fi
}

# ---------- Obtiene la lista de todos los repos del usuario vía API ----------
fetch_all_repos() {
  local page=1
  local repos=()
  while :; do
    local response
    response=$(curl -s "${CURL_AUTH[@]}" \
      "https://api.github.com/users/${GH_USER}/repos?per_page=100&page=${page}&type=owner")

    # Si la API devuelve un error (ej. rate limit o usuario no encontrado)
    if echo "$response" | jq -e 'type == "object" and has("message")' >/dev/null 2>&1; then
      err "Error de la API de GitHub: $(echo "$response" | jq -r '.message')"
      exit 1
    fi

    local count
    count=$(echo "$response" | jq 'length')
    [ "$count" -eq 0 ] && break

    while IFS= read -r line; do
      repos+=("$line")
    done < <(echo "$response" | jq -r '.[] | "\(.name)|\(.fork)"')

    page=$((page + 1))
  done

  printf '%s\n' "${repos[@]}"
}

# ---------- Lógica principal ----------
log "Usuario de GitHub: ${GH_USER}"
log "Carpeta destino: $(pwd)"
log "Profundidad de commits: ${DEPTH}"
log "Protocolo: ${PROTOCOL}"
[ "$STRIP_GIT" = "true" ] && log "Modo: snapshot sin .git"
echo ""

case "$MODE" in
  single)
    [ -z "$REPO_LIST" ] && { err "Modo 'single' requiere -r NOMBRE_REPO"; exit 1; }
    clone_repo "$REPO_LIST"
    ;;

  list)
    [ -z "$REPO_LIST" ] && { err "Modo 'list' requiere -r \"repo1,repo2,...\""; exit 1; }
    IFS=',' read -ra REPOS <<< "$REPO_LIST"
    for repo in "${REPOS[@]}"; do
      repo="$(echo "$repo" | xargs)"  # trim espacios
      clone_repo "$repo"
    done
    ;;

  all)
    log "Consultando lista de repos vía API de GitHub..."
    mapfile -t ALL_REPOS < <(fetch_all_repos)

    if [ "${#ALL_REPOS[@]}" -eq 0 ]; then
      err "No se encontraron repos para el usuario '${GH_USER}'."
      exit 1
    fi

    IFS=',' read -ra EXCLUDES <<< "$EXCLUDE_LIST"

    log "Se encontraron ${#ALL_REPOS[@]} repos. Iniciando descarga..."
    echo ""

    for entry in "${ALL_REPOS[@]}"; do
      name="${entry%%|*}"
      is_fork="${entry##*|}"

      # Saltar forks salvo que se pida lo contrario
      if [ "$is_fork" = "true" ] && [ "$INCLUDE_FORKS" = "false" ]; then
        warn "Omitiendo '${name}' (es un fork; usa -F para incluir forks)"
        continue
      fi

      # Saltar excluidos
      skip="false"
      for ex in "${EXCLUDES[@]}"; do
        ex="$(echo "$ex" | xargs)"
        [ "$name" = "$ex" ] && skip="true"
      done
      [ "$skip" = "true" ] && { warn "Omitiendo '${name}' (en lista de exclusión)"; continue; }

      clone_repo "$name"
    done
    ;;

  *)
    err "Modo inválido: '${MODE}'. Usa all, list o single."
    exit 1
    ;;
esac

echo ""
ok "Proceso terminado. Repos en: $(pwd)"