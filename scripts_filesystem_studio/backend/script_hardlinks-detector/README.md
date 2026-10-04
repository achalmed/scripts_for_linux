---
tipo: readme
estado: activo
---
# script_hardlinks-detector/ — detecta los hard links de un árbol y los presenta por inodo como árbol, CSV, JSON o reporte

<!-- suite:inicio -->
**Suite `hardlinks_detector`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Detecta los hard links de un árbol y los presenta agrupados por inodo como árbol, CSV, JSON o reporte de auditoría.

- Escribe en: archivos · simula por defecto: no
- Entrada: cualquier carpeta (por defecto la actual)
- Depende de: bash >= 4, GNU findutils
- Nota: Backend de Filesystem Studio (pestañas Detectar y Reportes de Hardlinks); sigue siendo utilizable desde la terminal. Sin -o ni --report solo lee; -o escribe el archivo pedido y --report, reports/hardlinks-report.md.

Comandos:

```bash
main.sh [directorio]
main.sh <directorio> -f json -o salida.json
main.sh <directorio> --report
main.sh --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Recorre un árbol con `find -links` y `stat`, agrupa por inodo los archivos que tienen dos o más nombres (hard links) y
los presenta como árbol jerárquico, CSV o JSON, con el espacio total y el espacio que los enlaces ahorran. En formato
árbol añade un resumen y una guía breve de cómo se gestionan los hard links. Con `--report` escribe además un
reporte de auditoría en Markdown (estado general, inventario, categorías por tipo de archivo, los más compartidos,
los críticos —cinco enlaces o más—, resumen por carpeta, lista de comprobación y órdenes útiles).

No crea, borra ni modifica enlaces: solo lee. Escribe únicamente lo que se le pide: el archivo de `-o` (que se
sobrescribe) y, con `--report`, `reports/hardlinks-report.md` dentro de esta carpeta, que se sobrescribe en cada
corrida. `reports/` no se versiona. No tiene modo de simulación porque no lo necesita.

Es el backend de las pestañas Detectar y Reportes de la página Hardlinks de [Filesystem Studio](../../README.md), que
lo porta a `../../app/services/hardlink_service.py`. Para crear los enlaces, use
[`script_hardlinks-creator`](../script_hardlinks-creator/README.md).

## Uso

```bash
./main.sh                                              # analiza el directorio actual
./main.sh "$HOME/Documents/04 index"                   # el directorio va siempre primero
./main.sh ~/Documents -f json -o salida.json           # JSON a pantalla y a archivo
./main.sh ~/Documents -f csv -o enlaces.csv --no-color
./main.sh ~/Documents --min-links 5                    # solo inodos con cinco nombres o más
./main.sh ~/Documents --filter-inode 14820714          # un solo grupo
./main.sh ~/Documents --report                         # además, reports/hardlinks-report.md
./main.sh --version                                    # imprime la versión
```

| opción | por defecto | qué hace |
|---|---|---|
| `DIRECTORIO` (primer argumento) | directorio actual | raíz del análisis; tiene que ir antes que cualquier opción |
| `-f`, `--format FORMAT` | `tree` | `tree`, `csv` o `json` |
| `-o`, `--output FILE` | — | guarda la salida en un archivo, además de mostrarla |
| `--min-links N` | `2` | solo inodos con al menos N enlaces (entero ≥ 2) |
| `--filter-inode N` | — | solo el grupo de ese inodo |
| `--report` | apagado | escribe el reporte de auditoría en `reports/hardlinks-report.md` |
| `--no-color` | apagado | sin colores ANSI |
| `-v`, `--verbose` | apagado | mensajes de depuración |
| `--version`, `-h`, `--help` | — | versión y ayuda |

En `config.sh` se cambian el ancho de cabeceras y separadores (80), el nombre y la carpeta del reporte, el umbral de
«crítico» (5 enlaces) y cuántas filas lleva la tabla de los más compartidos (10). Su `DEFAULT_FORMAT` no tiene
efecto: el formato por defecto está fijo en `lib/cli.sh`.

Códigos de salida: 0 bien (también sin enlaces), 1 falta una herramienta o no se puede escribir el archivo de `-o`,
2 argumento inválido, 3 directorio inexistente, 4 sin permiso de lectura.

Requisitos: bash 4 o superior, GNU findutils y coreutils (`find`, `stat --format`, `sort`, `realpath`, `tee`), y
`core/shell-lib/logger.sh` del espacio de trabajo.

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | orquesta: argumentos → validación → escaneo → filtro → salida → resumen y guía → reporte |
| `config.sh` | versión, ancho, carpeta y nombre del reporte, umbrales, códigos de salida |
| `lib/cli.sh` | lectura de opciones y ayuda |
| `lib/logger.sh` | carga el logger común de `core/shell-lib/` |
| `lib/validator.sh` | herramientas requeridas, directorio y ruta de salida |
| `lib/scanner.sh` | `find -links` + `stat`; agrupa por inodo y suma espacio usado y ahorrado; filtro por inodo |
| `lib/renderer.sh` | salidas árbol, CSV y JSON con rutas relativas |
| `lib/ui.sh` | cabeceras, separadores, tamaños legibles y caja de resumen |
| `lib/report.sh` | reporte de auditoría en Markdown |
| `suite.yml` | manifiesto de la suite (de él sale el bloque generado de arriba) |

## Límite honesto

- **El reporte no tiene historial.** `reports/hardlinks-report.md` se sobrescribe y `reports/` está en el `.gitignore`:
  el mensaje final y la lista de comprobación del propio reporte sugieren compararlo con `git diff`, pero git no lo
  sigue y no debe añadirse con `git add`. Para comparar dos corridas, copie el reporte anterior antes de generar otro.
- **El directorio tiene que ser el primer argumento**: `./main.sh --report ~/Documents` falla con «Argumento
  desconocido».
- **Redirigir la salida mezcla los mensajes**: la cabecera y los avisos de información salen por la salida estándar;
  para un CSV o un JSON limpios use `-o`.
- **CSV y JSON no escapan las rutas**: una coma en el nombre rompe la fila del CSV y unas comillas o una barra
  invertida dejan el JSON inválido. Un `;` o un salto de línea en el nombre también parten el grupo.
- **Cuenta los enlaces de todo el disco, no solo los del árbol**: el número de enlaces y el espacio ahorrado salen de
  `stat`, así que un archivo con nombres fuera del directorio analizado aparece con menos rutas que enlaces.
- **Solo GNU/Linux** (`stat --format`, `realpath --relative-to`, `date --iso-8601`); no excluye carpetas y entra en
  `.git` y similares.
- **Necesita el espacio de trabajo**: `lib/logger.sh` busca `core/shell-lib/logger.sh` subiendo desde su carpeta.
