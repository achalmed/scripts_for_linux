---
tipo: estado
estado: activo
actualizado: 2026-10-06
---
# estado.md — scripts-linux (repo `scripts_for_linux`)

Lo primero que se lee y lo último que se escribe en cada sesión (regla 10 de la guía raíz). Lo decidido vive en
`docs/decisiones.md`; lo pendiente, aquí, en §Por hacer, con fecha y dueño. El remoto es **público**: nada personal
ni del despacho en esta página.

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-10-06 | ola 4, fase A (agente «linux»): L1–L3, un commit por ítem | la bitácora de abajo; `meta/programa/06-olas/ola-04-reingenieria.md` §2 |
| 2026-10-06 | ola 4, fase B (agente «studios»): las dos GUI salen al repo `gui-suites`; sus siete backends son suites de primer nivel | la bitácora de abajo; `docs/decisiones.md` §2.5 |

Bitácora de la ola 4 (etiqueta previa: `antes-ola-04-2026-10-06`):

- 2026-10-06 · L1a · `estado.md`; los pendientes de `docs/decisiones.md` pasan a §Por hacer y las citas a `§Pendientes` de los README apuntan aquí.
- 2026-10-06 · L1b · `tests/test_simulacion.py` + `tests/run.sh`: las suites que escriben corren en simulación sobre un `HOME` temporal sin escribir nada (las de red, hardware o datos personales, solo `--help` o `skip`; `pruebas:` en su `suite.yml`); `git_download_respos -n` ya no crea la carpeta destino y `photo_metadata apply` sin `--execute` ya no reescribe el plan.
- 2026-10-06 · L2 · `script_dni_a_copia` y `script_firma_digital` pasan con su historia a `herramientas-personales` (privado, sin remoto; `git subtree`) y salen de aquí con `git rm` (decisiones §1.7); ramas temporales del split borradas.
- 2026-10-06 · L3 · `script_backup_suite` sale del repo (`git rm`): la política de preservación tiene una sola herramienta, `meta/respaldos/bin/respaldar.sh` (copia 2 con papelera y verificación); `backup_suite` duplicaba `espejo` en otra carpeta del SSD y tenía el error `((failures++))` con `set -e` (P273/P275). Nada vivo la usaba (decisiones §1.8).

Bitácora de la fase B (etiqueta previa: `antes-ola-04-studios-2026-10-06`):

- 2026-10-06 · B1 · los backends de `scripts_filesystem_studio/backend/` y `scripts_git_studio/backend/` pasan a suites de primer nivel (`git mv`, con `repos-config.yml`, `archivos.txt` y `reports/` ignorados); cabeceras y README sin `backend/`; `tests/test_simulacion.py` los busca en la raíz.
- 2026-10-06 · B2 · las dos GUI salen con `git rm` tras copiarse con su historia (`git subtree`) a `gui-suites` (`filesystem/`, `git/`), donde sus pruebas pasan; los dos reportes viejos de `reports/` (ignorados) se movieron a `gui-suites/<studio>/reports/`. README, CLAUDE.md y `docs/` remiten a `gui-suites` (decisiones §2.5).

## En curso

nada en curso

## Por hacer

Prioritarios (seguridad y datos personales):

- 2026-10-06 · dueño: el autor · el historial público conserva un número de documento en `script_dni_a_copia` (commit 23e6d7b); reescribirlo (`git filter-repo`) lo decide el autor. La herramienta ya no está aquí: vive en `herramientas-personales` (privado), con sus pendientes.
- 2026-10-04 · dueño: el autor · clave de autorización publicada: `script_sync_usb/main.py` ya no la lleva en el código (la lee de un archivo de configuración del usuario o de `SGDP_USB_CLAVE_ESPERADA`, y sin ellas se niega); falta escribir una clave **nueva** en cada máquina que sincroniza (la vieja se da por expuesta: el historial público la conserva) y decidir si se reescribe la historia.
- 2026-10-04 · dueño: el autor · N-01: `script_sync_usb/main.py` lleva en comentarios y mensajes nombres de personas del despacho (regla 8 de la guía raíz; el doctor D12 no lo detecta): retirarlos del código y, si se quiere, de la historia.
- 2026-10-04 · dueño: el autor · N-15: correo del autor como constante en `script_hardlinks-creator/config.py` y `script_hardlinks-detector/config.sh`; no es secreto, pero no hace falta en el código.

Registro de repos de Git Studio:

- 2026-10-04 · dueño: el autor · ¿se genera `repos-config.yml` desde `meta/workspace.yml` o se acepta como registro propio? Hoy es un inventario a mano que no recoge buena parte de los repos del workspace e incluye uno deprecado (`scripts_for_zotero`).
- 2026-10-04 · dueño: el autor · N-03: un comentario en la misma línea rompe una entrada (`docencia/contenido`): ni el `awk` de `script_git_sync_respos/lib/config.sh` ni `config_service.py` (repo `gui-suites`) lo quitan, y ese repo no se encuentra en `sync.sh`, `status.sh` ni la GUI.
- 2026-10-04 · dueño: el autor · N-08: Git Studio reescribe `repos-config.yml` entero al guardar y cada alta deja un cambio en este repo; el pendiente vive en `gui-suites/estado.md` (es de la GUI).
- 2026-10-04 · dueño: el autor · N-05: `install.sh` no produce una instalación que funcione (la copia en `~/bin` no encuentra `core/`, solo detecta repos de primer nivel, siempre elige bash y escribe alias en el rc del shell, terreno de `~/.dotfiles`).
- 2026-10-04 · dueño: el autor · N-06: `sync.sh` no ve archivos nuevos sin seguimiento (`lib/git_ops.sh` usa `git diff-index HEAD`); Git Studio (repo `gui-suites`) sí los ve: las dos implementaciones divergen.
- 2026-10-04 · dueño: el autor · N-07: `script_git_download_respos/lib/github_api.sh` y el `github_service.py` de Git Studio consultan `users/<usuario>/repos`, que solo lista repos públicos; `-t` deja el token visible en `ps`.
- 2026-10-04 · dueño: el autor · N-13: `--init-config` no existe, y el mensaje de `script_git_sync_respos/lib/config.sh` lo aconseja.

Herramientas:

- 2026-10-04 · dueño: el autor · N-04: `sincronizar_usb.bat` llama a un archivo que no existe; debe invocar `main.py`.
- 2026-10-04 · dueño: el autor · N-09: rutas que no pasan por `core/env.sh` / `core/env.py`: `script_count_files_by_extension/config.sh`, `script_proyect_tree/config.sh`, `script_hardlinks-creator/config.py`, y `repos-config.yml` (`base_directory`). La GUI de Git Studio ya resuelve sus rutas por `core/env.py` (repo `gui-suites`).
- 2026-10-04 · dueño: el autor · N-10: listas con nombres de carpeta que ya no existen: los grupos `pub_*` y `CampusTeX-*` de `script_proyect_tree/config.sh` (los pubs viven en `04 index/_pubs`), las exclusiones `website-achalma` de `script_hardlinks-creator/config.py` y la lista por defecto de `script_create_folders_batch/config.sh`.
- 2026-10-04 · dueño: el autor · N-11: en `scripts_photo_metadata_suite` no todo se deshace: `embed-date` y `sync-digikam` escriben con `-overwrite_original` sin registro; `fix-names` no tiene `undo`.
- 2026-10-04 · dueño: el autor · `script_sync_usb` pide la clave aun con `--dry-run`, y en simulación anuncia PDF «apartados» que no mueve.
- 2026-10-04 · dueño: el autor · N-12: `script_video_downloader` crea su carpeta de archivo aun con `--simulate`.
- 2026-10-04 · dueño: el autor · `script_hardlinks-creator` toma las exclusiones como rutas relativas a la raíz de búsqueda (`_extensions/`, `_site/` y `.git/` solo se excluyen en el primer nivel; la GUI hereda lo mismo) y su confirmación por lote acepta por defecto y sin preguntar si la entrada se cierra.
- 2026-10-04 · dueño: el autor · `script_hardlinks-detector`: `DEFAULT_FORMAT` de `config.sh` no tiene efecto (la CLI fija `tree`), CSV y JSON no escapan las rutas, los mensajes salen por la salida estándar y el conteo de enlaces lo da `stat` para todo el disco, no solo para el árbol.
- 2026-10-04 · dueño: el autor · `script_create_folders_batch` crea la carpeta base al simular: con `-d` y un `-p` inexistente, `mkdir -p` la crea (`tests/test_simulacion.py` lo fija como `xfail` estricto: al corregirlo, quitar la marca).
- 2026-10-06 · dueño: el autor · `video_downloader --simulate` y `photo_metadata sync-digikam` quedan sin probar (red y base de digiKam). Las GUI tienen su prueba en `gui-suites` (`tests/run.sh`).
- 2026-10-04 · dueño: el autor · `script_proyect_tree` escribe `estructura.md`/`.json` sin que nada los ignore (solo `estructura.txt` está en `.gitignore`); sin `--target` escribe en la carpeta actual.
- 2026-10-04 · dueño: el autor · `script_git_sync_respos/lib/git_ops.sh` (y el `git_service.py` de Git Studio) exigen que `.git` sea una carpeta (un worktree o un submódulo con el gitdir fuera se rechaza); `script_git_download_respos -m single` toma una lista como un solo nombre.
- 2026-10-04 · dueño: el autor · `scripts_photo_metadata_suite` carga Pillow y numpy en todos los subcomandos, y `fix-names` exige `exiftool` aunque solo renombre.
- 2026-10-04 · dueño: orquestador DOC10 · manifiestos desfasados: varios `suite.yml` dicen cosas que el código no hace (resumen, `simula_por_defecto`, `escribe_en`, `depende_de`, `nota:` con historia); su corrección regenera bloques de README y `meta/INDICE_SCRIPTS.md`, y la hace la regeneración global.

## Futuro

- Las carpetas de herramientas siguen en snake_case (`script_<nombre>`), fuera del kebab-case de la normativa 2.3 (aviso RQ-IDN-03); renombrarlas es un cambio estructural (regla 4 de la guía raíz) que rompe las citas de otros proyectos y se haría en una ola propia.
