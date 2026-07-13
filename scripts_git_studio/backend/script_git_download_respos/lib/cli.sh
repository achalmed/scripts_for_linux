#!/usr/bin/env bash
# =============================================================================
# lib/cli.sh — Parseo de argumentos
# =============================================================================
# Mantiene las mismas flags getopts de la v1.x (-u -o -d -p -m -r -x -b
# -t -F -s -h) y añade -n (dry-run). -h ahora sale con 0; los errores
# de uso salen con 2.
#
# Author : Edison Achalma (@achalmed)
# Version: 2.0.0
# =============================================================================

# parse_arguments()
# Rellena las variables globales OPT_* a partir de "$@".
parse_arguments() {
    OPT_GH_USER=""
    OPT_DEST_DIR="${DEFAULT_DEST_DIR}"
    OPT_DEPTH="${DEFAULT_DEPTH}"
    OPT_PROTOCOL="${DEFAULT_PROTOCOL}"
    OPT_MODE="${DEFAULT_MODE}"
    OPT_REPO_LIST=""
    OPT_EXCLUDE_LIST=""
    OPT_BRANCH=""
    OPT_STRIP_GIT="false"
    OPT_INCLUDE_FORKS="false"
    OPT_DRY_RUN="false"
    OPT_GH_TOKEN="${GITHUB_TOKEN:-}"
    OPT_VERBOSE="false"
    OPT_NO_COLOR="false"

    local opt
    while getopts ":u:o:d:p:m:r:x:b:t:Fsnvh" opt; do
        case "${opt}" in
            u) OPT_GH_USER="${OPTARG}" ;;
            o) OPT_DEST_DIR="${OPTARG}" ;;
            d) OPT_DEPTH="${OPTARG}" ;;
            p) OPT_PROTOCOL="${OPTARG}" ;;
            m) OPT_MODE="${OPTARG}" ;;
            r) OPT_REPO_LIST="${OPTARG}" ;;
            x) OPT_EXCLUDE_LIST="${OPTARG}" ;;
            b) OPT_BRANCH="${OPTARG}" ;;
            t) OPT_GH_TOKEN="${OPTARG}" ;;
            F) OPT_INCLUDE_FORKS="true" ;;
            s) OPT_STRIP_GIT="true" ;;
            n) OPT_DRY_RUN="true" ;;
            v) OPT_VERBOSE="true" ;;
            h) show_help; exit 0 ;;
            :)
                printf 'La opción -%s requiere un valor\n' "${OPTARG}" >&2
                exit 2
                ;;
            *)
                printf 'Opción desconocida: -%s\n' "${OPTARG}" >&2
                show_help >&2
                exit 2
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Uso: $(basename "$0") -u USUARIO [opciones]

Descarga repos de GitHub con control de profundidad de commits.

Opciones obligatorias:
  -u USUARIO         Usuario u organización de GitHub (ej: achalmed)

Modo de selección de repos:
  -m all             Descargar TODOS los repos públicos (por defecto)
  -m list -r "a,b"   Descargar solo los repos listados (separados por coma)
  -m single -r "a"   Descargar un único repo

Control de profundidad:
  -d N               1 = solo último commit (default) | N = últimos N
                     full (o 0) = historial completo
  -b RAMA            Clonar solo una rama específica

Otras opciones:
  -o DIRECTORIO      Carpeta destino (default: ./)
  -p ssh|https       Protocolo de clonado (default: ssh)
  -x "repo1,repo2"   Excluir estos repos al usar -m all
  -F                 Incluir forks al usar -m all (por defecto se omiten)
  -s                 Eliminar .git tras clonar (snapshot sin historial)
  -t TOKEN           Token de GitHub (o variable GITHUB_TOKEN)
  -n                 Dry-run: mostrar qué se clonaría, sin clonar
  -v                 Modo detallado
  -h                 Mostrar esta ayuda

Ejemplos:
  # Todos los repos, solo último commit, vía SSH
  $(basename "$0") -u achalmed -d 1

  # Todos, últimos 5 commits, en carpeta específica
  $(basename "$0") -u achalmed -d 5 -o ~/Documents/github-backup

  # Solo repos puntuales
  $(basename "$0") -u achalmed -m list -r "chaska,website-achalma" -d 1

  # Un repo, snapshot sin .git
  $(basename "$0") -u achalmed -m single -r "scripts_for_zotero" -s

  # Simular la descarga de todos excluyendo algunos
  $(basename "$0") -u achalmed -n -x "Python,CampusTeX-Research"
EOF
}
