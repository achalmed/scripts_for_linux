# Count Files by Extension

> Analiza recursivamente un directorio y cuenta los archivos agrupados por
> extensión, mostrando cantidad, tamaño acumulado, ranking top-N y
> estadísticas generales — todo en una sola pasada sobre el disco.

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

Herramienta de diagnóstico de contenido de directorios (una biblioteca de
Zotero, un repositorio de materiales, un disco de fotografías). Recorre el
árbol una única vez con `find -printf` (obteniendo nombre y tamaño sin
ejecutar `stat` por archivo) y acumula los resultados en arrays asociativos
de Bash. Produce:

1. **Tabla por extensión** — cantidad y tamaño total, ordenada por frecuencia.
2. **Ranking top-N** — barras de porcentaje de las extensiones más comunes.
3. **Estadísticas generales** — totales de archivos, directorios y bytes.

Las extensiones se normalizan a minúsculas (`.TXT` y `.txt` cuentan juntas).
Los archivos sin punto y los dotfiles (`.bashrc`) se agrupan bajo
`sin_extension`.

## ⚙️ Requisitos

### Sistema Operativo

- Linux (probado en Kubuntu/Debian). Requiere GNU findutils — el `find` de
  BSD/macOS no soporta `-printf`.

### Dependencias

- `bash` >= 4.0 — arrays asociativos
- GNU `find` — escaneo con `-printf`
- `awk` — aritmética de punto flotante (porcentajes y tamaños legibles)

## 🚀 Instalación

```bash
cd script_count_files_by_extension
chmod +x main.sh lib/*.sh
```

## 💻 Uso

### Sintaxis

```bash
./main.sh [OPCIONES] [directorio]
```

### Opciones disponibles

| Flag            | Descripción                                                | Requerido |
| --------------- | ---------------------------------------------------------- | --------- |
| `directorio`    | Directorio a analizar (default: `~/Documents/biblioteca`)  | No        |
| `-t, --top N`   | Extensiones a mostrar en el ranking (default: 5)           | No        |
| `-v, --verbose` | Información de diagnóstico                                 | No        |
| `--no-color`    | Desactivar colores                                         | No        |
| `--version`     | Mostrar versión                                            | No        |
| `-h, --help`    | Mostrar ayuda                                              | No        |

### Ejemplos de uso

```bash
# Directorio por defecto (~/Documents/biblioteca)
./main.sh

# Analizar un directorio específico
./main.sh ~/Documents

# Ranking con 10 extensiones y sin colores (útil para redirigir a archivo)
./main.sh -t 10 --no-color /ruta/proyecto > reporte.txt
```

## 🗂️ Arquitectura

```
script_count_files_by_extension/
├── main.sh              # Punto de entrada — solo orquestación
├── config.sh            # Defaults editables (directorio, top-N, ancho de barra)
└── lib/
    ├── logger.sh        # Logging INFO/WARN/ERROR/DEBUG con colores auto-desactivables
    ├── cli.sh           # Parseo de argumentos → variables OPT_*
    ├── validator.sh     # Dependencias, permisos y validación de opciones
    ├── scanner.sh       # Escaneo en una sola pasada (find -printf + arrays asociativos)
    └── renderer.sh      # Tabla, ranking con barras y estadísticas
```

### Descripción de módulos

| Archivo            | Responsabilidad                                           |
| ------------------ | --------------------------------------------------------- |
| `main.sh`          | Cargar módulos y ejecutar el pipeline en orden            |
| `config.sh`        | Constantes editables por el usuario                       |
| `lib/logger.sh`    | Salida consistente; WARN/ERROR a stderr                   |
| `lib/cli.sh`       | Flags y ayuda; compatibilidad con el argumento posicional |
| `lib/validator.sh` | Fallar temprano con códigos de salida estándar (2/3/4/5)  |
| `lib/scanner.sh`   | Recolectar conteos y tamaños por extensión                |
| `lib/renderer.sh`  | Formatear resultados (no escanea nada)                    |

## 🐛 Bugs Corregidos

### Bug #1: Crash al ejecutar sin argumentos
- **Descripción**: con `set -u`, la comprobación `[[ "$1" == "-h" ]]` (línea
  258 de la v1.x) accedía a `$1` sin valor por defecto; sin argumentos el
  script moría con "unbound variable" antes de llegar a `main`.
- **Impacto**: el caso de uso principal documentado (`./script.sh` sin
  argumentos) no funcionaba.
- **Corrección**: parseo centralizado en `lib/cli.sh` con bucle `while` que
  nunca accede a posicionales inexistentes.

### Bug #2: Escaneo O(N×M) — un find + un stat por archivo por extensión
- **Descripción**: `get_size_by_extension()` relanzaba `find` sobre todo el
  árbol y un proceso `stat` por cada archivo, una vez POR CADA extensión;
  `show_statistics()` volvía a recorrer todo el árbol otra vez.
- **Impacto**: sobre directorios grandes la ejecución tardaba minutos; el
  trabajo crecía multiplicativamente con el número de extensiones.
- **Corrección**: `lib/scanner.sh` hace UNA pasada con
  `find -printf '%s\t%f\0'` y acumula en arrays asociativos, sin procesos
  por archivo.

### Bug #3: Conteo y tamaño calculados sobre conjuntos distintos
- **Descripción**: el conteo normalizaba extensiones a minúsculas, pero el
  tamaño se buscaba con `find -iname "*.$ext"`, un criterio distinto que
  además se rompía si la extensión contenía caracteres glob (`[`, `*`, `?`).
- **Impacto**: tamaños inconsistentes con los conteos mostrados.
- **Corrección**: ambos valores se acumulan en el mismo punto de la única
  pasada, siempre desde el mismo registro.

### Bug #4: `stat` de BSD intentado primero en Linux
- **Descripción**: `stat -f%z ... 2>/dev/null || stat -c%s ...` ejecutaba
  siempre un `stat` destinado a macOS que falla en Linux, silenciando el
  error y duplicando procesos.
- **Impacto**: rendimiento degradado y errores enmascarados.
- **Corrección**: el tamaño viene de `find -printf '%s'`; ya no se invoca
  `stat`.

### Bug #5: Dotfiles clasificados como extensión
- **Descripción**: para `.bashrc`, `${filename##*.}` devuelve `bashrc`, así
  que se contaba como extensión `.bashrc` en vez de "sin extensión".
- **Impacto**: extensiones fantasma en el reporte.
- **Corrección**: `extract_extension()` descarta el punto inicial antes de
  decidir si el nombre tiene extensión real.

### Bug #6: Nombres de archivo con saltos de línea rompían los totales
- **Descripción**: los conteos con `find | wc -l` y los bucles `while read`
  sin delimitador NUL cuentan/parten mal los nombres con `\n`.
- **Impacto**: totales incorrectos en árboles con nombres inusuales.
- **Corrección**: registros delimitados por NUL en el escaneo y conteo de
  directorios con `-printf '.'`.

## 🔧 Solución de Problemas

### Error: "Permission denied"

```bash
chmod +x main.sh lib/*.sh
```

### Error: "Este 'find' no soporta -printf"

Estás en un sistema BSD/macOS. Instala GNU findutils (`brew install findutils`)
o ejecuta en Linux.

### La salida muestra códigos de color al redirigir a archivo

Los colores se desactivan solos cuando stdout no es TTY; si tu entorno los
fuerza, usa `--no-color`.

## 🤝 Cómo Contribuir

1. Crea el módulo en `lib/nuevo_modulo.sh` con una única responsabilidad.
2. Añade sus flags en `lib/cli.sh` y sus tunables en `config.sh` (nunca
   hardcodeados en `lib/`).
3. Cárgalo con `source` en `main.sh` en orden de dependencias.
4. Verifica con `bash -n` cada archivo y actualiza este README.

### Estándares de código

- Máximo ~30 líneas por función; nombres verbo+sustantivo en inglés.
- Comentarios que explican el "por qué", no el "qué".
- `set -euo pipefail` y errores por stderr.

## ⚠️ Notas y Advertencias

- La v2 usa GNU `find -printf`, por lo que **no es portable a macOS/BSD** sin
  findutils GNU (la v1.x tampoco lo era en la práctica: mezclaba `stat` BSD
  con hábitos GNU).
- Los enlaces simbólicos **no** se siguen (`find -type f` no cuenta el
  destino de un symlink), igual que en la v1.x.
- El separador decimal de los porcentajes depende del `LC_NUMERIC` del
  sistema (coma en locales españoles).
