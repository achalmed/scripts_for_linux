#!/usr/bin/env bash
# =============================================================================
#  lib/validator.sh — Validación de requisitos y entorno
# =============================================================================
#
#  Centraliza todas las verificaciones previas al backup:
#    - Dependencias del sistema (rsync, pv, colordiff, bc)
#    - Punto de montaje del disco externo (Kubuntu y Arch Linux)
#    - Carpetas de origen
#    - Espacio libre en disco
#    - Permisos del usuario
#
#  Todas las funciones retornan 0 en éxito o llaman a exit con código
#  apropiado en fallo crítico.
# =============================================================================

# ── Variable global: comando diff disponible ──────────────────────────────────
DIFF_CMD=""

# ── detect_mount_point() ──────────────────────────────────────────────────────
# Detecta automáticamente el punto de montaje del disco externo según la
# distribución Linux en uso.
#
# Kubuntu/Ubuntu: /media/<usuario>/<label>
# Arch/Archcraft: /run/media/<usuario>/<label>
#
# Arguments:
#   $1 - Nombre de usuario del sistema
#   $2 - Etiqueta del disco (DISK_LABEL)
#
# Outputs (stdout):
#   Ruta completa al punto de montaje si se detecta
#
# Returns:
#   0 si se encontró, 1 si no está montado
detect_mount_point() {
    local user="$1"
    local label="$2"

    # Kubuntu / Ubuntu / Debian
    local kubuntu_path="/media/${user}/${label}"
    # Arch Linux / Archcraft / Manjaro
    local arch_path="/run/media/${user}/${label}"

    if [ -d "${kubuntu_path}" ]; then
        echo "${kubuntu_path}"
        return 0
    elif [ -d "${arch_path}" ]; then
        echo "${arch_path}"
        return 0
    fi

    # Intentar detectar via lsblk como fallback
    local lsblk_path
    lsblk_path=$(lsblk -o LABEL,MOUNTPOINT 2>/dev/null \
        | awk -v label="${label}" '$1 == label {print $2}' \
        | head -1)

    if [ -n "${lsblk_path}" ] && [ -d "${lsblk_path}" ]; then
        echo "${lsblk_path}"
        return 0
    fi

    return 1
}

# ── validate_not_root() ───────────────────────────────────────────────────────
# Advierte si el script se ejecuta como root.
# Ejecutar como root puede alterar la propiedad (ownership) de archivos
# del usuario, lo que rompería permisos en el home.
#
# Returns:
#   0 siempre (deja la decisión al usuario)
validate_not_root() {
    if [ "$(id -u)" -eq 0 ]; then
        log_warn "Estás ejecutando el script como root."
        log_warn "Ejecutarlo como usuario normal preserva mejor la propiedad de archivos."
        read -rp "  ¿Continuar de todas formas? [s/n]: " resp_root
        resp_root=$(echo "${resp_root}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
        if [[ ! "${resp_root}" =~ ^(s|si|sí|y|yes)$ ]]; then
            log_info "Operación cancelada por el usuario."
            exit 0
        fi
    fi
}

# ── validate_dependencies() ──────────────────────────────────────────────────
# Verifica que las dependencias obligatorias y opcionales estén instaladas.
# Detecta automáticamente el gestor de paquetes (pacman / apt) para mostrar
# el comando de instalación correcto según la distro.
#
# Returns:
#   0 si todas las dependencias obligatorias están presentes
#   exit 5 si falta alguna dependencia obligatoria
validate_dependencies() {
    log_title "Verificando dependencias del sistema..."
    log_separator

    # Detectar gestor de paquetes para mensajes de instalación
    local pkg_manager install_hint
    if command -v pacman &>/dev/null; then
        pkg_manager="pacman"
        install_hint="sudo pacman -S"
    elif command -v apt &>/dev/null; then
        pkg_manager="apt"
        install_hint="sudo apt install"
    else
        pkg_manager="desconocido"
        install_hint="tu gestor de paquetes"
    fi

    log_debug "Gestor de paquetes detectado: ${pkg_manager}"

    local failures=0

    # ── rsync: OBLIGATORIO ────────────────────────────────────────────────────
    if command -v rsync &>/dev/null; then
        local rsync_version
        rsync_version=$(rsync --version 2>/dev/null | head -1 | awk '{print $3}')
        log_ok "rsync encontrado: v${rsync_version}"
    else
        log_error "rsync no encontrado — es obligatorio."
        log_error "Instalar con: ${install_hint} rsync"
        ((failures++))
    fi

    # ── pv: RECOMENDADO (barra de progreso visual) ────────────────────────────
    if command -v pv &>/dev/null; then
        log_ok "pv encontrado (barras de progreso disponibles)"
    else
        log_warn "pv no encontrado — se usará --progress de rsync."
        log_warn "Para instalarlo: ${install_hint} pv"
    fi

    # ── colordiff / diff: OPCIONAL (vista de cambios) ─────────────────────────
    if command -v colordiff &>/dev/null; then
        log_ok "colordiff encontrado (diffs en color)"
        DIFF_CMD="colordiff"
    elif command -v diff &>/dev/null; then
        log_ok "diff encontrado"
        DIFF_CMD="diff"
    else
        log_warn "Ni diff ni colordiff encontrados — no se podrán mostrar diferencias."
    fi

    # ── bc: para cálculos de tamaño ───────────────────────────────────────────
    if ! command -v bc &>/dev/null; then
        log_warn "bc no encontrado — algunos cálculos de tamaño usarán método alternativo."
    fi

    if [ "${failures}" -gt 0 ]; then
        log_error "Faltan dependencias obligatorias. Abortando."
        exit 5
    fi

    echo ""
}

# ── validate_disk() ───────────────────────────────────────────────────────────
# Verifica que el disco externo esté montado, tenga espacio suficiente
# y que el directorio de destino exista (o lo crea).
#
# Arguments:
#   $1 - Ruta al punto de montaje del disco
#   $2 - Ruta al directorio de destino del backup
#   $3 - Modo simulación (true/false)
#   $4 - Bytes mínimos libres requeridos
#
# Returns:
#   0 si todo está correcto
#   exit 1 si el disco no está montado o no hay espacio
validate_disk() {
    local disk_path="$1"
    local dest_base="$2"
    local simulate="${3:-false}"
    local min_free="${4:-1073741824}"

    log_title "Verificando disco externo..."
    log_separator

    if [ ! -d "${disk_path}" ]; then
        log_error "El disco externo NO está montado."
        log_error ""
        log_error "Rutas buscadas:"
        log_error "  Kubuntu/Ubuntu : /media/${USUARIO}/${DISK_LABEL}"
        log_error "  Arch/Archcraft : /run/media/${USUARIO}/${DISK_LABEL}"
        log_error ""
        log_error "Para montar manualmente:"
        log_error "  udisksctl mount -b /dev/sdX1"
        log_error "O revisa los dispositivos con: lsblk"
        exit 1
    fi

    log_ok "Disco detectado en: ${disk_path}"

    # Información de espacio del disco
    local total used free
    total=$(df -h "${disk_path}" | tail -1 | awk '{print $2}')
    used=$(df -h  "${disk_path}" | tail -1 | awk '{print $3}')
    free=$(df -h  "${disk_path}" | tail -1 | awk '{print $4}')
    log_info "  Total: ${total} | Usado: ${used} | Libre: ${free}"

    # Verificar espacio mínimo
    local free_bytes
    free_bytes=$(df --block-size=1 "${disk_path}" | tail -1 | awk '{print $4}')
    if [ "${free_bytes}" -lt "${min_free}" ]; then
        log_warn "¡ATENCIÓN! Menos de 1 GB libre en el disco externo."
        log_warn "El backup podría fallar si los datos a copiar superan el espacio disponible."
    fi

    # Tipo de sistema de archivos (informativo)
    local fs_type
    fs_type=$(df -T "${disk_path}" | tail -1 | awk '{print $2}')
    log_debug "Sistema de archivos del disco: ${fs_type}"
    if [[ "${fs_type}" == "ntfs" || "${fs_type}" == "exfat" ]]; then
        log_warn "El disco usa ${fs_type} — los permisos Unix pueden no preservarse completamente."
        log_warn "Para backup completo de permisos se recomienda ext4."
    fi

    # Crear directorio destino si no existe
    if [ ! -d "${dest_base}" ]; then
        log_info "Creando directorio de backup: ${dest_base}"
        if [ "${simulate}" = false ]; then
            mkdir -p "${dest_base}" || {
                log_error "No se pudo crear el directorio: ${dest_base}"
                exit 1
            }
            log_ok "Directorio creado correctamente."
        else
            log_info "[SIMULACIÓN] Se crearía: ${dest_base}"
        fi
    else
        log_ok "Directorio de backup ya existe: ${dest_base}"
    fi

    echo ""
}

# ── validate_source_folders() ────────────────────────────────────────────────
# Verifica que cada carpeta del perfil exista en el sistema de origen.
# Las carpetas no encontradas se eliminan del array y se reporta al usuario.
# Modifica el array CARPETAS_BACKUP en el scope del llamador.
#
# Arguments:
#   $1 - Ruta base del home del usuario
#   $@ - Lista de carpetas a verificar (modificado in-place via nameref)
#
# Returns:
#   0 siempre (las carpetas inválidas se omiten con advertencia)
validate_source_folders() {
    local home_path="$1"
    shift
    local -n folders_ref="$1"   # nameref: modifica el array del llamador

    log_title "Verificando carpetas de origen..."
    log_separator

    local valid_folders=()
    local invalid_count=0

    for folder in "${folders_ref[@]}"; do
        local path="${home_path}/${folder}"
        if [ -d "${path}" ] || [ -L "${path}" ]; then
            valid_folders+=("${folder}")
            if [ "${LOGGER_VERBOSE}" = true ]; then
                local size
                size=$(du -sh "${path}" 2>/dev/null | cut -f1 || echo "?")
                log_ok "  ✓ ${folder} (${size})"
            else
                log_debug "  ✓ ${folder}"
            fi
        else
            log_warn "  ✗ Carpeta no encontrada (se omitirá): ${path}"
            ((invalid_count++))
        fi
    done

    if [ "${invalid_count}" -gt 0 ]; then
        log_warn "Se omitirán ${invalid_count} carpeta(s) no encontradas."
    fi

    log_ok "Se respaldarán ${#valid_folders[@]} carpeta(s)."
    folders_ref=("${valid_folders[@]}")
    echo ""
}

# ── build_rsync_exclude_args() ────────────────────────────────────────────────
# Construye los argumentos --exclude para rsync a partir de las listas
# GLOBAL_EXCLUDE y RSYNC_PATTERN_EXCLUDE definidas en config.sh.
#
# Outputs (stdout):
#   Cadena con todos los flags --exclude listos para pasar a rsync
build_rsync_exclude_args() {
    local args=()

    for item in "${GLOBAL_EXCLUDE[@]}"; do
        args+=("--exclude=${item}/")
    done

    for pattern in "${RSYNC_PATTERN_EXCLUDE[@]}"; do
        args+=("--exclude=${pattern}")
    done

    echo "${args[@]}"
}
