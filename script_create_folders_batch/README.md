# Create Folders Batch

> Crea múltiples carpetas de forma masiva a partir de una lista predefinida
> (en `config.sh`) o de un archivo de texto externo, con vista previa,
> confirmación interactiva y modo dry-run.

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Arquitectura](#-arquitectura)
- [Bugs Corregidos](#-bugs-corregidos)
- [Solución de Problemas](#-solución-de-problemas)
- [Cómo Contribuir](#-cómo-contribuir)
- [Notas y Advertencias](#-notas-y-advertencias)

## 📖 Descripción

Pensado para preparar lotes de carpetas de cursos, proyectos o publicaciones.
El flujo es siempre: leer lista → sanear nombres → vista previa → confirmar →
crear → resumen. Cada carpeta termina clasificada en exactamente una
categoría: **creada**, **ya existía**, **rechazada** (nombre inseguro) o
**error** (fallo de `mkdir`).

Formato del archivo de lista (`-f`):

```
carpeta-uno
carpeta-dos
carpeta-tres/subcarpeta     # se admiten rutas relativas
# las líneas con # y las vacías se ignoran
```

Por seguridad se **rechazan** rutas absolutas (`/algo`) y componentes `..`:
la herramienta nunca escribe fuera del directorio base.

## ⚙️ Requisitos

### Sistema Operativo

- Linux/macOS con `bash` >= 4.0. Solo usa utilidades estándar (`mkdir`,
  `grep`).

## 🚀 Instalación

```bash
cd script_create_folders_batch
chmod +x main.sh lib/*.sh
```

## 💻 Uso

### Sintaxis

```bash
./main.sh [OPCIONES]
```

### Opciones disponibles

| Flag                | Descripción                                       | Requerido |
| ------------------- | ------------------------------------------------- | --------- |
| `-f, --file ARCHIVO`| Leer nombres desde un archivo                     | No        |
| `-p, --path RUTA`   | Directorio base destino (default: `.`)            | No        |
| `-d, --dry-run`     | Simular sin crear nada                            | No        |
| `-y, --yes`         | No pedir confirmación (cron, scripts)             | No        |
| `-v, --verbose`     | Información detallada                             | No        |
| `--no-color`        | Desactivar colores                                | No        |
| `--version`         | Mostrar versión                                   | No        |
| `-h, --help`        | Mostrar ayuda                                     | No        |

### Ejemplos de uso

```bash
# Lista predefinida (config.sh) en el directorio actual
./main.sh

# Leer desde archivo y simular
./main.sh -d -f lista_carpetas.txt

# Crear en otro directorio sin confirmación interactiva
./main.sh -y -f lista.txt -p ~/proyectos
```

## 🗂️ Arquitectura

```
script_create_folders_batch/
├── main.sh              # Punto de entrada — solo orquestación
├── config.sh            # Defaults + lista predefinida de carpetas
└── lib/
    ├── logger.sh        # Logging INFO/WARN/ERROR/DEBUG con colores auto-desactivables
    ├── cli.sh           # Parseo de argumentos → variables OPT_*
    ├── validator.sh     # Directorio base, archivo de entrada, nombres seguros, confirmación
    ├── reader.sh        # Lectura de la lista + saneamiento de nombres
    ├── creator.sh       # mkdir con clasificación de resultados y contadores
    └── ui.sh            # Vista previa y resumen final
```

### Descripción de módulos

| Archivo            | Responsabilidad                                              |
| ------------------ | ------------------------------------------------------------ |
| `main.sh`          | Cargar módulos y ejecutar el pipeline en orden                |
| `config.sh`        | Lista predefinida y tunables (ítems de vista previa, destino) |
| `lib/logger.sh`    | Salida consistente; WARN/ERROR a stderr                       |
| `lib/cli.sh`       | Flags cortas/largas compatibles con la v1.x                   |
| `lib/validator.sh` | Precondiciones + regla de seguridad de nombres + confirmación |
| `lib/reader.sh`    | Fuente única de la lista; saneo de `\r` y espacios            |
| `lib/creator.sh`   | Creación con códigos de resultado distinguibles               |
| `lib/ui.sh`        | Presentación pura (no decide ni crea nada)                    |

## 🐛 Bugs Corregidos

### Bug #1: Ruta construida antes de sanear el nombre
- **Descripción**: en la v1.x `create_single_folder()` calculaba
  `full_path="$BASE_DIR/$folder_name"` con el nombre **crudo** y lo saneaba
  después; la comprobación de existencia y el `mkdir` usaban la ruta sucia.
- **Impacto**: con listas que traían espacios finales o `\r` (archivos
  editados en Windows) se creaban carpetas con caracteres invisibles en el
  nombre, y la detección de duplicados fallaba.
- **Corrección**: el saneo ocurre en `lib/reader.sh` antes de cualquier uso;
  `create_single_folder()` recibe el nombre ya limpio.

### Bug #2: Retornos de carro (`\r`) no eliminados
- **Descripción**: la línea que quitaba `\r` estaba comentada "por si acaso".
- **Impacto**: carpetas tipo `carpeta-uno\r` imposibles de distinguir a ojo.
- **Corrección**: `sanitize_folder_name()` siempre elimina `\r`.

### Bug #3: Dry-run contabilizado como "creadas"
- **Descripción**: en modo simulación el resumen final decía "✓ Carpetas
  creadas: N" y a la vez "no se creó ninguna carpeta realmente".
- **Impacto**: resumen contradictorio y confuso.
- **Corrección**: en dry-run la etiqueta cambia a "Se crearían:".

### Bug #4: "Ya existía" y "error" compartían código de retorno
- **Descripción**: `create_single_folder()` devolvía 1 en ambos casos y
  `main` re-verificaba con `[ -d ... ]` para adivinar cuál fue.
- **Impacto**: clasificación frágil (doble comprobación con posible carrera)
  y conteos potencialmente erróneos.
- **Corrección**: códigos de resultado distintos (`RESULT_CREATED/EXISTED/
  REJECTED/FAILED`) clasificados una sola vez.

### Bug #5: Escape del directorio base
- **Descripción**: una línea `../otro` o `/ruta/absoluta` en el archivo de
  lista creaba carpetas **fuera** del directorio destino.
- **Impacto**: escritura fuera del árbol elegido (riesgo de seguridad y de
  desorden).
- **Corrección**: `is_safe_folder_name()` rechaza rutas absolutas y
  componentes `..`; los rechazos se cuentan y reportan.

### Bug #6: Confirmación colgada sin terminal
- **Descripción**: `read -p` en entornos no interactivos (cron, pipes)
  fallaba o se quedaba esperando.
- **Impacto**: la herramienta no era usable de forma automatizada.
- **Corrección**: `confirm_action()` detecta la ausencia de TTY y pide usar
  `--yes`; con `--yes` o `--dry-run` no pregunta.

## 🔧 Solución de Problemas

### Error: "Permission denied"

```bash
chmod +x main.sh lib/*.sh
```

### "No hay terminal interactiva; use --yes"

Estás ejecutando desde cron o un pipe: añade `-y`/`--yes`.

### Una línea aparece como "Rechazada (ruta insegura)"

La línea contiene una ruta absoluta o `..`. Usa solo rutas relativas dentro
del directorio base.

## 🤝 Cómo Contribuir

1. Crea el módulo en `lib/nuevo_modulo.sh` con una única responsabilidad.
2. Añade sus flags en `lib/cli.sh` y sus tunables en `config.sh`.
3. Cárgalo con `source` en `main.sh` en orden de dependencias.
4. Verifica con `bash -n` y prueba siempre primero con `--dry-run`.

### Estándares de código

- Máximo ~30 líneas por función; nombres verbo+sustantivo en inglés.
- Comentarios que explican el "por qué", no el "qué".
- `set -euo pipefail` y errores por stderr.

## ⚠️ Notas y Advertencias

- La lista predefinida ahora vive en `config.sh` (`PREDEFINED_FOLDERS`), no
  dentro del script principal: edítala ahí.
- Los nombres de carpeta **pueden contener espacios internos**; solo se
  recortan los espacios al inicio/final.
- El código de salida es `1` si alguna carpeta falló, `0` en caso contrario
  (que existieran previamente no se considera fallo).
