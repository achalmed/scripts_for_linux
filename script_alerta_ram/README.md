---
tipo: readme
estado: activo
---
# script_alerta_ram/ — aviso sonoro creciente cuando la RAM se llena, con las apps que más consumen

<!-- suite:inicio -->
**Suite `alerta_ram`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Avisa con un sonido que crece en volumen e insistencia cuando la RAM usada pasa de un umbral, y en el nivel más alto muestra las apps abiertas para cerrarlas.

- Escribe en: sistema · simula por defecto: sí
- Depende de: paplay (PulseAudio o PipeWire), notify-send, kdialog (la lista para cerrar apps; o busctl con MODO_CIERRE=ventanas), systemd de usuario, core/env.sh, core/shell-lib/logger.sh
- Timer: `alerta-ram.service`
- Nota: Solo escribe la unidad de usuario (instalar/desinstalar con --aplicar); cerrar detiene las apps que se marcan en su ventana, y nada sin marcar. Umbrales, sonidos, volúmenes y modo de cierre en config.sh.

Comandos:

```bash
main.sh estado
main.sh probar
main.sh cerrar
main.sh instalar --aplicar
main.sh desinstalar --aplicar
main.sh vigilar
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-27); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Un servicio systemd de usuario que mide la RAM cada pocos segundos y, desde el 90 %, avisa con un sonido y una
notificación que dicen qué aplicaciones usan más. El aviso **crece de dos maneras**: con el porcentaje (cada nivel
tiene su sonido, su urgencia y su ritmo) y con la insistencia (cada repetición sin que la RAM baje suma volumen y
repite el sonido más veces). En el nivel más alto abre una ventana con **todas tus apps abiertas y su RAM**: marcas
las que quieres cerrar y se cierran juntas. Sirve sobre todo en un equipo sin swap, donde la RAM llena hace que el
kernel cierre procesos sin preguntar.

| RAM usada | sonido (tema Ocean) | notificación | se repite cada | además |
|---|---|---|---|---|
| 90–92 % | `message-attention` | normal, 15 s en pantalla | 60 s | |
| 93–94 % | `battery-caution` | crítica: se queda hasta cerrarla | 30 s | |
| 95 % o más | `dialog-error-critical` | crítica | 15 s | ventana para cerrar apps |

El volumen parte del 50 % en el 90 % de RAM y llega al 100 % en el 98 %. Cada repetición suma 10 % y el sonido suena 1,
1, 2, 2 y hasta 3 veces seguidas. Es relativo al volumen del sistema (`paplay --volume`), que no se toca. Al bajar del
87 % llega «RAM normal» y todo vuelve a empezar: la histéresis evita que suene en bucle si el uso oscila en el umbral.

**La ventana para cerrar** (`kdialog`) lista cada app con la RAM de todos sus procesos (Plasma lanza cada una en su
propia unidad `app-*.scope`, con las pestañas de un navegador incluidas; un Flatpak suma su sandbox y su lanzador).
Lo marcado se cierra con `systemctl --user stop`, que manda SIGTERM a todos sus procesos a la vez y deja que la app
guarde antes de salir. Si la descartas, no vuelve a abrirse hasta pasados 5 minutos con la RAM aún alta. Con
`MODO_CIERRE="ventanas"` abre en cambio la Vista general de KWin, con todas las ventanas a la vista.

## Uso

```bash
main.sh estado                 # RAM, nivel, tus apps abiertas con su RAM y si el servicio corre
main.sh probar                 # suena cada nivel y el escalamiento completo del más alto
main.sh cerrar                 # abre ya la ventana para cerrar apps, sin esperar al 95 %
main.sh instalar               # simula: muestra la unidad que escribiría
main.sh instalar --aplicar     # escribe ~/.config/systemd/user/alerta-ram.service, la activa y la reinicia
main.sh desinstalar --aplicar  # la detiene y la borra
```

Para llamarla desde cualquier carpeta como `alerta-ram estado`, un enlace (desde la raíz del repo):
`ln -s "$PWD/script_alerta_ram/main.sh" ~/.local/bin/alerta-ram`.

Umbrales, niveles, sonidos, volúmenes, modo de cierre y apps excluidas viven en `config.sh`; tras cambiarlos,
`main.sh instalar --aplicar`. Lo que registra el servicio se ve con `journalctl --user -u alerta-ram`.

## Estructura

```
script_alerta_ram/
├── main.sh                    # orquesta: parsear → logger → validar → subcomando
├── config.sh                  # umbrales, niveles, sonidos, volúmenes, nombre de la unidad
├── lib/
│   ├── cli.sh                 # subcomandos y --aplicar
│   ├── logger.sh              # envoltorio de core/shell-lib/logger.sh
│   ├── validator.sh           # MemAvailable, paplay, notify-send, sonidos, plantilla
│   ├── memoria.sh             # % de RAM y apps abiertas (unidades app-* de systemd) con su RAM
│   ├── alerta.sh              # niveles, escalamiento, sonido, notificación, bucle vigilar
│   ├── cierre.sh              # ventana de apps para cerrar (kdialog) o Vista general de KWin
│   └── servicio.sh            # instalar y desinstalar la unidad de usuario
└── systemd/alerta-ram.service.in   # plantilla; @SUITE@ se sustituye al instalar
```

## Límite honesto

- No cierra nada por su cuenta: solo lo que marcas en la ventana. Si la RAM se llena en menos de `INTERVALO` segundos
  (una compilación, un modelo grande), el aviso puede llegar tarde.
- Solo ofrece cerrar tus apps de escritorio (`app.slice`): los servicios del sistema y los contenedores Docker quedan
  fuera y se resumen en la notificación como «fuera de tus apps». Un programa lanzado desde una terminal cuenta dentro
  de la terminal.
- Necesita la sesión gráfica: sin ella (TTY, SSH) no suena ni notifica, y el servicio está atado a
  `graphical-session.target`.
- La RAM de cada app es la de su cgroup (`MemoryCurrent`), que incluye la caché de archivos que esa app leyó: es
  orientativa y puede superar lo que muestra el Monitor del sistema.
- Probado en KDE Plasma (Wayland) con PipeWire; otros escritorios dependen de que su servidor de notificaciones
  respete `--replace-id` y la urgencia.
