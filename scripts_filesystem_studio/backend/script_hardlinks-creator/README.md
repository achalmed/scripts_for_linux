# hardlinks-creator

> Busca archivos con el mismo nombre en un árbol de directorios, los agrupa
> por contenido idéntico (SHA-256) y crea hard links para eliminar duplicados
> sin perder datos — con operaciones atómicas, modo batch para procesar
> listas completas de nombres y reporte JSON opcional.

**Proyecto complementario:** [`hardlinks-detector`](../hardlinks-detector/) — visualiza los hard links existentes en estructura de árbol.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Novedades v3.1](#-novedades-v31--modo-batch)
- [Novedades v3.0](#-novedades-v30-respecto-al-script-original)
- [Bugs corregidos](#-bugs-corregidos)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Modo batch](#-modo-batch)
- [Arquitectura](#-arquitectura)
- [Casos de uso comunes](#-casos-de-uso-comunes)
- [Solución de problemas](#-solución-de-problemas)
- [Cómo contribuir](#-cómo-contribuir)
- [Notas y advertencias](#️-notas-y-advertencias)

---

## 📖 Descripción

`hardlinks-creator` escanea recursivamente un directorio buscando archivos
con un nombre específico (ej. `_metadata.yml`), calcula su hash SHA-256 y
agrupa los que tienen contenido idéntico. Para cada grupo, reemplaza las
copias duplicadas con hard links al mismo inodo, eliminando el espacio
redundante sin que ninguna herramienta note la diferencia.

Diseñado para proyectos Quarto/R Markdown con múltiples sitios que comparten
archivos de configuración (`_metadata.yml`, `_quarto.yml`, `.editorconfig`).

Admite dos modos de ejecución que comparten el mismo pipeline interno:

```bash
python main.py _metadata.yml          # modo single: un nombre de archivo
python main.py --batch archivos.txt   # modo batch: una lista de nombres
```

---

## 🆕 Novedades v3.1 — Modo batch

| Característica nueva    | Descripción                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------- |
| **`--batch FILE`**      | Procesa una lista completa de nombres (uno por línea) en una sola ejecución             |
| **Tolerancia a fallos** | Un error en un nombre no detiene el batch; se registra y se continúa con el resto       |
| **Resumen agregado**    | Progreso `[i/N]`, totales combinados, tiempo total y lista de errores al final          |
| **Reporte JSON batch**  | `--report-json` en modo batch genera un único JSON con el detalle por archivo           |
| **`lib/pipeline.py`**   | El pipeline de un archivo se extrajo a `process_filename()`, compartido por ambos modos |
| **`lib/batch.py`**      | Módulo dedicado al parseo del listado (comentarios, líneas vacías, duplicados)          |

El modo single (`python main.py _metadata.yml`) funciona exactamente igual que antes.

---

## 🆕 Novedades v3.0 (respecto al script original)

| Característica nueva       | Descripción                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **Operación atómica**      | `rename → link → remove backup` reemplaza el `remove → link` inseguro del original |
| **Reporte JSON**           | `--report-json FILE` exporta estadísticas para CI/cron                             |
| **`--directory` CLI**      | Directorio de trabajo sin tocar el código fuente                                   |
| **`--replace-exclude`**    | Reemplaza completamente la lista de exclusiones predefinida                        |
| **Guard cross-filesystem** | Detecta y omite candidatos en distinto sistema de archivos con mensaje claro       |
| **Logging a archivo**      | `LOG_FILE` en `config.py` activa un handler de archivo sin colores                 |
| **Arquitectura modular**   | 5 módulos con responsabilidad única, testeable de forma independiente              |

---

## 🐛 Bugs corregidos

### Bug #1 — Pérdida de archivo en fallo de enlace (`lib/linker.py`)

- **Original:** `os.remove(filepath)` se ejecutaba _antes_ de `os.link()`.
  Si `os.link()` fallaba (disco lleno, permisos, cross-device), el archivo
  quedaba destruido permanentemente.
- **Corrección:** Operación atómica: `os.rename(target, target.hltmp)` →
  `os.link(source, target)` → `os.remove(target.hltmp)`. En caso de fallo
  en el link, el `.hltmp` se restaura al path original.

### Bug #2 — Variables `inodes` sin inicialización (`lib/scanner.py`)

- **Original:** El diccionario `inodes` se declaraba dentro del loop de grupos
  pero podía ser referenciado antes en ciertas rutas de código.
- **Corrección:** Separación clara entre fase de escaneo y fase de enlace,
  cada una con su propio módulo e inicialización explícita.

---

## ⚙️ Requisitos

- **Python** ≥ 3.10 (usa `str | None` union syntax)
- **Sistema:** Linux/Unix con soporte para hard links (ext4, btrfs, xfs, etc.)
- **Paquetes:** solo biblioteca estándar (cero dependencias externas)
- **Permisos:** lectura en el directorio a escanear, escritura en los archivos a enlazar

---

## 🚀 Instalación

```bash
# 1. Clonar en tu carpeta de scripts
cd ~/Documents/scripts_for_linux
git clone https://github.com/achalmed/hardlinks-creator.git
cd hardlinks-creator

# 2. Dar permisos de ejecución
chmod +x main.py

# 3. (Opcional) Acceso global
mkdir -p ~/.local/bin
ln -s "$(pwd)/main.py" ~/.local/bin/hardlinks-creator
```

### Con entorno conda (recomendado para aislamiento)

```bash
conda create -n hardlinks python=3.11
conda activate hardlinks
chmod +x main.py
```

### Configuración inicial

Edita `config.py` para establecer tu directorio de trabajo predefinido:

```python
DEFAULT_DIRECTORY = "/home/achalmaedison/Documents/"
```

---

## 💻 Uso

### Sintaxis

```bash
python main.py FILENAME [OPCIONES]        # modo single
python main.py --batch FILE [OPCIONES]    # modo batch
# o si está en el PATH:
hardlinks-creator FILENAME [OPCIONES]
```

`FILENAME` y `--batch` son mutuamente excluyentes: se debe indicar
exactamente uno de los dos.

### Opciones disponibles

| Flag                       | Descripción                        | Requerido             |
| -------------------------- | ---------------------------------- | --------------------- |
| `filename`                 | Nombre exacto del archivo a buscar | **Sí** (o `--batch`)  |
| `-b, --batch FILE`         | Listado de nombres, uno por línea  | **Sí** (o `filename`) |
| `-d, --directory DIR`      | Directorio raíz de búsqueda        | No                    |
| `--exclude DIR...`         | Carpetas adicionales a excluir     | No                    |
| `--replace-exclude DIR...` | Reemplaza la lista de exclusiones  | No                    |
| `--auto`                   | Sin confirmación interactiva       | No                    |
| `--dry-run`                | Simular sin cambios                | No                    |
| `--report-json FILE`       | Exportar reporte JSON              | No                    |
| `--no-color`               | Desactivar colores ANSI            | No                    |
| `-v, --verbose`            | Mensajes de depuración             | No                    |
| `--version`                | Mostrar versión                    | No                    |
| `-h, --help`               | Mostrar ayuda                      | No                    |

### Ejemplos

```bash
# Inicio
cd ~/Documents/scripts_for_linux/script_hardlinks-creator

# Enlazar _metadata.yml con mismo contenido
python main.py _metadata.yml

# Directorio explícito + simulación
python main.py _metadata.yml -d ~/Documents --dry-run

# Automático + reporte JSON (ideal para cron)
python main.py _metadata.yml --auto --report-json /tmp/links-report.json

# Solo excluir build y dist (reemplaza lista predefinida)
python main.py .editorconfig --replace-exclude build dist

# Sin colores para log de CI
python main.py _quarto.yml --auto --no-color >> /var/log/hardlinks.log 2>&1

# Procesar decenas de nombres de una sola vez (ver "Modo batch")
cd ~/Documents/scripts_for_linux/script_hardlinks-creator
python main.py --batch archivos.txt --dry-run # primero simula
python main.py --batch archivos.txt           # ejecuta de verdad (confirmar)
python main.py --batch archivos.txt --auto    # ejecuta de verdad (sin confirmar)
```

---

## 📦 Modo batch

En lugar de ejecutar el programa una vez por cada nombre de archivo:

```bash
python main.py _metadata.yml
python main.py _quarto.yml
python main.py README.md
python main.py styles.css
# ... decenas de ejecuciones más
```

el modo batch procesa toda la lista en una sola ejecución:

```bash
python main.py --batch archivos.txt
```

Internamente ejecuta el mismo pipeline (escaneo → agrupación por hash →
enlace) para cada nombre del listado, reutilizando la configuración
(directorio, exclusiones, flags) resuelta una sola vez al inicio.

### Formato del archivo batch

Un nombre de archivo por línea. Se ignoran automáticamente:

- líneas vacías
- espacios al inicio/final de cada línea
- líneas que comienzan con `#` (comentarios)
- nombres duplicados (se conserva la primera aparición)

```text
# ── Configuración Quarto ──
_metadata.yml
_quarto.yml

# ── Contenido compartido ──
_contenido-inicio.qmd
_contenido-final.qmd
README.md
LICENSE
.gitignore

# ── Estilos ──
styles.css
theme-dark.scss
theme-light.scss
_typography.scss

# ── Scripts ──
navbar.js
scroll-effects.js
apa-floats-html.lua
```

### Ejemplos

```bash
# Simular todo el batch sin tocar el disco (recomendado como primer paso)
python main.py --batch archivos.txt --dry-run

# Batch completo sin confirmaciones interactivas
python main.py --batch archivos.txt --auto

# Directorio explícito
python main.py --batch archivos.txt --directory ~/Documents

# Batch con reporte JSON agregado (un solo archivo con el detalle por nombre)
python main.py --batch archivos.txt --auto --report-json reporte.json

# Combinación típica para cron/CI
python main.py --batch archivos.txt --auto --no-color --dry-run
```

Todas las opciones existentes (`--dry-run`, `--auto`, `--directory`,
`--exclude`, `--replace-exclude`, `--report-json`, `--no-color`,
`--verbose`) funcionan igual en modo batch; no hay variantes especiales.

### Salida y manejo de errores

Cada nombre se muestra con su progreso:

```text
[1/38] _metadata.yml
...
[2/38] README.md
...
```

Si un nombre falla (no encontrado, nombre inválido, error de E/S), el
error se registra y el batch **continúa con el siguiente**. Al final se
muestra un resumen agregado con la lista de errores:

```text
╔══════════════════════════════════════════════╗
║               BATCH FINALIZADO               ║
╚══════════════════════════════════════════════╝

📦 Archivos procesados: 38
✅ Correctos: 36
❌ Errores: 2
🔗 Hard links creados: 214
⏱️ Tiempo total: 12.6 segundos

Errores:
   • README2.md: No encontrado en el directorio.
   • styles2.css: 1 error(es) durante el enlace.
```

El código de salida es `0` si todos los nombres se procesaron sin
errores y `1` si alguno falló — útil para detectar fallos desde cron o CI.

---

## 🗂️ Arquitectura

```
hardlinks-creator/
├── main.py          # Punto de entrada: despacha al modo single o batch
├── config.py        # Constantes, paths predefinidos, exclusiones por defecto
└── lib/
    ├── __init__.py  # Marca lib/ como paquete Python
    ├── cli.py       # Definición de argumentos CLI (argparse)
    ├── logger.py    # Logger centralizado + constantes de color ANSI
    ├── ui.py        # Todo el output formateado al terminal
    ├── validator.py # Validación de directorio, filename, permisos, filesystem
    ├── batch.py     # Parseo del listado batch (comentarios, vacíos, duplicados)
    ├── pipeline.py  # process_filename(): pipeline completo para UN nombre
    ├── scanner.py   # Walk del árbol, cálculo SHA-256, agrupación por hash
    ├── linker.py    # Creación atómica de hard links, estadísticas
    └── reporter.py  # Exportación de reporte JSON (single y batch)
```

### Flujo de ejecución

Ambos modos convergen en el mismo pipeline:

```
Modo single                      Modo batch
───────────                      ──────────
main.py                          main.py
   │                                │
   │                             batch.py ──► lista de nombres
   │                                │  (por cada nombre)
   └──────────► pipeline.process_filename() ◄┘
                        │
                    scanner.py   (walk + SHA-256 + agrupación)
                        │
                    linker.py    (enlace atómico + estadísticas)
                        │
                    reporter.py  (reporte JSON opcional)
```

### Descripción de módulos

| Módulo             | Responsabilidad única                                                 |
| ------------------ | --------------------------------------------------------------------- |
| `main.py`          | Orquestar las fases y despachar el modo; sin lógica de negocio propia |
| `config.py`        | Todas las constantes y valores predefinidos                           |
| `lib/cli.py`       | Parsear argumentos; no valida ni ejecuta                              |
| `lib/logger.py`    | Configurar logger y constantes de color                               |
| `lib/ui.py`        | Imprimir output; no toma decisiones                                   |
| `lib/validator.py` | Validar entradas; aborta con código de salida apropiado               |
| `lib/batch.py`     | Leer y limpiar el listado batch; no sabe nada de hard links           |
| `lib/pipeline.py`  | Ejecutar el pipeline de UN nombre; compartido por ambos modos         |
| `lib/scanner.py`   | Descubrir archivos y calcular hashes; no crea links                   |
| `lib/linker.py`    | Crear links de forma atómica; no hace I/O de consola directo          |
| `lib/reporter.py`  | Serializar y guardar el reporte; no interactúa con el FS de links     |

---

## 💡 Casos de uso comunes

### Proyectos Quarto / blogs manager

```bash
# Sincronizar _metadata.yml en todos los sitios
python main.py _metadata.yml

# Sincronizar configuración Quarto global
python main.py _quarto.yml --auto

# Ver qué se haría sin hacer cambios
python main.py _metadata.yml --dry-run

# Sincronizar TODOS los archivos compartidos del sitio de una sola vez
python main.py --batch archivos-sitio.txt --auto --report-json /tmp/sync.json
```

### Configuraciones de desarrollo

```bash
python main.py .editorconfig --auto
python main.py .gitignore
python main.py requirements.txt
```

### Integración con cron

```bash
# /etc/cron.daily/hardlinks-sync
0 3 * * * /home/achalmaedison/.local/bin/hardlinks-creator \
    _metadata.yml --auto \
    --report-json /var/log/hardlinks/$(date +\%Y-\%m-\%d).json \
    --no-color >> /var/log/hardlinks/sync.log 2>&1
```

---

## 🔧 Solución de problemas

### "El directorio no existe"

Verifica que `DEFAULT_DIRECTORY` en `config.py` sea correcto, o usa `--directory`.

### "Sin permisos de escritura"

```bash
ls -la /ruta/al/archivo   # Verifica propietario y permisos
chmod u+w /ruta/al/archivo
```

### "Archivo en sistema de archivos diferente"

Los hard links no pueden cruzar particiones. Si tus sitios están en discos distintos,
usa enlaces simbólicos (`ln -s`) en su lugar.

### "Archivo .hltmp quedó en disco"

Ocurrió un fallo irrecuperable durante una operación. El `.hltmp` es el archivo original
renombrado. Recupéralo manualmente:

```bash
mv /ruta/archivo.yml.hltmp /ruta/archivo.yml
```

### Python < 3.10

Si usas Python 3.8 o 3.9, reemplaza `str | None` por `Optional[str]` en los type hints:

```python
from typing import Optional
def foo() -> Optional[str]: ...
```

---

## 🤝 Cómo contribuir

1. Fork el repositorio
2. `git checkout -b feature/nueva-funcion`
3. Crea tu módulo en `lib/nuevo_modulo.py` con responsabilidad única
4. Agrega el flag en `lib/cli.py` y llámalo desde `main.py`
5. Actualiza este README
6. `git commit -am 'feat: descripción clara'`
7. Abre Pull Request

**Estándares:** Python 3.10+, PEP 8, funciones ≤ 30 líneas, docstrings en todas las funciones públicas, sin `except Exception: pass`.

---

## ⚠️ Notas y advertencias

- **Todos los hard links comparten contenido:** modificar cualquier archivo enlazado modifica todos los demás. Esto es el comportamiento deseado para archivos de configuración compartidos.
- **Siempre haz backup antes de operaciones masivas** en directorios de producción.
- **El modo `--auto` no pide confirmación:** úsalo con `--dry-run` primero para revisar qué se enlazaría.
- **`_extensions/` está excluida por defecto** porque las extensiones Quarto pueden tener `_metadata.yml` con contenido diferente por diseño.

---

## 👤 Autor

**Edison Achalma** — Economista | Universidad Nacional de San Cristóbal de Huamanga  
GitHub: [@achalmed](https://github.com/achalmed) · LinkedIn: [achalmaedison](https://www.linkedin.com/in/achalmaedison) · Ayacucho, Perú

## 📄 Licencia

MIT License — ver archivo `LICENSE` para detalles.
