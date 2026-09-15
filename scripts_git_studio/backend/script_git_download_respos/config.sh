#!/usr/bin/env bash
# =============================================================================
# config.sh — Configuración de git_download_respos
# =============================================================================
# Valores por defecto editables por el usuario. El token puede venir
# de la variable de entorno GITHUB_TOKEN o de la opción -t.
#
# =============================================================================

readonly SCRIPT_NAME="git-download-respos"
readonly SCRIPT_VERSION="2.0.0"

# Carpeta destino por defecto (se crean subcarpetas por repo)
readonly DEFAULT_DEST_DIR="."

# Profundidad de commits: "1" solo el último, N últimos N, "full"/"0" todo
readonly DEFAULT_DEPTH="1"

# Protocolo de clonado: ssh | https
readonly DEFAULT_PROTOCOL="ssh"

# Modo de selección de repos: all | list | single
readonly DEFAULT_MODE="all"

# Repos por página al consultar la API de GitHub (máximo permitido: 100)
readonly GITHUB_API_PER_PAGE=100

# Endpoint base de la API de GitHub
readonly GITHUB_API_URL="https://api.github.com"
