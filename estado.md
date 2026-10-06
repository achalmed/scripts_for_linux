---
tipo: estado
estado: activo
actualizado: 2026-10-06
---
# estado.md — scripts_for_linux (repo `scripts_for_linux`)

Lo primero que se lee y lo último que se escribe en cada sesión (regla 10 de la guía raíz). Lo decidido vive en
`docs/decisiones.md`; lo pendiente, aquí, en §Por hacer, con fecha y dueño. El remoto es **público**: nada personal
ni del despacho en esta página.

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-10-06 | ola 4, fase A (agente «linux»): L1–L3, un commit por ítem | la bitácora de abajo; `meta/programa/06-olas/ola-04-reingenieria.md` §2 |

Bitácora de la ola 4 (etiqueta previa: `antes-ola-04-2026-10-06`):

- 2026-10-06 · L1a · `estado.md`; los pendientes de `docs/decisiones.md` pasan a §Por hacer y las citas a `§Pendientes` de los README apuntan aquí.
- 2026-10-06 · L1b · `tests/test_simulacion.py` + `tests/run.sh`: las suites que escriben corren en simulación sobre un `HOME` temporal sin escribir nada (las de red, hardware o datos personales, solo `--help` o `skip`; `pruebas:` en su `suite.yml`); `git_download_respos -n` ya no crea la carpeta destino y `photo_metadata apply` sin `--execute` ya no reescribe el plan.

## En curso

nada en curso

## Por hacer

Prioritarios (seguridad y datos personales):

- 2026-10-06 · dueño: el autor · el historial público conserva un número de documento en `script_dni_a_copia` (commit 23e6d7b); reescribirlo (`git filter-repo`) lo decide el autor.
- 2026-10-04 · dueño: el autor · clave de autorización publicada: `script_sync_usb/main.py` ya no la lleva en el código (la lee de un archivo de configuración del usuario o de `SGDP_USB_CLAVE_ESPERADA`, y sin ellas se niega); falta escribir una clave **nueva** en cada máquina que sincroniza (la vieja se da por expuesta: el historial público la conserva) y decidir si se reescribe la historia.
- 2026-10-04 · dueño: el autor · N-01: `script_sync_usb/main.py` lleva en comentarios y mensajes nombres de personas del despacho (regla 8 de la guía raíz; el doctor D12 no lo detecta): retirarlos del código y, si se quiere, de la historia.
- 2026-10-04 · dueño: el autor · N-15: correo del autor como constante en `scripts_filesystem_studio/backend/script_hardlinks-creator/config.py` y `scripts_filesystem_studio/backend/script_hardlinks-detector/config.sh`; no es secreto, pero no hace falta en el código.

Registro de repos de Git Studio:

- 2026-10-04 · dueño: el autor · ¿se genera `repos-config.yml` desde `meta/workspace.yml` o se acepta como registro propio? Hoy es un inventario a mano que no recoge buena parte de los repos del workspace e incluye uno deprecado (`scripts_for_zotero`).
- 2026-10-04 · dueño: el autor · N-03: un comentario en la misma línea rompe una entrada (`10 Class/docencia`): ni el `awk` de `scripts_git_studio/backend/script_git_sync_respos/lib/config.sh` ni `config_service.py` lo quitan, y ese repo no se encuentra en `sync.sh`, `status.sh` ni la GUI.
- 2026-10-04 · dueño: el autor · N-08: `config_service.save()` reescribe el archivo entero: pierde los comentarios y cada alta desde la GUI deja un cambio en este repo.
- 2026-10-04 · dueño: el autor · N-05: `install.sh` no produce una instalación que funcione (la copia en `~/bin` no encuentra `core/`, solo detecta repos de primer nivel, siempre elige bash y escribe alias en el rc del shell, terreno de `~/.dotfiles`).
- 2026-10-04 · dueño: el autor · N-06: `sync.sh` no ve archivos nuevos sin seguimiento (`lib/git_ops.sh` usa `git diff-index HEAD`); la GUI (`git_service.py`) sí los ve: las dos implementaciones divergen.
- 2026-10-04 · dueño: el autor · N-07: `script_git_download_respos/lib/github_api.sh` y `github_service.py` consultan `users/<usuario>/repos`, que solo lista repos públicos; `-t` deja el token visible en `ps`.
- 2026-10-04 · dueño: el autor · N-13: `--init-config` no existe, y el mensaje de `script_git_sync_respos/lib/config.sh` lo aconseja.

Herramientas:

- 2026-10-04 · dueño: el autor · N-04: `sincronizar_usb.bat` llama a un archivo que no existe; debe invocar `main.py`.
- 2026-10-04 · dueño: el autor · N-09: rutas que no pasan por `core/env.sh` / `core/env.py`: `script_count_files_by_extension/config.sh`, `script_proyect_tree/config.sh`, `script_hardlinks-creator/config.py`, `script_dni_a_copia/config.py` (`PERSONAL_DIR`), `repos-config.yml` (`base_directory`) y `scripts_git_studio/app/utils/paths.py`.
- 2026-10-04 · dueño: el autor · N-10: listas con nombres de carpeta que ya no existen: los grupos `pub_*` y `CampusTeX-*` de `script_proyect_tree/config.sh` (los pubs viven en `04 index/_pubs`), las exclusiones `website-achalma` de `script_hardlinks-creator/config.py` y la lista por defecto de `script_create_folders_batch/config.sh`.
- 2026-10-04 · dueño: el autor · N-11: en `scripts_photo_metadata_suite` no todo se deshace: `embed-date` y `sync-digikam` escriben con `-overwrite_original` sin registro; `fix-names` no tiene `undo`.
- 2026-10-04 · dueño: el autor · `script_sync_usb` pide la clave aun con `--dry-run`, y en simulación anuncia PDF «apartados» que no mueve.
- 2026-10-04 · dueño: el autor · `script_backup_suite` se detiene con el primer contador a cero: bajo `set -e`, `(( x++ ))` con valor 0 devuelve 1 (`lib/validator.sh`, `lib/processor.sh`); además `lib/analyzer.sh` corta en el espacio las rutas de los archivos modificados, y el perfil `custom` exige igualmente el disco de `DISK_LABEL`.
- 2026-10-04 · dueño: el autor · N-12: las copias de `script_backup_suite` llevan `|| true` sin distinguir el código de salida de rsync; `script_video_downloader` crea su carpeta de archivo aun con `--simulate`.
- 2026-10-04 · dueño: el autor · N-14: la ayuda de `script_dni_a_copia` dice 600 dpi; el valor es el de `config.py`.
- 2026-10-04 · dueño: el autor · N-16: en Filesystem Studio el reporte de Hardlinks se genera en el hilo de la interfaz, y la preferencia «hilos» se guarda sin que nada la use.
- 2026-10-04 · dueño: el autor · `script_hardlinks-creator` toma las exclusiones como rutas relativas a la raíz de búsqueda (`_extensions/`, `_site/` y `.git/` solo se excluyen en el primer nivel; la GUI hereda lo mismo) y su confirmación por lote acepta por defecto y sin preguntar si la entrada se cierra.
- 2026-10-04 · dueño: el autor · `script_hardlinks-detector`: `DEFAULT_FORMAT` de `config.sh` no tiene efecto (la CLI fija `tree`), CSV y JSON no escapan las rutas, los mensajes salen por la salida estándar y el conteo de enlaces lo da `stat` para todo el disco, no solo para el árbol.
- 2026-10-04 · dueño: el autor · `script_create_folders_batch` crea la carpeta base al simular: con `-d` y un `-p` inexistente, `mkdir -p` la crea (`tests/test_simulacion.py` lo fija como `xfail` estricto: al corregirlo, quitar la marca).
- 2026-10-06 · dueño: el autor · las dos GUI no tienen prueba automática (`--smoke` necesita pantalla o `QT_QPA_PLATFORM=offscreen` y escribe preferencias en `~/.config`); `video_downloader --simulate` y `photo_metadata sync-digikam` quedan sin probar (red y base de digiKam).
- 2026-10-04 · dueño: el autor · `script_proyect_tree` escribe `estructura.md`/`.json` sin que nada los ignore (solo `estructura.txt` está en `.gitignore`); sin `--target` escribe en la carpeta actual.
- 2026-10-04 · dueño: el autor · `script_git_sync_respos/lib/git_ops.sh` y `git_service.py` exigen que `.git` sea una carpeta (un worktree o un submódulo con el gitdir fuera se rechaza); `script_git_download_respos -m single` toma una lista como un solo nombre.
- 2026-10-04 · dueño: el autor · `scripts_photo_metadata_suite` carga Pillow y numpy en todos los subcomandos, y `fix-names` exige `exiftool` aunque solo renombre.
- 2026-10-04 · dueño: orquestador DOC10 · manifiestos desfasados: varios `suite.yml` dicen cosas que el código no hace (resumen, `simula_por_defecto`, `escribe_en`, `depende_de`, `nota:` con historia); su corrección regenera bloques de README y `meta/INDICE_SCRIPTS.md`, y la hace la regeneración global.

## Futuro

- Las carpetas de herramientas siguen en snake_case (`script_<nombre>`), fuera del kebab-case de la normativa 2.3 (aviso RQ-IDN-03); renombrarlas es un cambio estructural (regla 4 de la guía raíz) que rompe las citas de otros proyectos y se haría en una ola propia.
