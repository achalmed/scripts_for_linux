---
tipo: estado
estado: activo
actualizado: 2026-10-27
---
# estado.md — scripts-linux (repo `scripts_for_linux`)

Lo primero que se lee y lo último que se escribe en cada sesión (regla 10 de la guía raíz). Lo decidido vive en
`docs/decisiones.md`; lo pendiente, aquí, en §Por hacer, con fecha y dueño. El remoto es **público**: nada personal
ni del despacho en esta página.

## Hecho

| fecha | qué | dónde se ve |
|---|---|---|
| 2026-10-27 | **`script_alerta_ram`**: aviso sonoro que escala en volumen e insistencia desde el 90 % de RAM y, desde el 95 %, ventana con las apps abiertas para cerrarlas; servicio systemd de usuario (`main.sh instalar --aplicar`) | `script_alerta_ram/README.md`; `docs/decisiones.md` §3.5; `tests/run.sh -k alerta_ram` (4) |
| 2026-10-27 | **Las herramientas de archivos y de git salen con su GUI** (sesión 9 de la cola de la auditoría posterior): `git rm` de las siete, que viven con su historia en `filesystem-studio` y `git-studio`; sus pendientes (N-03, N-05–N-10, N-13, N-15 y los de cada herramienta) se fueron con ellas | `docs/decisiones.md` §2.6; `tests/run.sh` (44, 2 omitidas) |
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

Registro de tiempo (`script_registro_tiempo`, borrador desde el 2026-10-25):

- 2026-10-25 · dueño: el autor · **primera prueba real del plugin dentro de Super Productivity**: las pruebas lo corren contra un PluginAPI simulado (`tests/plugin_registro_tiempo.test.mjs`) y la API REST se leyó en el código de SP 18.10, pero no se ejercitó con la aplicación abierta. Con SP abierto: `main.py plugin --aplicar`, subir el .zip, `main.py recoger --aplicar` y comprobar en el panel que «Importar ahora» crea las tareas de «Registro automático»; si algo falla, el mensaje del panel o de la consola de SP va aquí.
- 2026-10-25 · dueño: el autor · instalar ActivityWatch con `awatcher` (KDE Wayland) y aw-watcher-web en Zen: sin ellos no hay tiempo de pantalla (Zen borra su historial al cerrar). Instalar `main.py timer --aplicar` después.
- 2026-10-25 · dueño: el autor · `planificar` no crea etiquetas ni proyectos (la API REST no puede): si se quiere, que el plugin los cree al recibir un plan; hoy los crea solo desde `estructura_sp`.


Herramientas:

- 2026-10-04 · dueño: el autor · N-04: `sincronizar_usb.bat` llama a un archivo que no existe; debe invocar `main.py`.
- 2026-10-04 · dueño: el autor · N-11: en `scripts_photo_metadata_suite` no todo se deshace: `embed-date` y `sync-digikam` escriben con `-overwrite_original` sin registro; `fix-names` no tiene `undo`.
- 2026-10-04 · dueño: el autor · `script_sync_usb` pide la clave aun con `--dry-run`, y en simulación anuncia PDF «apartados» que no mueve.
- 2026-10-04 · dueño: el autor · N-12: `script_video_downloader` crea su carpeta de archivo aun con `--simulate`.
- 2026-10-06 · dueño: el autor · `video_downloader --simulate` y `photo_metadata sync-digikam` quedan sin probar (red y base de digiKam).
- 2026-10-04 · dueño: el autor · `scripts_photo_metadata_suite` carga Pillow y numpy en todos los subcomandos, y `fix-names` exige `exiftool` aunque solo renombre.
- 2026-10-04 · dueño: orquestador DOC10 · manifiestos desfasados: varios `suite.yml` dicen cosas que el código no hace (resumen, `simula_por_defecto`, `escribe_en`, `depende_de`, `nota:` con historia); su corrección regenera bloques de README y `meta/INDICE_SCRIPTS.md`, y la hace la regeneración global.

## Futuro

- Las carpetas de herramientas siguen en snake_case (`script_<nombre>`), fuera del kebab-case de la normativa 2.3 (aviso RQ-IDN-03); renombrarlas es un cambio estructural (regla 4 de la guía raíz) que rompe las citas de otros proyectos y se haría en una ola propia.
