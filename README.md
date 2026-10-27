---
tipo: readme
estado: activo
---
# scripts-linux/ — utilidades Linux del workspace: herramientas CLI (sus GUI viven en studios)

<!-- suites:inicio -->
Suites de esta carpeta (7); índice global en `meta/INDICE_SCRIPTS.md`. Patrón: M main · C config · L lib.

| Suite | Carpeta | Objetivo | Escribe en | Simula | Timer | Estado | Patrón |
|---|---|---|---|---|---|---|---|
| `alerta_ram` | [scripts-linux/script_alerta_ram](script_alerta_ram/) | sistema | sistema | sí | alerta-ram.service | activo | `MCL` |
| `audio_converter` | [scripts-linux/script_audio_converter](script_audio_converter/) | multimedia | archivos | no |  | activo | `MCL` |
| `registro_tiempo` | [scripts-linux/script_registro_tiempo](script_registro_tiempo/) | personal | vault, archivos, sistema | sí | registro-tiempo.timer | borrador | `MCL` |
| `sync_usb` | [scripts-linux/script_sync_usb](script_sync_usb/) | sistema | archivos | no |  | activo | `M··` |
| `video_downloader` | [scripts-linux/script_video_downloader](script_video_downloader/) | multimedia | archivos | no |  | activo | `MCL` |
| `whisper_transcriber` | [scripts-linux/script_whisper_transcriber](script_whisper_transcriber/) | multimedia | archivos | no |  | activo | `MCL` |
| `photo_metadata_suite` | [scripts-linux/scripts_photo_metadata_suite](scripts_photo_metadata_suite/) | multimedia | archivos | sí |  | activo | `MCL` |

<sub>Bloque generado desde los `suite.yml` por `core/suites.py generar` (2026-10-27); no se edita a mano.</sub>
<!-- suites:fin -->

## Qué es

Suites independientes, en Bash y Python 3, para las tareas de escritorio que no tienen una
herramienta gráfica cómoda o que se repiten demasiado como para hacerlas a mano: descargar video o
audio y recortar tramos (`script_video_downloader`), transcribir con Whisper (`script_whisper_transcriber`), convertir las
notas de voz de WhatsApp a MP3 (`script_audio_converter`), sincronizar una carpeta por un USB que va y viene (`script_sync_usb`) y poner en orden fechas y
nombres de fotos de cámara (`scripts_photo_metadata_suite`).

Las herramientas de archivos (árbol de proyectos, conteo por extensión, carpetas por lote, hard links) y las de git
(sincronizar y clonar repos) ya no están aquí: desde el 2026-10-27 viven con su interfaz gráfica en dos repos propios,
`filesystem-studio` (Filesystem Studio y sus cinco herramientas) y `git-studio` (Git Studio y sus dos herramientas;
`docs/decisiones.md` §2.6). La tabla de arriba es la lista completa;
`python3 core/suites.py listar` la da para todo el workspace.

**No es** una biblioteca: cada suite es autónoma (`main.*` + `config.*` + `lib/`, `suite.yml`,
README) y solo comparte `core/` (raíz del workspace y logger). Nada del despacho debe vivir aquí; hoy
`script_sync_usb` lo incumple en el código (`estado.md` §Por hacer).
Tampoco es el lugar de PDF y ofimática: eso vive en `raphi`. El remoto en
GitHub se llama igual que la carpeta (`scripts-linux`) y es público.

## Uso

```bash
# yt-dlp + ffmpeg; -m audio, --batch lista.txt, --clip INI-FIN
script_video_downloader/main.sh --simulate <url>
# transcribe o traduce en local; --language es
python3 script_whisper_transcriber/main.py <archivo> --dry-run
# .opus de WhatsApp y otros → .mp3
python3 script_audio_converter/main.py <carpeta> --dry-run
python3 script_sync_usb/main.py --local <carpeta> --usb <montaje> --dry-run
# analyze no toca nada; apply simula salvo --execute
python3 scripts_photo_metadata_suite/main.py analyze <carpeta>
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
| `estado.md` | dónde está el repo: hecho (con la bitácora de cada ola), en curso, por hacer (con fecha y dueño) y futuro | a mano; primero que se lee y último que se escribe |
| `tests/` | `test_simulacion.py` (pytest): cada suite que escribe, en simulación, no escribe nada; `run.sh` la corre con la carpeta temporal en `~/.cache` | a mano |
| `docs/` | lo transversal: `decisiones.md` y, en su README, quién consume estas herramientas | a mano; índice por `core/docs.py indice` |
| `vendor/` | código ajeno conservado tal cual: el cuaderno Colab de Jason Boog del que nació `script_whisper_transcriber` (MIT) | ajeno; no se edita |
| `suite.yml` (uno por suite) | manifiesto de cada herramienta (`core/suite.schema.yml`) | a mano; los bloques de README los escribe `core/suites.py generar --aplicar` |
| `CLAUDE.md` · `AGENTS.md` | guía para el asistente; `AGENTS.md` es un enlace a `CLAUDE.md` | a mano |
| `.gitignore` | comentado por clase: bytecode, entornos, `reports/` | a mano |

La versión de cada herramienta es una constante de su código y la imprime `--version` donde existe
(`docs/decisiones.md` §1.6). Los informes (`reports/`) y las listas de trabajo de una corrida no se versionan.

## Documentación

| documento | para qué leerlo |
|---|---|
| `script_*/README.md` · `scripts_photo_metadata_suite/README.md` | manual de cada suite de primer nivel: uso, opciones, arquitectura, límites |
| `docs/README.md` | mapa por lector de lo transversal y §Consumidores (quién invoca estas herramientas) |
| `estado.md` | dónde está el repo y qué queda pendiente (§Por hacer) |
| `docs/decisiones.md` | por qué el repo es como es |
| `CLAUDE.md` | reglas para el asistente: patrón `main`/`config`/`lib`, cómo verificar, trampas |
| `meta/INDICE_SCRIPTS.md` | las suites de este repo entre las del workspace (generado) |
| `core/README.md` · `core/suite.schema.yml` | el contrato de suite y los bloques generados |

## Límite honesto

- **La única prueba automática es la de simulación** (`tests/run.sh`): cada suite que escribe corre en
  simulación sobre un `HOME` temporal y no debe escribir nada; las que piden red
  se prueban solo con `--help` o se saltan. No hay lint
  ni build: el resto es `bash -n` y `py_compile`.
- **Dependen de binarios del sistema** que no se instalan desde aquí: ffmpeg, yt-dlp, rsync,
  whisper, exiftool, tree, potrace, opencv (cada README dice cuáles). Las herramientas
  Bash son GNU/Linux (`find -printf`, Bash ≥ 4): no se prueban en macOS/BSD.
- **No todas simulan por defecto**: el campo «Simula» de la tabla de arriba lo dice por suite.
  Las operaciones destructivas piden confirmación salvo `--no-confirm`/`--auto`/`-y`/`--si`.
- **El repo es público y su historial conserva datos que ya no están en el código**: un número de documento
  (de `script_dni_a_copia`, que pasó a `herramientas-personales`, privado) y la clave vieja de
  `script_sync_usb`, que se da por expuesta. Reescribir la historia lo decide el autor (`estado.md` §Por hacer).
- **`script_sync_usb` está atada al archivo documental del SGDP**: sincroniza una carpeta `SGDP`,
  aplica su convención de nombres y mueve a la papelera los PDF gemelos con nombre antiguo; su
  lanzador de Windows está roto (su README).
- **`script_sync_usb` no sigue el patrón** `main` + `config` + `lib` (un solo archivo con
  lanzadores `.sh` y `.bat`); `core/suites.py validar` lo marca con aviso.
