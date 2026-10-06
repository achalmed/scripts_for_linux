---
tipo: readme
estado: activo
---
# script_backup_suite/ — respaldo rsync del home a un disco externo por perfiles, con exclusiones, confirmación y resumen
<!-- suite:inicio -->
**Suite `backup_suite`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Sincroniza carpetas del home hacia un disco externo por perfiles, con confirmación, exclusiones y resumen.

- Escribe en: archivos · simula por defecto: no
- Depende de: rsync

Comandos:

```bash
main.sh --simulate --verbose
main.sh --profile docs
main.sh --profile list
main.sh --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-03); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Copia carpetas del directorio personal a un disco externo montado, carpeta por carpeta y en tres pasos:

1. **Nuevos**: los archivos que no están en el disco se copian sin preguntar (`rsync --ignore-existing`).
2. **Modificados**: por cada archivo que difiere pregunta `[s]` actualizar, `[v]` ver diferencias (texto: `diff`
   o `colordiff`; binario: tamaño y fecha), `[i]` ignorar, `[t]` actualizar todos los de la carpeta, `[n]` ignorar
   todos. `--force` actualiza sin preguntar.
3. **Huérfanos** (están en el disco y ya no en el origen): `[e]` eliminar todos, `[r]` revisar uno a uno,
   `[c]` conservar. `--delete-all` los elimina sin preguntar.

- **Qué escribe:** en `<montaje>/backup_<usuario>/<carpeta>/`, donde `<montaje>` es `/media/<usuario>/<ETIQUETA>`,
  `/run/media/<usuario>/<ETIQUETA>` o el punto que `lsblk` dé para esa etiqueta (`DISK_LABEL` en `config.sh`). Con
  `-l`/`--log`, además, «~/backup_suite.log» (cabecera con usuario y nombre de equipo; se archiva como `.bak` al pasar
  de 10 MB).
- **Qué borra:** los huérfanos que se aprueben se eliminan con `rm -rf`, sin papelera.
- **Qué no hace:** no versiona, no cifra, no restaura y no copia a destinos remotos; el destino es un disco montado.
- **Simulación:** no simula por defecto; `-s`/`--simulate` (no `--dry-run`) muestra el plan sin copiar ni borrar.

## Uso

```bash
./main.sh --simulate --verbose          # simula con detalle: empezar siempre así
./main.sh                               # perfil home, interactivo
./main.sh --profile docs                # solo Documents
./main.sh --folder Pictures             # una sola carpeta del perfil
./main.sh --profile list                # lista los perfiles
./main.sh --fast --profile home         # compara por fecha y tamaño, sin checksum
./main.sh --src ~/Proyectos --dest "/media/<usuario>/<ETIQUETA>/otra/Proyectos"   # perfil custom
./main.sh --log --post-cmd "notify-send 'Respaldo' 'Terminado'"
```

| opción | qué hace | por defecto (`config.sh`) |
|---|---|---|
| `-h`, `--help` | ayuda | — |
| `--version` | imprime la versión | — |
| `-v`, `--verbose` | lista cada archivo y el tamaño de cada carpeta | `false` |
| `-s`, `--simulate` | simula; anula `--force` | `false` |
| `-l`, `--log` | escribe el log en «~/backup_suite.log» | `false` |
| `--no-confirm` | no pide la confirmación inicial (sí las de cada archivo) | `false` |
| `-p`, `--profile NOMBRE` | `home`, `docs`, `full` o `custom`; `list` los muestra | `home` |
| `--src RUTA` / `--dest RUTA` | origen y destino libres; van juntos y fuerzan el perfil `custom` | — |
| `-F`, `--folder NOMBRE` | solo esa carpeta; si no está en el perfil, la intenta igual desde el origen | — |
| `-f`, `--force` | actualiza los modificados sin preguntar | `false` |
| `-d`, `--delete-all` | elimina los huérfanos sin preguntar | `false` |
| `--fast` | quita `-c`: compara por fecha y tamaño | `false` |
| `--compress` | añade `--compress` a rsync (solo sirve por red) | `false` |
| `--post-cmd CMD` | ejecuta `CMD` con `eval` al terminar (no en simulación) | — |

Perfiles (`config.sh`): `home` recorre la lista `PROFILE_HOME_FOLDERS`; `docs`, solo `Documents`; `full`, cada
carpeta de primer nivel del home salvo `GLOBAL_EXCLUDE`; `custom`, la de `--src`. Las opciones de rsync son
`-ahc --human-readable --stats` más `--itemize-changes --copy-links --hard-links --protect-args`, con las exclusiones
de `GLOBAL_EXCLUDE` (carpetas) y `RSYNC_PATTERN_EXCLUDE` (patrones).

Códigos de salida: 0 hecho o cancelado · 1 disco no montado, sin carpetas válidas u otro error · 2 argumentos ·
5 falta rsync.

Requisitos: Bash ≥ 4.3 (`local -n`), `rsync`, `df`, `lsblk`, `file`; opcionales `pv` (barra de progreso),
`colordiff` o `diff`. Comprueba `bc` y avisa si falta, pero nada lo usa.

**Automatización al conectar el disco** (ejemplo; ver el Límite honesto antes de usarlo). Regla udev en
`/etc/udev/rules.d/99-backup-suite.rules`:

```text
ACTION=="add", SUBSYSTEM=="block", ENV{ID_FS_LABEL}=="<ETIQUETA>", \
    RUN+="/bin/systemctl start --no-block backup-disco.service"
```

Servicio en `/etc/systemd/system/backup-disco.service` (la unidad `.mount` es `media-<usuario>-<ETIQUETA>.mount`
si el disco monta en `/media`, `run-media-<usuario>-<ETIQUETA>.mount` si monta en `/run/media`):

```ini
[Unit]
Description=Respaldo al disco externo
After=media-<usuario>-<ETIQUETA>.mount

[Service]
Type=oneshot
User=<usuario>
Environment=TERM=xterm
ExecStart=<ruta-del-repo>/script_backup_suite/main.sh --force --delete-all --log --no-confirm
```

`TERM` hace falta porque `main.sh` empieza con `clear`. Tras `sudo udevadm control --reload-rules`, la salida queda
en `journalctl -u backup-disco.service`.

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | orquesta: argumentos → logger → validación → lista de carpetas del perfil → confirmación → carpeta a carpeta → resumen |
| `config.sh` | etiqueta del disco, carpeta destino, ruta del log, opciones de rsync, perfiles, exclusiones, valores por defecto |
| `lib/cli.sh` | parser de opciones, ayuda, lista de perfiles y combinaciones inválidas |
| `lib/logger.sh` | envoltorio del logger común (carpeta core del espacio de trabajo, shell-lib); abre el log solo con `--log` |
| `lib/validator.sh` | root, dependencias, punto de montaje, espacio y sistema de archivos del disco, carpetas de origen, exclusiones |
| `lib/analyzer.sh` | listas de nuevos, modificados (rsync `-n --itemize-changes`) y huérfanos (`find` + `comm`); diff; tamaños |
| `lib/processor.sh` | los tres pasos por carpeta, las preguntas, la copia de cada archivo y el borrado de huérfanos |
| `lib/summary.sh` | banner de configuración, resumen final, estado del disco y `--post-cmd` |

## Límite honesto

- **Los contadores abortan el respaldo.** Bajo `set -euo pipefail`, `(( x++ ))` con `x` en cero devuelve 1 y termina
  el script: la primera carpeta del perfil que no existe (`validate_source_folders`), el primer archivo omitido,
  actualizado o borrado detienen la ejecución sin resumen. Con el perfil `home`, basta una carpeta de la lista que no
  exista en el home. Es un fallo del código, no del uso; hasta corregirlo, el ejemplo de systemd se detiene en la
  primera actualización o borrado.
- **Los errores de la copia de nuevos se ocultan.** Esa copia lleva `2>/dev/null || true`: cualquier fallo de rsync
  (no solo el código 24) se ignora y el resumen cuenta los archivos como copiados (ver `estado.md`
  §Por hacer).
- **Nombres con espacios en el paso de modificados**: la lista sale de `awk '{print $2}'` sobre la salida de rsync,
  así que una ruta con espacios se corta en el primero y ese archivo no se actualiza (da error); lo mismo afecta a la
  cuenta de nuevos, no a su copia.
- **`--simulate` sigue preguntando**: las preguntas de modificados y huérfanos aparecen, pero nada se escribe.
- **`custom` no es libre del todo**: exige igualmente el disco de `DISK_LABEL` montado (crea en él
  `backup_<usuario>/`), y el destino real es la carpeta madre de `--dest` más el nombre de `--src`; si los dos nombres
  difieren, la copia no cae en `--dest`.
- **Un perfil desconocido** no da error de argumento: se queda sin carpetas y sale con «No hay carpetas válidas».
- **`--copy-links` está activo**: los enlaces simbólicos se copian como archivos reales.
- **Necesita terminal** (`TERM`) incluso para `--help`, porque empieza con `clear`; como root, pregunta antes de seguir.
- **`--post-cmd` pasa por `eval`**: el texto se ejecuta tal cual en el shell.
- **Discos NTFS o exFAT** no conservan permisos Unix; avisa, no lo impide.
- Escrito para Linux con `/media` o `/run/media`; usa `stat --printf` y `df --block-size` de GNU, así que no corre en
  macOS.
