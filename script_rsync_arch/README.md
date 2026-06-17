# backup_arch.sh — Backup Inteligente para Arch Linux
#readme 
Script de sincronización de backup para respaldar el directorio home de Arch Linux
hacia un disco externo, con comparación de contenido, interactividad y control total.

---

## Características principales

| Función                  | Descripción                                                      |
| ------------------------ | ---------------------------------------------------------------- |
| Comparación por checksum | Detecta cambios reales en el contenido, no solo por fecha        |
| Barra de progreso        | Muestra avance con `pv` (si está instalado)                      |
| Interactivo para cambios | Pregunta antes de sobreescribir archivos modificados             |
| Ver diferencias          | Muestra el diff del archivo antes de decidir                     |
| Control de huérfanos     | Lista archivos que ya no están en origen, tú decides si eliminar |
| Preserva metadatos       | Conserva permisos, fechas, enlaces simbólicos, subdirectorios    |
| Sin duplicados           | rsync asegura una copia limpia sin repeticiones                  |
| Log opcional             | Guarda registro detallado de cada operación                      |
| Modo simulación          | Previsualiza qué haría sin tocar nada                            |

---

## Requisitos

### Obligatorio

```bash
sudo pacman -S rsync
```

### Recomendado (barras de progreso visuales)

```bash
sudo pacman -S pv
```

### Opcional (diffs con colores)

```bash
sudo pacman -S colordiff
```

---

## Instalación

```bash
# 1. Clonar o copiar el script a tu home
cp backup_arch.sh ~/bin/backup_arch.sh

# 2. Dar permisos de ejecución
chmod +x ~/bin/backup_arch.sh

# 3. (Opcional) Agregar ~/bin al PATH si no está ya
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Probar en modo simulación primero
backup_arch.sh --simulate
```

---

## Uso

```
./backup_arch.sh [OPCIONES]
```

### Opciones disponibles

| Opción               | Descripción                            |
| -------------------- | -------------------------------------- |
| `-h`, `--help`       | Muestra la ayuda y sale                |
| `-v`, `--verbose`    | Lista cada archivo procesado           |
| `-s`, `--simulate`   | Simulación: no realiza cambios reales  |
| `-l`, `--log`        | Guarda log en `~/backup_arch.log`      |
| `-f`, `--force`      | Sobreescribe modificados sin preguntar |
| `-d`, `--delete-all` | Elimina huérfanos sin preguntar        |

### Ejemplos de uso

```bash
# Backup interactivo normal (recomendado para uso diario)
./backup_arch.sh

# Ver qué cambiaría sin tocar nada (ideal para primera vez)
./backup_arch.sh --simulate

# Backup con log y detalles completos
./backup_arch.sh --verbose --log

# Backup automatizado sin preguntas (para cron o scripts)
./backup_arch.sh --force --delete-all --log

# Solo ver cambios pendientes en detalle
./backup_arch.sh --simulate --verbose
```

---

## Carpetas respaldadas

El script respalda las siguientes carpetas de `/home/achalmaedison/`:

```
✓ Desktop       ✓ Documents     ✓ dotfiles
✓ Downloads     ✓ gretl         ✓ Music
✓ Pictures      ✓ Public        ✓ R
✓ Reading_Goal  ✓ sources       ✓ Templates
✓ Videos        ✓ Zotero
```

### Carpetas excluidas (configurables en el script)

```
✗ miniconda3    — Entorno conda (~3GB+, reinstalable con conda env export)
✗ paru          — Caché de AUR (regenerable)
✗ pyRenamer     — Aplicación del sistema
```

> Para incluir `miniconda3` u otras, elimina la línea correspondiente
> del array `CARPETAS_EXCLUIR` en el script.

---

## Flujo de trabajo

El script sigue este flujo para cada carpeta:

```
Para cada carpeta en CARPETAS_BACKUP:
  │
  ├─ PASO A: Archivos NUEVOS
  │   └─ Se copian automáticamente (no requieren confirmación)
  │
  ├─ PASO B: Archivos MODIFICADOS
  │   └─ Para cada uno, muestra info y pregunta:
  │       ├─ [s] Actualizar en disco externo
  │       ├─ [v] Ver diferencias primero
  │       ├─ [i] Ignorar (conservar versión del disco)
  │       ├─ [t] Actualizar TODOS los modificados de esta carpeta
  │       └─ [n] Ignorar TODOS los modificados de esta carpeta
  │
  └─ PASO C: Archivos HUÉRFANOS (en disco pero no en laptop)
      └─ Lista todos y pregunta:
          ├─ [e] Eliminar todos
          ├─ [r] Revisar uno por uno
          └─ [c] Conservar todos
```

---

## Estructura en el disco externo

```
/run/media/achalmaedison/ARCHDISK/
└── backup_achalmaedison/
    ├── Desktop/
    ├── Documents/
    ├── dotfiles/
    ├── Downloads/
    ├── gretl/
    ├── Music/
    ├── Pictures/
    ├── Public/
    ├── R/
    ├── Reading_Goal/
    ├── sources/
    ├── Templates/
    ├── Videos/
    └── Zotero/
```

---

## Log

Cuando usas `--log`, el archivo de log se guarda en:

```
/home/achalmaedison/backup_arch.log
```

El log se **rota automáticamente** si supera los 10MB (se guarda como `.bak`).

Formato de cada entrada del log:

```
[2026-04-22 15:30:01] [OK]     Archivos nuevos copiados: 42
[2026-04-22 15:30:01] [WARN]   Huérfano encontrado: Documents/viejo.pdf
[2026-04-22 15:30:05] [INFO]   Tiempo total: 00h 02m 15s
```

---

## Configuración personalizada

Puedes editar las siguientes variables en el script para adaptarlo:

```bash
# Líneas ~40-70 del script

# Usuario del sistema
USUARIO="achalmaedison"

# Carpetas a respaldar
CARPETAS_BACKUP=(
    "Desktop"
    "Documents"
    # Añade más aquí...
)

# Carpetas a excluir
CARPETAS_EXCLUIR=(
    "miniconda3"
    # Añade más aquí...
)

# Punto de montaje del disco
DISCO_EXTERNO="/run/media/${USUARIO}/ARCHDISK"
```

---

## Automatización con systemd (opcional)

Para ejecutar el backup automáticamente cada vez que conectas el disco,
puedes crear una regla udev + servicio systemd:

### 1. Regla udev (`/etc/udev/rules.d/99-archdisk-backup.rules`)

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
ExecStart=/home/achalmaedison/bin/backup_arch.sh --log --force
StandardOutput=journal
StandardError=journal
```

### 3. Activar la regla udev

```bash
sudo udevadm control --reload-rules
```

> **Nota:** Con `--force` el servicio no hará preguntas interactivas.
> Revisa el log después: `journalctl -u backup-archdisk.service`

---

## Preguntas frecuentes

**¿Por qué usa checksum y no solo fecha/tamaño?**
Porque es más confiable. La fecha de modificación puede cambiar al copiar un archivo
o sincronizar el reloj, pero el checksum detecta si el contenido cambió de verdad.

**¿Puede corromperse el backup si lo interrumpo?**
No. rsync es atómico por archivo: si se interrumpe, el archivo de destino
quedará en su estado anterior (no a medias).

**¿Qué pasa si hay archivos con el mismo nombre pero distinto contenido?**
El script lo detecta como "archivo modificado" y te pregunta qué hacer.

**¿Puedo añadir exclusiones por patrón (ej: archivos `.tmp`)?**
Sí, modifica la variable `RSYNC_OPTS` añadiendo `--exclude='*.tmp'` u otros patrones.

**¿Funciona con discos NTFS o exFAT?**
Sí, pero algunos metadatos de permisos Unix pueden no guardarse en NTFS/exFAT.
Para backup completo se recomienda ext4 en el disco externo.

---

## Solución de problemas

| Problema                        | Solución                                                                          |
| ------------------------------- | --------------------------------------------------------------------------------- |
| `Disco externo NO está montado` | Conecta el disco y espera, o monta manualmente con `udisksctl mount -b /dev/sda1` |
| `rsync: command not found`      | `sudo pacman -S rsync`                                                            |
| `Permission denied`             | No ejecutes como root; usa tu usuario normal                                      |
| `pv: command not found`         | `sudo pacman -S pv` (opcional, el script funciona sin él)                         |

---

## Licencia

Uso libre y personal. Modifica según tus necesidades.

---

_Generado para Arch Linux — `/home/achalmaedison` → `/run/media/achalmaedison/ARCHDISK`_
