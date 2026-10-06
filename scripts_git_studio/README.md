---
tipo: readme
estado: activo
---
# scripts_git_studio/ — Git Studio, aplicación de escritorio para ver el estado, sincronizar y clonar los repos de su registro
<!-- suite:inicio -->
**Suite `git_studio`** · objetivo *sistema* · estado *activo* · python · interfaz gui

Aplicación de escritorio (PySide6) para administrar los repositorios del workspace: estado, sincronización, clonado y reportes (repos-config.yml).

- Escribe en: git · simula por defecto: no
- Depende de: PySide6, git

Comandos:

```bash
main.py
main.py --smoke
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Aplicación PySide6 con cinco páginas (Dashboard, Repositorios, Sincronizar, Clonar y Reportes), una consola
acoplada y un diálogo de preferencias. Trabaja sobre los repos que lista
`backend/script_git_sync_respos/repos-config.yml`, el inventario propio de Git Studio (ver Límite honesto), y
porta a Python la lógica de sus dos backends de terminal, que siguen funcionando por su cuenta:
[`backend/script_git_sync_respos/`](backend/script_git_sync_respos/README.md) (sincronizar y estado) y
[`backend/script_git_download_respos/`](backend/script_git_download_respos/README.md) (clonar desde GitHub).

Qué escribe y dónde:

- **En los repos**: Sincronizar hace `git pull`, `git add -A`, `git commit` y `git push` de verdad; Clonar crea
  una carpeta por repo en el destino elegido y, con «snapshot», le borra `.git`.
- **En `backend/script_git_sync_respos/repos-config.yml`**: lo reescribe entero al añadir, quitar o habilitar un
  repo, al cambiar la carpeta base y al registrar los repos recién clonados.
- **Reportes** Markdown o CSV, por defecto en la carpeta `reports` de esta herramienta (se crea al generar el
  primero; git la ignora; se cambia en Preferencias).
- **Preferencias e historial** de operaciones y reportes en QSettings del usuario (aplicación `GitStudio`).
  El token de GitHub no se guarda: se lee de `GITHUB_TOKEN` o del campo de la página Clonar, por sesión.

No simula por defecto. Las vistas previas son la casilla «solo verificar» de Sincronizar (equivale a
`backend/script_git_sync_respos/sync.sh --check`), la tabla de Repositorios y la casilla «dry-run» de
Clonar. No gestiona ramas, etiquetas ni remotos: si la rama activa no es la del registro, sincroniza la
activa y lo avisa, sin `checkout`.

## Uso

```bash
python3 main.py            # abre la aplicación
python3 main.py --smoke    # construye la interfaz y sale (prueba de humo)
```

| opción | qué hace |
|---|---|
| `--smoke` | construye la ventana y sale en cuanto arranca el bucle de eventos |

Requisitos: Python ≥ 3.10, PySide6 y `git`. Los backends no necesitan PySide6.

| página | qué hace | controller | service |
|---|---|---|---|
| Dashboard | resumen del último análisis de estado, repos que necesitan atención, operaciones recientes | `app/controllers/dashboard_controller.py` | `app/services/history_service.py` |
| Repositorios | tabla de estado (con `git fetch` opcional); alta, baja y habilitación de repos; carpeta base; abrir la carpeta; pasar la selección a Sincronizar | `app/controllers/repos_controller.py` | `app/services/status_service.py`, `app/services/config_service.py` |
| Sincronizar | pull → add → commit → push sobre los repos marcados; «solo verificar» y «sin pull»; un botón ejecuta sync.sh con las mismas opciones y muestra su salida en la consola | `app/controllers/sync_controller.py` | `app/services/sync_service.py` |
| Clonar | lista los repos de un usuario de GitHub y clona los marcados con profundidad, protocolo, rama, exclusiones, forks, snapshot sin `.git` y dry-run; registra los clonados | `app/controllers/clone_controller.py` | `app/services/github_service.py`, `app/services/clone_service.py` |
| Reportes | genera el reporte de estado en Markdown o CSV, lista los generados, los abre o los borra | `app/controllers/reports_controller.py` | `app/services/report_service.py` |

Preferencias (menú): usuario de GitHub, protocolo y profundidad por defecto, días de actividad, formato y
carpeta de reportes, `fetch` antes del estado, tema y tamaño de iconos.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | crea la `QApplication`, aplica el tema guardado y abre la ventana |
| `app/main_window.py` | barra lateral, pila de páginas, consola acoplada, menús y registro de workers activos |
| `app/context.py` | `AppContext`: servicios compartidos, navegación y último análisis de estado |
| `app/controllers/base.py` | clase base de los controladores de página |
| `app/controllers/` (resto) | un controlador por página (tabla de Uso) |
| `app/dialogs/preferences_dialog.py` | diálogo de preferencias sobre `app/ui/dialog_preferences.ui` |
| `app/models/repo_status_model.py` | modelo de tabla del estado de los repos, con el color por estado |
| `app/services/git_service.py` | única implementación de comandos git de la aplicación |
| `app/services/config_service.py` | lee y reescribe repos-config.yml con el formato que entiende el parser Bash |
| `app/services/status_service.py` | estado por repo (cambios, ahead/behind con `fetch` previo) y actividad reciente |
| `app/services/sync_service.py` | motor de sincronización, port de `backend/script_git_sync_respos/lib/sync_engine.sh` |
| `app/services/clone_service.py` | clonado, exclusiones, forks, snapshot y dry-run, port de `backend/script_git_download_respos/lib/cloner.sh` |
| `app/services/github_service.py` | lista paginada de repos por la API de GitHub, con `urllib` |
| `app/services/report_service.py` | escribe el reporte en Markdown o CSV |
| `app/services/settings_service.py` | preferencias en QSettings |
| `app/services/history_service.py` | historial de operaciones y reportes en QSettings |
| `app/workers/function_worker.py` | hilo para funciones Python, con progreso y cancelación |
| `app/workers/process_worker.py` | hilo para procesos externos (sync.sh), con su salida en la consola |
| `app/widgets/console_dock.py` | consola, registro y barra de progreso con cancelar |
| `app/utils/paths.py` | rutas del proyecto, incluida la de repos-config.yml |
| `app/utils/ui_loader.py` | carga de las vistas de `app/ui/` en tiempo de ejecución |
| `app/utils/theming.py` | temas QSS oscuro, claro y del sistema |
| `app/utils/icons.py` | iconos SVG de `resources/icons/` (o los compilados con pyside6-rcc, si se generan) |
| `app/utils/format.py` | formato de fechas, tamaños y duraciones |
| `app/ui/` | vistas de Qt Designer: ventana, cuatro páginas y preferencias |
| `resources/icons/`, `resources/themes/` | iconos SVG y hojas QSS |
| `backend/script_git_sync_respos/` | suite de terminal sync.sh y status.sh, dueña de repos-config.yml |
| `backend/script_git_download_respos/` | suite de terminal de clonado desde GitHub |
| `suite.yml` | manifiesto de la suite (genera el bloque de arriba) |

## Límite honesto

- **El registro (repos-config.yml) es el inventario propio de Git Studio, no el del workspace.** Lo leen
  sync.sh, status.sh y la GUI; está escrito a mano, es paralelo al manifiesto del workspace
  (`meta/workspace.yml`, fuera de este repo) y no coincide con él. Si debe generarse desde allí está por
  decidir: ver `estado.md` §Por hacer.
- **La GUI reescribe el registro entero** cada vez que lo guarda: pierde los comentarios y deja un cambio en
  este repo (ver `estado.md` §Por hacer).
- **El parser del registro es estricto**: `- name:` con dos espacios delante, `branch:` y `enabled:` con
  cuatro, sin comillas ni anidación, y **sin comentarios en la misma línea de una entrada**: el comentario pasa
  a formar parte del nombre y ese repo no se encuentra. Hoy le ocurre a la entrada de «10 Class/docencia» (ver
  `estado.md` §Por hacer).
- **La GUI y sync.sh no detectan los cambios igual**: `app/services/git_service.py` usa
  `git status --porcelain` y ve los archivos nuevos sin seguimiento; sync.sh usa `git diff-index` y no los ve.
  El botón que ejecuta sync.sh puede dar «sin cambios» donde la página no.
- **Los servicios son ports, no los mismos módulos**: un cambio de comportamiento se hace en el backend y en
  el servicio que lo porta (`docs/decisiones.md` §2.2). `app/utils/`, `app/workers/` y `app/widgets/` son copia
  de los de Filesystem Studio (§2.4).
- **Un repo se reconoce por una carpeta `.git`**: si `.git` es un archivo (worktree, submódulo con el gitdir
  fuera) se rechaza como «no es un repositorio Git».
- **Clonar solo habla con GitHub** y consulta `users/<usuario>/repos`, que lista los repos públicos; no está
  verificado contra la API si un token cambia eso. El usuario por defecto está escrito en
  `app/services/settings_service.py` y se cambia en la página o en Preferencias. Los clonados solo se registran
  si el destino coincide con `base_directory`.
- **Abrir carpeta y abrir reporte llaman a `xdg-open`** desde el controlador; fuera de un escritorio Linux no
  funcionan. «Eliminar» en Reportes borra el archivo, no solo la entrada del historial.
- **Sin pruebas automáticas**: `--smoke` solo comprueba que la interfaz se construye.
