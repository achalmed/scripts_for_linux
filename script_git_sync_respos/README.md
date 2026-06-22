# git-sync v2.0

Herramienta modular para sincronizar y monitorear múltiples repositorios Git
desde una sola fuente de configuración. Reemplaza el conjunto anterior de
tres scripts redundantes (`sync-repos.sh`, `sync-repos.py`, `quick-sync.sh`)
con una arquitectura limpia: un módulo por responsabilidad, cero dependencias
externas (sin Python, sin `jq`, sin `pip install`).

---

## 📋 Índice

1. [Qué cambió en v2.0](#1-qué-cambió-en-v20)
2. [Bugs corregidos](#2-bugs-corregidos)
3. [Estructura del proyecto](#3-estructura-del-proyecto)
4. [Requisitos](#4-requisitos)
5. [Instalación](#5-instalación)
6. [Configuración](#6-configuración)
7. [Uso de sync.sh](#7-uso-de-syncsh)
8. [Uso de status.sh](#8-uso-de-statussh)
9. [Flujos de trabajo comunes](#9-flujos-de-trabajo-comunes)
10. [Aliases de shell](#10-aliases-de-shell)
11. [Automatización con cron](#11-automatización-con-cron)
12. [Añadir funcionalidades nuevas](#12-añadir-funcionalidades-nuevas)
13. [Solución de problemas](#13-solución-de-problemas)

---

## 1. Qué cambió en v2.0

| Antes (v1.x)                                                                   | Ahora (v2.0)                                              |
| ------------------------------------------------------------------------------ | --------------------------------------------------------- |
| `sync-repos.sh`, `sync-repos.py`, `quick-sync.sh` (tres formas de sincronizar) | `sync.sh` (una sola)                                      |
| Lista de repos duplicada en 3 archivos                                         | Una sola fuente de verdad: `repos-config.yml`             |
| `sync-repos.py` requería PyYAML instalado                                      | Sin dependencias externas                                 |
| `repo-status.sh` con su propio array hardcodeado                               | `status.sh` lee el mismo `repos-config.yml` que `sync.sh` |
| Código monolítico (~600 líneas en 2 archivos)                                  | Arquitectura modular: `main.sh` + 4 módulos en `lib/`     |
| 7 bugs identificados                                                           | Todos corregidos (ver sección 2)                          |
| Repos con nombres viejos sin prefijo                                           | Actualizado al formato `pub_*` + `website-achalma`        |

---

## 2. Bugs corregidos

### Bug 1 — `git diff-index` fallaba en repos sin commits

**Archivo:** `lib/git_ops.sh` → `git_has_local_changes()`

**Problema original:** `git diff-index --quiet HEAD` retorna exit code 128 cuando
el repo no tiene ningún commit todavía (recién clonado o inicializado vacío).
El script interpretaba ese error como "sin cambios", ignorando cualquier
archivo presente.

**Corrección:** Se verifica si `HEAD` existe antes de llamar `diff-index`. En
repos sin commits, se usa `git status --porcelain` para detectar cambios.

---

### Bug 2 — Contadores `behind`/`ahead` siempre incorrectos sin fetch previo

**Archivo:** `lib/status_reporter.sh` → `status_collect_repo()`

**Problema original:** `git log origin/main..main` compara contra la copia
**local** de `origin/`, no contra el servidor. Si no se había hecho `fetch`
en días, el contador de "commits remotos pendientes" era siempre 0 aunque
hubiera docenas de commits nuevos en GitHub.

**Corrección:** `status_collect_repo()` llama `git_fetch_remote()` antes de
calcular los contadores. El fallo de fetch (sin red) es silencioso y los
contadores quedan en 0, sin abortar el script.

---

### Bug 3 — Variable `remote` declarada y nunca usada

**Archivo:** `lib/status_reporter.sh`

**Problema original:** En `get_repo_info()` del script original, se declaraba
`local branch remote last_commit` pero `remote` nunca se asignaba ni usaba.
Era un residuo de código anterior que confundía al lector (shellcheck SC2034).

**Corrección:** Variable eliminada.

---

### Bug 4 — `set -uo pipefail` podía abortar el loop completo

**Archivo:** `sync.sh` + `lib/sync_engine.sh`

**Problema original:** El loop principal llamaba `process_repo` y luego
`result=$?`. Con `set -uo pipefail` activo, si `process_repo` generaba algún
error no capturado antes del `return`, pipefail abortaba el script entero en
vez de dejar que el loop continuara con el siguiente repositorio.

**Corrección:** Todos los paths de error dentro de `sync_process_repo` terminan
con `return` explícito. El llamador usa `|| result=$?` para capturar el código
de retorno sin dejar que ningún error burbujee hacia `pipefail`.

---

### Bug 5 — `sed -i.bak` no portátil en macOS

**Archivo:** `install.sh`

**Problema original:** `sed -i.bak -E "..."` funciona en Linux (GNU sed) pero
en macOS (BSD sed) la sintaxis es `sed -i '' -E "..."`. En macOS, el script
creaba un archivo `.bak` extra y no editaba el archivo original correctamente.

**Corrección:** La función `sed_inplace()` detecta la versión de sed (`gnu`
vs `bsd`) y usa la sintaxis correcta para cada caso.

---

### Bug 6 — `--check` no detectaba commits remotos pendientes

**Archivo:** `lib/sync_engine.sh` → `sync_process_repo()`

**Problema original:** El modo `--check` usaba `git diff-index HEAD` para
detectar cambios locales. Si un repo solo tenía commits nuevos en el remoto
(necesitaba `pull`) pero ningún cambio local, `--check` lo reportaba como
"SINCRONIZADO", ocultando que había trabajo pendiente.

**Corrección:** En modo `--check`, después de verificar cambios locales, se
hace `git fetch` y se cuenta `behind`. Si `behind > 0` se reporta
"commits remotos pendientes" explícitamente.

---

### Bug 7 — Nombres de repos desactualizados en `repos-config.yml`

**Archivo:** `repos-config.yml`

**Problema original:** Los repos estaban listados sin prefijo (`axiomata`,
`chaska`, etc.) pero las carpetas reales en `~/Documents` ahora usan el
formato `pub_axiomata`, `pub_chaska`, etc.

**Corrección:** Todos los nombres de blogs actualizados al formato `pub_*`.
`base_directory` actualizado a `~/Documents` (en vez de `~/Documents/publicaciones`).

---

## 3. Estructura del proyecto

```
git-sync/
├── sync.sh                   ⭐ Sincroniza repos: pull + add + commit + push
├── status.sh                 📊 Reporte de estado de todos los repos
├── install.sh                🔧 Instalador interactivo
├── repos-config.yml          ⚙️  Lista de repos y configuración (fuente única)
├── README.md                 📖 Este archivo
└── lib/
    ├── logging.sh            🖨️  Sistema de logging (INFO/OK/AVISO/ERROR)
    ├── config.sh             📄 Parser de repos-config.yml y variables globales
    ├── git_ops.sh            🐙 Wrappers seguros para comandos git
    ├── sync_engine.sh        🔄 Motor de sincronización (lógica de process_repo)
    └── status_reporter.sh    📈 Recolección y presentación del estado
```

**Cada módulo tiene una responsabilidad única.** `sync.sh` y `status.sh` son
orquestadores: parsean argumentos, cargan módulos y llaman funciones. Toda la
lógica real vive en `lib/`.

---

## 4. Requisitos

Solo `git` y `bash` versión 4 o superior (para `mapfile`). Sin Python, sin
`jq`, sin `pip install`.

```bash
# Verificar bash (necesario ≥ 4.0)
bash --version

# Verificar git
git --version
```

---

## 5. Instalación

### Opción A: instalador interactivo (recomendado)

```bash
chmod +x install.sh
./install.sh
```

El instalador pregunta dónde instalar (default `~/bin/git-sync`) y dónde están
tus repositorios (default `~/Documents`), copia todos los archivos (incluyendo
`lib/`), ajusta `base_directory` automáticamente, detecta qué carpetas con
`.git` existen y avisa cuáles faltan en el config, y opcionalmente agrega
aliases a `.bashrc` o `.zshrc`.

Si ya tienes un `repos-config.yml` instalado, **no lo sobrescribe** (para
proteger ediciones manuales).

### Opción B: instalación manual

```bash
mkdir -p ~/bin/git-sync/lib
cp sync.sh status.sh repos-config.yml README.md ~/bin/git-sync/
cp lib/*.sh ~/bin/git-sync/lib/
chmod +x ~/bin/git-sync/sync.sh ~/bin/git-sync/status.sh
```

Luego edita `~/bin/git-sync/repos-config.yml` para ajustar `base_directory`
y la lista de repositorios.

---

## 6. Configuración

Todo vive en `repos-config.yml`:

```yaml
base_directory: ~/Documents

repositories:
  - name: pub_axiomata
    branch: main
    enabled: true

  - name: pub_epsilon-y-beta
    branch: main
    enabled: true

  - name: website-achalma
    branch: main
    enabled: true

  - name: blog-experimental
    branch: develop
    enabled: false # pausado: sync.sh y status.sh lo ignoran

default_commit_message: "update: sincronización automática de contenidos"
```

**Reglas de formato** (el parser es ligero, no es YAML genérico):

- `name` con exactamente 2 espacios + `- ` antes.
- `branch` y `enabled` con exactamente 4 espacios.
- `enabled: false` pausa el repo sin borrarlo: cómodo para repos temporalmente inactivos.
- `base_directory` acepta `~` al inicio o ruta absoluta.
- No uses comillas, anchors, listas inline ni anidación adicional.

**Para agregar un repo nuevo**, añade un bloque más al final de `repositories:` siguiendo el mismo patrón y ejecuta `status.sh` para verificar que lo detecta.

---

## 7. Uso de sync.sh

```
Uso: sync.sh [OPCIONES]

  -m, --message "texto"   Mensaje de commit. Default: default_commit_message del config.
  -r, --repos "a,b,c"     Sincronizar solo estos repos (nombres separados por coma).
  -c, --check              Solo mostrar qué cambió, sin hacer commit ni push.
                           Detecta también commits remotos pendientes (hace fetch).
  -v, --verbose            Modo detallado (salida completa de git en tiempo real).
  -n, --no-pull            No hacer git pull antes de commitear.
      --config RUTA        Usar un archivo de configuración distinto.
  -h, --help               Mostrar esta ayuda.
```

Por cada repo habilitado, `sync.sh` ejecuta en orden:

1. `git pull` (salvo `-n` o `-c`)
2. Detectar cambios (`git status --porcelain`)
3. Si hay cambios: `git add -A` → `git commit -m "mensaje"` → `git push`
4. Si no hay cambios: reportar y pasar al siguiente

Si `git pull` falla (ramas divergentes, conflictos), **detiene ese repo y lo
marca como error** sin intentar commit ni push sobre un estado inconsistente.

### Ejemplos

```bash
# Sincronizar todos los repos habilitados con mensaje por defecto
./sync.sh

# Con mensaje personalizado
./sync.sh -m "feat: nuevo artículo sobre inflación"

# Solo dos repos específicos
./sync.sh -r "pub_axiomata,pub_chaska" -m "docs: actualizar índices"

# Solo revisar qué cambió (seguro, no modifica nada)
./sync.sh --check

# Ver exactamente qué hace cada comando git
./sync.sh -v -m "chore: actualizar scripts"

# Sincronizar sin hacer pull primero
./sync.sh -n -m "docs: cambio rápido"

# Simular en un archivo de config alternativo
./sync.sh --config ~/bin/git-sync/repos-config.yml --check
```

---

## 8. Uso de status.sh

```
Uso: status.sh [OPCIONES]

      --config RUTA    Usar un archivo de configuración distinto.
      --days N         Días de actividad a mostrar (default: 7).
  -h, --help           Mostrar esta ayuda.
```

Recorre todos los repos habilitados, hace `git fetch` por cada uno, y muestra:

- Tabla con: repositorio, rama, estado, y contadores de cambios (M:n ↑n ↓n).
- Bloque detallado de repos que necesitan atención.
- Leyenda.
- Acciones sugeridas (con los comandos exactos).
- Actividad reciente (commits en los últimos N días).

```bash
./status.sh
./status.sh --days 30    # actividad del último mes
```

### Estados posibles

| Estado                             | Significado                                              |
| ---------------------------------- | -------------------------------------------------------- |
| `SINCRONIZADO`                     | Todo al día                                              |
| `CAMBIOS SIN COMMIT`               | Archivos modificados sin commitear                       |
| `COMMITS SIN PUSH`                 | Commits locales no enviados al remoto                    |
| `COMMITS REMOTOS (PULL NECESARIO)` | El remoto tiene commits que no tienes localmente         |
| `DIVERGIDO (PULL + PUSH)`          | Hay commits tanto locales sin push como remotos sin pull |

En la tabla, los contadores indican:

- `M:n` → n archivos con cambios sin commit
- `↑n` → n commits locales sin push
- `↓n` → n commits remotos que necesitas hacer pull
- `✓` → sincronizado

---

## 9. Flujos de trabajo comunes

### Fin del día de trabajo

```bash
# 1. Ver qué cambió en todos los repos
./status.sh

# 2. Si hay cambios, sincronizar todos
./sync.sh -m "update: cambios del $(date +%Y-%m-%d)"

# 3. Confirmar que todo quedó sincronizado
./status.sh
```

### Archivo compartido que afecta varios repos (ej. \_metadata.yml como enlace duro)

```bash
# Ver qué repos se afectaron
./sync.sh --check

# Sincronizar con mensaje descriptivo
./sync.sh -m "feat(config): activar comentarios en todos los blogs"
```

### Actualizar solo los blogs de un tema

```bash
./sync.sh -r "pub_pecunia-fluxus,pub_epsilon-y-beta,pub_optimums" \
    -m "docs: actualizar índices económicos Q4-2025"

./sync.sh -r "pub_axiomata,pub_dialectica-y-mercado,pub_res-publica" \
    -m "docs: actualizar índices filosóficos"
```

### Después de regenerar índices con otro script

```bash
# 1. Regenerar índices
cd ~/Documents/scripts/scripts_for_quarto
./generar_indices.sh

# 2. Sincronizar
cd ~/bin/git-sync
./sync.sh -m "docs: regenerar índices automáticos - $(date +%Y-%m-%d)"
```

### Verificación antes de un push importante

```bash
./status.sh
read -r -p "¿Continuar? (s/n): " confirm
[[ "$confirm" == [sS] ]] && ./sync.sh -m "feat: cambio importante" -v
```

---

## 10. Aliases de shell

Si usaste el instalador y aceptaste agregar aliases, ya tienes `gsync`,
`gstatus` y `gsyncm`. Si los quieres agregar manualmente, esto va en
`~/.bashrc` o `~/.zshrc`:

```bash
alias gsync='~/bin/git-sync/sync.sh'
alias gstatus='~/bin/git-sync/status.sh'
gsyncm() {
    ~/bin/git-sync/sync.sh -m "$1"
}
```

Recargar:

```bash
source ~/.bashrc   # o source ~/.zshrc
```

Uso:

```bash
gstatus                        # ver estado de todos los repos
gsync                           # sincronizar todos
gsyncm "feat: nuevo post"      # sincronizar con mensaje personalizado
```

---

## 11. Automatización con cron

```bash
crontab -e
```

Agregar (ejemplo: sincronizar a las 18:00 todos los días):

```
0 18 * * * /home/achalmaedison/bin/git-sync/sync.sh -m "auto: sincronización diaria" >> /tmp/git-sync.log 2>&1
```

**Importante:** En cron no hay `$HOME` garantizado igual que en tu shell
interactivo. Usa siempre rutas absolutas tanto para invocar `sync.sh` como
dentro de `repos-config.yml` (en vez de `~`).

Para verificar los logs:

```bash
tail -f /tmp/git-sync.log
```

---

## 12. Añadir funcionalidades nuevas

La arquitectura modular facilita extender el sistema sin tocar el código existente.

| Módulo                   | Qué cambias aquí                                       |
| ------------------------ | ------------------------------------------------------ |
| `lib/logging.sh`         | Nuevos niveles de log, formato de timestamps           |
| `lib/config.sh`          | Nuevos campos en `repos-config.yml`, validaciones      |
| `lib/git_ops.sh`         | Nuevas operaciones git (stash, tag, cherry-pick, etc.) |
| `lib/sync_engine.sh`     | Cambios en el flujo pull→add→commit→push               |
| `lib/status_reporter.sh` | Nuevas métricas o formatos de reporte                  |
| `sync.sh`                | Nuevos flags CLI, nueva lógica de orquestación         |
| `status.sh`              | Nuevas secciones en el reporte                         |

### Ejemplo: agregar un comando `--tag VERSION`

1. En `lib/git_ops.sh`, añadir:

   ```bash
   git_create_tag() {
       local path="$1" tag="$2" message="${3:-Release $2}"
       git -C "$path" tag -a "$tag" -m "$message"
       git -C "$path" push origin "$tag"
   }
   ```

2. En `sync.sh`, agregar el flag al parser:

   ```bash
   --tag) TAG_VERSION="$2"; shift 2 ;;
   ```

3. En `lib/sync_engine.sh`, llamar `git_create_tag` si `TAG_VERSION` está definido.

### Ejemplo: nuevo campo `remote_url` en repos-config.yml

1. Añadir en `lib/config.sh` dentro de `_config_parse_repos()` (en el awk):

   ```awk
   /^    remote_url:/ { remote_url = $0; sub(/^    remote_url:[[:space:]]*/, "", remote_url) }
   ```

   Y en el `END` y la línea de impresión, agregar el campo nuevo.

2. En `lib/git_ops.sh`, usar el `remote_url` para configurar el remote si no existe.

### Guía general

1. Escribe la función en el módulo temáticamente correcto.
2. Si el módulo no existe todavía, créalo en `lib/` y agrégalo al bloque
   de `source` del script principal que lo necesite.
3. Prueba con `bash -n lib/nuevo_modulo.sh` y `shellcheck -S error`.
4. Actualiza este README.

---

## 13. Solución de problemas

### "No se encontró el archivo de configuración"

`sync.sh` y `status.sh` buscan `repos-config.yml` en su propio directorio.
Si lo moviste o renombraste, usa `--config /ruta/completa/repos-config.yml`.

### "git pull falló" / ramas divergentes

Cuando el historial local y remoto divergen, `sync.sh` detiene ese repo en
vez de intentar merge automático (podría generar commits sobre un estado
inconsistente). Entra al repo manualmente:

```bash
cd ~/Documents/pub_axiomata
git pull           # verás el conflicto y las opciones de git
# resolver conflictos si los hay
git add .
git commit
git push
```

Después vuelve a correr `sync.sh`; ese repo ya estará al día.

### Un repo aparece como "SINCRONIZADO" pero hay commits en GitHub

Esto ya está corregido en v2.0 (Bug 2). Si lo ves en v2.0, puede ser:

1. Sin conexión a internet durante el `git fetch` — los contadores quedan en 0.
2. El upstream no está configurado (`git branch -vv` mostrará `[gone]`).

Para el caso 2:

```bash
git -C ~/Documents/pub_axiomata branch -u origin/main main
```

### Un repo no aparece en status.sh aunque existe

Revisa:

1. Que esté en `repos-config.yml` con `enabled: true`.
2. Que el `name:` coincida exactamente con el nombre de la carpeta.
3. Que la carpeta contenga `.git` (es un repo Git válido).

```bash
ls -la ~/Documents/pub_axiomata/.git
```

### "Permission denied" al ejecutar los scripts

```bash
chmod +x ~/bin/git-sync/sync.sh ~/bin/git-sync/status.sh
```

### Ver exactamente qué comando git está fallando

```bash
./sync.sh -v -m "debug"
```

En modo verbose, la salida completa de `git pull`, `git status` y `git push`
se muestra sin silenciar nada.

### `mapfile` no encontrado / error de bash

`mapfile` requiere bash ≥ 4.0. En macOS, el bash del sistema es 3.2 (por
licencia). Instala bash moderno:

```bash
brew install bash
# Luego invoca explícitamente:
/opt/homebrew/bin/bash ~/bin/git-sync/sync.sh
```

O agrega `/opt/homebrew/bin/bash` al shebang de los scripts.

---

**Autor:** Edison Achalma (`achalmed`)  
ORCID: 0000-0001-6996-3364  
Universidad Nacional de San Cristóbal de Huamanga, Ayacucho, Perú
