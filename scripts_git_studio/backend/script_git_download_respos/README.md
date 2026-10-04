---
tipo: readme
estado: activo
---
# script_git_download_respos/ — clonado de uno, varios o todos los repos de una cuenta de GitHub con la profundidad de historial que se pida

<!-- suite:inicio -->
**Suite `git_download_respos`** · objetivo *sistema* · estado *activo* · bash · interfaz cli

Clona uno, varios o todos los repos de una cuenta de GitHub con la profundidad de historial que se pida, por SSH o HTTPS, con dry-run.

- Escribe en: git · simula por defecto: no
- Entrada: la API de GitHub (users/<usuario>/repos) o una lista de repos
- Depende de: bash, git, curl y jq (solo en modo all)
- Nota: Backend de Git Studio (página Clonar; la GUI lo porta a app/services/clone_service.py y github_service.py) desde 2026-07-13; sigue siendo utilizable desde la terminal. GITHUB_TOKEN o -t para repos privados.

Comandos:

```bash
main.sh -u <usuario> -n
main.sh -u <usuario> -m list -r "repo1,repo2" -d full
main.sh -u <usuario> -o <carpeta> -s
main.sh -h
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Clona repos de una cuenta de GitHub en tres modos: **todos** los de la cuenta (`-m all`, por defecto, que
consulta la API), una **lista** (`-m list`) o **uno** (`-m single`). Controla la profundidad del historial
(último commit, los N últimos o completo), el protocolo (SSH o HTTPS), la rama, las exclusiones y los forks,
y puede dejar una copia sin `.git` (snapshot). Es el backend de la página Clonar de Git Studio, que lo porta a
`../../app/services/clone_service.py` y `../../app/services/github_service.py`; desde la terminal funciona por
su cuenta.

Qué escribe y dónde: crea la carpeta destino (`-o`, por defecto la actual) y dentro una subcarpeta por repo con
`git clone`. Una carpeta que ya existe se omite, nunca se sobrescribe. Con `-s` borra el `.git` de cada copia.
No escribe registro en disco: la salida va a la terminal (avisos y errores a stderr) y termina con el resumen
«Descargados · Omitidos · Fallidos».

No simula por defecto; `-n` muestra qué se clonaría sin ejecutar `git clone`.

## Uso

```bash
./main.sh -u <usuario> -n                               # simula: qué repos de la cuenta se clonarían
./main.sh -u <usuario> -d 1 -o "<carpeta destino>"     # todos, solo el último commit
./main.sh -u <usuario> -m list -r "repo1,repo2" -d full # dos repos con todo el historial
./main.sh -u <usuario> -m single -r repo1 -s           # un repo, sin .git
./main.sh -u <usuario> -n -x "repo1,repo2" -F          # todos menos dos, forks incluidos
./main.sh -h
```

| opción | qué hace | por defecto |
|---|---|---|
| `-u USUARIO` | usuario u organización de GitHub (obligatoria) | — |
| `-m all\|list\|single` | modo de selección | `all` |
| `-r "a,b"` | repos a clonar (obligatoria con `list` y `single`) | — |
| `-d N\|full` | profundidad: `1` último commit, `N` los N últimos, `full` o `0` todo | `1` |
| `-b RAMA` | clona solo esa rama (`--single-branch`) | la del remoto |
| `-o DIRECTORIO` | carpeta destino; se crea si no existe | `.` |
| `-p ssh\|https` | protocolo; otro valor es error | `ssh` |
| `-x "a,b"` | repos que se excluyen en modo `all` | — |
| `-F` | incluye los forks en modo `all` | se omiten |
| `-s` | borra `.git` tras clonar | no |
| `-t TOKEN` | token de GitHub para la API | `GITHUB_TOKEN` |
| `-n` | simula | no |
| `-v` | salida detallada | no |
| `-h` | ayuda | — |

Los valores por defecto viven en `config.sh`. Códigos de salida: `0` todo bien, `1` algún repo falló o la API
no respondió, `2` error de uso, `4` no se pudo crear el destino, `5` falta una dependencia.

Requisitos: bash ≥ 4.3 (usa `local -n`), `git`; `curl` y `jq` solo en modo `all`; el logger común del
workspace (`core/shell-lib/logger.sh`, en su raíz), que `lib/logger.sh` busca subiendo carpetas.

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | carga módulos, valida, prepara el destino, despacha por modo y resume |
| `config.sh` | valores por defecto (destino, profundidad, protocolo, modo) y la URL de la API |
| `lib/cli.sh` | lectura de opciones con `getopts` y la ayuda |
| `lib/validator.sh` | dependencias según el modo, coherencia de opciones y creación del destino |
| `lib/github_api.sh` | lista paginada de repos (`nombre\|es_fork`) y traducción de errores de la API |
| `lib/cloner.sh` | URL y opciones de `git clone`, clonado, snapshot, exclusiones y contadores |
| `lib/logger.sh` | envoltorio del logger común y colores |
| `suite.yml` | manifiesto de la suite (genera el bloque de arriba) |

## Límite honesto

- **Repos privados**: el modo `all` consulta `users/<usuario>/repos`, que lista los repos públicos; el token
  solo se envía como cabecera de autorización. No está verificado contra la API si con token aparecen los
  privados (ver `docs/decisiones.md` §Pendientes). Con `-m list` o `-m single` no se consulta la API: se clona
  por nombre con las credenciales de git (clave SSH o HTTPS).
- **`-t` deja el token visible** en la lista de procesos mientras corre; es preferible `GITHUB_TOKEN`.
- **`-n` no es inocuo del todo**: crea la carpeta destino y, en modo `all`, consulta la API. En simulación,
  «Descargados» significa «se clonarían».
- **`-m single` toma `-r` entero como un nombre**: `-r "a,b"` no clona dos repos, intenta uno llamado `a,b`.
- **`-s` borra el historial de la copia sin vuelta atrás**; el remoto no se toca.
- **No actualiza repos ya clonados**: los omite. Actualizar es `../script_git_sync_respos/`.
- **Solo GitHub**: la URL de clonado y la API están fijas a github.com.
