---
tipo: readme
estado: activo
---
# script_git_sync_respos/ — sincronización (pull, commit, push) y estado de los repos del registro de Git Studio

<!-- suite:inicio -->
**Suite `git_sync_respos`** · objetivo *sistema* · estado *activo* · - · interfaz cli

Sincroniza (pull, add, commit, push) y reporta el estado de los repos del workspace listados en repos-config.yml, el registro que comparte con Git Studio.

- Escribe en: git · simula por defecto: no
- Entrada: repos-config.yml (base_directory y lista de repos habilitados)
- Depende de: bash >= 4, git
- Nota: Backend de Git Studio (páginas Sincronizar, Repositorios y Reportes); sigue siendo utilizable desde la terminal. Sin main.sh a propósito, dos entradas (sync.sh y status.sh) y config en lib/config.sh; repos-config.yml es el registro de repos que comparte con la GUI.

Comandos:

```bash
sync.sh --check
sync.sh -m "mensaje" -r "repo1,repo2"
status.sh --days 30
sync.sh --help
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Dos entradas de terminal sobre los repos que lista `repos-config.yml`, el inventario propio de Git Studio:

- **`sync.sh`** recorre los repos habilitados (o los que se le pidan con `-r`) y en cada uno hace `git pull`,
  detecta cambios, y si los hay `git add -A`, `git commit -m` y `git push`. Si el `pull` falla (ramas
  divergentes, conflictos) marca ese repo como error y sigue con el siguiente; no intenta fusionar. No hace
  `checkout`: si la rama activa no es la del registro, lo avisa y sigue en la activa.
- **`status.sh`** hace `git fetch` en cada repo habilitado y muestra el resumen global, la tabla de estado
  (cambios sin commit, commits sin push, commits remotos, divergencia), los repos que necesitan atención,
  la leyenda, las acciones sugeridas y la actividad de los últimos días. Limpia la pantalla al empezar.

Qué escribe: solo en los repos (commits y push) y solo `sync.sh`. Ninguno escribe registro en disco: la salida
va a la terminal. `status.sh` no modifica nada salvo las referencias remotas que actualiza `git fetch`.

No simula por defecto. `sync.sh --check` es la vista previa: no hace `pull`, `commit` ni `push`, muestra los
cambios pendientes y, si no hay cambios locales, hace `fetch` y avisa de los commits remotos pendientes.

Es el backend de las páginas Sincronizar, Repositorios y Reportes de Git Studio, que lo portan a
`gui-suites/git/git_app/services/` y comparten con él este mismo `repos-config.yml`.

## Uso

```bash
./status.sh                                   # estado de todos los repos habilitados
./status.sh --days 30                         # con la actividad del último mes
./sync.sh --check                             # vista previa: qué se sincronizaría
./sync.sh -m "docs: actualizar índices"       # sincroniza todos los habilitados
./sync.sh -r "04 index,04 index/_pubs/pub_axiomata" -m "docs: tema común"
./sync.sh -n -m "docs: cambio rápido"         # sin pull previo
./sync.sh --config "<otro registro>.yml" --check
```

`sync.sh`:

| opción | qué hace | por defecto |
|---|---|---|
| `-m`, `--message "texto"` | mensaje de commit | `default_commit_message` del registro |
| `-r`, `--repos "a,b"` | solo esos repos, por su `name` exacto; también los que tienen `enabled: false` | todos los habilitados |
| `-c`, `--check` | vista previa, sin pull, commit ni push | no |
| `-n`, `--no-pull` | no hace `git pull` antes de commitear | no |
| `-v`, `--verbose` | muestra la salida completa de git | no |
| `--config RUTA` | otro archivo de registro | `repos-config.yml` de esta carpeta |
| `-h`, `--help` | ayuda | — |

`status.sh`:

| opción | qué hace | por defecto |
|---|---|---|
| `--days N` | días de actividad reciente | `7` |
| `--config RUTA` | otro archivo de registro | `repos-config.yml` de esta carpeta |
| `-h`, `--help` | ayuda | — |

Salida: `sync.sh` termina con `1` si algún repo dio error o no hay repos que procesar; `status.sh`, con `1` si
no hay repos habilitados.

Requisitos: bash ≥ 4 (usa `mapfile`), `git`, y el logger común del workspace (`core/shell-lib/logger.sh`, en
su raíz), que `lib/logging.sh` busca subiendo carpetas.

### El registro

```yaml
base_directory: ~/Documents

repositories:

  - name: 04 index/_pubs/pub_axiomata
    branch: main
    enabled: true

  - name: 04 index
    branch: main
    enabled: false

default_commit_message: "update: sincronización automática de contenidos"
```

`name` es la ruta del repo relativa a `base_directory` (que admite `~` al principio) y puede llevar espacios
sin comillas. El parser no es YAML: `- name:` va con exactamente dos espacios delante, `branch:` y `enabled:`
con cuatro; sin comillas, anclas, listas en línea ni anidación; los comentarios solo en líneas propias, **nunca
detrás de una entrada** (pasan a formar parte del nombre). `enabled: false` aparta el repo sin borrarlo.
Una entrada sin `branch` o sin `enabled` toma `main` y `true`.

## Estructura

| archivo | qué hace |
|---|---|
| `sync.sh` | entrada de sincronización: opciones, filtro de repos, bucle y resumen |
| `status.sh` | entrada del reporte de estado |
| `repos-config.yml` | el registro: `base_directory`, repos y mensaje de commit por defecto |
| `lib/config.sh` | parser del registro (`grep`, `sed` y `awk`) y filtro de repos habilitados o pedidos |
| `lib/git_ops.sh` | envoltorios de los comandos git (cambios, ahead/behind, pull, add, commit, push) |
| `lib/sync_engine.sh` | proceso de un repo: validaciones, pull, cambios, commit y push |
| `lib/status_reporter.sh` | estado por repo, tabla, atención, sugerencias y actividad |
| `lib/logging.sh` | envoltorio del logger común con cabeceras y resumen propios |
| `install.sh` | instalador interactivo en otra carpeta; no funciona (ver Límite honesto) |
| `suite.yml` | manifiesto de la suite (genera el bloque de arriba) |

## Límite honesto

- **`repos-config.yml` no es el registro del workspace**: es el inventario propio de Git Studio, escrito a mano y
  paralelo al manifiesto del workspace (`meta/workspace.yml`, fuera de este repo), con el que no coincide. Lo leen
  `sync.sh`, `status.sh` y la GUI, y la GUI lo reescribe entero al añadir un repo o registrar uno clonado,
  perdiendo los comentarios. Si debe generarse desde el manifiesto está por decidir: ver `estado.md`
  §Por hacer.
- **Hoy una entrada lleva un comentario en su línea** («10 Class/contenido»), y por eso ni `sync.sh` ni
  `status.sh` la encuentran (ver `estado.md` §Por hacer).
- **`sync.sh` no ve archivos nuevos sin seguimiento**: detecta cambios con `git diff-index HEAD`, así que un
  repo cuyo único cambio es un archivo nuevo queda «sin cambios» y no se commitea. `status.sh` (con
  `git status --short`) y la GUI sí lo ven y lo marcan como cambio (ver `estado.md` §Por hacer).
- **`git add -A` sube todo** lo que el `.gitignore` de cada repo no excluya, con un solo mensaje para todos los
  repos.
- **Un repo se reconoce por una carpeta `.git`**: si `.git` es un archivo (worktree, submódulo con el gitdir
  fuera) se da como «no es un repositorio Git».
- **Sin red, los contadores de commits remotos quedan en 0** y el repo puede salir «SINCRONIZADO»; también sin
  upstream configurado.
- **`install.sh` no es una vía de uso.** La copia que deja en ~/bin/git-sync no arranca, porque `lib/logging.sh`
  no encuentra `core/` fuera del workspace; además solo detecta repos de primer nivel de la carpeta base y
  escribe alias en `~/.bashrc`. Se usa desde esta carpeta (ver `estado.md` §Por hacer).
- **Si falta el registro**, el mensaje aconseja `--init-config`, una opción que no existe.
- **No hay automatización en el repo**: ni unidad systemd ni entrada de cron; si se programa, hay que dar rutas
  absolutas y tener en cuenta que `sync.sh` hace push sin pedir confirmación.
