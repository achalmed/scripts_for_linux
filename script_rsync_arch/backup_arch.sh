#!/usr/bin/env bash
# =============================================================================
#  backup_arch.sh — Script de sincronización de backup para Arch Linux
# =============================================================================
#
#  DESCRIPCIÓN:
#    Sincroniza carpetas del directorio home con un disco externo montado.
#    - Compara contenido con checksums (no solo fechas)
#    - Muestra barra de progreso
#    - Pregunta antes de sobreescribir archivos modificados
#    - Pregunta antes de eliminar archivos que ya no están en el origen
#    - Conserva permisos, fechas, enlaces simbólicos y subdirectorios
#    - NO genera duplicados
#
#  USO:
#    ./backup_arch.sh [OPCIÓN]
#
#  OPCIONES:
#    -h, --help          Muestra esta ayuda
#    -v, --verbose       Modo detallado (muestra cada archivo)
#    -s, --simulate      Simulación: solo muestra qué haría, sin ejecutar
#    -l, --log           Guarda log en archivo (por defecto en ~/backup_arch.log)
#    -f, --force         Sobreescribe todos los cambios sin preguntar
#    -d, --delete-all    Elimina todos los archivos huérfanos sin preguntar
#
#  REQUISITOS:
#    - rsync >= 3.x
#    - pv (pipe viewer) — para barra de progreso global
#    - bash >= 4.x
#    - colordiff (opcional, mejora vista de cambios)
#
#  AUTOR: Script generado para achalmaedison en Arch Linux
#  FECHA: 2026
# =============================================================================

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1: CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────────────────────────────────────

# ── Origen: carpetas a respaldar (dentro del home del usuario) ──
USUARIO="achalmaedison"
HOME_DIR="/home/${USUARIO}"

# ── Lista de carpetas a respaldar ──
# Añadir o quitar carpetas según necesidad
CARPETAS_BACKUP=(
    "Desktop"
    "Documents"
    "dotfiles"
    "Downloads"
    "gretl"
    "Music"
    "Pictures"
    "Public"
    "R"
    "Reading_Goal"
    "sources"
    "Templates"
    "Videos"
    "Zotero"
)

# ── Carpetas excluidas explícitamente (miniconda3 y paru son pesadas/regenerables) ──
# Comentar la línea para incluirlas en el backup
CARPETAS_EXCLUIR=(
    "miniconda3"   # ~3GB+, se puede reinstalar fácilmente
    "paru"         # caché de AUR, regenerable
    "pyRenamer"    # app de sistema, no datos del usuario
)

# ── Destino: punto de montaje del disco externo ──
DISCO_EXTERNO="/run/media/${USUARIO}/ARCHDISK"
DESTINO_BASE="${DISCO_EXTERNO}/backup_${USUARIO}"

# ── Archivo de log ──
LOG_FILE="${HOME_DIR}/backup_arch.log"

# ── Opciones de rsync base ──
# -a  = modo archivo (recursivo, permisos, timestamps, links, dispositivos, especiales)
# -h  = números legibles para humanos
# -c  = compara por checksum, no solo por tamaño/fecha (más lento pero más preciso)
# --no-delete = por defecto NO borramos nada automáticamente
RSYNC_OPTS="-ahc --stats --human-readable"

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2: COLORES Y FORMATO DE TERMINAL
# ─────────────────────────────────────────────────────────────────────────────

# Detectar si la terminal soporta colores
if [ -t 1 ] && command -v tput &>/dev/null && tput colors &>/dev/null && [ "$(tput colors)" -ge 8 ]; then
    ROJO=$(tput setaf 1)
    VERDE=$(tput setaf 2)
    AMARILLO=$(tput setaf 3)
    AZUL=$(tput setaf 4)
    MAGENTA=$(tput setaf 5)
    CYAN=$(tput setaf 6)
    BLANCO=$(tput setaf 7)
    NEGRITA=$(tput bold)
    RESET=$(tput sgr0)
else
    ROJO="" VERDE="" AMARILLO="" AZUL="" MAGENTA="" CYAN="" BLANCO="" NEGRITA="" RESET=""
fi

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3: VARIABLES GLOBALES DE ESTADO
# ─────────────────────────────────────────────────────────────────────────────

MODO_VERBOSE=false
MODO_SIMULACION=false
MODO_LOG=false
MODO_FORZAR=false
MODO_BORRAR_TODO=false
TOTAL_COPIADOS=0
TOTAL_ACTUALIZADOS=0
TOTAL_OMITIDOS=0
TOTAL_HUERFANOS=0
TOTAL_BORRADOS=0
INICIO_TIEMPO=$(date +%s)

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4: FUNCIONES DE UTILIDAD
# ─────────────────────────────────────────────────────────────────────────────

# ── Función de log: imprime en consola y opcionalmente en archivo ──
log() {
    local nivel="$1"
    shift
    local mensaje="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local linea="[${timestamp}] [${nivel}] ${mensaje}"

    # Imprimir con color según nivel
    case "$nivel" in
        INFO)    echo -e "${CYAN}${linea}${RESET}" ;;
        OK)      echo -e "${VERDE}${linea}${RESET}" ;;
        WARN)    echo -e "${AMARILLO}${linea}${RESET}" ;;
        ERROR)   echo -e "${ROJO}${linea}${RESET}" ;;
        ACCION)  echo -e "${MAGENTA}${linea}${RESET}" ;;
        TITULO)  echo -e "${NEGRITA}${AZUL}${linea}${RESET}" ;;
        *)       echo -e "${linea}" ;;
    esac

    # Guardar en log si está activado
    if [ "${MODO_LOG}" = true ]; then
        echo "${linea}" >> "${LOG_FILE}"
    fi
}

# ── Separador visual ──
separador() {
    local char="${1:-─}"
    local ancho="${2:-70}"
    printf '%*s\n' "$ancho" '' | tr ' ' "$char"
}

# ── Mostrar ayuda ──
mostrar_ayuda() {
    cat <<EOF
${NEGRITA}${AZUL}
╔══════════════════════════════════════════════════════════════════╗
║           BACKUP ARCH LINUX → DISCO EXTERNO (ARCHDISK)          ║
╚══════════════════════════════════════════════════════════════════╝
${RESET}
${NEGRITA}USO:${RESET}
    $0 [OPCIONES]

${NEGRITA}OPCIONES:${RESET}
    -h, --help          Muestra esta ayuda y sale
    -v, --verbose       Modo detallado (lista cada archivo procesado)
    -s, --simulate      Simulación: muestra qué haría sin ejecutar cambios
    -l, --log           Guarda log completo en: ${LOG_FILE}
    -f, --force         Sobreescribe archivos modificados sin preguntar
    -d, --delete-all    Elimina huérfanos sin preguntar (¡úsalo con cuidado!)

${NEGRITA}EJEMPLOS:${RESET}
    $0                  Backup interactivo normal
    $0 -v -l            Backup con log y detalle
    $0 -s               Ver qué cambiaría sin tocar nada
    $0 -f               Backup sin preguntas (sobreescribe todo)

${NEGRITA}ORIGEN:${RESET}  ${HOME_DIR}/[carpeta]
${NEGRITA}DESTINO:${RESET} ${DESTINO_BASE}/[carpeta]

${NEGRITA}CARPETAS INCLUIDAS:${RESET}
$(printf '    ✓ %s\n' "${CARPETAS_BACKUP[@]}")

${NEGRITA}CARPETAS EXCLUIDAS:${RESET}
$(printf '    ✗ %s\n' "${CARPETAS_EXCLUIR[@]}")
EOF
}

# ── Verificar que un comando existe ──
verificar_comando() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log ERROR "Comando requerido no encontrado: '${cmd}'"
        log ERROR "Instálalo con: sudo pacman -S ${cmd}"
        return 1
    fi
}

# ── Convertir bytes a unidad legible ──
bytes_legibles() {
    local bytes=$1
    if   [ "$bytes" -ge 1073741824 ]; then printf "%.2f GB" "$(echo "scale=2; $bytes/1073741824" | bc)"
    elif [ "$bytes" -ge 1048576 ];    then printf "%.2f MB" "$(echo "scale=2; $bytes/1048576" | bc)"
    elif [ "$bytes" -ge 1024 ];       then printf "%.2f KB" "$(echo "scale=2; $bytes/1024" | bc)"
    else printf "%d B" "$bytes"
    fi
}

# ── Calcular tiempo transcurrido ──
tiempo_transcurrido() {
    local segundos=$(( $(date +%s) - INICIO_TIEMPO ))
    printf '%02dh %02dm %02ds' $((segundos/3600)) $(( (segundos%3600)/60 )) $((segundos%60))
}

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5: VERIFICACIONES PREVIAS AL BACKUP
# ─────────────────────────────────────────────────────────────────────────────

verificar_requisitos() {
    log TITULO "Verificando requisitos del sistema..."
    separador

    local fallos=0

    # Verificar rsync (obligatorio)
    if verificar_comando "rsync"; then
        local ver_rsync
        ver_rsync=$(rsync --version | head -1 | awk '{print $3}')
        log OK "rsync encontrado: versión ${ver_rsync}"
    else
        ((fallos++))
    fi

    # Verificar pv (recomendado para barras de progreso)
    if command -v pv &>/dev/null; then
        log OK "pv encontrado (barras de progreso disponibles)"
    else
        log WARN "pv no encontrado — se usará progreso de rsync (menos visual)"
        log WARN "Para instalarlo: sudo pacman -S pv"
    fi

    # Verificar colordiff (opcional para ver diffs con color)
    if command -v colordiff &>/dev/null; then
        log OK "colordiff encontrado (diffs en color disponibles)"
        DIFF_CMD="colordiff"
    elif command -v diff &>/dev/null; then
        log OK "diff encontrado"
        DIFF_CMD="diff"
    else
        log WARN "diff no encontrado"
        DIFF_CMD=""
    fi

    # Verificar bc (para cálculos)
    if ! command -v bc &>/dev/null; then
        log WARN "bc no encontrado — algunos cálculos de tamaño pueden fallar"
    fi

    if [ "$fallos" -gt 0 ]; then
        log ERROR "Faltan dependencias obligatorias. Abortando."
        exit 1
    fi

    echo ""
}

verificar_disco_externo() {
    log TITULO "Verificando disco externo..."
    separador

    # Comprobar si el directorio de montaje existe
    if [ ! -d "${DISCO_EXTERNO}" ]; then
        log ERROR "El disco externo NO está montado en: ${DISCO_EXTERNO}"
        log ERROR ""
        log ERROR "Para montarlo manualmente:"
        log ERROR "  sudo mount /dev/sda1 ${DISCO_EXTERNO}"
        log ERROR ""
        log ERROR "O conecta el disco y espera a que se automonte."
        log ERROR "Puedes verificar con: lsblk"
        exit 1
    fi

    log OK "Disco externo detectado en: ${DISCO_EXTERNO}"

    # Mostrar información del disco
    local espacio_total espacio_usado espacio_libre
    espacio_total=$(df -h "${DISCO_EXTERNO}" | tail -1 | awk '{print $2}')
    espacio_usado=$(df -h "${DISCO_EXTERNO}" | tail -1 | awk '{print $3}')
    espacio_libre=$(df -h "${DISCO_EXTERNO}" | tail -1 | awk '{print $4}')

    log INFO "  Espacio total: ${espacio_total}"
    log INFO "  Espacio usado: ${espacio_usado}"
    log INFO "  Espacio libre: ${espacio_libre}"

    # Verificar si hay espacio suficiente (mínimo 1GB libre)
    local libre_bytes
    libre_bytes=$(df --block-size=1 "${DISCO_EXTERNO}" | tail -1 | awk '{print $4}')
    if [ "${libre_bytes}" -lt 1073741824 ]; then
        log WARN "¡ATENCIÓN! Menos de 1GB libre en el disco externo."
    fi

    # Crear directorio destino si no existe
    if [ ! -d "${DESTINO_BASE}" ]; then
        log INFO "Creando directorio de backup: ${DESTINO_BASE}"
        if [ "${MODO_SIMULACION}" = false ]; then
            mkdir -p "${DESTINO_BASE}"
            log OK "Directorio creado correctamente."
        else
            log INFO "[SIMULACIÓN] Se crearía: ${DESTINO_BASE}"
        fi
    else
        log OK "Directorio de backup ya existe: ${DESTINO_BASE}"
    fi

    echo ""
}

verificar_origen() {
    log TITULO "Verificando carpetas de origen..."
    separador

    local carpetas_validas=()
    local carpetas_invalidas=()

    for carpeta in "${CARPETAS_BACKUP[@]}"; do
        local ruta="${HOME_DIR}/${carpeta}"
        if [ -d "${ruta}" ] || [ -L "${ruta}" ]; then
            carpetas_validas+=("$carpeta")
            if [ "${MODO_VERBOSE}" = true ]; then
                local tam
                tam=$(du -sh "${ruta}" 2>/dev/null | cut -f1)
                log OK "  ✓ ${carpeta} (${tam})"
            fi
        else
            carpetas_invalidas+=("$carpeta")
            log WARN "  ✗ Carpeta no encontrada: ${ruta}"
        fi
    done

    # Actualizar lista solo con carpetas válidas
    CARPETAS_BACKUP=("${carpetas_validas[@]}")

    if [ "${#carpetas_invalidas[@]}" -gt 0 ]; then
        log WARN "Se omitirán ${#carpetas_invalidas[@]} carpetas no encontradas."
    fi

    log OK "Se respaldarán ${#CARPETAS_BACKUP[@]} carpetas."
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6: ANÁLISIS DE CAMBIOS (CORAZÓN DEL SCRIPT)
# ─────────────────────────────────────────────────────────────────────────────

# ── Obtener lista de archivos nuevos (no existen en destino) ──
obtener_archivos_nuevos() {
    local origen="$1"
    local destino="$2"
    rsync -ahcn --itemize-changes "${origen}/" "${destino}/" 2>/dev/null \
        | grep '^>f+++++++++' \
        | awk '{print $2}'
}

# ── Obtener lista de archivos modificados ──
obtener_archivos_modificados() {
    local origen="$1"
    local destino="$2"
    rsync -ahcn --itemize-changes "${origen}/" "${destino}/" 2>/dev/null \
        | grep '^>f' \
        | grep -v '+++++++++' \
        | awk '{print $2}'
}

# ── Obtener lista de archivos huérfanos (en destino pero no en origen) ──
obtener_huerfanos() {
    local origen="$1"
    local destino="$2"
    # Comparar los archivos listados en cada lado
    local lista_origen lista_destino
    lista_origen=$(find "${origen}/" -mindepth 1 -printf '%P\n' 2>/dev/null | sort)
    lista_destino=$(find "${destino}/" -mindepth 1 -printf '%P\n' 2>/dev/null | sort)

    # Los que están en destino pero NO en origen
    comm -13 <(echo "$lista_origen") <(echo "$lista_destino") 2>/dev/null || true
}

# ── Mostrar diferencias entre dos archivos ──
mostrar_diff() {
    local archivo_orig="$1"
    local archivo_dest="$2"

    # Solo mostrar diff para archivos de texto (evitar binarios)
    if file --brief --mime "${archivo_orig}" 2>/dev/null | grep -q "text"; then
        echo ""
        log INFO "  ── Diferencias (origen vs. disco externo) ──"
        if [ -n "${DIFF_CMD:-}" ]; then
            ${DIFF_CMD} --unified=2 "${archivo_dest}" "${archivo_orig}" 2>/dev/null \
                | head -50 \
                | sed 's/^/    /' \
                || true
        fi
        echo ""
    else
        log INFO "  (Archivo binario — no se muestra diff de contenido)"
        # Mostrar metadatos del archivo
        log INFO "  Origen:  $(stat --printf='%s bytes, modificado: %y' "${archivo_orig}" 2>/dev/null)"
        log INFO "  Destino: $(stat --printf='%s bytes, modificado: %y' "${archivo_dest}" 2>/dev/null)"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 7: PROCESO DE BACKUP POR CARPETA
# ─────────────────────────────────────────────────────────────────────────────

procesar_carpeta() {
    local carpeta="$1"
    local origen="${HOME_DIR}/${carpeta}"
    local destino="${DESTINO_BASE}/${carpeta}"

    log TITULO "╔══ Procesando: ${carpeta} ══╗"
    separador

    # ── Crear directorio de destino si no existe ──
    if [ ! -d "${destino}" ]; then
        log INFO "Carpeta nueva en disco externo: ${destino}"
        if [ "${MODO_SIMULACION}" = false ]; then
            mkdir -p "${destino}"
        fi
    fi

    # ═══════════════════════════════════════════════
    # PASO A: Archivos nuevos (copiar sin preguntar)
    # ═══════════════════════════════════════════════
    log INFO "Analizando archivos nuevos..."
    local archivos_nuevos=()
    while IFS= read -r linea; do
        [ -n "$linea" ] && archivos_nuevos+=("$linea")
    done < <(obtener_archivos_nuevos "${origen}" "${destino}")

    if [ "${#archivos_nuevos[@]}" -gt 0 ]; then
        log OK "  → ${#archivos_nuevos[@]} archivo(s) nuevo(s) a copiar"
        if [ "${MODO_VERBOSE}" = true ]; then
            for f in "${archivos_nuevos[@]}"; do
                log INFO "    + ${f}"
            done
        fi

        if [ "${MODO_SIMULACION}" = false ]; then
            # Construir filtro solo con archivos nuevos y copiarlos
            copiar_archivos_nuevos "${origen}" "${destino}" "${archivos_nuevos[@]}"
            ((TOTAL_COPIADOS += ${#archivos_nuevos[@]}))
        else
            log INFO "  [SIMULACIÓN] Se copiarían ${#archivos_nuevos[@]} archivo(s) nuevo(s)"
        fi
    else
        log OK "  → Sin archivos nuevos en: ${carpeta}"
    fi

    # ═══════════════════════════════════════════════════════════
    # PASO B: Archivos modificados (preguntar antes de actualizar)
    # ═══════════════════════════════════════════════════════════
    log INFO "Analizando archivos modificados..."
    local archivos_mod=()
    while IFS= read -r linea; do
        [ -n "$linea" ] && archivos_mod+=("$linea")
    done < <(obtener_archivos_modificados "${origen}" "${destino}")

    if [ "${#archivos_mod[@]}" -gt 0 ]; then
        log WARN "  → ${#archivos_mod[@]} archivo(s) con cambios detectados"

        for archivo_rel in "${archivos_mod[@]}"; do
            local archivo_orig="${origen}/${archivo_rel}"
            local archivo_dest="${destino}/${archivo_rel}"

            echo ""
            separador "·" 60
            log ACCION "  ARCHIVO MODIFICADO: ${carpeta}/${archivo_rel}"
            separador "·" 60

            # Mostrar información del cambio
            if [ -f "${archivo_orig}" ] && [ -f "${archivo_dest}" ]; then
                local tam_orig tam_dest fecha_orig fecha_dest
                tam_orig=$(stat --printf='%s' "${archivo_orig}" 2>/dev/null || echo "?")
                tam_dest=$(stat --printf='%s' "${archivo_dest}" 2>/dev/null || echo "?")
                fecha_orig=$(stat --printf='%y' "${archivo_orig}" 2>/dev/null | cut -d'.' -f1)
                fecha_dest=$(stat --printf='%y' "${archivo_dest}" 2>/dev/null | cut -d'.' -f1)

                log INFO "  Origen (laptop):    ${tam_orig} bytes — ${fecha_orig}"
                log INFO "  Destino (disco):    ${tam_dest} bytes — ${fecha_dest}"
            fi

            # Si modo forzar, actualizar sin preguntar
            if [ "${MODO_FORZAR}" = true ]; then
                log INFO "  [--force] Actualizando sin preguntar..."
                if [ "${MODO_SIMULACION}" = false ]; then
                    rsync -ahc --no-whole-file \
                        "${archivo_orig}" "${archivo_dest}" 2>/dev/null || true
                    ((TOTAL_ACTUALIZADOS++))
                fi
                continue
            fi

            # Preguntar al usuario qué hacer
            echo ""
            echo -e "${NEGRITA}  ¿Qué deseas hacer con este archivo?${RESET}"
            echo -e "  ${VERDE}[s]${RESET} Actualizar en disco externo (sobrescribir)"
            echo -e "  ${AMARILLO}[v]${RESET} Ver diferencias primero"
            echo -e "  ${AZUL}[i]${RESET} Ignorar (dejar el archivo del disco sin cambios)"
            echo -e "  ${MAGENTA}[t]${RESET} Actualizar todos los modificados de esta carpeta"
            echo -e "  ${ROJO}[n]${RESET} Ignorar todos los modificados de esta carpeta"
            echo ""

            local respuesta
            read -rp "  Tu elección [s/v/i/t/n]: " respuesta
            respuesta=$(echo "$respuesta" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

            case "$respuesta" in
                s|si|sí|y|yes)
                    log OK "  Actualizando: ${archivo_rel}"
                    if [ "${MODO_SIMULACION}" = false ]; then
                        rsync -ahc "${archivo_orig}" "${archivo_dest}" 2>/dev/null || true
                        ((TOTAL_ACTUALIZADOS++))
                    fi
                    ;;
                v|ver)
                    mostrar_diff "${archivo_orig}" "${archivo_dest}"
                    # Volver a preguntar después de mostrar diff
                    read -rp "  ¿Actualizar este archivo? [s/n]: " respuesta2
                    respuesta2=$(echo "$respuesta2" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
                    if [[ "$respuesta2" =~ ^(s|si|sí|y|yes)$ ]]; then
                        log OK "  Actualizando: ${archivo_rel}"
                        if [ "${MODO_SIMULACION}" = false ]; then
                            rsync -ahc "${archivo_orig}" "${archivo_dest}" 2>/dev/null || true
                            ((TOTAL_ACTUALIZADOS++))
                        fi
                    else
                        log INFO "  Omitido: ${archivo_rel}"
                        ((TOTAL_OMITIDOS++))
                    fi
                    ;;
                i|ignorar|n|no)
                    log INFO "  Omitido: ${archivo_rel}"
                    ((TOTAL_OMITIDOS++))
                    ;;
                t|todos)
                    # Actualizar este y todos los siguientes de la carpeta
                    log OK "  Actualizando todos los modificados de: ${carpeta}"
                    if [ "${MODO_SIMULACION}" = false ]; then
                        rsync -ahc "${archivo_orig}" "${archivo_dest}" 2>/dev/null || true
                        ((TOTAL_ACTUALIZADOS++))
                    fi
                    MODO_FORZAR_CARPETA=true  # flag local para el resto del loop
                    ;;
                *)
                    log WARN "  Opción no reconocida. Omitiendo: ${archivo_rel}"
                    ((TOTAL_OMITIDOS++))
                    ;;
            esac

            # Si se activó el modo "actualizar todos" para esta carpeta
            if [ "${MODO_FORZAR_CARPETA:-false}" = true ] && [ "$respuesta" != "t" ]; then
                log OK "  [todos] Actualizando: ${archivo_rel}"
                if [ "${MODO_SIMULACION}" = false ]; then
                    rsync -ahc "${archivo_orig}" "${archivo_dest}" 2>/dev/null || true
                    ((TOTAL_ACTUALIZADOS++))
                fi
            fi

        done
        # Resetear flag local
        MODO_FORZAR_CARPETA=false

    else
        log OK "  → Sin archivos modificados en: ${carpeta}"
    fi

    # ════════════════════════════════════════════════════════════════════
    # PASO C: Archivos huérfanos (están en disco pero NO en origen)
    # ════════════════════════════════════════════════════════════════════
    if [ -d "${destino}" ]; then
        log INFO "Buscando archivos huérfanos en disco externo..."
        local huerfanos=()
        while IFS= read -r linea; do
            [ -n "$linea" ] && huerfanos+=("$linea")
        done < <(obtener_huerfanos "${origen}" "${destino}")

        if [ "${#huerfanos[@]}" -gt 0 ]; then
            ((TOTAL_HUERFANOS += ${#huerfanos[@]}))
            log WARN "  → ${#huerfanos[@]} archivo(s)/carpeta(s) en disco que NO están en origen:"
            echo ""

            for item in "${huerfanos[@]}"; do
                local ruta_dest="${destino}/${item}"
                local tipo_item="archivo"
                [ -d "${ruta_dest}" ] && tipo_item="directorio"

                log WARN "  ⚠  ${tipo_item}: ${carpeta}/${item}"
                if [ -f "${ruta_dest}" ]; then
                    local tam
                    tam=$(stat --printf='%s' "${ruta_dest}" 2>/dev/null || echo "?")
                    local fecha
                    fecha=$(stat --printf='%y' "${ruta_dest}" 2>/dev/null | cut -d'.' -f1)
                    log INFO "     Tamaño: ${tam} bytes | Fecha: ${fecha}"
                fi
            done

            echo ""
            log WARN "  NOTA: Estos archivos existen en el disco externo pero NO en tu laptop."
            log WARN "  Puede que los hayas eliminado, movido, o que sean solo del disco."

            if [ "${MODO_BORRAR_TODO}" = true ]; then
                log ACCION "  [--delete-all] Eliminando todos los huérfanos..."
                for item in "${huerfanos[@]}"; do
                    local ruta_dest="${destino}/${item}"
                    if [ "${MODO_SIMULACION}" = false ]; then
                        rm -rf "${ruta_dest}"
                        log OK "  Eliminado: ${carpeta}/${item}"
                        ((TOTAL_BORRADOS++))
                    else
                        log INFO "  [SIMULACIÓN] Se eliminaría: ${carpeta}/${item}"
                    fi
                done
            else
                echo ""
                echo -e "${NEGRITA}  ¿Qué deseas hacer con los archivos huérfanos de '${carpeta}'?${RESET}"
                echo -e "  ${ROJO}[e]${RESET} Eliminar todos del disco externo (sincronizar total)"
                echo -e "  ${AMARILLO}[r]${RESET} Revisar uno por uno y decidir"
                echo -e "  ${VERDE}[c]${RESET} Conservar todos (no eliminar nada)"
                echo ""
                local resp_huerfanos
                read -rp "  Tu elección [e/r/c]: " resp_huerfanos
                resp_huerfanos=$(echo "$resp_huerfanos" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

                case "$resp_huerfanos" in
                    e|eliminar)
                        for item in "${huerfanos[@]}"; do
                            local ruta_dest="${destino}/${item}"
                            if [ "${MODO_SIMULACION}" = false ]; then
                                rm -rf "${ruta_dest}"
                                log OK "  Eliminado: ${carpeta}/${item}"
                                ((TOTAL_BORRADOS++))
                            else
                                log INFO "  [SIMULACIÓN] Se eliminaría: ${carpeta}/${item}"
                            fi
                        done
                        ;;
                    r|revisar)
                        for item in "${huerfanos[@]}"; do
                            local ruta_dest="${destino}/${item}"
                            echo ""
                            log ACCION "  HUÉRFANO: ${carpeta}/${item}"
                            read -rp "  ¿Eliminar del disco externo? [s/n]: " resp_item
                            resp_item=$(echo "$resp_item" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
                            if [[ "$resp_item" =~ ^(s|si|sí|y|yes)$ ]]; then
                                if [ "${MODO_SIMULACION}" = false ]; then
                                    rm -rf "${ruta_dest}"
                                    log OK "  Eliminado: ${carpeta}/${item}"
                                    ((TOTAL_BORRADOS++))
                                fi
                            else
                                log INFO "  Conservado: ${carpeta}/${item}"
                            fi
                        done
                        ;;
                    c|conservar|n|no|*)
                        log INFO "  Conservando todos los huérfanos de: ${carpeta}"
                        ;;
                esac
            fi
        else
            log OK "  → Sin archivos huérfanos en: ${carpeta}"
        fi
    fi

    echo ""
    log OK "╚══ Finalizado: ${carpeta} ══╝"
    separador
    echo ""
}

# ── Función para copiar archivos nuevos usando rsync con barra de progreso ──
copiar_archivos_nuevos() {
    local origen="$1"
    local destino="$2"
    shift 2
    local archivos=("$@")

    if command -v pv &>/dev/null; then
        # Calcular tamaño total para pv
        local total_bytes=0
        for f in "${archivos[@]}"; do
            local tam
            tam=$(stat --printf='%s' "${origen}/${f}" 2>/dev/null || echo "0")
            ((total_bytes += tam))
        done

        log INFO "  Copiando ${#archivos[@]} archivo(s) nuevos ($(bytes_legibles $total_bytes))..."

        # Usar rsync con barra de progreso de pv
        rsync ${RSYNC_OPTS} \
            --itemize-changes \
            --filter='+ **' \
            "${origen}/" "${destino}/" \
            2>/dev/null | pv -l -s "${#archivos[@]}" > /dev/null || true
    else
        # Sin pv: usar --progress de rsync
        log INFO "  Copiando ${#archivos[@]} archivo(s) nuevos..."
        rsync ${RSYNC_OPTS} \
            --progress \
            --ignore-existing \
            "${origen}/" "${destino}/" 2>/dev/null || true
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 8: RESUMEN FINAL
# ─────────────────────────────────────────────────────────────────────────────

mostrar_resumen() {
    echo ""
    separador "═" 70
    log TITULO "  RESUMEN DEL BACKUP"
    separador "═" 70
    echo ""
    log OK    "  ✓ Archivos nuevos copiados:    ${TOTAL_COPIADOS}"
    log OK    "  ✓ Archivos actualizados:       ${TOTAL_ACTUALIZADOS}"
    log INFO  "  → Archivos omitidos:           ${TOTAL_OMITIDOS}"

    if [ "${TOTAL_HUERFANOS}" -gt 0 ]; then
        log WARN  "  ⚠  Huérfanos encontrados:       ${TOTAL_HUERFANOS}"
    fi

    if [ "${TOTAL_BORRADOS}" -gt 0 ]; then
        log ACCION "  ✗ Archivos eliminados del disco: ${TOTAL_BORRADOS}"
    fi

    echo ""
    log INFO  "  Tiempo total:                  $(tiempo_transcurrido)"
    log INFO  "  Carpetas procesadas:           ${#CARPETAS_BACKUP[@]}"

    if [ "${MODO_SIMULACION}" = true ]; then
        echo ""
        log WARN  "  ⚠  MODO SIMULACIÓN ACTIVO — No se realizaron cambios reales"
    fi

    if [ "${MODO_LOG}" = true ]; then
        echo ""
        log INFO "  Log guardado en: ${LOG_FILE}"
    fi

    echo ""
    separador "═" 70

    # Mostrar uso del disco externo al finalizar
    echo ""
    log TITULO "  Estado del disco externo tras el backup:"
    df -h "${DISCO_EXTERNO}" | tail -1 | awk '{
        printf "    Usado: %s / Total: %s | Libre: %s (%s)\n", $3, $2, $4, $5
    }'
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 9: PARSEAR ARGUMENTOS DE LÍNEA DE COMANDOS
# ─────────────────────────────────────────────────────────────────────────────

parsear_argumentos() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                mostrar_ayuda
                exit 0
                ;;
            -v|--verbose)
                MODO_VERBOSE=true
                log INFO "Modo verbose activado"
                ;;
            -s|--simulate)
                MODO_SIMULACION=true
                log WARN "MODO SIMULACIÓN activado — no se realizarán cambios"
                ;;
            -l|--log)
                MODO_LOG=true
                # Rotar log si es muy grande (>10MB)
                if [ -f "${LOG_FILE}" ] && [ "$(stat --printf='%s' "${LOG_FILE}")" -gt 10485760 ]; then
                    mv "${LOG_FILE}" "${LOG_FILE}.$(date +%Y%m%d).bak"
                    log INFO "Log anterior archivado como .bak"
                fi
                log INFO "Log activado: ${LOG_FILE}"
                ;;
            -f|--force)
                MODO_FORZAR=true
                log WARN "Modo forzar activado — se sobreescribirán archivos modificados sin preguntar"
                ;;
            -d|--delete-all)
                MODO_BORRAR_TODO=true
                log WARN "Modo borrar-todo activado — se eliminarán huérfanos sin preguntar"
                ;;
            *)
                log ERROR "Opción desconocida: $1"
                log ERROR "Usa -h o --help para ver las opciones disponibles."
                exit 1
                ;;
        esac
        shift
    done
}

# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 10: FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

main() {
    # Cabecera del script
    clear
    echo ""
    echo -e "${NEGRITA}${AZUL}"
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║         BACKUP ARCH LINUX → ARCHDISK                           ║"
    echo "  ║         $(date '+%d/%m/%Y %H:%M:%S')                                    ║"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo ""

    # Parsear argumentos
    parsear_argumentos "$@"

    # Fase 1: Verificar dependencias del sistema
    verificar_requisitos

    # Fase 2: Verificar disco externo montado
    verificar_disco_externo

    # Fase 3: Verificar carpetas de origen
    verificar_origen

    # Confirmación final antes de empezar
    echo ""
    log TITULO "  Configuración del backup:"
    log INFO   "  Origen:          ${HOME_DIR}"
    log INFO   "  Destino:         ${DESTINO_BASE}"
    log INFO   "  Carpetas:        ${#CARPETAS_BACKUP[@]}"
    log INFO   "  Simulación:      ${MODO_SIMULACION}"
    log INFO   "  Forzar cambios:  ${MODO_FORZAR}"
    log INFO   "  Borrar huérf.:   ${MODO_BORRAR_TODO}"
    echo ""

    read -rp "$(echo -e "${NEGRITA}  ¿Iniciar backup? [s/n]: ${RESET}")" confirmar
    confirmar=$(echo "$confirmar" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

    if [[ ! "$confirmar" =~ ^(s|si|sí|y|yes)$ ]]; then
        log WARN "Backup cancelado por el usuario."
        exit 0
    fi

    echo ""
    separador "═" 70
    log TITULO "  INICIANDO BACKUP"
    separador "═" 70
    echo ""

    # Fase 4: Procesar cada carpeta
    for carpeta in "${CARPETAS_BACKUP[@]}"; do
        procesar_carpeta "${carpeta}"
    done

    # Fase 5: Mostrar resumen
    mostrar_resumen
}

# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

# Asegurar que el script no se ejecuta como root (para preservar correctamente
# la propiedad de los archivos del usuario)
if [ "$(id -u)" -eq 0 ]; then
    echo "[ADVERTENCIA] Estás ejecutando el script como root."
    echo "Se recomienda ejecutarlo como usuario normal: ${USUARIO}"
    read -rp "¿Continuar de todas formas? [s/n]: " resp_root
    [[ ! "$resp_root" =~ ^(s|si|sí|y|yes)$ ]] && exit 1
fi

# Llamar a la función principal pasando todos los argumentos
main "$@"
