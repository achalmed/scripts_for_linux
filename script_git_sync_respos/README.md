# git-sync

Herramienta consolidada para sincronizar y monitorear múltiples repositorios Git desde una sola fuente de configuración. Reemplaza un conjunto anterior de tres scripts redundantes (`sync-repos.sh`, `sync-repos.py`, `quick-sync.sh`) que hacían esencialmente lo mismo con listas de repos duplicadas y desincronizadas entre sí.

Todo en Bash puro, sin dependencias externas (sin Python, sin PyYAML): un único script de sincronización, un único script de estado, ambos leyendo la misma lista de repos desde un solo archivo de configuración.

## Tabla de contenidos

- [Qué cambió respecto a la versión anterior](#qué-cambió-respecto-a-la-versión-anterior)
- [Estructura de archivos](#estructura-de-archivos)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso de sync.sh](#uso-de-syncsh)
- [Uso de status.sh](#uso-de-statussh)
- [Ejemplos de flujo de trabajo](#ejemplos-de-flujo-de-trabajo)
- [Aliases de shell](#aliases-de-shell)
- [Automatización con cron](#automatización-con-cron)
- [Solución de problemas](#solución-de-problemas)
- [Notas de diseño](#notas-de-diseño)

## Qué cambió respecto a la versión anterior

| Antes | Ahora |
|---|---|
| `sync-repos.sh`, `sync-repos.py`, `quick-sync.sh` (tres formas de sincronizar) | `sync.sh` (una sola) |
| Lista de repos duplicada en 3 archivos (`quick-sync.sh`, `repo-status.sh`, `repos-config.yml`) | Lista de repos en un solo lugar: `repos-config.yml` |
| `sync-repos.py` requería PyYAML instalado | Sin dependencias de Python |
| `repo-status.sh` tenía su propio array de repos, podía desincronizarse del resto | `status.sh` lee el mismo `repos-config.yml` que `sync.sh` |
| Pull fallido (ramas divergentes) se reportaba como advertencia y seguía de largo | Pull fallido detiene el procesamiento de ese repo y se reporta como error explícito |

## Estructura de archivos

```
git-sync/
├── sync.sh             # Sincroniza repos: pull + add + commit + push
├── status.sh           # Muestra el estado de todos los repos configurados
├── install.sh           # Instalador interactivo
├── repos-config.yml     # Lista de repos y configuración (única fuente de verdad)
└── README.md            # Este archivo
```

`sync.sh` y `status.sh` buscan `repos-config.yml` automáticamente en el mismo directorio donde están ellos mismos, así que no importa desde qué carpeta los ejecutes (siempre que uses la ruta completa o estés en esa carpeta).

## Requisitos

Solo `git` y `bash` (versión 4 o superior, por el uso de `mapfile`). Nada de Python, nada de `jq`, nada de `pip install`.

Verificar versión de bash si hay dudas:
```bash
bash --version
```

## Instalación

### Opción A: instalador interactivo

```bash
chmod +x install.sh
./install.sh
```

El instalador va a preguntar dónde instalar los scripts (por defecto `~/bin/git-sync`) y dónde están tus repositorios (por defecto `~/Documents/publicaciones`), copiará los archivos, ajustará `base_directory` en `repos-config.yml` automáticamente, detectará qué carpetas con `.git` existen en tu directorio de repos y te avisará cuáles ya están en la configuración y cuáles te falta agregar, y opcionalmente añadirá alias a tu `.bashrc` o `.zshrc`.

Si ya tienes un `repos-config.yml` instalado previamente, el instalador **no lo sobrescribe** (para no perder ediciones manuales tuyas); solo lo avisa.

### Opción B: instalación manual

```bash
mkdir -p ~/bin/git-sync
cp sync.sh status.sh repos-config.yml README.md ~/bin/git-sync/
chmod +x ~/bin/git-sync/sync.sh ~/bin/git-sync/status.sh
```

Luego edita `~/bin/git-sync/repos-config.yml` manualmente (ver siguiente sección).

## Configuración

Todo vive en `repos-config.yml`:

```yaml
base_directory: ~/Documents/publicaciones

repositories:
  - name: axiomata
    branch: main
    enabled: true

  - name: chaska
    branch: main
    enabled: true

  - name: experimental-blog
    branch: develop
    enabled: false   # deshabilitado: sync.sh y status.sh lo ignoran

default_commit_message: "update: sincronización automática de contenidos"
```

Reglas del formato (importante, porque el parser es ligero y espera esta estructura exacta):

- `name` debe coincidir exactamente con el nombre de la carpeta del repo dentro de `base_directory`.
- Cada repo necesita sus tres campos (`name`, `branch`, `enabled`) con la indentación exacta del ejemplo (`name` con 2 espacios antes de `- `, `branch` y `enabled` con 4 espacios).
- `enabled: false` saca al repo de las ejecuciones normales de `sync.sh` y `status.sh` sin necesidad de borrarlo del archivo. Útil para pausar temporalmente un repo sin perder su configuración.
- `base_directory` acepta `~` al inicio (se expande automáticamente) o una ruta absoluta.

Ya viene pre-cargado con tu lista de repos actual (los blogs de Quarto, los repos de scripts, CampusTeX, Python, etc.). Si creas un repo nuevo, solo añade un bloque más siguiendo el mismo patrón.

## Uso de sync.sh

```
Uso: sync.sh [OPCIONES]

Opciones:
  -m, --message "texto"      Mensaje de commit. Si no se indica, se usa
                              default_commit_message del archivo de config.
  -r, --repos "a,b,c"        Sincronizar solo estos repos (nombres separados
                              por coma). Si no se indica, se procesan todos
                              los repos con enabled: true.
  -c, --check                Solo mostrar qué cambió, sin hacer commit ni push.
  -v, --verbose               Modo detallado (muestra git status, salida de pull/push).
  -n, --no-pull               No hacer 'git pull' antes de sincronizar.
      --config RUTA           Usar un archivo de configuración distinto.
  -h, --help                  Mostrar esta ayuda.
```

Por cada repo, `sync.sh` hace en orden: `git pull` (salvo `-n`/`-c`), revisa si hay cambios sin commitear, si los hay hace `git add -A`, `git commit -m "mensaje"` y `git push`. Si no hay cambios, lo reporta y pasa al siguiente sin tocar nada.

Si `git pull` falla (por ejemplo, ramas divergentes que requieren resolución manual), el script **detiene el procesamiento de ese repo específico y lo marca como error**, en vez de continuar como si no hubiera pasado nada. Esto evita que un conflicto silencioso termine generando un commit o push sobre un estado inconsistente.

### Ejemplos

Sincronizar todos los repos habilitados con el mensaje por defecto:
```bash
./sync.sh
```

Con mensaje personalizado:
```bash
./sync.sh -m "feat: nuevo artículo sobre inflación"
```

Solo un subconjunto de repos:
```bash
./sync.sh -r "axiomata,chaska" -m "docs: actualizar índices"
```

Solo revisar qué cambió, sin commitear ni pushear nada (seguro, no modifica nada):
```bash
./sync.sh -c
```

Modo detallado, para ver exactamente qué hace cada comando git internamente:
```bash
./sync.sh -v -m "chore: actualizar scripts"
```

Sincronizar sin hacer pull primero (por ejemplo, si sabes que no hay nada nuevo en remoto y quieres ahorrar tiempo):
```bash
./sync.sh -n -m "docs: cambio rápido"
```

## Uso de status.sh

```
Uso: status.sh [OPCIONES]

Opciones:
      --config RUTA    Usar un archivo de configuración distinto.
  -h, --help            Mostrar esta ayuda.
```

Sin opciones, simplemente recorre todos los repos habilitados en `repos-config.yml` y muestra una tabla con: rama actual, estado (sincronizado, cambios sin commit, commits sin push, o commits remotos pendientes de pull), y un detalle ampliado de los repos que necesitan atención, además de un resumen de actividad de los últimos 7 días.

```bash
./status.sh
```

Los estados posibles, de mayor a menor prioridad si se combinan varios:

| Estado | Significado |
|---|---|
| `CAMBIOS SIN COMMIT` | Hay archivos modificados que no se han agregado/commiteado |
| `COMMITS SIN PUSH` | Hay commits locales que no se han enviado al remoto |
| `COMMITS REMOTOS (PULL NECESARIO)` | El remoto tiene commits que no están en tu copia local |
| `SINCRONIZADO` | Todo al día |

Un repo puede mostrar simultáneamente "commits sin push" y "commits remotos pendientes" (ramas divergentes); en ese caso aparecen ambos contadores (`↑n ↓n`) en la tabla.

Al final, si hay repos que necesitan atención, `status.sh` sugiere el comando exacto de `sync.sh` para resolverlo.

## Ejemplos de flujo de trabajo

### Fin del día de trabajo

```bash
# 1. Ver qué cambió en todos los repos
./status.sh

# 2. Si hay cambios, sincronizar todos
./sync.sh -m "update: cambios del $(date +%Y-%m-%d)"

# 3. Confirmar que todo quedó sincronizado
./status.sh
```

### Modificaste un archivo compartido (enlace duro, tema, configuración global)

Como estos archivos suelen reflejarse en varios repos a la vez (por ejemplo `_metadata.yml` como enlace duro entre blogs de Quarto):

```bash
./sync.sh -c                                    # ver qué repos se afectaron
./sync.sh -m "feat(config): activar comentarios Giscus en todos los blogs"
```

### Script regeneró todos los índices

```bash
# 1. Ejecutar el generador de índices (fuera de git-sync)
cd ~/Documents/scripts_for_quarto/script_generador_indice_quarto
./generar_indices.sh

# 2. Sincronizar con mensaje apropiado
cd ~/bin/git-sync
./sync.sh -m "docs: regenerar índices automáticos - $(date +%Y-%m-%d)"
```

### Actualizar solo los blogs de un tema específico

```bash
./sync.sh -r "pecunia-fluxus,epsilon-y-beta,optimums" \
  -m "docs: actualizar índices económicos Q4-2025"

./sync.sh -r "axiomata,dialectica-y-mercado,res-publica" \
  -m "docs: actualizar índices filosóficos"
```

### Verificación antes de un push importante

```bash
./status.sh
read -p "¿Continuar con la sincronización? (s/n): " confirm
[[ $confirm == [sS] ]] && ./sync.sh -m "feat: cambio importante" -v
```

## Aliases de shell

Si usaste el instalador y aceptaste agregar aliases, ya tienes disponibles `gsync`, `gstatus` y la función `gsyncm`. Si los agregas manualmente, esto va en tu `~/.bashrc` o `~/.zshrc`:

```bash
alias gsync='~/bin/git-sync/sync.sh'
alias gstatus='~/bin/git-sync/status.sh'
gsyncm() {
    ~/bin/git-sync/sync.sh -m "$1"
}
```

Después de editar, recarga la configuración:
```bash
source ~/.bashrc   # o source ~/.zshrc
```

Uso:
```bash
gstatus                              # ver estado de todos los repos
gsync                                 # sincronizar todos
gsyncm "feat: nuevo post"            # sincronizar con mensaje
```

## Automatización con cron

Para sincronizar automáticamente todos los días a una hora fija:

```bash
crontab -e
```

Agregar (ejemplo: sincronizar a las 6pm todos los días):
```
0 18 * * * /home/achalmaedison/bin/git-sync/sync.sh -m "auto: sincronización diaria" >> /tmp/git-sync.log 2>&1
```

Importante: en cron no hay variables de entorno interactivas (no hay `$HOME` garantizado igual que en tu shell), así que usa siempre rutas absolutas tanto para invocar `sync.sh` como dentro de `repos-config.yml`.

## Solución de problemas

### "No se encontró el archivo de configuración"

`sync.sh` y `status.sh` buscan `repos-config.yml` en su propio directorio. Si lo moviste o renombraste, usa `--config /ruta/a/tu/archivo.yml`.

### "git pull falló" / ramas divergentes

Esto ocurre cuando el historial local y remoto divergieron (por ejemplo, hiciste commits en dos máquinas distintas sin sincronizar entre medio). `sync.sh` detiene el procesamiento de ese repo en vez de intentar resolverlo automáticamente, porque forzar una estrategia de merge sin que lo decidas tú es peligroso. Entra al repo manualmente:

```bash
cd ~/Documents/publicaciones/repo-con-problema
git pull   # verás el conflicto real y las opciones de git para reconciliarlo
# resolver conflictos si los hay
git add .
git commit
git push
```

Luego vuelve a correr `sync.sh` normalmente; ese repo ya estará al día.

### Un repo no aparece en status.sh aunque existe

Revisa que esté en `repos-config.yml` con `enabled: true`, que el `name:` coincida exactamente con el nombre de la carpeta, y que la carpeta efectivamente contenga un `.git` (si clonaste con `--depth 1` y luego eliminaste `.git`, por ejemplo, ya no cuenta como repo Git).

### "Permission denied" al ejecutar los scripts

```bash
chmod +x sync.sh status.sh install.sh
```

### Quiero ver exactamente qué comando git está fallando

Usa `-v` en `sync.sh`; en modo verbose se muestra la salida completa de `git pull`, `git status`, y `git push`, sin silenciar nada.

## Notas de diseño

- **Por qué Bash y no Python**: se eliminó la dependencia de PyYAML deliberadamente. El parser de YAML incluido en ambos scripts es deliberadamente simple (basado en `awk`/`grep`/`sed`), no un parser YAML genérico. Funciona correctamente con la estructura exacta de `repos-config.yml` tal como se documenta arriba; no soporta YAML arbitrario (anidación profunda, listas inline, anchors, etc.).
- **Por qué un solo script de sync y no tres**: los tres scripts anteriores (`sync-repos.sh`, `sync-repos.py`, `quick-sync.sh`) cubrían el mismo caso de uso central (pull + commit + push masivo) con distintos niveles de opciones. Mantener tres implementaciones significaba mantener tres listas de repos y tres lugares donde un bug podía vivir sin que el otro lo heredara. `sync.sh` cubre el caso simple (`./sync.sh`) y el caso avanzado (`-r`, `-c`, `-v`, `-n`) en un solo árbol de opciones.
- **Por qué pull fallido detiene el repo en vez de continuar**: en la versión anterior, un `git pull` fallido por ramas divergentes se registraba como advertencia y el script seguía como si el repo estuviera limpio, lo cual podía llevar a hacer commit/push sobre un estado de merge sin resolver. Ahora se trata como error explícito y ese repo queda fuera del conteo de "sincronizados".
- **Por qué `status.sh` y `sync.sh` comparten el mismo `repos-config.yml`**: en la versión anterior, `repo-status.sh` tenía su propio array de nombres de repos hardcodeado, independiente del de `quick-sync.sh` y de `repos-config.yml`. Si agregabas un repo nuevo, había que recordar actualizarlo en tres lugares. Ahora hay una sola fuente de verdad.

---

**Autor**: Edison Achalma (achalmed)
