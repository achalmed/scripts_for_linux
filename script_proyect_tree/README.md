---
tipo: readme
estado: activo
---
# script_proyect_tree/ — escribe en cada proyecto un archivo con su árbol de directorios (txt, md o json)

<!-- suite:inicio -->
**Suite `proyect_tree`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Genera el árbol de carpetas (txt, md o json) de la carpeta actual o de los proyectos del workspace por grupos, con exclusiones y estadísticas de disco.

- Escribe en: archivos · simula por defecto: no
- Entrada: la carpeta actual o los grupos de proyectos de config.sh
- Depende de: bash, tree
- Nota: Backend de Filesystem Studio (página Árbol, modo Proyectos); sigue siendo utilizable desde la terminal. Escribe estructura.txt, derivado que NORMATIVA §15.8 (D07) no admite dentro de un repo; úsese para vista previa, --list, --stats o salidas fuera de git.

Comandos:

```bash
main.sh --list
main.sh --stats
main.sh --dry-run -t all
main.sh -f md -L 3
main.sh --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Genera con `tree` un archivo con la estructura de directorios de cada proyecto y lo deja **dentro de la carpeta del
proyecto**: `estructura.txt` (con una cabecera de proyecto, ruta, fecha, profundidad y exclusiones), `estructura.md` o
`estructura.json` según `--format`. Excluye por defecto los artefactos de Quarto, LaTeX, Python, Node, git y del
sistema operativo, y el propio `estructura.txt`.

Los proyectos se eligen por grupos que se buscan en el primer nivel de `~/Documents` (`config.sh`):

| grupo | qué busca | qué encuentra hoy |
|---|---|---|
| `pub` | carpetas `pub_*` | nada (los blogs viven en `04 index/_pubs/`) |
| `scripts` | carpetas `scripts_*` | los repos de scripts del espacio de trabajo |
| `campustex` | carpetas `CampusTeX-*` | nada (los repos se llaman `docencia` y `11 Book` en disco) |
| `website` | la carpeta `04 index` | el hub |
| `extra` | la lista `EXTRA_PROJECTS` | `03 writing` |

`all` es la unión de todos. Sin `--target`, trabaja sobre la carpeta actual, salvo si se ejecuta desde `~/Documents`
o desde `$HOME`, donde equivale a `all`.

Qué escribe: el archivo de estructura de cada proyecto elegido, que se sobrescribe (lo escribe primero en un temporal
`.estructura_tmp.*` del mismo proyecto y luego lo mueve). No deja log. **No simula por defecto**: la simulación se
pide con `--dry-run`; `--list` y `--stats` tampoco escriben.

Es el backend del modo «Proyectos» de la página Árbol de Filesystem Studio (`filesystem/` del repo `gui-suites`), que ejecuta este
`main.sh` (con la simulación marcada por defecto); la vista previa y la exportación de un árbol suelto las hace la GUI
por su cuenta.

## Uso

```bash
cd "$HOME/Documents/03 writing" && /ruta/a/main.sh   # estructura.txt de la carpeta actual
./main.sh --target all --dry-run                      # qué se escribiría en todos los grupos
./main.sh --target scripts                            # solo los scripts_*
./main.sh --target "03 writing" --format md --depth 4 # un proyecto por su nombre exacto
./main.sh --target website --exclude-dir data -x "*.csv"
./main.sh --list                                      # proyectos detectados por grupo
./main.sh --stats --target scripts                    # tamaño y número de archivos, sin escribir
./main.sh --version                                   # imprime nombre y versión
```

| opción | por defecto | qué hace |
|---|---|---|
| `-t`, `--target TARGET` | carpeta actual (`all` desde `~/Documents` o `$HOME`) | `all`, `pub`, `scripts`, `campustex`, `website`, `extra`, `.` o el nombre exacto de una carpeta de `~/Documents` |
| `-L`, `--depth N` | `6` | profundidad del árbol |
| `-X`, `--exclude-dir DIR` | — | carpeta adicional que se excluye (repetible) |
| `-x`, `--exclude-file PAT` | — | patrón de archivo adicional que se excluye (repetible) |
| `-f`, `--format FORMAT` | `txt` | `txt`, `md` o `json` |
| `--no-meta` | apagado | sin tamaños ni fechas en el árbol (`-h -D` de `tree`) |
| `-l`, `--list` | — | lista los proyectos detectados y sale |
| `-s`, `--summary` | apagado | al terminar, tamaño en disco y resumen de lo escrito |
| `--stats` | — | solo estadísticas de disco (`du`, número de archivos); no escribe |
| `--dry-run` | apagado | simula; con `-v` muestra las 30 primeras líneas de cada árbol |
| `-v`, `--verbose` | apagado | mensajes de depuración |
| `--no-color` | apagado | sin colores |
| `--version`, `-h`, `--help` | — | versión y ayuda |

En `config.sh` se cambian la raíz de proyectos, los grupos, `EXTRA_PROJECTS`, las exclusiones, la profundidad y las
banderas de metadatos.

Códigos de salida: 0 bien (también si un grupo no encuentra nada), 2 argumento o target inválido, 3 no existe la raíz
de proyectos, 5 falta una dependencia.

Requisitos: bash 5 (lo declara `main.sh`), `tree`, `find`, `du`, `date`, y
`core/shell-lib/logger.sh` del espacio de trabajo.

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | orquesta: argumentos → colores → target por defecto → validación → lista, estadísticas o generación → resumen |
| `config.sh` | versión, raíz de proyectos, grupos, `EXTRA_PROJECTS`, exclusiones, profundidad, estado de ejecución |
| `lib/cli.sh` | lectura de opciones, ayuda y target por defecto según la carpeta actual |
| `lib/logger.sh` | carga el logger común de `core/shell-lib/` y decide si hay colores |
| `lib/validator.sh` | dependencias, raíz de proyectos y target |
| `lib/generator.sh` | resuelve los proyectos de cada grupo y escribe (o simula) cada archivo de estructura |
| `lib/tree_utils.sh` | patrón de exclusión, cabecera y llamadas a `tree` en txt, md y json |
| `lib/stats.sh` | estadísticas de disco, resumen final y `--list` |
| `suite.yml` | manifiesto de la suite (de él sale el bloque generado de arriba) |

## Límite honesto

- **Los grupos `pub` y `campustex` ya no encuentran nada**: buscan `pub_*` y `CampusTeX-*` en el primer nivel de
  `~/Documents`, y esas carpetas ya no están ahí. `--target all` solo cubre los `scripts_*`, `04 index` y
  `03 writing` (ver `../estado.md` §Por hacer).
- **La raíz de proyectos está escrita en `config.sh`** (`$HOME/Documents`) y no pasa por `core/env.sh`.
- **Escribe dentro de los repos.** `estructura.txt` no se versiona: lo ignoran el `.gitignore` de varios repos (este
  incluido) y el gitignore global del usuario. `estructura.md` y `estructura.json` no los ignora ni el de este repo ni
  el global, y aparecen como archivos nuevos en `git status`; además, el árbol txt no excluye esos dos.
- **Sin `--target` escribe en la carpeta actual**: ejecutado desde cualquier carpeta que no sea `~/Documents` ni
  `$HOME`, deja ahí un `estructura.txt`.
- **La cabecera del txt lleva la ruta absoluta** del proyecto.
- **Necesita el espacio de trabajo**: `lib/logger.sh` busca `core/shell-lib/logger.sh` subiendo desde su carpeta.
