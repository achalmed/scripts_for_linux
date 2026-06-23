#!/usr/bin/env bash
# =============================================================================
#  config.sh — Configuración centralizada de backup-suite
# =============================================================================
#
#  Todas las variables de entorno, perfiles y opciones rsync viven aquí.
#  Edita este archivo para personalizar el comportamiento del script
#  sin tocar la lógica de ningún módulo.
#
#  PERFILES DISPONIBLES:
#    home     — Respalda carpetas de usuario (comportamiento original)
#    docs     — Solo Documents (backup rápido de trabajo activo)
#    full     — Todo el home excepto exclusiones globales
#    custom   — Origen/destino libres vía --src / --dest
# =============================================================================

# ── Usuario del sistema ──────────────────────────────────────────────────────
# Se detecta automáticamente; solo cámbialo si ejecutas el script en nombre
# de otro usuario (caso inusual).
USUARIO="${SUDO_USER:-${USER:-achalmaedison}}"
HOME_DIR="/home/${USUARIO}"

# ── Disco externo ────────────────────────────────────────────────────────────
# Kubuntu monta en /media/<usuario>/<label>
# Arch/Archcraft monta en /run/media/<usuario>/<label>
# La función detect_mount_point() en validator.sh resuelve cuál aplica.
DISK_LABEL="ARCHDISK"
DESTINO_BASE_NAME="backup_${USUARIO}"

# ── Archivo de log ───────────────────────────────────────────────────────────
LOG_FILE="${HOME_DIR}/backup_suite.log"
LOG_MAX_BYTES=10485760   # 10 MB — rota automáticamente si supera este límite

# ── Opciones rsync base ──────────────────────────────────────────────────────
# -a  : archive (recursivo + permisos + timestamps + links + dispositivos)
# -h  : tamaños legibles para humanos
# -c  : checksum real (no solo fecha/tamaño) — más lento, más preciso
# --human-readable : estadísticas en MB/GB
RSYNC_BASE_OPTS="-ahc --human-readable --stats"

# ── Opciones rsync extra (matching grsync avanzado) ──────────────────────────
# Estas flags replican exactamente tu configuración de grsync.
# Están separadas para que puedas activarlas/desactivarlas sin romper la base.
RSYNC_EXTRA_OPTS=(
    "--itemize-changes"      # muestra lista detallada de cambios (grsync: show itemized changes)
    "--copy-links"           # copia symlinks como archivos reales si el destino no los soporta
    "--hard-links"           # preserva hardlinks (grsync: copy hardlinks as hardlinks)
    "--protect-args"         # protege argumentos de interpretación remota (grsync: protect remote args)
)

# ── Opciones NO activadas por defecto (disponibles vía --compress) ────────────
# "--compress"             # comprime en tránsito — útil solo para red, no para disco local
# "--backup"               # guarda versiones previas de archivos modificados

# ─────────────────────────────────────────────────────────────────────────────
# PERFILES DE BACKUP
# Cada perfil define: CARPETAS_BACKUP y CARPETAS_EXCLUIR
# Se selecciona con --profile <nombre> o --profile list
# ─────────────────────────────────────────────────────────────────────────────

# ── Perfil: home (DEFAULT) ───────────────────────────────────────────────────
# Replica exactamente el comportamiento original del script.
# Incluye las carpetas de usuario más importantes.
PROFILE_HOME_FOLDERS=(
    "Desktop"
    "Documents"
    "Downloads"
    "Music"
    "Pictures"
    "Public"
    "Reading_Goal"
    "Templates"
    "Videos"
    "dotfiles"
    "gretl"
    "R"
    "sources"
    "Zotero"
)

# ── Perfil: docs ─────────────────────────────────────────────────────────────
# Solo Documents — backup rápido para trabajo activo diario.
PROFILE_DOCS_FOLDERS=(
    "Documents"
)

# ── Perfil: full ─────────────────────────────────────────────────────────────
# Respalda TODO el home excepto las exclusiones globales de abajo.
# Se expande dinámicamente listando $HOME_DIR al momento de ejecutar.
PROFILE_FULL_FOLDERS=("__DYNAMIC__")   # marcador: se llena en runtime

# ── Exclusiones globales (aplican a TODOS los perfiles) ──────────────────────
# Agrega aquí carpetas pesadas, temporales o regenerables que nunca
# quieres en el backup independientemente del perfil usado.
GLOBAL_EXCLUDE=(
    "miniconda3"    # ~3GB+, reproducible con: conda env export
    "paru"          # caché AUR, regenerable con: paru -Sc
    "pyRenamer"     # aplicación del sistema, no datos de usuario
    ".cache"        # cachés del sistema operativo
    ".local/share/Trash"  # papelera
    "snap"          # paquetes snap, regenerables
    ".npm"          # caché npm
    "__pycache__"   # cachés Python
    "node_modules"  # dependencias JS, regenerables con npm install
)

# ── Exclusiones por patrón (rsync --exclude) ─────────────────────────────────
# Patrones de archivos que rsync ignorará en cualquier carpeta.
RSYNC_PATTERN_EXCLUDE=(
    "*.tmp"
    "*.swp"
    "*.pyc"
    ".DS_Store"
    "Thumbs.db"
    "*.part"      # descargas incompletas
)

# ─────────────────────────────────────────────────────────────────────────────
# VALORES POR DEFECTO GLOBALES (sobreescribibles por flags CLI)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_PROFILE="home"
DEFAULT_VERBOSE=false
DEFAULT_SIMULATE=false
DEFAULT_LOG=false
DEFAULT_FORCE=false
DEFAULT_DELETE_ALL=false
DEFAULT_COMPRESS=false
DEFAULT_NO_CHECKSUM=false   # --fast: usa fecha/tamaño en vez de checksum
MIN_FREE_BYTES=1073741824   # 1 GB mínimo libre en disco externo
