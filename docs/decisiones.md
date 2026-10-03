---
tipo: decision
titulo: "Decisiones de scripts_for_linux"
estado: activo
---
# Decisiones de scripts_for_linux

Por qué el repo es como es. Una entrada por decisión, con su fecha y el commit o la fase que la
aplicó; lo vigente que resulta de cada una está en `../README.md`, `../CLAUDE.md` y el README de
cada herramienta. Las entradas no se renumeran: se añaden al final de su sección.

## 1. Forma del repo

**1.1 Una suite por carpeta, con el patrón `main` + `config` + `lib`** (2026-07-05, `7dd4326`;
contrato común 2026-09-07, FS1–FS3). Cada herramienta es autónoma y declara su manifiesto en
`suite.yml` (`core/suite.schema.yml`); la raíz del workspace y el logger salen de `core/`
(`core/env.sh`, `core/env.py`, `core/shell-lib`, `core/py-common`). Los bloques `suite:` y
`suites:` de los README los escribe `core/suites.py generar --aplicar` desde los `suite.yml`.

**1.2 PDF y ofimática fuera de este repo** (2026-07-13, `756aa73`). `script_pdf-suite` y el
contador de páginas salieron de aquí; hoy son `scripts_document_studio/backends/pdf-suite/` y
`scripts_document_studio/backends/page-counter/`.

**1.3 Sin derivados de árbol en git** (2026-09-20, DOC2). `estructura.txt`, que escribe
`script_proyect_tree`, es un derivado que `meta/NORMATIVA_ARCHIVOS.md` §15.8 (D07) no admite
dentro de un repo: se retiró del árbol versionado y queda ignorado por `.gitignore`. La
herramienta sigue sirviendo para la vista previa de Filesystem Studio, `--list`, `--stats` y
salidas fuera de git.

**1.4 Las visiones de producto son historia, no pendientes** (trasladadas del vault el
2026-09-20, DOC8/D15; a `historial/` el 2026-10-03). Las tres visiones de Backup Studio,
Filesystem Studio y Git Studio describen productos mucho mayores que lo construido (motor de
respaldo con cifrado y restauración, base de datos y modo vigilancia, gestor de cientos de
repos con analítica y releases); el código no implementa esas partes y nadie las tiene
asignadas. Se conservan en `historial/` como el origen de las dos GUI; lo vigente de cada
herramienta es su README.

## 2. Las dos GUI

**2.1 Siete scripts sueltos pasan a ser backends de dos GUI PySide6** (Filesystem Studio el
2026-07-13, `756aa73`; Git Studio el mismo día, `5ad12ec`). Los scripts se conservan intactos en
`backend/` de cada GUI, con su `suite.yml` y su README, y siguen siendo CLI.

**2.2 La GUI porta, no envuelve** (2026-07-13). Para tener progreso, cancelación y datos
estructurados, los servicios de la carpeta app/services/ de cada GUI reescriben en Python la lógica
de los backends. Hay dos excepciones en Filesystem Studio: la creación de hard links importa la
`lib/` de `script_hardlinks-creator`, y el árbol en modo «proyectos» ejecuta el `main.sh` de
`script_proyect_tree`. Consecuencia: un cambio de comportamiento se hace en el backend y en el
servicio que lo porta.

**2.3 Un solo registro de repos** (2026-07-13). `repos-config.yml` de
`scripts_git_studio/backend/script_git_sync_respos/` lo leen `sync.sh`, `status.sh` y la GUI
(`scripts_git_studio/app/services/config_service.py`), y la GUI lo escribe al añadir o clonar. Las
áreas `Academic_Class-*` se sustituyeron por `10 Class/docencia` el 2026-09-15 (`e7ce35b`, M6).

## 3. Herramientas concretas

**3.1 `--clip` corta con ffmpeg, no con `--download-sections`** (2026-07-25, `90fb4ad`). La
opción de yt-dlp trunca los formatos DASH; `script_video_downloader` corta desde las URL crudas
y verifica con ffprobe.

**3.2 `script_sync_usb` se acepta fuera del patrón** (2026-09-15, `b39900b`, M10 D2). Vino de
`05_sgdp/sincronizacion_usb` como un solo `main.py` con lanzadores `.sh` y `.bat`; se incorporó
sin `config` ni `lib/` (patrón `M··`, que `core/suites.py validar` marca como aviso).

**3.3 El destino del log se llama `RUTA_LOG`, no `LOG_FILE`** (2026-10-03). `script_backup_suite` y
`script_video_downloader` asignaban `LOG_FILE` en su `config.sh`, y ese nombre es del logger de
`core/` (`core/docs/logger.md`): cada mensaje se copiaba al log de la suite en el directorio
personal (`backup_suite.log`, `video_downloader.log`) aunque `--log` estuviera apagado. Ahora `config.sh` declara `RUTA_LOG`, y
`logger_init` solo asigna `LOG_FILE` con `--log` (y lo vacía sin él, aunque venga del entorno).

**3.4 `HOME_DIR` sale de `core/env.sh`** (2026-10-03). Los `config.sh` de `script_backup_suite` y
`script_video_downloader` escribían `HOME_DIR="/home/${USUARIO}"` (y un usuario de respaldo a mano),
contra la regla 5 del `CLAUDE.md` raíz. Ahora cargan `core/env.sh` y usan la carpeta madre de
`DOCS_ROOT`, que `env.sh` resuelve por la ubicación del script y no por `$HOME`: con `sudo` sigue
siendo el directorio personal de quien invoca. `USUARIO` cae en `id -un`.

## Pendientes

- **Datos personales en un repo público** (anotado 2026-10-03; dueño: el autor). El remoto es
  público (`meta/workspace.yml`) y `script_dni_a_copia/config.py` y `script_dni_a_copia/lib/cli.py`
  llevan el número y las rutas de un DNI real como valores por defecto. Retirarlos exige cambiar el
  código y, si se quiere borrar del historial, reescribirlo: decisión del autor.
- **Clave de autorización en el código** (anotado 2026-10-03; dueño: el autor).
  `script_sync_usb/main.py` fija la clave en una constante; `SGDP_USB_CLAVE` solo la evita en
  modo no interactivo.
