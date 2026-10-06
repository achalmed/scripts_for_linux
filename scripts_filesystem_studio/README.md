---
tipo: readme
estado: activo
---
# scripts_filesystem_studio/ — Filesystem Studio, GUI PySide6 de las cinco herramientas de sistema de archivos de backend/
<!-- suite:inicio -->
**Suite `filesystem_studio`** · objetivo *sistema* · estado *activo* · python · interfaz gui

Aplicación de escritorio (PySide6) que reúne las herramientas de sistema de archivos: explorador, árbol de proyectos, estadísticas, creación de carpetas, hard links y reportes.

- Escribe en: archivos · simula por defecto: no
- Depende de: PySide6

Comandos:

```bash
main.py
main.py --smoke
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Aplicación de escritorio (PySide6 / Qt6) que reúne en siete páginas las cinco herramientas de sistema de archivos
de `backend/`, más un explorador, un tablero y un historial de reportes. No renombra ni limpia archivos: explora,
cuenta extensiones, genera árboles, crea carpetas en lote y detecta o crea hardlinks.

Qué escribe y dónde:

- **Reportes y exportaciones** (árboles, estadísticas, hardlinks): por defecto en `reports/` dentro de esta carpeta
  (preferencia «carpeta de reportes»); `reports/` no se versiona.
- **Preferencias, historial de operaciones y reportes, y el diario de deshacer de Carpetas**: en `~/.config/`
  (QSettings), no en el repositorio.
- **Carpetas** y **hardlinks** en el directorio que se elija, solo al pulsar la acción correspondiente.

Simulación: la página **Carpetas** **no** simula por defecto (la casilla «Simulación (dry-run)» viene desmarcada);
«Vista previa» solo planifica. El modo «Proyectos» de **Árbol** sí trae marcada la simulación. **Hardlinks → Crear**
trabaja en dos fases: planificar (no toca nada) y aplicar.

## Uso

```bash
python3 main.py            # abre la aplicación
python3 main.py --smoke    # construye la interfaz y sale (prueba de humo)
./tools/build_resources.sh # opcional: compila resources/resources.qrc a resources_rc.py
```

No hay más opciones de línea de órdenes; todo se configura en Archivo → Preferencias.

| página | backend que lanza o porta | qué hace |
|---|---|---|
| Dashboard | — | operaciones recientes, favoritas, últimos reportes, espacio en disco, accesos directos |
| Explorador | — | navegación, propiedades, copiar rutas, abrir con el gestor de archivos, «Usar en…» (envía la carpeta a otra página) |
| Árbol | `backend/script_proyect_tree` | vista previa y exportación txt, md o json con `tree`; el modo «Proyectos» ejecuta su `backend/script_proyect_tree/main.sh` |
| Estadísticas | `backend/script_count_files_by_extension` | escaneo recursivo, tabla ordenable y filtrable, gráfico de pastel (QtCharts), exportación CSV, Markdown o Excel |
| Carpetas | `backend/script_create_folders_batch` | lista manual o importada (TXT, CSV, Markdown), vista previa, simulación, deshacer |
| Hardlinks | `backend/script_hardlinks-detector` y `backend/script_hardlinks-creator` | pestañas Detectar, Crear y Reportes; la creación usa el enlace atómico del creador |
| Reportes | — | historial de todo lo generado; abre el archivo o su carpeta |

La **Consola** es un panel inferior acoplable (Ver → Consola): muestra el comando, la salida de los procesos,
el progreso y un botón Cancelar.

Preferencias (Archivo → Preferencias): rutas favoritas (por defecto, la raíz del espacio de trabajo), exclusiones
comunes a todas las páginas, profundidad (6), formato de exportación (csv), idioma, tema (oscuro, claro o sistema),
tamaño de iconos, hilos, carpeta de reportes y carpeta temporal.

Requisitos: Python 3.10 o superior, `PySide6>=6.5` (QtCharts viene en PySide6-Addons), `openpyxl` solo para exportar a
Excel (`requirements.txt`), el binario `tree` para la página Árbol, `xdg-open` para abrir archivos y carpetas, y
`pyside6-rcc` solo si se compilan los recursos.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | crea la QApplication, aplica el tema guardado y abre la ventana; `--smoke` |
| `app/main_window.py` | carga `app/ui/mainwindow.ui`, arma la barra lateral con las siete páginas, acopla la Consola y guarda los workers vivos |
| `app/context.py` | contexto que reciben los controllers: preferencias, historial, consola, workers, navegación |
| `app/ui/*.ui` | vistas de Qt Designer, cargadas en tiempo de ejecución con QUiLoader |
| `app/controllers/dashboard_controller.py` | página Dashboard → `history_service`, `settings_service` |
| `app/controllers/explorer_controller.py` | página Explorador (propiedades en `app/dialogs/properties_dialog.py`) |
| `app/controllers/tree_controller.py` | página Árbol → `tree_service` |
| `app/controllers/stats_controller.py` | página Estadísticas → `scanner_service`, `export_service` |
| `app/controllers/folders_controller.py` | página Carpetas → `folder_service`, diario de deshacer en `history_service` |
| `app/controllers/hardlinks_controller.py` | página Hardlinks → `hardlink_service`, `export_service` |
| `app/controllers/reports_controller.py` | página Reportes → `history_service` |
| `app/controllers/base.py` | base común de los controllers (diálogos de archivo, listas separadas por comas) |
| `app/services/tree_service.py` | construye la orden de `tree` y la del `main.sh` de `script_proyect_tree` |
| `app/services/scanner_service.py` | conteo de extensiones (port de `script_count_files_by_extension`) |
| `app/services/folder_service.py` | creación de carpetas (port de `script_create_folders_batch`) e importación TXT/CSV/Markdown; deshacer con `rmdir` solo de carpetas vacías |
| `app/services/hardlink_service.py` | detección nativa, plan y aplicación; importa `backend/script_hardlinks-creator/lib/`; reporte Markdown |
| `app/services/export_service.py` | guardado en texto, JSON, CSV, Markdown, HTML, PDF y Excel |
| `app/services/settings_service.py` | QSettings tipado y exclusiones por defecto |
| `app/services/history_service.py` | historial de operaciones y reportes, diario de deshacer |
| `app/models/extension_model.py` | modelo de tabla de extensiones |
| `app/workers/function_worker.py`, `app/workers/process_worker.py` | QThread para funciones y procesos, con progreso y cancelación |
| `app/widgets/console_dock.py` | la Consola |
| `app/dialogs/preferences_dialog.py` | Preferencias |
| `app/utils/` | rutas (`app/utils/paths.py`), formato, iconos, temas, cargador de `.ui` |
| `resources/` | iconos SVG, `resources/resources.qrc`, temas QSS |
| `tools/build_resources.sh` | compila el `.qrc` (opcional: sin él los SVG se leen del disco) |
| `backend/` | las cinco herramientas de terminal, cada una con su README |

Backends: [`script_count_files_by_extension`](backend/script_count_files_by_extension/README.md) ·
[`script_create_folders_batch`](backend/script_create_folders_batch/README.md) ·
[`script_hardlinks-creator`](backend/script_hardlinks-creator/README.md) ·
[`script_hardlinks-detector`](backend/script_hardlinks-detector/README.md) ·
[`script_proyect_tree`](backend/script_proyect_tree/README.md).

## Límite honesto

- **La regla de la UI se cumple a medias.** Las escrituras pasan por `app/services/` y las operaciones largas por
  workers con progreso y cancelación, pero varios controllers abren archivos y carpetas con `xdg-open`, consultan el
  disco (existencia de rutas, espacio libre con `shutil.disk_usage`) y el reporte de auditoría de la página Hardlinks se
  genera y se guarda en el hilo de la interfaz (ver `../estado.md` §Por hacer).
- **La preferencia «hilos» se guarda y nada la usa** (ver `../estado.md` §Por hacer).
- **Carpetas crea de verdad por defecto**: marque «Simulación (dry-run)» antes de «Crear carpetas» si solo quiere ver el
  resultado. Deshacer borra solo las carpetas vacías de la última creación.
- **El modo «Proyectos» de Árbol** ofrece los grupos del backend (`all`, `pub`, `scripts`, `campustex`, `website`,
  `extra`); `pub` y `campustex` hoy no encuentran nada (ver el [README del backend](backend/script_proyect_tree/README.md)).
- **No es la fuente de verdad de sus backends**: importa `backend/script_hardlinks-creator/lib/`, ejecuta
  `backend/script_proyect_tree/main.sh` y porta el resto a `app/services/`; un cambio de comportamiento se hace en los dos sitios
  (`../docs/decisiones.md` §2.2).
- **Las traducciones no existen**: el selector de idioma guarda la preferencia y la interfaz es en español.
- **Sin pruebas automáticas**: la comprobación es `python3 main.py --smoke` y usar la aplicación. Solo probada en
  Linux (depende de `xdg-open`).
