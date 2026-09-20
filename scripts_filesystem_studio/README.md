---
tipo: readme
estado: activo
---
# scripts_filesystem_studio/ — Filesystem Studio, GUI PySide6 de las cinco herramientas de sistema de archivos que viven en backend/
<!-- suite:inicio -->
**Suite `filesystem_studio`** · objetivo *sistema* · estado *activo* · python · interfaz gui

Aplicación de escritorio (PySide6) que unifica las herramientas de sistema de archivos: renombrado, limpieza, árbol de proyectos.

- Escribe en: archivos · simula por defecto: sí
- Depende de: PySide6

Comandos:

```bash
main.py
main.py --smoke
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

Aplicación de escritorio (PySide6 / Qt6) que unifica las cinco herramientas
de gestión del sistema de archivos que antes vivían como scripts CLI
independientes. Los scripts originales se conservan **intactos** en
`backend/` y siguen siendo utilizables desde la terminal.

```bash
python3 main.py            # ejecutar la aplicación
python3 main.py --smoke    # prueba de humo (construye la UI y sale)
```

Requisitos: Python ≥ 3.10, PySide6 ≥ 6.5, `tree` (para el módulo Árbol),
`openpyxl` (opcional, exportación a Excel). Ver `requirements.txt`.

## Módulos (organización por funcionalidad)

| Página           | Origen                                                   | Qué hace                                                                                                           |
| ---------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Dashboard**    | nuevo                                                    | Operaciones recientes, favoritas, últimos reportes, espacio en disco, accesos directos                             |
| **Explorador**   | nuevo                                                    | Navegación, propiedades, copiar rutas, abrir con el gestor, «Usar en…» (envía la carpeta a otro módulo)            |
| **Árbol**        | `script_proyect_tree`                                    | Vista previa/exportación txt·md·json con profundidad y exclusiones; el modo «Proyectos» ejecuta el backend intacto |
| **Estadísticas** | `script_count_files_by_extension`                        | Escaneo recursivo, tabla ordenable/filtrable, gráfico (QtCharts), exportar CSV/Markdown/Excel                      |
| **Carpetas**     | `script_create_folders_batch`                            | Lista manual o importada (TXT/CSV/Markdown), vista previa, dry-run, deshacer                                       |
| **Hardlinks**    | `script_hardlinks-detector` + `script_hardlinks-creator` | Pestañas Detectar / Crear / Reportes; creación en dos fases (planificar → aplicar) con enlace atómico              |
| **Reportes**     | nuevo                                                    | Historial central de todo lo generado                                                                              |

La **Consola** es un panel inferior acoplable (menú Ver → Consola):
muestra el comando ejecutado, stdout/stderr de los backends, progreso con
porcentaje/archivo actual/tiempo estimado y botón Cancelar.

## Arquitectura

```
main.py                 # QApplication + tema + MainWindow
app/
├── ui/                 # .ui de Qt Designer (cargados con QUiLoader)
├── controllers/        # 1 por página: conectan vista ↔ servicios
├── services/           # ÚNICA capa que toca disco y backend/
│   ├── scanner_service.py    # extensiones (migrado de count_files)
│   ├── hardlink_service.py   # detect (migrado) + create (REUTILIZA
│   │                         #   lib/ de script_hardlinks-creator)
│   ├── tree_service.py       # envuelve `tree` y el backend proyect_tree
│   ├── folder_service.py     # port de create_folders_batch + deshacer
│   ├── export_service.py     # CSV/JSON/MD/HTML/PDF/Excel unificado
│   ├── settings_service.py   # QSettings tipado (exclusiones únicas)
│   └── history_service.py    # historial, favoritas, diario de deshacer
├── models/             # QAbstractTableModel (extensiones)
├── workers/            # FunctionWorker y ProcessWorker (QThread)
├── widgets/            # ConsoleDock (consola + progreso)
├── dialogs/            # Preferencias (.ui), Propiedades
└── utils/              # format, paths, iconos, temas, cargador .ui
backend/                # Los 5 scripts originales, intactos y ejecutables
resources/              # iconos SVG, resources.qrc, temas QSS
tools/build_resources.sh  # opcional: compila el .qrc a resources_rc.py
```

Reglas: la UI nunca ejecuta scripts ni toca `os.*` — todo pasa por
`services/`; toda operación larga corre en un worker con progreso y
cancelación; las operaciones destructivas tienen vista previa y dry-run.

## Configuración

Archivo → Preferencias (persistido con QSettings en
`~/.config/EdisonAchalma/FilesystemStudio.conf`): rutas favoritas,
exclusiones por defecto (perfil único para todos los módulos),
profundidad, formato de exportación, idioma, tema (oscuro/claro/sistema),
tamaño de iconos, hilos, carpeta de reportes y temporal.

## Notas

- Los `.ui` se cargan en tiempo de ejecución con QUiLoader; no hace falta
  compilar nada. `tools/build_resources.sh` genera `resources_rc.py`
  (opcional): sin él los SVG se cargan directamente del disco.
- El selector de idioma guarda la preferencia, pero las traducciones
  (.ts/.qm) aún no están generadas; la interfaz es en español.
- Al mover los scripts aquí, corrige los alias del shell que apuntaban a
  las rutas antiguas (p. ej. `ptree`).

## Límite honesto

- **Sin pruebas automáticas**: la comprobación es `python3 main.py --smoke` y usar la aplicación.
- **No es la fuente de verdad de sus backends**: reutiliza la `lib/` de `script_hardlinks-creator` y reimplementa el resto en `app/services/`; un cambio de comportamiento se hace en los dos sitios.
- **Los cinco backends de `backend/` son suites** con `suite.yml`, README y CLI propios; la GUI los lanza o los porta, no los sustituye.
- **Las traducciones no existen** (el selector de idioma guarda la preferencia, la interfaz es en español) y `resources_rc.py` es opcional.
- **`reports/` no se versiona**: es un historial local de lo generado.