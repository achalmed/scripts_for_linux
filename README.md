---
tipo: readme
estado: activo
---
# scripts_for_linux/ — utilidades Linux del workspace: herramientas CLI y dos GUI PySide6

<!-- suites:inicio -->
Suites de esta carpeta (14); índice global en `meta/INDICE_SCRIPTS.md`. Patrón: M main · C config · L lib.

| Suite | Carpeta | Objetivo | Escribe en | Simula | Timer | Estado | Patrón |
|---|---|---|---|---|---|---|---|
| `audio_converter` | [scripts_for_linux/script_audio_converter](script_audio_converter/) | multimedia | archivos | no |  | activo | `MCL` |
| `sync_usb` | [scripts_for_linux/script_sync_usb](script_sync_usb/) | sistema | archivos | no |  | activo | `M··` |
| `video_downloader` | [scripts_for_linux/script_video_downloader](script_video_downloader/) | multimedia | archivos | no |  | activo | `MCL` |
| `whisper_transcriber` | [scripts_for_linux/script_whisper_transcriber](script_whisper_transcriber/) | multimedia | archivos | no |  | activo | `MCL` |
| `count_files_by_extension` | [scripts_for_linux/scripts_filesystem_studio/backend/script_count_files_by_extension](scripts_filesystem_studio/backend/script_count_files_by_extension/) | sistema | ninguno | no |  | activo | `MCL` |
| `create_folders_batch` | [scripts_for_linux/scripts_filesystem_studio/backend/script_create_folders_batch](scripts_filesystem_studio/backend/script_create_folders_batch/) | sistema | archivos | no |  | activo | `MCL` |
| `hardlinks_creator` | [scripts_for_linux/scripts_filesystem_studio/backend/script_hardlinks-creator](scripts_filesystem_studio/backend/script_hardlinks-creator/) | sistema | archivos | no |  | activo | `MCL` |
| `hardlinks_detector` | [scripts_for_linux/scripts_filesystem_studio/backend/script_hardlinks-detector](scripts_filesystem_studio/backend/script_hardlinks-detector/) | sistema | archivos | no |  | activo | `MCL` |
| `proyect_tree` | [scripts_for_linux/scripts_filesystem_studio/backend/script_proyect_tree](scripts_filesystem_studio/backend/script_proyect_tree/) | sistema | archivos | no |  | activo | `MCL` |
| `filesystem_studio` | [scripts_for_linux/scripts_filesystem_studio](scripts_filesystem_studio/) | sistema | archivos | no |  | activo | `MCL` |
| `git_download_respos` | [scripts_for_linux/scripts_git_studio/backend/script_git_download_respos](scripts_git_studio/backend/script_git_download_respos/) | sistema | git | no |  | activo | `MCL` |
| `git_sync_respos` | [scripts_for_linux/scripts_git_studio/backend/script_git_sync_respos](scripts_git_studio/backend/script_git_sync_respos/) | sistema | git | no |  | activo | `··L` |
| `git_studio` | [scripts_for_linux/scripts_git_studio](scripts_git_studio/) | sistema | git | no |  | activo | `MCL` |
| `photo_metadata_suite` | [scripts_for_linux/scripts_photo_metadata_suite](scripts_photo_metadata_suite/) | multimedia | archivos | sí |  | activo | `MCL` |

<sub>Bloque generado desde los `suite.yml` por `core/suites.py generar` (2026-10-06); no se edita a mano.</sub>
<!-- suites:fin -->

## Qué es

Suites independientes, en Bash y Python 3, para las tareas de escritorio que no tienen una
herramienta gráfica cómoda o que se repiten demasiado como para hacerlas a mano: descargar video o
audio y recortar tramos (`script_video_downloader`), transcribir con Whisper (`script_whisper_transcriber`), convertir las
notas de voz de WhatsApp a MP3 (`script_audio_converter`), sincronizar una carpeta por un USB que va y viene (`script_sync_usb`) y poner en orden fechas y
nombres de fotos de cámara (`scripts_photo_metadata_suite`).

Dos aplicaciones de escritorio agrupan las herramientas de archivos y de git:
**Filesystem Studio** (`scripts_filesystem_studio`: árbol de proyectos, conteo por extensión,
carpetas por lote, hard links) y **Git Studio** (`scripts_git_studio`: clonar desde GitHub,
sincronizar y ver el estado de los repos). Cada herramienta vive en `backend/` de su GUI, con su
`suite.yml` y su README, y se usa también desde la terminal. La
tabla de arriba es la lista completa; `python3 core/suites.py listar` la da para todo el workspace.

**No es** una biblioteca: cada suite es autónoma (`main.*` + `config.*` + `lib/`, `suite.yml`,
README) y solo comparte `core/` (raíz del workspace y logger). Nada del despacho debe vivir aquí; hoy
`script_sync_usb` lo incumple en el código (`estado.md` §Por hacer).
Tampoco es el lugar de PDF y ofimática: eso vive en `scripts_document_studio`. El remoto en
GitHub se llama igual que la carpeta (`scripts_for_linux`) y es público.

## Uso

```bash
# GUI; --smoke construye la UI y sale
python3 scripts_filesystem_studio/main.py
python3 scripts_git_studio/main.py
# yt-dlp + ffmpeg; -m audio, --batch lista.txt, --clip INI-FIN
script_video_downloader/main.sh --simulate <url>
# transcribe o traduce en local; --language es
python3 script_whisper_transcriber/main.py <archivo> --dry-run
# .opus de WhatsApp y otros → .mp3
python3 script_audio_converter/main.py <carpeta> --dry-run
python3 script_sync_usb/main.py --local <carpeta> --usb <montaje> --dry-run
# analyze no toca nada; apply simula salvo --execute
python3 scripts_photo_metadata_suite/main.py analyze <carpeta>
# los backends de las GUI son también CLI; Git Studio lee su registro repos-config.yml
scripts_filesystem_studio/backend/script_proyect_tree/main.sh --list
scripts_git_studio/backend/script_git_sync_respos/sync.sh --check
```

Regla de oro: simular antes de aplicar. La forma cambia según la suite (`--simulate`,
`--dry-run`, `-d`, `-n`, `--check`, o `apply` sin `--execute`); el bloque de arriba muestra la de
cada una, y cada herramienta tiene `--help`.

## Estructura

| carpeta | qué es | dueño / generador |
|---|---|---|
| `script_audio_converter/` | Python: `.opus` y otros → `.mp3` por lotes con ffmpeg | a mano |
| `script_sync_usb/` | Python: sincronización bidireccional carpeta ↔ USB con papelera y conflictos (sin `config`/`lib`, patrón `M··`) | a mano |
| `script_video_downloader/` | Bash: descarga por URL o lote, recorte exacto con ffmpeg | a mano |
| `script_whisper_transcriber/` | Python: transcripción y traducción local con Whisper, subtítulos | a mano |
| `scripts_photo_metadata_suite/` | Python: fechas y nombres de fotos y videos de cámara, OCR de la marca, digiKam | a mano |
| `scripts_filesystem_studio/` | GUI PySide6 (`main.py`, `app/`, `resources/`) y `backend/` con las herramientas CLI de archivos, cada una con `suite.yml` | a mano; `resources_rc.py` lo genera `scripts_filesystem_studio/tools/build_resources.sh` |
| `scripts_git_studio/` | GUI PySide6 (`main.py`, `app/`, `resources/`) y `backend/` con las herramientas Bash de git; `scripts_git_studio/backend/script_git_sync_respos/repos-config.yml` es el inventario de repos que comparten CLI y GUI, escrito a mano y paralelo a `meta/workspace.yml` | a mano |
| `estado.md` | dónde está el repo: hecho (con la bitácora de cada ola), en curso, por hacer (con fecha y dueño) y futuro | a mano; primero que se lee y último que se escribe |
| `tests/` | `test_simulacion.py` (pytest): cada suite que escribe, en simulación, no escribe nada; `run.sh` la corre con la carpeta temporal en `~/.cache` | a mano |
| `docs/` | lo transversal: `decisiones.md` y, en su README, quién consume estas herramientas | a mano; índice por `core/docs.py indice` |
| `vendor/` | código ajeno conservado tal cual: el cuaderno Colab de Jason Boog del que nació `script_whisper_transcriber` (MIT) | ajeno; no se edita |
| `suite.yml` (uno por suite y por backend) | manifiesto de cada herramienta (`core/suite.schema.yml`) | a mano; los bloques de README los escribe `core/suites.py generar --aplicar` |
| `CLAUDE.md` · `AGENTS.md` | guía para el asistente; `AGENTS.md` es un enlace a `CLAUDE.md` | a mano |
| `.gitignore` | comentado por clase: bytecode, entornos, `reports/`, `estructura.txt`, `resources_rc.py` | a mano |

La versión de cada herramienta es una constante de su código y la imprime `--version` donde existe
(`docs/decisiones.md` §1.6). Los informes que generan las GUI (`reports/`) y las listas de trabajo de
una corrida no se versionan.

## Documentación

| documento | para qué leerlo |
|---|---|
| `script_*/README.md` · `scripts_photo_metadata_suite/README.md` | manual de cada suite de primer nivel: uso, opciones, arquitectura, límites |
| `scripts_filesystem_studio/README.md` · `scripts_git_studio/README.md` | las GUI: módulos, arquitectura `ui → controllers → services`, cómo extender |
| `scripts_filesystem_studio/backend/*/README.md` · `scripts_git_studio/backend/*/README.md` | manual de cada herramienta absorbida por una GUI |
| `docs/README.md` | mapa por lector de lo transversal y §Consumidores (quién invoca estas herramientas) |
| `estado.md` | dónde está el repo y qué queda pendiente (§Por hacer) |
| `docs/decisiones.md` | por qué el repo es como es |
| `CLAUDE.md` | reglas para el asistente: patrón `main`/`config`/`lib`, las dos GUI, cómo verificar, trampas |
| `meta/INDICE_SCRIPTS.md` | las suites de este repo entre las del workspace (generado) |
| `core/README.md` · `core/suite.schema.yml` | el contrato de suite y los bloques generados |

## Límite honesto

- **La única prueba automática es la de simulación** (`tests/run.sh`): cada suite que escribe corre en
  simulación sobre un `HOME` temporal y no debe escribir nada; las que piden red
  se prueban solo con `--help` o se saltan, y las GUI no se prueban. No hay lint ni build: el resto es
  `bash -n`, `py_compile` y `python3 main.py --smoke` en las GUI.
- **Dependen de binarios del sistema** que no se instalan desde aquí: ffmpeg, yt-dlp, rsync,
  whisper, exiftool, tree, potrace, opencv, PySide6 (cada README dice cuáles). Las herramientas
  Bash son GNU/Linux (`find -printf`, Bash ≥ 4): no se prueban en macOS/BSD.
- **No todas simulan por defecto**: el campo «Simula» de la tabla de arriba lo dice por suite.
  Las operaciones destructivas piden confirmación salvo `--no-confirm`/`--auto`/`-y`/`--si`.
- **Las GUI no son la fuente de verdad de sus backends**: portan su lógica a la carpeta
  app/services/ de cada GUI (Filesystem Studio importa la `lib/` de `script_hardlinks-creator` y
  ejecuta el `main.sh` de `script_proyect_tree` en modo proyectos; el resto es un port). Un cambio
  de comportamiento hay que hacerlo en los dos sitios (`docs/decisiones.md` §2.2); `sync.sh` y la GUI
  ya divergen en qué cuentan como cambio.
- **`repos-config.yml` es un inventario a mano, paralelo a `meta/workspace.yml`**, y no coincide con él
  (`docs/decisiones.md` §2.3 y `estado.md` §Por hacer).
- **`script_proyect_tree` genera `estructura.txt`**, un derivado que la normativa (§15.8, D07) no
  admite dentro de un repo: se usa para vista previa en la GUI, `--list`, `--stats` o salidas
  `md`/`json` fuera del árbol versionado.
- **El repo es público y su historial conserva datos que ya no están en el código**: un número de documento
  (de `script_dni_a_copia`, que pasó a `herramientas-personales`, privado) y la clave vieja de
  `script_sync_usb`, que se da por expuesta. Reescribir la historia lo decide el autor (`estado.md` §Por hacer).
- **`script_sync_usb` está atada al archivo documental del SGDP**: sincroniza una carpeta `SGDP`,
  aplica su convención de nombres y mueve a la papelera los PDF gemelos con nombre antiguo; su
  lanzador de Windows está roto (su README).
- **`script_sync_usb` no sigue el patrón** `main` + `config` + `lib` (un solo archivo con
  lanzadores `.sh` y `.bat`); `core/suites.py validar` lo marca con aviso.
