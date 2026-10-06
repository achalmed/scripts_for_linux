---
tipo: readme
estado: activo
---
# script_create_folders_batch/ — creación de carpetas en lote desde una lista, con vista previa y simulación

<!-- suite:inicio -->
**Suite `create_folders_batch`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Crea carpetas por lote desde una lista predefinida o un archivo, con vista previa, confirmación y dry-run.

- Escribe en: archivos · simula por defecto: no
- Entrada: lista de nombres (config.sh o archivo -f)
- Depende de: bash
- Nota: Backend de Filesystem Studio (página Carpetas); sigue siendo utilizable desde la terminal. Rechaza rutas absolutas y componentes «..».

Comandos:

```bash
main.sh -d -f lista.txt
main.sh -y -f lista.txt -p <carpeta>
main.sh --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Crea carpetas en lote dentro de un directorio base, a partir de un archivo de lista (`-f`) o, si no se le da ninguno,
de la lista predefinida de `config.sh`. El flujo es siempre: leer la lista → sanear nombres → vista previa (las
diez primeras y el total) → confirmar → crear → resumen. Cada carpeta acaba en una de cuatro categorías: creada,
ya existía, rechazada (nombre inseguro) o error de `mkdir`.

Solo crea carpetas (con `mkdir -p`, así que admite `carpeta/subcarpeta`): nunca borra, renombra ni escribe archivos,
y no deja log ni reporte. **No simula por defecto**: la simulación se pide con `-d`/`--dry-run`, y la confirmación
interactiva se salta con `-y`/`--yes`.

Es el backend de la página Carpetas de Filesystem Studio (`filesystem/` del repo `studios`), que lo porta a
`filesystem/fs_app/services/folder_service.py` (repo `studios`) y le añade importación CSV y Markdown y deshacer.

Formato del archivo de lista: un nombre por línea; se ignoran las líneas vacías y las que empiezan por `#`; se quitan
los `\r` de archivos de Windows y los espacios al principio y al final (los internos se conservan). Se rechazan las
rutas absolutas y cualquier componente `..`.

## Uso

```bash
./main.sh -d -f lista.txt                       # simula: muestra qué se crearía
./main.sh -f lista.txt -p "~/ruta/con espacios" # crea en otra carpeta, tras confirmar
./main.sh -y -f lista.txt -p ~/proyectos        # sin confirmación (scripts, cron)
./main.sh --version                             # imprime nombre y versión
```

| opción | por defecto | qué hace |
|---|---|---|
| `-f`, `--file ARCHIVO` | — (lista predefinida de `config.sh`) | archivo con un nombre de carpeta por línea |
| `-p`, `--path RUTA` | `.` (directorio actual) | directorio base; admite `~` aunque llegue entre comillas |
| `-d`, `--dry-run` | apagado | simula: no crea las carpetas de la lista (y no pregunta) |
| `-y`, `--yes` | apagado | no pide confirmación |
| `-v`, `--verbose` | apagado | mensajes de diagnóstico |
| `--no-color` | apagado | sin colores (también se apagan solos si la salida no es una terminal) |
| `--version` | — | imprime nombre y versión y sale |
| `-h`, `--help` | — | ayuda |

En `config.sh` se cambian el directorio base por defecto, cuántas carpetas enseña la vista previa (10) y la lista
predefinida (`PREDEFINED_FOLDERS`).

Códigos de salida: 0 bien (las carpetas que ya existían no cuentan como fallo), 1 si alguna carpeta falló, 2 uso
incorrecto o sin terminal para confirmar, 3 no existe el archivo o el directorio base (y no se acepta crearlo), 4 sin
permisos.

Requisitos: bash 4 o superior, `grep`, y `core/shell-lib/logger.sh` del espacio de trabajo.

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | carga la configuración y los módulos y ejecuta: argumentos → validación → lista → vista previa → confirmación → creación → resumen |
| `config.sh` | valores editables: directorio base, tamaño de la vista previa, lista predefinida |
| `lib/cli.sh` | lectura de opciones (`OPT_*`) y ayuda |
| `lib/logger.sh` | carga el logger común de `core/shell-lib/` y decide si hay colores |
| `lib/validator.sh` | directorio base (lo crea si se confirma), archivo de entrada, nombres seguros y confirmación |
| `lib/reader.sh` | lee la lista (archivo o predefinida) y sanea cada nombre |
| `lib/creator.sh` | crea o simula cada carpeta y lleva los cuatro contadores |
| `lib/ui.sh` | vista previa y resumen final |
| `suite.yml` | manifiesto de la suite (de él sale el bloque generado de arriba) |

## Límite honesto

- **Crea de verdad si no se pide `-d`.** Sin `-f` usa la lista predefinida de `config.sh`, que hoy son seis carpetas de
  un curso de 2022: ejecutar `./main.sh` a secas en una carpeta cualquiera y confirmar las crea ahí (ver
  `../estado.md` §Por hacer).
- **El directorio base se crea aunque se simule**: si `-p` apunta a una carpeta inexistente, con `-d` o `-y` la
  confirmación se da por aceptada y `mkdir -p` crea el directorio base antes de simular la lista.
- **Sin terminal pide `--yes`**: desde cron o una tubería sale con código 2 en vez de quedarse esperando.
- **No lee CSV ni Markdown** (eso lo hace la GUI) **ni tiene deshacer**: lo creado se borra a mano.
- **Necesita el espacio de trabajo**: `lib/logger.sh` busca `core/shell-lib/logger.sh` subiendo desde su carpeta;
  copiado fuera de `~/Documents` no arranca.
