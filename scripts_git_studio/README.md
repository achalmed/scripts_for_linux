---
tipo: readme
estado: activo
---
# scripts_git_studio/ — Git Studio, GUI PySide6 para clonar, sincronizar y ver el estado de los repos del workspace (backend/ y repos-config.yml)
<!-- suite:inicio -->
**Suite `git_studio`** · objetivo *sistema* · estado *activo* · python · interfaz gui

Aplicación de escritorio (PySide6) para administrar los repositorios del workspace: estado, sincronización, ramas (repos-config.yml).

- Escribe en: git · simula por defecto: no
- Depende de: PySide6, git

Comandos:

```bash
main.py
main.py --smoke
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

Aplicación de escritorio (PySide6/Qt6) para la **administración unificada de
repositorios Git**: clonado masivo desde GitHub, sincronización
pull → commit → push, estado detallado y generación de reportes.

Unifica dos herramientas CLI que antes vivían separadas y que siguen siendo
utilizables desde la terminal en `backend/`:

| Herramienta original | Página de la GUI | Qué hace |
|---|---|---|
| `script_git_download_respos` | **Clonar** | Descarga repos de GitHub con control de profundidad de commits |
| `script_git_sync_respos` (`sync.sh`) | **Sincronizar** | pull → add → commit → push sobre múltiples repos |
| `script_git_sync_respos` (`status.sh`) | **Repositorios** / **Reportes** | Estado (cambios, ahead/behind) y reporte de actividad |

## Ejecución

```bash
python3 main.py            # ejecución normal
python3 main.py --smoke    # prueba de humo: construye la UI y sale
```

Requisitos: Python ≥ 3.10, PySide6 (`pip install PySide6`), git.
Los scripts CLI de `backend/` no necesitan PySide6 y conservan sus
dependencias originales (bash, git; curl/jq solo para el modo `all`
del descargador).

## Arquitectura

```
scripts_git_studio/
├── main.py                  # Punto de entrada (orquestación mínima)
├── app/
│   ├── main_window.py       # Sidebar + stack de páginas + consola acoplada
│   ├── context.py           # AppContext: servicios compartidos entre páginas
│   ├── ui/                  # Vistas de Qt Designer (.ui, cargadas con QUiLoader)
│   ├── controllers/         # Un controlador por página: conecta vista ↔ servicios
│   ├── services/            # TODA la lógica de negocio (ver tabla de ports abajo)
│   ├── models/              # Modelos Qt (tabla de estado de repos)
│   ├── workers/             # QThread genéricos: FunctionWorker / ProcessWorker
│   ├── widgets/             # ConsoleDock: consola + registro + barra de progreso
│   └── utils/               # paths, ui_loader, theming, icons, format
├── backend/                 # Scripts Bash originales, intactos y ejecutables
│   ├── script_git_download_respos/
│   └── script_git_sync_respos/
└── resources/               # Iconos SVG y temas QSS (oscuro/claro/sistema)
```

Reglas del diseño (mismas que Filesystem Studio):

- **La UI nunca invoca git ni toca el disco.** Los controladores llaman a
  `app/services/` a través de workers; toda operación larga corre en un
  `QThread` (la interfaz nunca se bloquea y siempre se puede cancelar).
- **`app/services/git_service.py` es la única implementación de comandos
  git.** Sincronización, estado, clonado y reportes la reutilizan; antes
  esa lógica estaba repetida entre `cloner.sh` y `git_ops.sh`.
- Las vistas viven en `.ui` editables con Qt Designer (sin paso de
  compilación: se cargan con `QUiLoader`).

### Correspondencia con los scripts originales

Los servicios son *ports fieles* de los módulos Bash — conservan las
correcciones de bugs documentadas en ellos (detección de cambios en repos
sin HEAD, fetch previo al conteo ahead/behind, errores por repo que no
abortan el lote):

| Servicio | Origen |
|---|---|
| `git_service.py` | `backend/script_git_sync_respos/lib/git_ops.sh` + `backend/script_git_download_respos/lib/cloner.sh` (URLs y flags) |
| `config_service.py` | `backend/script_git_sync_respos/lib/config.sh` (mismo `repos-config.yml`) |
| `status_service.py` | `backend/script_git_sync_respos/lib/status_reporter.sh` |
| `sync_service.py` | `backend/script_git_sync_respos/lib/sync_engine.sh` |
| `clone_service.py` | `backend/script_git_download_respos/lib/cloner.sh` + despachador de `main.sh` |
| `github_service.py` | `backend/script_git_download_respos/lib/github_api.sh` (urllib en vez de curl+jq) |

### Un solo registro de repositorios

La GUI y los scripts CLI comparten
`backend/script_git_sync_respos/repos-config.yml`: un repo agregado desde
la página **Repositorios** (o registrado automáticamente al clonar) queda
disponible de inmediato para `sync.sh` y `status.sh`, y viceversa. La
página **Sincronizar** incluye además el botón «Ejecutar sync.sh en la
consola (CLI)», que lanza el script Bash original con las opciones
elegidas y muestra su salida completa en la Consola integrada.

## Extender la aplicación

Para una nueva funcionalidad (ramas, commits, etiquetas, remotos,
estadísticas…):

1. Añadir las operaciones git necesarias a `app/services/git_service.py`
   (o un servicio nuevo de dominio, p. ej. `branch_service.py`).
2. Diseñar la vista en Qt Designer → `app/ui/page_<nombre>.ui`.
3. Crear `controllers/<nombre>_controller.py` heredando de
   `PageController`, ejecutando el servicio vía `FunctionWorker`.
4. Registrar la página en la lista `pages` de `app/main_window.py`
   (una línea) y añadir su icono SVG en `resources/icons/`.

Nada más: navegación, consola, progreso, cancelación, historial y
preferencias ya son transversales.

## Límite honesto

- **No simula**: sincronizar es `pull → add → commit → push` de verdad; la vista previa es la página Repositorios o `sync.sh --check`.
- **Los servicios son ports de los módulos Bash, no los mismos módulos**: `git_service.py` es la única implementación git de la GUI y puede divergir de `git_ops.sh` si uno cambia y el otro no.
- **Los dos backends de `backend/` son suites** con `suite.yml`, README y CLI propios; lo único que comparten con la GUI de verdad es `backend/script_git_sync_respos/repos-config.yml`, cuyo parser es ligero (sin comillas, anclas ni anidación).
- **Sin pruebas automáticas**: `python3 main.py --smoke` construye la UI y sale; PySide6 solo lo necesita la GUI.
- **Solo GitHub** en Clonar (API `users/<usuario>/repos`; repos privados con token).