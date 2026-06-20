# download_respos

Script en Bash para descargar repositorios de GitHub con control total sobre la profundidad del historial de commits: desde un snapshot del último commit hasta el historial completo, para uno, varios o todos los repos de una cuenta.

Nace de un caso de uso concreto: descargar manualmente, repo por repo, solo el commit más reciente de una veintena de proyectos personales (`git clone --depth 1 ...` repetido a mano). Este script automatiza ese flujo y lo extiende con todas las variantes razonables: profundidad ajustable, selección de repos, exclusión de forks, snapshot sin historial git, y soporte SSH/HTTPS.

## Tabla de contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso rápido](#uso-rápido)
- [Referencia de opciones](#referencia-de-opciones)
- [Casos de uso](#casos-de-uso)
- [Cómo funciona la profundidad de commits](#cómo-funciona-la-profundidad-de-commits)
- [Autenticación y límites de la API](#autenticación-y-límites-de-la-api)
- [Comportamiento ante errores y carpetas existentes](#comportamiento-ante-errores-y-carpetas-existentes)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Preguntas frecuentes](#preguntas-frecuentes)
- [Licencia](#licencia)

## Características

- **Profundidad de commits ajustable**: descarga solo el último commit (`-d 1`), los últimos N commits (`-d 5`), o el historial completo (`-d full`).
- **Tres modos de selección de repos**: todos los repos de una cuenta (`all`), una lista específica (`list`), o un solo repo (`single`).
- **Descubrimiento automático vía API de GitHub**: en modo `all`, el script consulta la API pública de GitHub y pagina automáticamente, sin necesidad de listar nombres de repos a mano.
- **Exclusión de forks por defecto**: al descargar "todos", los forks se omiten salvo que se indique lo contrario.
- **Exclusión de repos puntuales**: lista de nombres a saltar, útil para repos ya actualizados o irrelevantes.
- **Snapshot sin `.git`**: opción para eliminar el historial git tras clonar, dejando solo los archivos.
- **SSH o HTTPS**: elegible según la configuración de llaves del usuario.
- **Rama específica**: opción para clonar solo una rama en particular.
- **Soporte de token de autenticación**: para repos privados o para evitar el límite de peticiones de la API pública.
- **Idempotente por carpeta**: si una carpeta destino ya existe, se omite en vez de sobrescribirla.

## Requisitos

| Herramienta | Uso | Instalación (Kubuntu/Debian) | Instalación (Arch) |
|---|---|---|---|
| `git` | Clonado de repositorios | `sudo apt install git` | `sudo pacman -S git` |
| `curl` | Peticiones a la API de GitHub | `sudo apt install curl` | `sudo pacman -S curl` |
| `jq` | Parseo de respuestas JSON de la API | `sudo apt install jq` | `sudo pacman -S jq` |

Adicionalmente, si se usa el protocolo SSH (por defecto), se necesita una llave SSH configurada y asociada a la cuenta de GitHub. Para HTTPS no se requiere configuración previa de llaves, pero sí puede pedir credenciales según el repo.

## Instalación

```bash
# Descargar el script (o copiarlo desde donde se haya guardado)
chmod +x download_respos.sh

# Opcional: moverlo a un directorio en el PATH para invocarlo desde cualquier lugar
mv download_respos.sh ~/.local/bin/download_respos
```

## Uso rápido

```bash
./download_respos.sh -u USUARIO [opciones]
```

Ejemplo mínimo, descargar todos los repos propios con solo el último commit de cada uno:

```bash
cd Documents

./download_respos.sh -u achalmed -d 1
```

## Referencia de opciones

### Obligatoria

| Flag | Descripción |
|---|---|
| `-u USUARIO` | Usuario u organización de GitHub del cual descargar repos. |

### Modo de selección de repos

| Flag | Valores | Descripción |
|---|---|---|
| `-m` | `all` (por defecto), `list`, `single` | Define si se descargan todos los repos, una lista, o uno solo. |
| `-r` | string | Nombre(s) de repo(s). Obligatorio si `-m` es `list` (separados por coma) o `single`. |

### Control de profundidad

| Flag | Valores | Descripción |
|---|---|---|
| `-d` | `1` (por defecto), `N`, `full` | Profundidad de commits: `1` trae solo el último, `N` trae los últimos N, `full` trae el historial completo. |
| `-b` | nombre de rama | Clona solo esa rama, en vez de la rama por defecto del repo. |

### Otras opciones

| Flag | Valores | Descripción |
|---|---|---|
| `-o` | ruta | Carpeta destino donde se crean las subcarpetas de cada repo. Por defecto, el directorio actual. |
| `-p` | `ssh` (por defecto), `https` | Protocolo usado para clonar. |
| `-x` | string | Repos a excluir al usar `-m all`, separados por coma. |
| `-F` | (flag, sin valor) | Incluye forks al usar `-m all`. Por defecto se omiten. |
| `-s` | (flag, sin valor) | Elimina la carpeta `.git` tras clonar, dejando solo los archivos (snapshot puro). |
| `-t` | token | Token personal de GitHub. Alternativa: variable de entorno `GITHUB_TOKEN`. |
| `-h` | — | Muestra la ayuda y termina. |

## Casos de uso

### 1. Descargar todos los repos, solo el último commit

Equivale a automatizar la secuencia de `git clone --depth 1` repo por repo:

```bash
./download_respos.sh -u achalmed -d 1 -o ~/Documents/github-backup
```

### 2. Descargar todos los repos con un historial corto (últimos 5 commits)

Útil cuando se necesita algo de contexto reciente sin traer todo el historial:

```bash
./download_respos.sh -u achalmed -d 5
```

### 3. Descargar todo el historial completo de todos los repos

Equivale a un `git clone` normal, repo por repo:

```bash
./download_respos.sh -u achalmed -d full
```

### 4. Descargar solo repos puntuales

```bash
./download_respos.sh -u achalmed -m list -r "chaska,website-achalma,axiomata" -d 1
```

### 5. Descargar un único repo

```bash
./download_respos.sh -u achalmed -m single -r "scripts_for_zotero" -d 1
```

### 6. Descargar todos, excluyendo algunos puntuales

Útil para saltar repos que ya se tienen actualizados localmente:

```bash
./download_respos.sh -u achalmed -d 1 -x "Python,CampusTeX-Research"
```

### 7. Snapshot puro, sin historial git

Para cuando solo se necesitan los archivos tal como están, sin carpeta `.git` (más liviano, no permite hacer `git log`, `git pull`, etc.):

```bash
./download_respos.sh -u achalmed -d 1 -s
```

### 8. Usar HTTPS en vez de SSH

Útil en máquinas donde no hay una llave SSH configurada:

```bash
./download_respos.sh -u achalmed -d 1 -p https
```

### 9. Incluir forks en la descarga masiva

Por defecto los forks se omiten; para incluirlos:

```bash
./download_respos.sh -u achalmed -d 1 -F
```

### 10. Clonar solo una rama específica

```bash
./download_respos.sh -u achalmed -m single -r "website-achalma" -d 1 -b main
```

### 11. Combinar varias opciones

Todos los repos, últimos 3 commits, snapshot sin `.git`, excluyendo dos repos, en una carpeta específica:

```bash
./download_respos.sh -u achalmed -d 3 -s -x "Python,axiomata" -o ~/Documents/backup-2026
```

## Cómo funciona la profundidad de commits

El script traduce el valor de `-d` a las flags correspondientes de `git clone`:

| Valor de `-d` | Flag de git aplicada | Resultado |
|---|---|---|
| `1` | `--depth 1` | Solo el commit más reciente (HEAD). Más rápido y liviano. |
| `N` (ej. `5`) | `--depth 5` | Los últimos N commits de la rama clonada. |
| `full` o `0` | (ninguna, clon normal) | Historial completo, equivalente a `git clone` sin `--depth`. |

Importante: un clon con `--depth` (`1` o `N`) es un **shallow clone**. Esto significa que no se puede hacer `git log` más allá de la profundidad descargada, ni `git rebase`/`cherry-pick` contra commits fuera de ese rango, ni `git push` sin antes ejecutar `git fetch --unshallow` para recuperar el historial completo. Si el objetivo es solo trabajar con los archivos actuales (copiar a otro repo, revisar código, hacer una build), esto no representa ninguna limitación práctica.

## Autenticación y límites de la API

El script usa el endpoint público `https://api.github.com/users/{usuario}/repos` para listar repos en modo `all`. Esta API tiene límites de peticiones (rate limit):

- **Sin autenticar**: 60 peticiones por hora, compartidas por dirección IP.
- **Autenticado con token**: 5,000 peticiones por hora.

Si se descargan muchos repos seguidos o se ejecuta el script repetidamente en poco tiempo, es posible toparse con el límite sin token. El script detecta este caso (la API responde con un campo `message` de error) y lo reporta claramente en vez de fallar en silencio.

Para evitarlo, generar un token personal en GitHub (`Settings → Developer settings → Personal access tokens`) y pasarlo de cualquiera de estas dos formas:

```bash
# Como variable de entorno (recomendado, no queda en el historial de comandos)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
./download_respos.sh -u achalmed -d 1

# O como flag directo
./download_respos.sh -u achalmed -d 1 -t "ghp_xxxxxxxxxxxx"
```

Un token también es necesario si se quiere listar y descargar repositorios **privados** del usuario, ya que la API pública sin autenticar solo devuelve repos públicos.

## Comportamiento ante errores y carpetas existentes

- **Carpeta ya existente**: si la carpeta destino de un repo ya existe, el script la omite con un aviso, en vez de sobrescribirla o fallar. Para volver a descargar ese repo, hay que eliminar o mover la carpeta existente primero.
- **Repo individual que falla al clonar**: se reporta el error puntual de ese repo y el script continúa con el resto (no se detiene la descarga masiva por un solo fallo).
- **Usuario inexistente o error de API**: el script detecta la respuesta de error de la API de GitHub y termina con un mensaje claro, sin intentar procesar una lista vacía o corrupta.
- **Dependencias faltantes** (`git`, `curl`, `jq`): se valida su presencia al inicio y el script termina inmediatamente si falta alguna, indicando cuál.

## Limitaciones conocidas

- Solo lista repos del tipo `owner` (propios del usuario), no repos donde el usuario es colaborador pero no dueño.
- No descarga submódulos automáticamente (se podría añadir `--recurse-submodules` a `build_clone_flags` si se necesita en el futuro).
- El modo `all` no diferencia entre repos públicos y privados visualmente en el log; ambos se procesan igual si se usa un token con los permisos adecuados.
- No hay verificación de espacio en disco antes de iniciar la descarga masiva.

## Preguntas frecuentes

**¿Por qué `--depth 1` y no clonar todo y luego recortar?**
Porque `--depth` limita lo que se transfiere desde el servidor, no solo lo que se guarda localmente. Para repos con mucho historial acumulado, esto reduce tanto el tiempo de descarga como el espacio usado, no solo el resultado final.

**¿Puedo luego recuperar el historial completo de un repo descargado con `--depth 1`?**
Sí. Dentro de la carpeta del repo (siempre que no se haya usado `-s` para eliminar `.git`):

```bash
git fetch --unshallow
```

**¿Qué pasa si interrumpo el script a la mitad de una descarga masiva?**
Los repos ya clonados quedan completos en disco. Al volver a ejecutar el mismo comando, esos repos se omitirán automáticamente (por la validación de carpeta existente) y continuará con los que falten.

**¿Sirve para repos de una organización, no solo de un usuario personal?**
El script usa el endpoint `/users/{usuario}/repos`. Para organizaciones, GitHub también expone `/orgs/{org}/repos`, que tiene una estructura de respuesta similar; se podría adaptar el script cambiando esa URL si el caso de uso lo requiere.

## Licencia

Script de uso personal, sin licencia formal asignada. Libre de adaptar y reutilizar.