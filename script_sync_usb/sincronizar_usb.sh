#!/usr/bin/env bash
# script_sync_usb/sincronizar_usb.sh — lanzador de main.py (Linux y Mac); reenvía los argumentos
# Reenvía todos los argumentos al script de Python.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/main.py" "$@"
