#!/usr/bin/env bash
# =============================================================================
#  lib/cli.sh — Interfaz de línea de comandos
# =============================================================================
#
#  Un subcomando y dos banderas. Los OPT_* parten de config.sh.
# =============================================================================

OPT_SUBCOMANDO=""
OPT_APLICAR=false
OPT_VERBOSE="${DEFAULT_VERBOSE}"

# --- show_help() -----------------------------------------------------------
show_help() {
    cat <<AYUDA
Uso: main.sh <subcomando> [opciones]

Avisa con un sonido que crece (en volumen y en insistencia) cuando la RAM
usada pasa del ${UMBRAL}%, con una notificación que dice qué apps usan más;
en el nivel más alto abre la lista de apps para cerrarlas.

Subcomandos:
  vigilar       Mide cada ${INTERVALO} s y avisa (lo que corre el servicio).
  estado        Muestra la RAM, las apps que más usan y si el servicio está activo.
  probar        Hace sonar cada nivel y el escalamiento, y manda una notificación de muestra.
  cerrar        Abre ya la lista de apps abiertas para cerrar las que marques.
  instalar      Escribe ~/.config/systemd/user/${UNIDAD} y lo activa (simula sin --aplicar).
  desinstalar   Lo detiene y borra la unidad (simula sin --aplicar).

Opciones:
  --aplicar     Con instalar o desinstalar: hacerlo de verdad.
  -v, --verbose Mensajes de depuración.
  -h, --help    Esta ayuda.

Los umbrales, sonidos y volúmenes se cambian en config.sh.
AYUDA
}

# --- parse_args() ----------------------------------------------------------
# Arguments: "$@" de main.sh. Sale con 2 si los argumentos no son válidos.
parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)    show_help; exit 0 ;;
            --aplicar)    OPT_APLICAR=true ;;
            -v|--verbose) OPT_VERBOSE=true ;;
            vigilar|estado|probar|cerrar|instalar|desinstalar)
                if [ -n "${OPT_SUBCOMANDO}" ]; then
                    echo "[ERROR] un solo subcomando por vez (ya hay «${OPT_SUBCOMANDO}»)" >&2; exit 2
                fi
                OPT_SUBCOMANDO="$1" ;;
            *) echo "[ERROR] argumento desconocido: $1 (ver --help)" >&2; exit 2 ;;
        esac
        shift
    done
    if [ -z "${OPT_SUBCOMANDO}" ]; then
        show_help; exit 2
    fi
    if [ "${OPT_APLICAR}" = true ] && [ "${OPT_SUBCOMANDO}" != instalar ] && [ "${OPT_SUBCOMANDO}" != desinstalar ]; then
        echo "[ERROR] --aplicar solo vale con instalar o desinstalar" >&2; exit 2
    fi
    return 0
}
