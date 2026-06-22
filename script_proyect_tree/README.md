# script_project_tree

> Genera y actualiza archivos `estructura.txt` con el árbol de directorios
> de cada proyecto en `~/Documents`, con soporte para grupos (`pub_*`,
> `scripts_*`, `CampusTeX-*`, `website-achalma`), actualización individual
> o global, múltiples formatos de salida y control total de exclusiones.

---

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Solución de Problemas](#solución-de-problemas)
- [Cómo Extender el Script](#cómo-extender-el-script)
- [Notas y Advertencias](#notas-y-advertencias)

---

## 📖 Descripción

`script_project_tree` automatiza la documentación de la estructura de
carpetas de todos tus proyectos de desarrollo. Cada vez que ejecutas el
script, genera (o actualiza) un archivo `estructura.txt` en la raíz de
cada proyecto seleccionado.

**Casos de uso principales:**

- Documentar el estado actual de un proyecto antes de un commit
- Comparar la estructura de un proyecto entre fechas distintas
- Generar snapshots en formato Markdown para incluir en READMEs
- Auditar el uso de disco por proyecto
- Listar todos los proyectos detectados en `~/Documents`

**Versión 2.0 — arquitectura modular:**
El script original (monolítico, 669 líneas) fue refactorizado en 8 archivos
independientes. Cada módulo tiene una única responsabilidad, es testeable de
forma aislada y puede extenderse sin tocar el resto del código.

---

## ⚙️ Requisitos

### Sistema Operativo
- Kubuntu 22.04+ / Debian / Ubuntu (o cualquier distro con APT)
- Bash >= 5.0

### Dependencias

| Herramienta | Versión mínima | Para qué se usa                 |
|-------------|----------------|---------------------------------|
| `tree`      | >= 1.7         | Generar el árbol de directorios |
| `find`      | GNU findutils  | Descubrir proyectos por patrón  |
| `du`        | GNU coreutils  | Estadísticas de disco           |
| `date`      | GNU coreutils  | Timestamps en los encabezados   |

---

## 🚀 Instalación

### Paso 1: Copiar el proyecto a tu carpeta de scripts

```bash
cp -r script_project_tree/ ~/Documents/scripts_for_linux/
```

### Paso 2: Dar permisos de ejecución

```bash
chmod +x ~/Documents/scripts_for_linux/script_project_tree/main.sh
chmod +x ~/Documents/scripts_for_linux/script_project_tree/lib/*.sh
```

### Paso 3: Instalar `tree` (si no lo tienes)

```bash
sudo apt install tree
```

### Paso 4 (opcional): Crear alias en `.zshrc`

Para ejecutarlo desde cualquier lugar sin escribir la ruta completa:

```bash
echo 'alias ptree="~/Documents/scripts_for_linux/script_project_tree/main.sh"' >> ~/.zshrc
source ~/.zshrc
```

Con el alias activo, todos los ejemplos de esta guía funcionan usando
`ptree` en lugar de `./main.sh`.

---

## 💻 Uso

### Sintaxis

```bash
./main.sh [OPCIONES]
```

### Opciones disponibles

| Flag                    | Descripción                                              | Default   |
|-------------------------|----------------------------------------------------------|-----------|
| `-t, --target TARGET`   | Qué proyectos actualizar (ver valores abajo)             | `all`     |
| `-L, --depth N`         | Profundidad del árbol                                    | `6`       |
| `-X, --exclude-dir DIR` | Excluir carpeta adicional (repetible)                    | —         |
| `-x, --exclude-file PAT`| Excluir patrón de archivo adicional (repetible)          | —         |
| `-f, --format FORMAT`   | Formato de salida: `txt` \| `md` \| `json`               | `txt`     |
| `--no-meta`             | Omitir tamaños y fechas en el árbol                      | off       |
| `-l, --list`            | Listar proyectos detectados y salir                      | off       |
| `-s, --summary`         | Mostrar tabla resumen al finalizar                       | off       |
| `--stats`               | Mostrar solo estadísticas de disco (sin generar archivos)| off       |
| `-v, --verbose`         | Activar mensajes de depuración                           | off       |
| `--dry-run`             | Simular sin escribir ningún archivo                      | off       |
| `--no-color`            | Deshabilitar colores en la terminal                      | off       |
| `--version`             | Mostrar versión                                          | —         |
| `-h, --help`            | Mostrar ayuda                                            | —         |

### Valores de `--target`

| Valor                 | Proyectos afectados                         |
|-----------------------|---------------------------------------------|
| `all`                 | Todos los grupos (comportamiento por defecto)|
| `pub`                 | Todos los `pub_*`                           |
| `scripts`             | Todos los `scripts_*`                       |
| `campustex`           | Todos los `CampusTeX-*`                     |
| `website`             | Solo `website-achalma`                      |
| `pub_numerus-scriptum`| Solo ese proyecto exacto (nombre de carpeta)|

---

### Ejemplos de uso

```bash
# ── ACTUALIZACIÓN GLOBAL ────────────────────────────────────────────────────

# Actualizar todos los proyectos (configuración por defecto)
./main.sh

# Actualizar todos con resumen de disco al final
./main.sh --summary

# Simular todo sin escribir nada (ver qué haría)
./main.sh --dry-run --verbose

# ── POR GRUPO ───────────────────────────────────────────────────────────────

# Solo publicaciones
./main.sh --target pub

# Solo scripts
./main.sh --target scripts

# Solo CampusTeX
./main.sh --target campustex

# Solo el website
./main.sh --target website

# ── PROYECTO ESPECÍFICO ─────────────────────────────────────────────────────

# Un pub_ concreto
./main.sh --target pub_numerus-scriptum

# Un script concreto
./main.sh --target scripts_for_latex

# ── EXCLUSIONES ADICIONALES ─────────────────────────────────────────────────

# Excluir carpeta "data" y "raw" además de las exclusiones por defecto
./main.sh --target pub --exclude-dir "data" --exclude-dir "raw"

# Excluir archivos .csv en esta ejecución
./main.sh --exclude-file "*.csv"

# ── FORMATOS ALTERNATIVOS ───────────────────────────────────────────────────

# Generar estructura.md en lugar de estructura.txt
./main.sh --target pub_numerus-scriptum --format md

# Generar estructura.json para procesar con jq u otro programa
./main.sh --target pub_numerus-scriptum --format json

# ── INFORMACIÓN Y ESTADÍSTICAS ──────────────────────────────────────────────

# Ver todos los proyectos detectados (sin generar nada)
./main.sh --list

# Ver estadísticas de disco por proyecto (sin generar archivos)
./main.sh --stats
./main.sh --stats --target pub

# ── PROFUNDIDAD Y METADATOS ─────────────────────────────────────────────────

# Árbol más superficial (ideal para proyectos muy grandes)
./main.sh --target website --depth 3

# Sin tamaños ni fechas (salida más limpia)
./main.sh --target pub --no-meta

# Árbol profundo con todos los metadatos
./main.sh --target pub_numerus-scriptum --depth 8 --summary
```

---

## 🗂️ Arquitectura

La versión 2.0 separa el monolito original en módulos con responsabilidad única.
`main.sh` solo orquesta — toda la lógica vive en `lib/`.

```
script_project_tree/
├── main.sh              # Punto de entrada — carga módulos y orquesta el flujo
├── config.sh            # Constantes y variables de runtime (única fuente de verdad)
├── README.md            # Esta documentación
└── lib/
    ├── logger.sh        # Funciones de logging: info / ok / warn / error / verbose / section
    ├── validator.sh     # Validación de dependencias, rutas y argumentos
    ├── cli.sh           # Parsing de flags CLI y texto de ayuda
    ├── tree_utils.sh    # Construcción de patrones de exclusión y runners por formato
    ├── generator.sh     # Descubrimiento de proyectos y escritura atómica de archivos
    └── stats.sh         # Estadísticas de disco, resumen y listado de proyectos
```

### Descripción de módulos

| Archivo            | Responsabilidad                                                              |
|--------------------|------------------------------------------------------------------------------|
| `main.sh`          | Carga módulos, llama `parse_arguments`, valida, despacha y reporta           |
| `config.sh`        | Define `PROJECT_GROUPS`, `DEFAULT_EXCLUDE_*`, `DEFAULT_DEPTH` y runtime vars |
| `lib/logger.sh`    | `log_info/ok/warn/error/verbose/section` + `_setup_colors()`                 |
| `lib/validator.sh` | `validate_dependencies`, `validate_projects_root`, `validate_target`         |
| `lib/cli.sh`       | `parse_arguments`, `show_help`, helpers `_parse_target/depth/format`         |
| `lib/tree_utils.sh`| `build_exclude_pattern`, `build_meta_flags`, `run_tree_txt/json/markdown`    |
| `lib/generator.sh` | `find_projects_by_pattern`, `collect_target_paths`, `generate_project_structure` |
| `lib/stats.sh`     | `show_disk_stats`, `show_summary`, `list_all_projects`                       |

### Flujo de ejecución

```
main.sh
  ├── parse_arguments()       ← cli.sh
  ├── _setup_colors()         ← logger.sh
  ├── validate_*()            ← validator.sh
  ├── list_all_projects()     ← stats.sh       [solo --list]
  ├── collect_target_paths()  ← generator.sh
  ├── show_disk_stats()       ← stats.sh       [solo --stats]
  ├── generate_project_structure() × N         [bucle principal]
  │     ├── _resolve_output_file()  ← generator.sh
  │     ├── _build_tree_output()    ← generator.sh → tree_utils.sh
  │     └── _write_structure_file() ← generator.sh
  ├── show_disk_stats()       ← stats.sh       [solo --summary]
  └── show_summary()          ← stats.sh       [solo --summary]
```

---

## 🔧 Solución de Problemas

### Error: `tree: command not found`

```bash
sudo apt install tree
```

### El script no encuentra ningún proyecto

Verifica que el directorio raíz sea correcto. La variable `PROJECTS_ROOT`
apunta a `${HOME}/Documents` en `config.sh`. Si tus proyectos están en
otra ruta, edita esa línea.

### `Permission denied` al ejecutar

```bash
chmod +x main.sh lib/*.sh
```

### El archivo `estructura.txt` incluye carpetas que no quiero

Usa `--exclude-dir` para añadir exclusiones en esa ejecución, o edita
`DEFAULT_EXCLUDE_DIRS` en `config.sh` para que el cambio sea permanente.

### La salida en JSON está vacía o malformada

Verifica que la versión de `tree` soporta `-J`:
```bash
tree --version
# Se recomienda tree >= 1.8 para JSON limpio
```

---

## 🤝 Cómo Extender el Script

### Agregar un nuevo grupo de proyectos

En `config.sh`, añade una entrada al array `PROJECT_GROUPS`:

```bash
PROJECT_GROUPS[misitio]="mi-sitio-*"
```

A partir de ahí, `--target misitio` funciona automáticamente.

### Cambiar las exclusiones permanentes

Edita `DEFAULT_EXCLUDE_DIRS` o `DEFAULT_EXCLUDE_FILES` en `config.sh`.

### Añadir un nuevo formato de salida

1. En `lib/tree_utils.sh`, añade una función `run_tree_<formato>()`.
2. En `lib/generator.sh`, añade un `case` en `_build_tree_output()`.
3. En `lib/generator.sh`, actualiza `_resolve_output_file()` con la extensión.
4. En `lib/cli.sh`, actualiza la validación en `_parse_format()`.
5. En `lib/cli.sh`, actualiza `show_help()` con el nuevo valor válido.

### Estándares de código

- Máximo 30 líneas por función
- Nombres descriptivos en inglés técnico: `verbo_sustantivo()`
- Comenta el *por qué*, no el *qué*
- Usa `local` para todas las variables dentro de funciones
- Valida argumentos antes de usarlos

---

## ⚠️ Notas y Advertencias

- **Escritura atómica**: el script escribe primero a un archivo temporal
  y luego lo mueve al destino final. Si el proceso se interrumpe, el
  archivo anterior no queda corrupto.

- **El propio `estructura.txt` se excluye**: el patrón de exclusión
  incluye el nombre del archivo de salida para evitar que aparezca
  dentro de su propio árbol.

- **`website-achalma` es un nombre fijo**: a diferencia de los otros
  grupos que usan globs, `website` apunta exactamente a `website-achalma`.
  Si renombras la carpeta, actualiza `PROJECT_GROUPS[website]` en `config.sh`.

- **Colores en CI/CD**: si el script se ejecuta sin terminal (cron,
  GitHub Actions, etc.), los colores se desactivan automáticamente
  porque se detecta que `stdout` no es un TTY. También puedes forzarlo
  con `--no-color`.

- **Los `doc_*`, `01 notes`, `meta`, `biblioteca`** y otros directorios
  que no coinciden con ningún grupo son ignorados por diseño. Si quieres
  incluirlos, añade un nuevo grupo en `PROJECT_GROUPS` dentro de `config.sh`.

- **`_GEN_SUCCESS` y `_GEN_FAIL`**: son variables globales usadas para
  comunicar el conteo entre `_run_generation_loop()` y `_print_final_status()`.
  Son privadas por convención (prefijo `_`) y no deben usarse fuera de `main.sh`.
