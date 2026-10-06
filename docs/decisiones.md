---
tipo: decision
titulo: "Decisiones de scripts_for_linux"
estado: activo
---
# Decisiones de scripts_for_linux

Por qué el repo es como es. Una entrada por decisión, con su fecha y el commit o la fase que la
aplicó; lo vigente que resulta de cada una está en `../README.md`, `../CLAUDE.md` y el README de
cada herramienta, y lo pendiente, en `../estado.md` §Por hacer. Las entradas no se renumeran: se añaden al final de su sección.

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
`script_proyect_tree`, es un derivado que `meta/docs/historial/NORMATIVA_ARCHIVOS.md` §15.8 (D07) no admite
dentro de un repo: se retiró del árbol versionado y queda ignorado por `.gitignore`. La
herramienta sigue sirviendo para la vista previa de Filesystem Studio, `--list`, `--stats` y
salidas fuera de git.

**1.4 Las visiones de producto son historia, no pendientes** (2026-09-20, DOC8/D15; a docs/historial/
el 2026-10-03). Superada por §1.5 (2026-10-04).

**1.5 Las visiones de producto se retiran del repo** (2026-10-04, DOC10). Las tres «visiones» de
Backup Studio, Filesystem Studio y Git Studio (notas del vault del 2026-07-13 y del 2026-07-20) eran la
transcripción de una conversación con un asistente, no una descripción del proyecto: se eliminan (git
conserva su historia) y queda aquí lo que de ellas sigue siendo cierto. Proponían un motor de respaldo con
versionado, cifrado, restauración y destinos remotos; un administrador de archivos con base de datos,
reglas y modo vigilancia, y un gestor de repositorios con analítica, doctor y publicación de versiones.
Nada de eso se construyó ni tiene dueño: lo construido es un respaldo rsync por perfiles
(`script_backup_suite/`) y las dos GUI que describen sus README. Las notas del vault
(`01 notes/proyecto-*-studio.md`) remiten a esta entrada.

**1.6 Forma única del README de una herramienta** (2026-10-04, DOC10). Cada suite, GUI o backend tiene
un README con `Qué es`, `Uso` (opciones sacadas del parser), `Estructura` y `Límite honesto`, y el
bloque `suite:` generado. El H1 no lleva versión: la versión es una constante del código y la imprime
`--version` donde existe. Lo que el código corrigió en el pasado está en el historial de git, no en el
README.

**1.7 Lo personal sale a un repo privado** (2026-10-06, ola 4, L2). `script_dni_a_copia` y
`script_firma_digital` trabajan con documentos y datos personales del autor, y este repo es público:
pasaron con su historia (`git subtree split` + `git subtree add` desde la ruta local) a
`herramientas-personales`, privado y sin remoto, y aquí se retiraron con `git rm`. El historial de este
repo sigue conservando un número de documento (`estado.md` §Por hacer).

**1.8 Sin herramienta de respaldo propia** (2026-10-06, ola 4, L3). `script_backup_suite` sale del repo
(`git rm`; el historial la conserva). La política de preservación tiene una sola herramienta:
`meta/respaldos/bin/respaldar.sh` (copia 2 con papelera y verificación). `script_backup_suite` duplicaba
`espejo` en otra carpeta del SSD y tenía el error `((failures++))` con `set -e` (P273/P275): el primer
contador a cero cortaba el respaldo sin resumen. Nada vivo la usaba (ni unidades systemd, ni
`~/.dotfiles`, ni otro proyecto). Las entradas 1.5, 3.3 y 3.4 que la citan quedan como historia.

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

**2.3 Un registro de repos propio de Git Studio** (2026-07-13; precisada el 2026-10-04). `repos-config.yml`
de `scripts_git_studio/backend/script_git_sync_respos/` lo leen `sync.sh`, `status.sh` y la GUI
(`scripts_git_studio/app/services/config_service.py`), y la GUI lo reescribe entero al añadir o clonar. Es
un inventario escrito a mano, paralelo a `meta/workspace.yml` (el manifiesto del workspace), y no
coincide con él: ver `../estado.md` §Por hacer. Las áreas `Academic_Class-*` se sustituyeron por `10 Class/docencia` el
2026-09-15 (`e7ce35b`, M6).

**2.4 Cada GUI lleva su propia infraestructura** (2026-10-04, al retirar las visiones). Las visiones
proponían un núcleo común a todas las GUI; no se hizo. Filesystem Studio y Git Studio llevan copias
idénticas del cargador de `.ui`, los temas, el formato, los *workers* y la consola integrada
(`scripts_filesystem_studio/app/utils/`, `scripts_filesystem_studio/app/workers/`,
`scripts_filesystem_studio/app/widgets/` y sus pares en `scripts_git_studio/app/`), y su
controller base casi igual. Consecuencia: un
arreglo en esa infraestructura se hace en las dos.

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
