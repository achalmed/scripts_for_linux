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
coincide con él: ver §Pendientes. Las áreas `Academic_Class-*` se sustituyeron por `10 Class/docencia` el
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

## Pendientes

Cada entrada: fecha de anotación · dueño · qué decide o hace falta. Los códigos `N-NN` remiten al
diagnóstico DOC10 (2026-10-04) del ecosistema.

### Prioritarios (seguridad y datos personales)

- **Clave de autorización publicada** (anotado 2026-10-03; ampliado 2026-10-04 · dueño: el autor).
  `script_sync_usb/main.py` fija la clave en una constante (y la repite en un comentario); `SGDP_USB_CLAVE`
  solo la evita en modo no interactivo. Estuvo también en su README hasta el 2026-10-04, y el historial
  público de git la conserva: hay que rotarla, sacarla del código (variable de entorno o archivo local
  ignorado) y decidir si se reescribe la historia.
- **Nombres de personas de un cliente en el código** (N-01; anotado 2026-10-04 · dueño: el autor).
  `script_sync_usb/main.py` lleva en comentarios y mensajes nombres de personas del despacho, contra la
  regla 8 del `CLAUDE.md` raíz; el doctor (D12) no lo detecta. Retirarlos del código y, si se quiere,
  de la historia.
- **Datos personales en un repo público** (anotado 2026-10-03 · dueño: el autor). El remoto es público y
  `script_dni_a_copia/config.py` y `script_dni_a_copia/lib/cli.py` llevan el número y las rutas de un DNI
  real como valores por defecto. Retirarlos exige cambiar el código y, si se quiere borrar del historial,
  reescribirlo.
- **Correo del autor como constante** (N-15; 2026-10-04 · el autor). `scripts_filesystem_studio/backend/script_hardlinks-creator/config.py`
  y `scripts_filesystem_studio/backend/script_hardlinks-detector/config.sh`; no es secreto, pero no hace falta en el código.

### Registro de repos de Git Studio

- **¿Se genera `repos-config.yml` desde `meta/workspace.yml` o se acepta como registro propio?**
  (2026-10-04 · el autor). Hoy es un inventario a mano que no recoge buena parte de los repos del
  workspace e incluye uno deprecado (`scripts_for_zotero`).
- **Un comentario en la misma línea rompe una entrada** (N-03; 2026-10-04 · el autor). La entrada
  `10 Class/docencia` lleva un comentario tras el nombre; ni el `awk` de `scripts_git_studio/backend/script_git_sync_respos/lib/config.sh` ni
  `config_service.py` lo quitan, y ese repo no se encuentra en `sync.sh`, `status.sh` ni la GUI.
- **`config_service.save()` reescribe el archivo entero** (N-08; 2026-10-04 · el autor): pierde los
  comentarios y cada alta desde la GUI deja un cambio en este repo.
- **`install.sh` no produce una instalación que funcione** (N-05; 2026-10-04 · el autor): la copia en
  ~/bin/git-sync no encuentra `core/`, solo detecta repos de primer nivel, siempre elige bash y escribe
  alias en el rc del shell (terreno de `~/.dotfiles`).
- **`sync.sh` no ve archivos nuevos sin seguimiento** (N-06; 2026-10-04 · el autor): `scripts_git_studio/backend/script_git_sync_respos/lib/git_ops.sh`
  usa `git diff-index HEAD`; la GUI (`git_service.py`) sí los ve. Las dos implementaciones divergen.
- **Repos privados y token** (N-07; 2026-10-04 · el autor): `scripts_git_studio/backend/script_git_download_respos/lib/github_api.sh` y `github_service.py`
  consultan `users/<usuario>/repos`, que solo lista repos públicos; `-t` deja el token visible en `ps`.
- **`--init-config` no existe** (N-13; 2026-10-04 · el autor): el mensaje de
  `scripts_git_studio/backend/script_git_sync_respos/lib/config.sh` lo aconseja.

### Herramientas

- **`sincronizar_usb.bat` llama a un archivo que no existe** (N-04; 2026-10-04 · el autor): debe invocar
  `main.py`.
- **Rutas que no pasan por `core/env.sh` / `core/env.py`** (N-09; 2026-10-04 · el autor): `scripts_filesystem_studio/backend/script_count_files_by_extension/config.sh`,
  `scripts_filesystem_studio/backend/script_proyect_tree/config.sh`, `scripts_filesystem_studio/backend/script_hardlinks-creator/config.py`, `script_dni_a_copia/config.py`
  (`PERSONAL_DIR`), `repos-config.yml` (`base_directory`) y `scripts_git_studio/app/utils/paths.py`.
- **Listas con nombres de carpeta que ya no existen** (N-10; 2026-10-04 · el autor): los grupos `pub_*` y
  `CampusTeX-*` de `scripts_filesystem_studio/backend/script_proyect_tree/config.sh` (los pubs viven en `04 index/_pubs`), las exclusiones
  `website-achalma` de `scripts_filesystem_studio/backend/script_hardlinks-creator/config.py` y la lista por defecto de
  `scripts_filesystem_studio/backend/script_create_folders_batch/config.sh`.
- **`scripts_photo_metadata_suite` no todo se deshace** (N-11; 2026-10-04 · el autor): `apply` sin
  `--execute` reescribe `rename_plan.csv`; `embed-date` y `sync-digikam` escriben con
  `-overwrite_original` sin registro; `fix-names` no tiene `undo`.
- **`script_backup_suite` se detiene con el primer contador a cero** (2026-10-04 · el autor, prioritario
  para quien lo automatice): bajo `set -e`, `(( x++ ))` con valor 0 devuelve 1, y está en
  `script_backup_suite/lib/validator.sh` y `script_backup_suite/lib/processor.sh`; la primera carpeta inexistente o el primer archivo omitido,
  actualizado o borrado cortan el respaldo sin resumen. La misma trampa ya se corrigió en
  `script_video_downloader` (`var=$((var + 1))`). Además `script_backup_suite/lib/analyzer.sh` corta en el espacio las rutas
  de los archivos modificados, y el perfil `custom` exige igualmente el disco de `DISK_LABEL`.
- **`script_sync_usb` pide la clave aun con `--dry-run`** (2026-10-04 · el autor), y en simulación anuncia
  PDF «apartados» que no mueve.
- **Errores de rsync ignorados** (N-12; 2026-10-04 · el autor): las copias de `script_backup_suite` llevan
  `|| true` sin distinguir el código de salida; `script_video_downloader` crea su carpeta de archivo aun
  con `--simulate`.
- **La ayuda de `script_dni_a_copia` dice 600 dpi** (N-14; 2026-10-04 · el autor); el valor es el de
  `config.py`.
- **Filesystem Studio** (N-16; 2026-10-04 · el autor): el reporte de Hardlinks se genera en el hilo de la
  interfaz, y la preferencia «hilos» se guarda sin que nada la use.
- **Hard links: exclusiones y confirmación** (2026-10-04 · el autor): `script_hardlinks-creator` toma
  las exclusiones como rutas relativas a la raíz de búsqueda (`_extensions/`, `_site/` y `.git/` solo se
  excluyen en el primer nivel; la GUI hereda lo mismo) y su confirmación por lote acepta por defecto y
  sin preguntar si la entrada se cierra.
- **`script_hardlinks-detector`** (2026-10-04 · el autor): `DEFAULT_FORMAT` de `config.sh` no tiene
  efecto (la CLI fija `tree`), CSV y JSON no escapan las rutas, los mensajes salen por la salida estándar
  y el conteo de enlaces lo da `stat` para todo el disco, no solo para el árbol.
- **`script_create_folders_batch` crea la carpeta base al simular** (2026-10-04 · el autor): con `-d` y
  un `-p` inexistente, `mkdir -p` la crea.
- **`script_proyect_tree` escribe `estructura.md`/`.json` sin que nada los ignore** (2026-10-04 · el
  autor): solo `estructura.txt` está en `.gitignore`; sin `--target` escribe en la carpeta actual.
- **Git: repos con `.git` en archivo y simulación de clonado** (2026-10-04 · el autor): `scripts_git_studio/backend/script_git_sync_respos/lib/git_ops.sh`
  y `git_service.py` exigen que `.git` sea una carpeta (un worktree o un submódulo con el gitdir fuera se
  rechaza); `script_git_download_respos -n` crea la carpeta destino y consulta la API, y `-m single`
  toma una lista como un solo nombre.
- **`scripts_photo_metadata_suite` carga Pillow y numpy en todos los subcomandos** (2026-10-04 · el
  autor), y `fix-names` exige `exiftool` aunque solo renombre.
- **Manifiestos desfasados** (2026-10-04 · orquestador DOC10): varios `suite.yml` dicen cosas que el código
  no hace (resumen, `simula_por_defecto`, `escribe_en`, `depende_de`, `nota:` con historia); su
  corrección regenera bloques de README y `meta/INDICE_SCRIPTS.md`, y la hace la regeneración global.
