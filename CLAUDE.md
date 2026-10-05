---
tipo: guia_ia
estado: activo
---
# CLAUDE.md — scripts_for_linux

Guía para el asistente. En español, como todo el ecosistema. `AGENTS.md` es un enlace a este
archivo. Léase antes: `README.md` (qué es, uso, estructura), el `suite.yml` y el README de la
herramienta que se toque, `scripts_filesystem_studio/README.md` o `scripts_git_studio/README.md`
si el cambio es en una GUI, y `docs/decisiones.md` (por qué el repo es así y qué queda pendiente).

## Reglas que no se negocian

- **Cada suite es autónoma y sigue el patrón `main` + `config` + `lib`**, en Bash y en Python por
  igual (`core/suite.schema.yml` §`patron`; excepción aceptada: `script_sync_usb`, un solo archivo):

  ```
  script_<nombre>/
  ├── main.sh|main.py     # entrada: solo orquestación (≈120 líneas como máximo)
  ├── config.sh|config.py # valores editables: rutas, exclusiones, opciones de rsync, colores
  └── lib/                # un módulo por responsabilidad
      ├── cli.*           # parseo de argumentos (OPT_* en Bash / argparse en Python)
      ├── logger.*        # envoltorio del logger de core/ (shell-lib o py-common)
      ├── validator.*     # dependencias, entradas y entorno
      └── ...             # dominio: scanner, processor, renderer, …
  ```

  **`main` orquesta, `lib/` implementa.** La entrada carga `config`, luego los módulos de `lib/`
  en orden de dependencia y ejecuta fases numeradas (parsear → logger → validar → confirmar →
  procesar → resumen). La lógica de negocio nunca vive en `main`. **Los tunables nuevos van al
  `config`**, no a un módulo de `lib/`.
- **Sin rutas de máquina ni logger propio**: la raíz se resuelve con `core/env.sh` o `core/env.py`
  y `lib/logger.*` envuelve el de `core/`. Las herramientas Bash usan `set -euo pipefail` y
  resuelven `SCRIPT_DIR` para funcionar desde cualquier directorio; las Python anteponen su carpeta
  a `sys.path`.
- **Lo destructivo pide confirmación** salvo `--no-confirm`/`--auto`/`-y`/`--si`, y la simulación
  (`--dry-run`, `--simulate`, `-d`, `-n`, `--check`) se respeta de punta a punta. La bandera de
  simulación **no es la misma en todas las suites**: compruébala en su `--help` o en su `suite.yml`
  antes de escribirla en un README. Un script nuevo de un solo archivo se lleva al patrón modular
  antes de ampliarlo; los bugs que esa migración corrija van al mensaje de commit, no al README.
- **En las dos GUI (PySide6/Qt6) toda escritura y toda ejecución de un backend pasan por la carpeta
  app/services/** de cada una, y las operaciones largas corren en un worker (`QThread`) con progreso
  y cancelación. Hoy hay excepciones que no se amplían: algunos controllers abren archivos con
  `xdg-open` y consultan el disco, y el reporte de Hardlinks se genera en el hilo de la interfaz. Las
  vistas son `.ui` de Qt Designer cargadas con `QUiLoader` (sin compilar). Se ejecutan con `python3 scripts_filesystem_studio/main.py` y
  `python3 scripts_git_studio/main.py`; `--smoke` construye la UI y sale.
- **Los backends de las GUI son suites completas** (`suite.yml`, README, `main.*` + `config` +
  `lib/`) y siguen siendo CLI desde su carpeta: `scripts_filesystem_studio/backend/` y
  `scripts_git_studio/backend/`. Un cambio de comportamiento se hace en el backend y en el
  servicio de la GUI que lo porta (`docs/decisiones.md` §2.2).
- **`scripts_git_studio/backend/script_git_sync_respos/repos-config.yml` es el inventario propio de
  Git Studio**: lo leen `sync.sh`, `status.sh` y la GUI
  (`scripts_git_studio/app/services/config_service.py`), y la GUI lo reescribe entero al añadir o
  clonar. Es paralelo a `meta/workspace.yml`, que es el manifiesto del workspace: no lo presentes como
  registro de repos del ecosistema (`docs/decisiones.md` §2.3 y §Pendientes).
- **`scripts_git_studio/app/services/git_service.py` es la única implementación de comandos git**
  de Git Studio: sync, estado, clonado y reportes la reutilizan.
- **Lo generado no se edita**: los bloques `<!-- suite:inicio -->`/`<!-- suites:inicio -->` de los
  README salen de los `suite.yml` (`core/suites.py generar --aplicar`); el índice de
  `docs/README.md`, de `core/docs.py indice`; `resources_rc.py` lo escribe
  `scripts_filesystem_studio/tools/build_resources.sh`; `reports/` y `estructura.txt` no se
  versionan.
- **Dónde va cada cosa nueva** (NORMATIVA §15.11, concretada aquí): el uso o una opción de una
  herramienta, a su README (`Qué es`, `Uso`, `Estructura`, `Límite honesto`; sin versión en el H1,
  `docs/decisiones.md` §1.6); el porqué, a `docs/decisiones.md`; un fallo o una tarea, a su
  §Pendientes con fecha y dueño; quién invoca una herramienta desde otro proyecto, a `docs/README.md`
  §Consumidores; un dato que un `suite.yml` contiene, al `suite.yml` (el bloque se regenera). Nunca un
  `.md` por sesión ni en la raíz, ni historia de bugs en un README, ni cantidades que cambian (las
  cuenta `python3 core/suites.py listar`).
- **Español con tildes** en mensajes, comentarios y docs (excepción heredada: el código y los
  docstrings de `script_dni_a_copia` están en inglés). Nada del despacho ni de sus personas en este
  repo, ni secretos ni datos personales en un documento: es público.

## Cómo se verifica un cambio

```bash
# desde ~/Documents
python3 core/archivos.py validar scripts_for_linux     # A01–A14 y D01–D12
python3 core/suites.py validar                          # cada suite.yml contra el esquema
python3 core/suites.py generar                          # ¿bloques de README desfasados? (simula)
python3 core/docs.py verificar scripts_for_linux        # el índice de docs/ al día
bash -n scripts_for_linux/script_backup_suite/main.sh   # sintaxis Bash; un archivo por invocación
python3 -m py_compile scripts_for_linux/script_audio_converter/main.py
scripts_for_linux/script_video_downloader/main.sh --simulate <url>   # simulación de la suite tocada
python3 scripts_for_linux/scripts_filesystem_studio/main.py --smoke  # la GUI construye y sale
python3 scripts_for_linux/scripts_git_studio/main.py --smoke
scripts_for_linux/scripts_git_studio/backend/script_git_sync_respos/status.sh  # registro de la GUI
meta/doctor/main.sh --breve
```

No hay pruebas automáticas: un cambio se prueba con `--help`, con la simulación de la suite sobre
una carpeta de prueba y, si es de una GUI, abriéndola y mirando la Consola integrada (comando,
stdout, stderr, código de salida).

## Detalles que cuesta redescubrir

- **Nombres que despistan**: la GUI de archivos es `scripts_filesystem_studio/`, el árbol es
  `script_proyect_tree` (con esa grafía), las herramientas de hard links son
  `scripts_filesystem_studio/backend/script_hardlinks-{creator,detector}/`, y el PDF vive en
  `scripts_document_studio/backends/` (`docs/decisiones.md` §1.2).
- **`script_proyect_tree` escribe `estructura.txt`**, derivado que la normativa no admite en un
  repo (§15.8, D07; `docs/decisiones.md` §1.3). Se usa para la vista previa de la GUI, `--list`,
  `--stats` o formatos `md`/`json` fuera de git. Su `config.sh` fija por nombre los grupos de
  proyectos (`pub_*`, `scripts_*`, `CampusTeX-*`, `website-achalma`) y `EXTRA_PROJECTS`.
- **`script_backup_suite/main.sh` necesita `TERM` incluso para `--help`**: empieza con `clear`
  bajo `set -e`, y sin terminal sale 1. Su simulación es `--simulate`, no `--dry-run` (opción
  desconocida: sale 2), y los perfiles son `home`, `docs`, `full` y `custom`.
- **`script_hardlinks-creator` compara por SHA-256 y solo enlaza contenido idéntico**;
  `_extensions/` está excluida a propósito (los `_metadata.yml` de extensiones Quarto difieren por
  diseño). Su reporte lo consume `script_hardlinks-detector --report`.
- **`script_git_sync_respos` no tiene `main.sh`**: sus entradas son `sync.sh` y `status.sh`, y su
  parser de `repos-config.yml` es ligero (dos espacios antes de `- name`, cuatro en
  `branch`/`enabled`; sin comillas, sin anidación y **sin comentarios en la línea de una entrada**:
  el comentario pasa a formar parte del nombre). Su `install.sh` no deja una copia que funcione.
- **`script_sync_usb` está atada al archivo documental del SGDP** (`docs/decisiones.md` §3.2):
  sincroniza una carpeta `SGDP`, gana el más nuevo con papelera .sgdp-papelera/, conserva ambos en
  conflicto, mueve a la papelera los PDF gemelos de nombre antiguo y pide una clave fija en el código
  (`SGDP_USB_CLAVE` la evita; `--si` omite la confirmación). Nunca escribas la clave en un documento.
- **`script_dni_a_copia/config.py` trae por defecto las rutas de un DNI real** en un repo público
  (pendiente en `docs/decisiones.md`): no copies ese número a ningún README. Las entradas son
  `--front`/`--back`, no posicionales; `--pre-cropped` es obligatorio con DNIe o escaneos planos.
- **`script_video_downloader --clip` no usa `--download-sections`** de yt-dlp (trunca DASH): corta
  con ffmpeg desde las URL crudas y verifica con ffprobe (`docs/decisiones.md` §3.1). El modo audio
  es `-m audio`, no `--audio`. En `script_video_downloader/lib/options.sh` las funciones terminan
  con `return 0` y los contadores son `var=$((var + 1))` por `set -e`.
- **`vendor/transcribir_whisper_jason_boog.py`** es el cuaderno Colab original (MIT) del
  transcriptor: se conserva como referencia y no se edita.

## Dónde está cada cosa

| pregunta | documento |
|---|---|
| qué suites hay, cómo se invocan, qué escribe cada una | `README.md` y el bloque generado `suites:` |
| por qué el repo es así; qué queda pendiente | `docs/decisiones.md` (mapa por lector en `docs/README.md`) |
| de dónde salieron las dos GUI y qué no se construyó | `docs/decisiones.md` §1.5 y §2.4 |
| quién usa estas herramientas desde otros proyectos | `docs/README.md` §Consumidores |
| módulos y cómo extender cada GUI | `scripts_filesystem_studio/README.md`, `scripts_git_studio/README.md` |
| manual de una herramienta absorbida | `scripts_*_studio/backend/<herramienta>/README.md` |
| manual de una suite de primer nivel | `<suite>/README.md` |
| el contrato de suite, el patrón y los bloques generados | `core/suite.schema.yml`, `core/README.md` |
| las suites de este repo entre las del workspace | `meta/INDICE_SCRIPTS.md` (generado) |
| normativa de archivos, cabeceras y documentación | `meta/docs/historial/NORMATIVA_ARCHIVOS.md` (§6, §9, §15) |
