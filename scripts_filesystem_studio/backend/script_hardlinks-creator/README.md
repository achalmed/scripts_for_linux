---
tipo: readme
estado: activo
---
# script_hardlinks-creator/ — sustituye por hard links los archivos de igual nombre y contenido idéntico de un árbol

<!-- suite:inicio -->
**Suite `hardlinks_creator`** · objetivo *sistema* · estado *activo* · python · interfaz cli

Sustituye por hard links los archivos de igual nombre y contenido idéntico (SHA-256) de un árbol, uno a uno o por lotes de nombres.

- Escribe en: archivos · simula por defecto: no
- Entrada: un árbol de proyectos (por defecto la raíz del workspace)
- Depende de: python3
- Nota: Backend de Filesystem Studio (pestaña Crear de Hardlinks; la GUI reutiliza su lib/); sigue siendo utilizable desde la terminal. Enlace atómico; _extensions/ excluida por defecto.

Comandos:

```bash
main.py <nombre> --dry-run
main.py <nombre> -d <carpeta> --auto --report-json reporte.json
main.py --batch archivos.txt --dry-run
main.py --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Busca en un árbol todos los archivos con un nombre exacto (por ejemplo `_metadata.yml`), los agrupa por contenido
idéntico (SHA-256) y sustituye las copias por hard links a una de ellas, de modo que el contenido se guarda una sola
vez. Trabaja con un nombre suelto o con una lista de nombres (`--batch`).

Para cada grupo distingue los archivos que ya comparten inodo (ya enlazados) de los candidatos, descarta los que
están en otro sistema de archivos o sin permiso de escritura y, salvo con `--auto`, pide confirmación por grupo. El
enlace es atómico: renombra el destino a `<archivo>.hltmp`, crea el enlace y solo entonces borra el temporal; si el
enlace falla, restaura el original.

Qué escribe: solo reemplaza archivos del árbol por hard links, y un reporte JSON si se pide con `--report-json`
(crea las carpetas que falten). No deja log. **No simula por defecto**: la simulación se pide con `--dry-run`.

Es el backend de la pestaña Crear de la página Hardlinks de [Filesystem Studio](../../README.md), que importa
directamente su `lib/`. Para solo auditar qué hard links existen ya, use
[`script_hardlinks-detector`](../script_hardlinks-detector/README.md).

## Uso

```bash
python3 main.py _metadata.yml --dry-run                       # simula sobre el directorio por defecto
python3 main.py _quarto.yml -d "$HOME/Documents/04 index"     # otro directorio raíz
python3 main.py --batch archivos.txt --dry-run                # varios nombres, simulado
python3 main.py .editorconfig --exclude build dist --auto     # sin confirmación por grupo
python3 main.py _metadata.yml --report-json /tmp/reporte.json
python3 main.py --version                                     # imprime la versión
```

| opción | por defecto | qué hace |
|---|---|---|
| `filename` (posicional) | — | nombre exacto que se busca, sin rutas; excluyente con `--batch` (uno de los dos es obligatorio) |
| `-b`, `--batch FILE` | — | archivo con un nombre por línea; ignora líneas vacías, las que empiezan por `#` y los duplicados |
| `-d`, `--directory DIR` | `$DOCS_ROOT` o, si no está definida, `~/Documents` | directorio raíz de la búsqueda |
| `--exclude DIR …` | — | carpetas que se suman a las exclusiones de `config.py` |
| `--replace-exclude DIR …` | — | sustituye por completo las exclusiones de `config.py` |
| `--auto` | apagado | enlaza todos los grupos sin preguntar |
| `--dry-run` | apagado | simula: dice cuántos enlaces crearía, sin tocar el disco |
| `--report-json FILE` | — | guarda un reporte JSON con estadísticas y grupos |
| `--no-color` | apagado | sin colores ANSI |
| `-v`, `--verbose` | apagado | mensajes de depuración |
| `--version`, `-h`, `--help` | — | versión y ayuda |

En `config.py` se cambian el directorio por defecto, la lista de exclusiones, el tamaño de bloque del hash y un archivo
de log opcional (`LOG_FILE`, desactivado).

Códigos de salida: 0 bien, 1 algún enlace falló (en `--batch`, también si un nombre no se encontró o era inválido),
2 argumentos inválidos o lista vacía, 3 directorio o lista inexistente, 4 sin permisos de lectura, 130 interrumpido.

Requisitos: Python 3.10 o superior (solo biblioteca estándar) y `core/py-common/logger.py` del espacio de trabajo.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | resuelve directorio y exclusiones y despacha al modo de un nombre o al de lista |
| `config.py` | versión, directorio por defecto, exclusiones, tamaño de bloque, log opcional, códigos de salida |
| `lib/cli.py` | definición de las opciones (`argparse`) |
| `lib/validator.py` | directorio, nombre sin rutas, permiso de escritura, mismo sistema de archivos |
| `lib/scanner.py` | recorrido con poda de exclusiones, SHA-256 por bloques, agrupación por contenido |
| `lib/linker.py` | agrupación por inodo, confirmación y enlace atómico (`_atomic_link`, que también usa la GUI) |
| `lib/pipeline.py` | escaneo → enlace para un nombre; lo comparten los dos modos |
| `lib/batch.py` | lectura y limpieza de la lista de `--batch` |
| `lib/reporter.py` | reporte JSON de un nombre o de un lote |
| `lib/ui.py` | salida en terminal: cabeceras, grupos, resúmenes, pregunta por grupo |
| `lib/logger.py` | carga el logger común de `core/py-common/` y las constantes de color |
| `lib/__init__.py` | marca `lib/` como paquete |
| `suite.yml` | manifiesto de la suite (de él sale el bloque generado de arriba) |

`archivos.txt`, si existe, es una lista local de ejemplo para `--batch`; no se versiona (está en el `.gitignore` raíz).

## Límite honesto

- **Las exclusiones son rutas relativas a la raíz de búsqueda, no nombres**: `.git`, `_site` o `_extensions` solo se
  excluyen justo debajo del directorio indicado con `-d`; las de un nivel más hondo (`04 index/_site`, una
  `_extensions/` dentro de un sitio) se recorren. Para excluir una carpeta profunda, pásela relativa a la raíz con
  `--exclude`.
- **La lista de exclusiones por sitio de `config.py` está desfasada**: nombra `pub_*/` y `website-achalma/` en la raíz,
  rutas que hoy no existen; no excluyen nada (ver `../../../docs/decisiones.md` §Pendientes).
- **Sin terminal, enlaza sin preguntar**: la pregunta por grupo toma `[S/n]` como sí por defecto, también si la entrada
  se cierra (tubería, cron). Use `--dry-run` primero.
- **La fuente de cada grupo es arbitraria**: es el primer inodo que aparece en el recorrido; como el contenido es
  idéntico, no se pierde nada, pero los metadatos (dueño, permisos, fechas) que quedan son los de ese archivo.
- **Los hard links comparten contenido**: editar uno edita todos; un editor que guarda escribiendo un archivo nuevo y
  renombrándolo rompe el enlace sin avisar.
- **No cruza sistemas de archivos**: los candidatos en otro volumen se omiten y cuentan como error.
- **Necesita el espacio de trabajo**: `lib/logger.py` busca `core/py-common/logger.py` subiendo desde su carpeta.
