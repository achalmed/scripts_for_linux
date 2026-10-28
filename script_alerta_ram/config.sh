#!/usr/bin/env bash
# =============================================================================
#  config.sh — Configuración centralizada de alerta_ram
# =============================================================================
#
#  Todo valor ajustable vive aquí. Tras cambiarlo:  main.sh instalar --aplicar
#  El porcentaje de RAM usada se calcula con MemAvailable (lo que las apps
#  pueden pedir de verdad), no con MemFree, que la caché de disco deja casi
#  siempre baja.
# =============================================================================

# --- Raíz del workspace (core/env.sh), sin rutas de máquina ----------------
_d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
while [ "$_d" != / ] && [ ! -f "$_d/core/env.sh" ]; do _d="$(dirname "$_d")"; done
[ -f "$_d/core/env.sh" ] || { echo "[ERROR] no encuentro core/env.sh subiendo desde ${BASH_SOURCE[0]}" >&2; exit 1; }
source "$_d/core/env.sh"; unset _d

# --- Umbrales (% de RAM usada) ---------------------------------------------
UMBRAL=90          # desde aquí empieza a avisar
REARME=87          # bajo esto se da por normal y la alarma vuelve a quedar lista (histéresis)
INTERVALO=2        # segundos entre mediciones (sin swap la RAM puede llenarse en segundos)

# --- Niveles: "desde_%|sonido|urgencia|repetir_cada_s|acción", de mayor a menor
# El último debe empezar en UMBRAL. Los sonidos se buscan en DIR_SONIDOS.
# Urgencia de notify-send: normal (se cierra sola tras NOTIF_DURACION_MS) o
# critical (se queda hasta que la cierras). En Plasma, «low» no muestra ventana
# emergente: solo va al historial, por eso no se usa.
# Acción: «cerrar» abre la lista de apps para cerrar (ver MODO_CIERRE); «-» nada.
# La lista se abre en el primer nivel «cerrar» (92 %): al 95 % puede no dar
# tiempo, porque de ahí al 100 % se llega en un instante y el kernel cierra una
# app por su cuenta.
NIVELES=(
    "95|dialog-error-critical.oga|critical|15|cerrar"
    "92|battery-caution.oga|critical|30|cerrar"
    "${UMBRAL}|message-attention.oga|normal|60|-"
)

# --- Subida rápida ------------------------------------------------------------
# Si entre dos mediciones la RAM sube SUBIDA_RAPIDA puntos o más y ya está en
# SUBIDA_DESDE % o más, se abre la lista sin esperar a los niveles.
SUBIDA_RAPIDA=3
SUBIDA_DESDE=85
DIR_SONIDOS="/usr/share/sounds/ocean/stereo"   # tema de sonidos de Plasma 6 (1–1,5 s cada uno)

# --- Volumen (% del volumen del sistema, que no se toca) -------------------
# Base: crece en línea recta de VOL_MIN (en UMBRAL) a VOL_MAX (en VOL_TOPE_PCT).
# Escalamiento: cada aviso repetido sin que la RAM baje suma VOL_PASO y repite
# el sonido una vez más (hasta SONIDO_VECES_MAX seguidas). paplay admite más de
# 100 (amplifica); por encima de ~130 puede distorsionar.
VOL_MIN=50
VOL_MAX=100
VOL_TOPE_PCT=98
VOL_PASO=10
SONIDO_VECES_MAX=3

# --- Notificación -----------------------------------------------------------
TOP_APPS=3                     # cuántas apps listar en la notificación
NOMBRE_APP="Alerta de RAM"
NOTIF_DURACION_MS=15000        # cuánto dura en pantalla la de urgencia normal

# --- Cerrar apps ---------------------------------------------------------------
# lista    — ventana con tus apps abiertas y su RAM; marcas las que quieres cerrar
# ventanas — abre la Vista general de KWin (todas las ventanas; se cierran con la X)
MODO_CIERRE="lista"
CIERRE_ESPERA=300              # s antes de volver a abrir la lista si la descartaste y la RAM sigue alta
                               # (si la RAM sube a un nivel «cerrar» más alto, se reabre sin esperar)
VENTANA_ENCIMA=true            # la lista aparece encima de las demás ventanas y con el foco (KWin)
APPS_MIN_MB=50                 # en la lista solo apps que usen al menos esto
# Apps que nunca se ofrecen para cerrar (patrón de bash sobre el id de la app,
# p. ej. org.kde.konsole o com.anthropic.Claude).
EXCLUIR_CIERRE=("org.kde.kdeconnect*" "org.kde.discover.notifier" "geoclue*" "org.kde.kwalletd*")

# --- Servicio systemd de usuario -------------------------------------------
UNIDAD="alerta-ram.service"

# --- Salida -------------------------------------------------------------------
DEFAULT_VERBOSE=false
