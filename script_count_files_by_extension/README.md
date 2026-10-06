---
tipo: readme
estado: activo
---
# script_count_files_by_extension/ — conteo de archivos por extensión con tamaños, ranking y estadísticas

<!-- suite:inicio -->
**Suite `count_files_by_extension`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Cuenta los archivos de un árbol por extensión, con tamaño acumulado, ranking top-N y estadísticas, en una sola pasada de find.

- Escribe en: ninguno · simula por defecto: no
- Entrada: cualquier carpeta (por defecto la biblioteca)
- Depende de: bash, GNU findutils
- Nota: Backend de Filesystem Studio (página Estadísticas); sigue siendo utilizable desde la terminal. Solo lee; GNU-only (find -printf).

Comandos:

```bash
main.sh [directorio]
main.sh -t 10 --no-color <directorio>
main.sh --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Recorre un directorio de forma recursiva en una sola pasada (`find -printf`) y cuenta los archivos por extensión.
Imprime en la terminal tres bloques: una tabla con cantidad y tamaño acumulado por extensión (ordenada por
frecuencia), un ranking de las N extensiones más comunes con barra de porcentaje y unas estadísticas generales
(archivos, directorios, tamaño total, ruta analizada).

Las extensiones se normalizan a minúsculas (`.PDF` y `.pdf` cuentan juntas); los archivos sin punto y los dotfiles
como `.bashrc` se agrupan bajo `sin_extension`.

No escribe nada en disco ni tiene modo de simulación (solo lee). Para guardar el resultado, redirija la salida con
`--no-color`. Es el backend de la página Estadísticas de Filesystem Studio (`filesystem/` del repo `studios`), que lo porta a
`filesystem/fs_app/services/scanner_service.py` (repo `studios`).

## Uso

```bash
./main.sh                                   # analiza el directorio por defecto (la biblioteca)
./main.sh ~/Documents                       # analiza otra carpeta
./main.sh -t 10 --no-color "/ruta/con espacios" > reporte.txt
./main.sh --version                         # imprime nombre y versión
```

| opción | por defecto | qué hace |
|---|---|---|
| `directorio` (posicional) | `~/Documents/biblioteca` | carpeta que se analiza; admite `~` aunque llegue entre comillas |
| `-t`, `--top N` | `5` | cuántas extensiones entran en el ranking (entero positivo) |
| `-v`, `--verbose` | apagado | mensajes de diagnóstico |
| `--no-color` | apagado | sin colores (también se apagan solos si la salida no es una terminal) |
| `--version` | — | imprime nombre y versión y sale |
| `-h`, `--help` | — | ayuda |

En `config.sh` se cambian el directorio por defecto, el tamaño del ranking, el ancho de la barra (50 caracteres) y
la etiqueta de los archivos sin extensión.

Códigos de salida: 0 bien (también si no hay archivos), 2 uso incorrecto, 3 directorio inexistente, 4 sin permisos de
lectura, 5 falta GNU `find` con `-printf`.

Requisitos: bash 4 o superior, GNU findutils, `awk`, `sort`, y `core/shell-lib/logger.sh` del espacio de trabajo.

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | carga la configuración y los módulos y ejecuta: argumentos → colores → validación → escaneo → salida |
| `config.sh` | valores editables: directorio por defecto, tamaño del ranking, ancho de barra, etiqueta sin extensión |
| `lib/cli.sh` | lectura de opciones (`OPT_*`) y ayuda |
| `lib/logger.sh` | carga el logger común de `core/shell-lib/` y decide si hay colores |
| `lib/validator.sh` | comprueba GNU `find`, el valor de `--top` y el directorio, y lo vuelve absoluto |
| `lib/scanner.sh` | una pasada con `find -printf` separada por NUL; acumula conteo y bytes por extensión |
| `lib/renderer.sh` | tabla, ranking con barras y estadísticas (solo presenta) |
| `suite.yml` | manifiesto de la suite (de él sale el bloque generado de arriba) |

## Límite honesto

- **Solo GNU/Linux**: necesita `find -printf`; con el `find` de BSD o macOS sale con código 5.
- **Necesita el espacio de trabajo**: `lib/logger.sh` busca `core/shell-lib/logger.sh` subiendo desde su carpeta;
  copiado fuera de `~/Documents` no arranca.
- **El directorio por defecto está escrito en `config.sh`** y no pasa por `core/env.sh` (ver `../estado.md`
  §Por hacer).
- **No excluye nada**: entra en `.git`, `node_modules` y similares (la página Estadísticas de la GUI sí tiene
  exclusiones).
- **Cuenta entradas, no contenido**: no sigue enlaces simbólicos y cada nombre de un hardlink cuenta como un archivo
  con su tamaño completo.
