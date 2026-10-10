---
tipo: readme
estado: activo
---
# docs/ — documentación transversal de `scripts-linux`: las decisiones del repo y sus consumidores

Cada herramienta se documenta en su carpeta (su `README.md` es su manual); aquí vive solo lo que
no pertenece a una herramienta sola: por qué el repo es como es, qué queda pendiente y quién usa
estas herramientas desde otros proyectos.

## Por dónde empezar

| si eres… | empieza por |
|---|---|
| **quien usa** una herramienta | `../README.md` (§Uso) → el `README.md` de la herramienta |
| **quien amplía** una suite | `../CLAUDE.md` → el `README.md` de la suite → [decisiones.md](decisiones.md) |
| **quien amplía** una GUI | el repo `gui-suites` (`gui-suites/filesystem/README.md`, `gui-suites/git/README.md`) → [decisiones.md](decisiones.md) §2 |
| **quien mantiene** el repo | `../estado.md` (§Por hacer) → [decisiones.md](decisiones.md) → `core/README.md` y `core/suite.schema.yml` |
| quien quiere saber **de dónde** salieron las GUI y adónde fueron | [decisiones.md](decisiones.md) §1.5, §2.4 y §2.5 |
| **otro proyecto** que invoca una herramienta | §Consumidores, abajo |

## Cómo se mantiene

- Lo de una herramienta va a su README; lo transversal, aquí, en el documento de su concepto.
  Nunca un `.md` por sesión, fase o fecha.
- La decisión y su porqué van a [decisiones.md](decisiones.md); lo pendiente, a `../estado.md` §Por hacer.
- Un proyecto nuevo que invoque una herramienta se añade a §Consumidores.
- Las cantidades que cambian no se escriben: las suites las cuenta `python3 core/suites.py listar`.
- La tabla de abajo la genera `python3 core/docs.py indice scripts-linux --aplicar` desde
  `~/Documents`.

## Índice

<!-- docs:inicio -->
| documento | tipo | estado | qué es |
|---|---|---|---|
| [decisiones.md](decisiones.md) | `decision` | `activo` | Decisiones de scripts-linux |

<sub>Bloque generado por `core/docs.py indice` desde el frontmatter de docs/ (2026-10-06); no se edita a mano.</sub>
<!-- docs:fin -->

## Consumidores

El contrato con quien usa estas herramientas es la sección `Uso` del README de cada una (opciones y
bandera de simulación); los consumidores la citan, no la copian.

| quién | qué usa | dónde lo cita |
|---|---|---|
| la cadena de prompts del programa de radio | `script_whisper_transcriber` (transcribir), `script_audio_converter` (a MP3), `script_video_downloader` (audio de terceros) | `prompts/08 radio/` (pasos 01, 04, 05 y 08) y `prompts/docs/dominios/radio.md` |
| las GUI del repo `gui-suites` (Filesystem Studio y Git Studio) | los backends de archivos y de git y `script_git_sync_respos/repos-config.yml` (Git Studio lo lee y lo reescribe) | `gui-suites/comun/rutas.py` (`BACKENDS`, por `SCRIPTS_LINUX`) |
| el índice de suites del workspace | los `suite.yml` de este repo (generado) | `meta/INDICE_SCRIPTS.md` |
| las notas de proyecto del vault | el origen de las dos GUI y del respaldo | `notas/proyecto-backup-studio.md`, `notas/proyecto-filesystem-studio.md`, `notas/proyecto-git-studio.md` → [decisiones.md](decisiones.md) §1.5 |
