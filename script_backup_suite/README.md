# backup-suite — Sincronización Inteligente de Backup

> Script modular de backup para Linux que sincroniza tu directorio home
> hacia un disco externo con control total, perfiles configurables,
> detección automática de distro y compatibilidad con Kubuntu y Arch Linux.

---

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Novedades v3.0.0](#novedades-v300)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Perfiles de Backup](#perfiles-de-backup)
- [Arquitectura](#arquitectura)
- [Bugs Corregidos](#bugs-corregidos)
- [Automatización con systemd](#automatización-con-systemd)
- [Solución de Problemas](#solución-de-problemas)
- [Cómo Agregar Funcionalidades](#cómo-agregar-funcionalidades)
- [Notas y Advertencias](#notas-y-advertencias)

---

## 📖 Descripción

`backup-suite` sincroniza carpetas de tu directorio home hacia un disco externo
usando `rsync` con comparación por checksum real. A diferencia de un simple
`cp -r`, el script detecta exactamente qué cambió, te pregunta qué hacer con
cada archivo modificado, y gestiona los archivos que ya no existen en tu laptop.

**Flujo de backup por carpeta:**

```
Para cada carpeta del perfil activo:
  │
  ├─ PASO A: Archivos NUEVOS
  │   └─ Se copian automáticamente
  │
  ├─ PASO B: Archivos MODIFICADOS
  │   └─ Pregunta qué hacer:
  │       [s] Actualizar  [v] Ver diff  [i] Ignorar
  │       [t] Todos       [n] Ignorar todos
  │
  └─ PASO C: Archivos HUÉRFANOS (en disco pero no en laptop)
      └─ Pregunta qué hacer:
          [e] Eliminar todos  [r] Revisar uno a uno  [c] Conservar
```

---

## 🆕 Novedades v3.0.0

| Característica                 | Descripción                                                          |
| ------------------------------ | -------------------------------------------------------------------- |
| Arquitectura modular           | 7 archivos con responsabilidad única (SRP) — fácil de mantener       |
| Detección automática de distro | Soporta `/media` (Kubuntu) y `/run/media` (Arch) sin configuración   |
| Perfiles de backup             | `home`, `docs`, `full`, `custom` — seleccionables con `--profile`    |
| `--folder`                     | Respalda una sola carpeta sin modificar el perfil completo           |
| `--src` / `--dest`             | Origen y destino completamente libres (reemplaza grsync para esto)   |
| `--fast`                       | Modo rápido sin checksum (fecha/tamaño) — ideal para backups diarios |
| `--compress`                   | Compresión rsync activable (útil para rsync sobre red)               |
| `--no-confirm`                 | Omite confirmación inicial (para cron/systemd)                       |
| `--post-cmd`                   | Ejecuta un comando al finalizar (notificaciones, scripts, etc.)      |
| Opciones grsync replicadas     | hardlinks, protect-args, itemize-changes incluidos por defecto       |
| Exclusiones por patrón         | `*.tmp`, `*.swp`, `*.pyc`, `node_modules`, etc. desde `config.sh`    |
| Logging mejorado               | Encabezado de sesión, niveles DEBUG visibles solo con `--verbose`    |

---

## ⚙️ Requisitos

### Sistema Operativo

- Kubuntu / Ubuntu 22.04 o superior
- Arch Linux / Archcraft (cualquier versión reciente)
- Bash >= 4.0

### Dependencias

| Paquete     | Tipo        | Instalación (Arch)         | Instalación (Kubuntu)        |
| ----------- | ----------- | -------------------------- | ---------------------------- |
| `rsync`     | Obligatorio | `sudo pacman -S rsync`     | `sudo apt install rsync`     |
| `pv`        | Recomendado | `sudo pacman -S pv`        | `sudo apt install pv`        |
| `colordiff` | Opcional    | `sudo pacman -S colordiff` | `sudo apt install colordiff` |

> `bc` ya no es necesario — los cálculos de tamaño usan `awk` puro.

---

## 🚀 Instalación

### 1. Clonar o copiar el proyecto

```bash
cp -r backup-suite/ ~/Documents/scripts_for_linux/script_backup_suite/
```

### 2. Dar permisos de ejecución

```bash
chmod +x ~/Documents/scripts_for_linux/script_backup_suite/main.sh
chmod +x ~/Documents/scripts_for_linux/script_backup_suite/lib/*.sh
```

### 3. Añadir alias conveniente (opcional)

```bash
# En ~/.bashrc o ~/.zshrc
alias backup='~/Documents/scripts_for_linux/script_backup_suite/main.sh'
```

### 4. Probar en modo simulación primero

```bash
~/Documents/scripts_for_linux/script_backup_suite/main.sh --simulate --verbose
```

### 5. Verificar que el disco se detecta correctamente

```bash
# Debe mostrar la ruta detectada (Kubuntu: /media/..., Arch: /run/media/...)
~/Documents/scripts_for_linux/script_backup_suite/main.sh --simulate
```

---

## 💻 Uso

```bash
./main.sh [OPCIONES]
```

### Opciones disponibles

| Flag                   | Descripción                                          | Default |
| ---------------------- | ---------------------------------------------------- | ------- |
| `-h, --help`           | Muestra la ayuda y sale                              | —       |
| `--version`            | Muestra la versión                                   | —       |
| `-v, --verbose`        | Modo detallado (lista cada archivo procesado)        | false   |
| `-s, --simulate`       | Simulación: sin cambios reales                       | false   |
| `-l, --log`            | Guarda log en `~/backup_suite.log`                   | false   |
| `--no-confirm`         | Omite la confirmación inicial                        | false   |
| `-p, --profile <name>` | Selecciona perfil (`home`, `docs`, `full`, `custom`) | `home`  |
| `--profile list`       | Lista todos los perfiles disponibles                 | —       |
| `--src <ruta>`         | Carpeta de origen personalizada                      | —       |
| `--dest <ruta>`        | Carpeta de destino personalizada                     | —       |
| `-F, --folder <name>`  | Respalda solo esta carpeta del perfil                | —       |
| `-f, --force`          | Sobreescribe modificados sin preguntar               | false   |
| `-d, --delete-all`     | Elimina huérfanos sin preguntar                      | false   |
| `--fast`               | Sin checksum (usa fecha/tamaño — más rápido)         | false   |
| `--compress`           | Activa compresión rsync                              | false   |
| `--post-cmd <cmd>`     | Comando a ejecutar al finalizar                      | —       |

### Ejemplos de uso

```bash
# Inicio
cd /home/achalmaedison/Documents/scripts_for_linux/script_backup_suite

# Backup interactivo con perfil por defecto (recomendado para uso diario)
./main.sh

# Ver qué cambiaría sin tocar nada
./main.sh --simulate --verbose

# Backup solo de Documents (rápido)
./main.sh --profile docs

# Backup de una sola carpeta
./main.sh --folder Pictures

# Backup sin preguntas (ideal para cron o systemd)
./main.sh --force --delete-all --log --no-confirm

# Origen y destino personalizados (equivale a grsync en modo manual)
./main.sh --src ~/Documents --dest /run/media/user/DISK/Documents

# Backup rápido sin checksum (más veloz, menos preciso)
./main.sh --fast --profile home

# Con notificación de escritorio al finalizar
./main.sh --log --post-cmd "notify-send 'Backup' 'Completado exitosamente'"

# Ver todos los perfiles disponibles
./main.sh --profile list
```

---

## 🗂️ Perfiles de Backup

Los perfiles se definen en `config.sh` y se seleccionan con `--profile`:

### `home` (default)

Respalda las carpetas principales del usuario:

```
Desktop, Documents, Downloads, Music, Pictures, Public,
Reading_Goal, Templates, Videos, dotfiles, gretl, R, sources, Zotero
```

### `docs`

Solo `Documents` — backup rápido del trabajo activo diario.

### `full`

Todo el home excepto las exclusiones globales de `config.sh` (miniconda3, paru, .cache, snap, etc.)

### `custom`

Requiere `--src` y `--dest`. Origen y destino completamente libres:

```bash
./main.sh --profile custom \
  --src /home/user/Proyectos \
  --dest /run/media/user/ARCHDISK/Proyectos
```

---

## 🗂️ Arquitectura

```
backup-suite/
├── main.sh                  # Punto de entrada — orquesta todos los módulos (~120 líneas)
├── config.sh                # Configuración centralizada: perfiles, rutas, opciones rsync
├── README.md                # Esta documentación
└── lib/
    ├── logger.sh            # Sistema de logging: colores, niveles, rotación de log
    ├── validator.sh         # Validaciones: dependencias, disco, carpetas origen
    ├── cli.sh               # CLI: parseo de flags, ayuda, lista de perfiles
    ├── analyzer.sh          # Análisis rsync: archivos nuevos, modificados, huérfanos
    ├── processor.sh         # Lógica de backup por carpeta: copia, interactividad
    └── summary.sh           # Resumen final, estado del disco, post-comando
```

### Descripción de módulos

| Archivo            | Responsabilidad única                                            |
| ------------------ | ---------------------------------------------------------------- |
| `main.sh`          | Orquestación del flujo completo (sin lógica de negocio)          |
| `config.sh`        | Variables, perfiles, opciones rsync — el único lugar para editar |
| `lib/logger.sh`    | Todo el output del script pasa por aquí                          |
| `lib/validator.sh` | Verificaciones previas al backup (falla rápido si algo falta)    |
| `lib/cli.sh`       | Definición y parseo de todos los flags CLI                       |
| `lib/analyzer.sh`  | Comparaciones rsync para detectar cambios (sin modificar nada)   |
| `lib/processor.sh` | Ejecuta las operaciones de backup y gestiona la interactividad   |
| `lib/summary.sh`   | Informe final y post-comando                                     |

---

## 🐛 Bugs Corregidos

### Bug #1: `bc` como dependencia implícita

- **Descripción**: `bytes_legibles()` usaba `bc` para aritmética decimal,
  pero `bc` no está instalado por defecto en muchas distros.
- **Impacto**: El script fallaba silenciosamente con cálculos de tamaño incorrectos.
- **Corrección**: Reemplazado por `awk` puro en `format_file_size()` (lib/analyzer.sh).

### Bug #2: `MODO_FORZAR_CARPETA` no declarada con `local`

- **Descripción**: La variable `MODO_FORZAR_CARPETA` se usaba sin declarar en el
  scope local de `procesar_carpeta()`, pudiendo persistir entre carpetas.
- **Impacto**: En ciertas condiciones, el flag "actualizar todos" se aplicaba
  a la carpeta siguiente involuntariamente.
- **Corrección**: Convertida en variable local dentro de `_handle_modified()`.

### Bug #3: Punto de montaje hardcodeado para Arch

- **Descripción**: El disco externo solo se buscaba en `/run/media/`.
  En Kubuntu/Ubuntu el punto de montaje es `/media/`.
- **Impacto**: El script nunca detectaba el disco en Kubuntu.
- **Corrección**: `detect_mount_point()` en validator.sh prueba ambas rutas
  y también hace fallback via `lsblk`.

### Bug #4: `set -e` + `rsync` con código 24 (archivos desaparecidos)

- **Descripción**: rsync puede retornar código 24 (archivo desaparecido durante
  transferencia) sin que sea un error crítico. Con `set -euo pipefail` el script
  abortaba en estos casos.
- **Impacto**: Backups interrumpidos en sistemas con archivos temporales activos.
- **Corrección**: Las llamadas rsync críticas usan `|| true` donde el código 24
  es esperado (archivos temporales desaparecen durante la copia).

### Bug #5: `diff` sin `--label` producía cabeceras confusas

- **Descripción**: El diff mostraba rutas completas del sistema en las cabeceras,
  lo que dificultaba identificar cuál era el archivo origen y cuál el destino.
- **Impacto**: El usuario no sabía cuál versión era "nueva" y cuál "en disco".
- **Corrección**: `show_file_diff()` añade `--label` con textos descriptivos
  ("DISCO EXTERNO" / "ORIGEN laptop").

---

## ⚙️ Automatización con systemd

Para ejecutar el backup automáticamente al conectar el disco:

### 1. Regla udev (`/etc/udev/rules.d/99-backup-suite.rules`)

```
ACTION=="add", SUBSYSTEM=="block", ENV{ID_FS_LABEL}=="ARCHDISK", \
    RUN+="/bin/systemctl start --no-block backup-archdisk.service"
```

### 2. Servicio systemd (`/etc/systemd/system/backup-archdisk.service`)

```ini
[Unit]
Description=Backup automático a ARCHDISK
After=media-achalmaedison-ARCHDISK.mount

[Service]
Type=oneshot
User=achalmaedison
Environment=DISPLAY=:0
ExecStartPre=/bin/sleep 5
ExecStart=/home/achalmaedison/Documents/scripts_for_linux/script_backup_suite/main.sh \
    --force --delete-all --log --no-confirm \
    --post-cmd "notify-send 'Backup ARCHDISK' 'Completado'"
StandardOutput=journal
StandardError=journal
```

### 3. Activar regla udev

```bash
sudo udevadm control --reload-rules
```

> Con `--no-confirm` el servicio no hará preguntas interactivas.
> Revisa el log después: `journalctl -u backup-archdisk.service`

---

## 🔧 Solución de Problemas

| Problema                                  | Solución                                                                    |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| `El disco no está montado`                | Conecta el disco; el script detecta `/media` y `/run/media` automáticamente |
| `rsync: command not found`                | `sudo pacman -S rsync` o `sudo apt install rsync`                           |
| `Permission denied`                       | No ejecutes como root; usa tu usuario normal                                |
| `pv: command not found`                   | Opcional: `sudo pacman -S pv` (el script funciona sin él)                   |
| Backup muy lento                          | Usa `--fast` para comparar por fecha/tamaño en vez de checksum              |
| Disco NTFS/exFAT: permisos no preservados | Normal en NTFS/exFAT; usa ext4 para backup completo de permisos             |
| `validate_source_folders: nameref`        | Requiere Bash >= 4.3; actualiza con `sudo pacman -Syu bash`                 |

---

## 🤝 Cómo Agregar Funcionalidades

La arquitectura modular hace que extender el script sea simple:

### Para agregar un nuevo perfil de backup:

1. Abre `config.sh`
2. Añade tu array:
   ```bash
   PROFILE_MYPROFILE_FOLDERS=("Carpeta1" "Carpeta2")
   ```
3. Abre `main.sh` y añade el caso en el bloque `case "${OPT_PROFILE}"`:
   ```bash
   myprofile)
       carpetas_backup=("${PROFILE_MYPROFILE_FOLDERS[@]}")
       ;;
   ```
4. Documenta el nuevo perfil en `lib/cli.sh` → `show_profiles()`

### Para agregar un nuevo flag CLI:

1. Abre `lib/cli.sh`
2. Añade la variable default al inicio:
   ```bash
   OPT_MY_FLAG=false
   ```
3. Añade el caso en `parse_args()`:
   ```bash
   --my-flag)
       OPT_MY_FLAG=true
       shift
       ;;
   ```
4. Úsalo en `lib/processor.sh` o `main.sh` según corresponda.

### Para agregar un nuevo módulo:

1. Crea `lib/mi_modulo.sh` con funciones de responsabilidad única.
2. Agrégalo en el bloque de `source` de `main.sh`.
3. Llama sus funciones desde la fase correspondiente en `main()`.

### Estándares de código

- Máximo 30 líneas por función
- Prefijo `_` para funciones privadas de un módulo
- `local` para todas las variables dentro de funciones
- Documenta el "por qué", no el "qué"
- Usa `|| true` explícitamente cuando un fallo no es crítico

---

## ⚠️ Notas y Advertencias

**Compatibilidad de nameref (Bash 4.3+):**
`validate_source_folders()` usa `local -n` (nameref de Bash 4.3+).
En sistemas muy antiguos con Bash < 4.3 esta función fallará.
Kubuntu 22.04+ y Arch reciente incluyen Bash 5.x, por lo que no debería ser problema.

**Checksum vs. velocidad:**
La opción `-c` (checksum) es más precisa pero más lenta que comparar por fecha/tamaño.
Para backups diarios de archivos que cambias frecuentemente, `--fast` puede ser
preferible. Para backups semanales o de verificación, mantén el checksum.

**`--delete-all` con `--no-confirm` en systemd:**
Esta combinación elimina huérfanos sin ninguna confirmación.
Úsala solo cuando estés seguro de que el disco externo no tiene archivos
que quieras conservar independientemente del laptop.

**Límite de archivos con `set -euo pipefail`:**
El script usa `set -euo pipefail` para fallar rápido ante errores inesperados.
Las llamadas rsync que pueden devolver códigos no-cero esperables (como el código 24)
usan `|| true` explícitamente para no abortar el backup.

---

_backup-suite v3.0.0 — Compatible con Kubuntu y Arch Linux_
_achalmaedison — `/home/achalmaedison` → `/media/*/ARCHDISK`_
