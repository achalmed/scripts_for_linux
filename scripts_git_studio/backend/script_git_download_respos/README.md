---
tipo: readme
estado: activo
---
# script_git_download_respos/ — clonado de uno, varios o todos los repos de una cuenta de GitHub con la profundidad que se pida (v2.0)

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

> Vive bajo la GUI `scripts_git_studio` desde 2026-07-13 (Git Studio); el CLI sigue funcionando desde esta carpeta y su `suite.yml` lo declara como suite.
> Descarga repositorios de GitHub con control total sobre la profundidad del
> historial de commits: desde un snapshot del último commit hasta el
> historial completo, para uno, varios o todos los repos de una cuenta.

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

Nace de un caso de uso concreto: descargar solo el commit más reciente de
una veintena de proyectos personales sin repetir `git clone --depth 1 ...` a
mano. Cubre:

1. Descargar **un** repo con N commits de profundidad (o todo el historial).
2. Descargar **varios** repos específicos (lista separada por comas).
3. Descargar **todos** los repos de un usuario/organización vía API de GitHub.
4. Clonar con `.git` (historial usable) o snapshot puro de archivos (`-s`).
5. Protocolo SSH o HTTPS, exclusión de repos, inclusión opcional de forks.
6. **Dry-run** (`-n`): ver qué se clonaría sin tocar la red de git.

## ⚙️ Requisitos

### Sistema Operativo

- Linux (Kubuntu/Debian, Arch) con `bash` >= 4.3 (namerefs).

### Dependencias

- `git` — siempre
- `curl` y `jq` — solo para el modo `-m all` (consulta a la API)

```bash
sudo apt install jq      # Kubuntu/Debian
sudo pacman -S jq        # Arch
```

## 🚀 Instalación

```bash
cd script_git_download_respos
chmod +x main.sh lib/*.sh
```

## 💻 Uso

### Sintaxis

```bash
./main.sh -u USUARIO [OPCIONES]
```

### Opciones disponibles

| Flag             | Descripción                                              | Requerido |
| ---------------- | -------------------------------------------------------- | --------- |
| `-u USUARIO`     | Usuario u organización de GitHub                          | Sí        |
| `-m all\|list\|single` | Modo de selección de repos (default: `all`)         | No        |
| `-r "a,b,c"`     | Repos a descargar (obligatorio con `list`/`single`)       | Según modo|
| `-d N\|full`     | Profundidad: 1 último commit (default), N últimos, `full`/`0` todo | No |
| `-b RAMA`        | Clonar solo una rama específica                           | No        |
| `-o DIRECTORIO`  | Carpeta destino (default: `./`)                           | No        |
| `-p ssh\|https`  | Protocolo de clonado (default: `ssh`)                     | No        |
| `-x "r1,r2"`     | Excluir repos en modo `all`                               | No        |
| `-F`             | Incluir forks en modo `all`                               | No        |
| `-s`             | Eliminar `.git` tras clonar (snapshot)                    | No        |
| `-t TOKEN`       | Token de GitHub (o variable `GITHUB_TOKEN`)               | No        |
| `-n`             | Dry-run: mostrar qué se clonaría                          | No        |
| `-v`             | Modo detallado                                            | No        |
| `-h`             | Mostrar ayuda                                             | No        |

### Ejemplos de uso

```bash
# Todos los repos, solo último commit, vía SSH
./main.sh -u achalmed -d 1

# Todos, últimos 5 commits, en carpeta específica
./main.sh -u achalmed -d 5 -o ~/Documents/github-backup

# Historial completo de todos los repos
./main.sh -u achalmed -d full

# Solo repos puntuales
./main.sh -u achalmed -m list -r "chaska,website-achalma,axiomata" -d 1

# Un repo, snapshot sin .git
./main.sh -u achalmed -m single -r "scripts_for_zotero" -s

# Simular la descarga de todos, excluyendo algunos
./main.sh -u achalmed -n -x "Python,CampusTeX-Research"
```

## 🗂️ Arquitectura

```
script_git_download_respos/
├── main.sh              # Punto de entrada — despacho por modo y resumen
├── config.sh            # Defaults editables (destino, profundidad, protocolo, API)
└── lib/
    ├── logger.sh        # Logging INFO/WARN/ERROR/DEBUG con colores auto-desactivables
    ├── cli.sh           # getopts compatible con la v1.x + dry-run
    ├── validator.sh     # Dependencias por modo, coherencia de opciones, destino
    ├── github_api.sh    # Lista paginada de repos con manejo de errores de red/API
    └── cloner.sh        # URL, flags, clonado individual y contadores
```

### Descripción de módulos

| Archivo              | Responsabilidad                                          |
| -------------------- | -------------------------------------------------------- |
| `main.sh`            | Orquestación y bucles de los modos `list`/`all`           |
| `config.sh`          | Constantes editables por el usuario                       |
| `lib/logger.sh`      | Salida consistente; WARN/ERROR a stderr                   |
| `lib/cli.sh`         | Flags y ayuda (mismas letras que la v1.x)                 |
| `lib/validator.sh`   | Fallar temprano: usuario, modo, protocolo, profundidad    |
| `lib/github_api.sh`  | Única pieza que habla con la red HTTP                     |
| `lib/cloner.sh`      | Única pieza que ejecuta `git clone`                       |

## 🐛 Bugs Corregidos

### Bug #1: Cuenta sin repos producía un clon de nombre vacío
- **Descripción**: con 0 repos, `printf '%s\n' "${repos[@]}"` sobre el array
  vacío emitía una línea en blanco; `mapfile` la convertía en un elemento
  `""` y el script intentaba `git clone` de un repo sin nombre.
- **Impacto**: error confuso de git en vez del mensaje "no se encontraron
  repos".
- **Corrección**: `fetch_all_repos()` no emite nada si no hay repos y `main`
  lo detecta con un mensaje claro.

### Bug #2: Flags de clone reconstruidas partiendo un string
- **Descripción**: `read -ra flags <<< "$(build_clone_flags)"` aplanaba el
  array a texto y lo re-partía por espacios.
- **Impacto**: nombres de rama con espacios o caracteres especiales rompían
  el comando `git clone`.
- **Corrección**: `build_clone_flags()` llena un array real por nameref
  (bash 4.3+); nunca se aplanan los argumentos.

### Bug #3: Protocolo inválido caía a HTTPS en silencio
- **Descripción**: `build_url` hacía `if ssh ... else https`; un typo como
  `-p shh` clonaba por HTTPS sin avisar.
- **Impacto**: comportamiento distinto al pedido sin ningún aviso (con repos
  privados, fallo de autenticación difícil de diagnosticar).
- **Corrección**: `validate_options()` rechaza cualquier protocolo que no
  sea `ssh` o `https` (salida 2).

### Bug #4: Profundidad sin validar
- **Descripción**: `-d abc` se pasaba tal cual a `git clone --depth abc`.
- **Impacto**: error críptico de git en cada repo del lote.
- **Corrección**: se valida como entero, `0` o `full` antes de empezar.

### Bug #5: Fallos de red de curl sin mensaje
- **Descripción**: con `set -e`, un fallo de `curl` (sin conexión, timeout)
  abortaba el script sin explicación; además no había timeout, con riesgo de
  cuelgue indefinido.
- **Impacto**: cortes silenciosos a mitad de proceso.
- **Corrección**: `curl -sf --max-time 30` con captura del error, mensaje
  específico ("¿sin conexión?") y extracción del mensaje real de la API
  cuando existe.

### Bug #6: La ayuda (-h) salía con código de error
- **Descripción**: `usage()` terminaba siempre con `exit 1`, incluso cuando
  el usuario pidió la ayuda explícitamente.
- **Impacto**: `./script -h && siguiente_comando` nunca ejecutaba la segunda
  parte; semántica de exit codes rota para scripting.
- **Corrección**: `-h` sale con 0; los errores de uso salen con 2.

### Bug #7: Dependencias exigidas aunque no se usaran
- **Descripción**: `curl` y `jq` se exigían siempre, pero solo el modo `all`
  los usa.
- **Impacto**: los modos `single`/`list` fallaban en máquinas sin `jq` pese a
  no necesitarlo.
- **Corrección**: `validate_dependencies()` exige `curl`/`jq` solo con
  `-m all`.

## 🔧 Solución de Problemas

### Error: "Falta el comando 'jq'"

```bash
sudo apt install jq        # Kubuntu/Debian
sudo pacman -S jq          # Arch
```

### Error de la API: "API rate limit exceeded"

Sin token, GitHub limita a 60 peticiones/hora por IP. Usa un token:

```bash
export GITHUB_TOKEN="ghp_..."
./main.sh -u achalmed
```

### "La carpeta 'X' ya existe, se omite"

Es el comportamiento esperado: el script nunca sobreescribe. Borra o mueve
la carpeta si quieres re-descargar el repo.

### Falla el clonado por SSH

Verifica tu clave (`ssh -T git@github.com`) o usa `-p https`.

## 🤝 Cómo Contribuir

1. Crea el módulo en lib/<tema>.sh con una única responsabilidad
   (p. ej. soporte de GitLab iría en su propio `gitlab_api.sh`).
2. Añade sus flags en `lib/cli.sh` y sus tunables en `config.sh`.
3. Cárgalo con `source` en `main.sh` en orden de dependencias.
4. Verifica con `bash -n` y prueba siempre primero con `-n` (dry-run).

### Estándares de código

- Máximo ~30 líneas por función; nombres verbo+sustantivo en inglés.
- Comentarios que explican el "por qué", no el "qué".
- `set -euo pipefail` y errores por stderr.

## ⚠️ Notas y Advertencias

- El endpoint `users/USUARIO/repos` **solo lista repos públicos** salvo que
  el token tenga permisos sobre los privados.
- En dry-run el contador "Descargados" significa "se clonarían".
- `-s` (strip `.git`) borra el historial local de forma irreversible para
  esa copia; el repo remoto no se toca.
- El código de salida es `1` si algún repo falló, `0` en caso contrario.

## Límite honesto

- **Solo GitHub**: el modo `all` usa `users/<usuario>/repos`, que sin token lista solo los públicos; `curl` y `jq` solo hacen falta ahí.
- **`-s` borra `.git` de la copia de forma irreversible**; el remoto no se toca.
- **No simula por defecto**: `-n` muestra qué se clonaría sin tocar la red de git.
- **No actualiza repos ya clonados**: eso es `script_git_sync_respos`.