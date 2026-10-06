#!/usr/bin/env bash
# tests/run.sh — corre las pruebas de scripts_for_linux con pytest, con la carpeta temporal en disco y sin caché.
# Uso: tests/run.sh [opciones de pytest]   (p. ej. -k audio_converter)
# La carpeta temporal va a ~/.cache (no a /tmp, que es RAM); pytest no deja .pytest_cache en el repo.
set -euo pipefail

DIR_PRUEBAS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_TMP="${XDG_CACHE_HOME:-$HOME/.cache}/pytest/linux-ola4"
mkdir -p "$BASE_TMP"

export PYTHONDONTWRITEBYTECODE=1
exec python3 -m pytest "$DIR_PRUEBAS" --basetemp "$BASE_TMP" -p no:cacheprovider -q "$@"
