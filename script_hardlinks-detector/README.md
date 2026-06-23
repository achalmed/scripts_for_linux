# hardlinks-detector

> Detecta y visualiza todos los hard links existentes en un árbol de directorios,
> en formato árbol jerárquico, CSV o JSON — con filtros por inodo y conteo mínimo de enlaces.

**Proyecto complementario:** [`hardlinks-creator`](../hardlinks-creator/) — crea hard links entre archivos con contenido idéntico.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Novedades v3.0](#-novedades-v30-respecto-al-script-original)
- [Bugs corregidos](#-bugs-corregidos)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Arquitectura](#-arquitectura)
- [Casos de uso comunes](#-casos-de-uso-comunes)
- [Solución de problemas](#-solución-de-problemas)
- [Cómo contribuir](#-cómo-contribuir)
- [Notas y advertencias](#️-notas-y-advertencias)

---

## 📖 Descripción

`hardlinks-detector` escanea recursivamente un directorio usando `find -links +1`,
agrupa los archivos por inodo y los presenta en:

- **Árbol jerárquico** (por defecto) — para revisión visual
- **CSV** — para importar en hojas de cálculo o Zotero/Calibre workflows
- **JSON** — para CI/CD pipelines o consumir desde `hardlinks-creator`'s reporter

Diseñado como la herramienta de verificación y auditoría del par
`hardlinks-creator` / `hardlinks-detector`, usados juntos para optimizar
los proyectos Quarto/blog de publicaciones académicas.

---

## 🆕 Novedades v3.0 (respecto al script original)

| Característica nueva           | Descripción                                                 |
| ------------------------------ | ----------------------------------------------------------- |
| **Formato CSV**                | `--format csv` exporta datos para hojas de cálculo          |
| **Formato JSON**               | `--format json` para integración con CI y otros scripts     |
| **`--output FILE`**            | Guarda la salida en archivo y también la muestra en consola |
| **`--min-links N`**            | Filtra grupos con menos de N enlaces                        |
| **`--filter-inode N`**         | Muestra solo el grupo de un inodo específico                |
| **Un solo `stat` por archivo** | El scan original hacía 2 llamadas a stat; ahora es 1        |
| **Arquitectura modular**       | 5 módulos con responsabilidad única                         |

---

## 🐛 Bugs corregidos

### Bug #1 — `format_size()` requería `bc` sin verificar disponibilidad (`lib/ui.sh`)

- **Original:** Usaba `$(echo "$size >= 1024" | bc -l)` en un bucle `while`.
  Si `bc` no está instalado (ausente en imágenes Docker mínimas), el script
  fallaba silenciosamente produciendo output vacío.
- **Corrección:** Reimplementado con aritmética entera pura de Bash
  (`(( size >= 1024 ))`), sin dependencias externas.

### Bug #2 — Padding desalineado en la caja de resumen (`lib/ui.sh`)

- **Original:** El padding usaba `${#variable} / 10` (longitud de string como
  entero crudo), produciendo columnas desalineadas cuando el número tenía
  más de un dígito.
- **Corrección:** Reimplementado con `printf "%-Ns"` de ancho fijo que alinea
  correctamente independientemente del valor.

---

## ⚙️ Requisitos

- **Bash** ≥ 4.0 (arrays asociativos con `declare -A`)
- **Herramientas:** `find`, `stat`, `sort`, `realpath` (paquete `coreutils`)
- **Sistema:** Linux/Unix
- **Permisos:** lectura en el directorio a escanear

```bash
# Verificar versión de Bash
bash --version

# Instalar dependencias si faltan (Debian/Ubuntu)
sudo apt install coreutils findutils
```

---

## 🚀 Instalación

```bash
# 1. Clonar en tu carpeta de scripts
cd ~/Documents/scripts_for_linux
git clone https://github.com/achalmed/hardlinks-detector.git
cd hardlinks-detector

# 2. Dar permisos de ejecución
chmod +x main.sh lib/*.sh

# 3. (Opcional) Acceso global
mkdir -p ~/.local/bin
ln -s "$(pwd)/main.sh" ~/.local/bin/hardlinks-detector

# Agregar al PATH si no está (añadir a ~/.zshrc o ~/.bashrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 💻 Uso

### Sintaxis

```bash
./main.sh [DIRECTORIO] [OPCIONES]
# o si está en el PATH:
hardlinks-detector [DIRECTORIO] [OPCIONES]
```

### Opciones disponibles

| Flag                  | Descripción                                   | Por defecto       |
| --------------------- | --------------------------------------------- | ----------------- |
| `DIRECTORIO`          | Directorio raíz a analizar                    | Directorio actual |
| `-f, --format FORMAT` | Formato de salida: `tree`, `csv`, `json`      | `tree`            |
| `-o, --output FILE`   | Guardar salida en archivo (además de consola) | —                 |
| `--min-links N`       | Solo grupos con ≥ N enlaces                   | `2`               |
| `--filter-inode N`    | Solo el grupo con ese inodo                   | —                 |
| `--no-color`          | Desactivar colores ANSI                       | —                 |
| `-v, --verbose`       | Mensajes de depuración                        | —                 |
| `--version`           | Mostrar versión                               | —                 |
| `-h, --help`          | Mostrar ayuda                                 | —                 |

### Ejemplos

```bash
# Ver hard links en el directorio actual
./main.sh

# Analizar directorio de publicaciones
./main.sh ~/Documents

# Exportar como JSON
./main.sh ~/Documents --format json --output links.json

# Exportar como CSV
./main.sh ~/Documents --format csv --output links.csv

# Solo grupos con 10 o más enlaces (proyectos grandes)
./main.sh ~/Documents --min-links 10

# Inspeccionar un inodo específico (tras ver el reporte)
./main.sh ~/Documents --filter-inode 14820714

# Sin colores para log de CI o pipe
./main.sh ~/Documents --no-color | grep "Conjunto"
```

---

## 🗂️ Arquitectura

```
hardlinks-detector/
├── main.sh          # Punto de entrada: orquesta las 5 fases del pipeline
├── config.sh        # Constantes, paths, valores predefinidos
└── lib/
    ├── logger.sh    # Logging centralizado (INFO/WARN/ERROR/DEBUG) + colores ANSI
    ├── ui.sh        # Output formateado: headers, separadores, mensajes, format_size
    ├── validator.sh # Validación de directorio, permisos, herramientas del sistema
    ├── cli.sh       # Parsing de argumentos y función show_help
    ├── scanner.sh   # find + stat, agrupación por inodo en arrays asociativos
    └── renderer.sh  # Tres renderers: render_tree, render_csv, render_json
```

### Descripción de módulos

| Módulo             | Responsabilidad única                               |
| ------------------ | --------------------------------------------------- |
| `main.sh`          | Orquestar las 5 fases; sin lógica de negocio propia |
| `config.sh`        | Todas las constantes y valores predefinidos         |
| `lib/logger.sh`    | Funciones de log y constantes de color ANSI         |
| `lib/ui.sh`        | Todo el output formateado; no toma decisiones       |
| `lib/validator.sh` | Validar entradas y herramientas; aborta temprano    |
| `lib/cli.sh`       | Parsear argumentos; no valida ni ejecuta            |
| `lib/scanner.sh`   | Descubrir hard links; popula arrays globales        |
| `lib/renderer.sh`  | Renderizar datos en tree/csv/json; no accede al FS  |

---

## 💡 Casos de uso comunes

### Verificar después de usar hardlinks-creator

```bash
# Crear links
python ~/Documents/scripts_for_linux/hardlinks-creator/main.py _metadata.yml --auto

# Verificar resultado
hardlinks-detector ~/Documents
```

### Auditoría en formato JSON para reporte automatizado

```bash
hardlinks-detector ~/Documents \
    --format json \
    --output ~/reports/hardlinks-$(date +%Y-%m-%d).json
```

### Integración con blog manager scripts

```bash
# Ver cuántos _metadata.yml comparten inodo (confirmación de sync)
hardlinks-detector ~/Documents \
    --format csv \
    --no-color | grep "_metadata.yml" | wc -l
```

### Diagnosticar un inodo específico

```bash
# Primero obtener el inodo
stat -c '%i' ~/Documents/blog/posts/_metadata.yml

# Luego ver todos los enlaces de ese inodo
hardlinks-detector ~/Documents --filter-inode 14820714
```

---

## 🔧 Solución de problemas

### "Permission denied" al ejecutar

```bash
chmod +x main.sh lib/*.sh
```

### "bash: declare -A: invalid option" (Bash < 4.0)

En macOS, el Bash del sistema es 3.x. Instala Bash moderno:

```bash
brew install bash
# Luego ejecuta con:
/usr/local/bin/bash main.sh
```

### "realpath: command not found"

```bash
# Debian/Ubuntu
sudo apt install coreutils

# Arch Linux
sudo pacman -S coreutils
```

### La salida JSON no es válida

Verifica que el directorio no contenga nombres de archivo con comillas dobles o backslashes,
que se generan raramente pero podrían romper el JSON manual. En ese caso usa `--format csv`.

---

## 🤝 Cómo contribuir

1. Fork el repositorio
2. `git checkout -b feature/nueva-funcion`
3. Crea tu módulo en `lib/nuevo_modulo.sh` con responsabilidad única
4. Agrégalo con `source` en `main.sh`
5. Documenta cada función con el bloque de comentario estándar
6. Actualiza este README
7. Abre Pull Request

**Estándares:** Bash 4.0+, `set -uo pipefail`, funciones ≤ 30 líneas, sin `2>/dev/null` sin comentario explicativo, variables locales siempre declaradas con `local`.

---

## ⚠️ Notas y advertencias

- **Los arrays asociativos requieren Bash 4.0+.** En macOS el shell por defecto es zsh; este script es Bash-only.
- **Directorios con millones de archivos** pueden tardar; el scan hace una sola pasada de `find` pero el `stat` por archivo es inevitable.
- **El formato JSON es manual** (sin `jq`), por diseño de cero dependencias. Si necesitas JSON robusto con caracteres especiales, pasa la salida por `jq .`.
- **`--filter-inode` es case-sensitive** respecto al número; cópialo exactamente del output de `stat -c '%i'`.

---

## 👤 Autor

**Edison Achalma** — Economista | Universidad Nacional de San Cristóbal de Huamanga  
GitHub: [@achalmed](https://github.com/achalmed) · LinkedIn: [achalmaedison](https://www.linkedin.com/in/achalmaedison) · Ayacucho, Perú

## 📄 Licencia

MIT License — ver archivo `LICENSE` para detalles.
