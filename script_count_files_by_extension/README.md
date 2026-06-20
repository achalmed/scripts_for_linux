# count_files_by_extension.sh

Script de Bash que analiza recursivamente un directorio y genera un reporte estadístico de los archivos agrupados por extensión: cantidad, tamaño total y proporción visual.

## Descripción

Pensado para revisar bibliotecas grandes de archivos (por ejemplo una carpeta de Zotero, un repositorio de materiales académicos o un disco de fotografías), el script recorre todo el árbol de directorios indicado, identifica la extensión de cada archivo (ignorando mayúsculas/minúsculas) y produce:

- una tabla con cantidad y tamaño total por extensión,
- un ranking de las 5 extensiones más comunes con barra de progreso visual y porcentaje,
- estadísticas generales del directorio (total de archivos, subdirectorios y tamaño combinado).

Los archivos sin extensión se agrupan bajo la etiqueta `sin_extension`.

## Requisitos

- Bash 4 o superior.
- Utilidades estándar: `find`, `stat`, `awk`, `sort`, `uniq`, `grep`, `basename`.
- Compatible tanto con `stat` de GNU/Linux (`stat -c%s`) como con la variante BSD/macOS (`stat -f%z`); el script intenta ambas automáticamente.

## Instalación

```bash
chmod +x count_files_by_extension.sh
```

## Uso

```bash
./count_files_by_extension.sh [directorio]
```

Si no se especifica un directorio, el script usa `~/Documents/biblioteca` por defecto.

### Ejemplos

```bash
# Usar el directorio por defecto (~/Documents/biblioteca)
./count_files_by_extension.sh

# Analizar una carpeta específica
./count_files_by_extension.sh ~/Documents

# Analizar con ruta absoluta
./count_files_by_extension.sh /home/usuario/proyectos

# Ver la ayuda
./count_files_by_extension.sh -h
```

## Salida esperada

El reporte se divide en tres bloques:

1. **Tabla por extensión** — extensión, cantidad de archivos y tamaño total formateado (B, KB, MB o GB según corresponda).
2. **Top 5 extensiones más comunes** — con barra de progreso (`█`) proporcional al porcentaje que representa cada extensión sobre el total de archivos.
3. **Estadísticas generales** — total de archivos, total de directorios (sin contar el directorio raíz analizado), tamaño total y nombre de la ruta analizada.

## Notas de la versión corregida

Esta versión corrige un defecto del script original en la función `show_top_extensions()`: el porcentaje de cada extensión se calcula como número decimal (por ejemplo `42.9`), pero la aritmética nativa de Bash (`$(( ))`) **no admite punto flotante**, así que la línea `bar_length=$((percentage / 2))` lanzaba un error de sintaxis (`invalid arithmetic operator`) y el script se detenía antes de mostrar las estadísticas generales. Se corrigió usando `awk` para hacer la división y truncar el resultado a entero:

```bash
bar_length=$(awk "BEGIN {printf \"%d\", $percentage/2}")
```

También se añadió `set -uo pipefail` al inicio del script para que errores de variables no definidas o fallos en tuberías se detecten de inmediato en lugar de continuar silenciosamente.

## Limitaciones conocidas

- El cálculo de tamaño por extensión recorre el árbol de archivos una vez por cada extensión encontrada (`get_size_by_extension`), lo cual es razonable para bibliotecas de tamaño moderado pero puede ser lento en directorios con cientos de miles de archivos y docenas de extensiones distintas.
- Los nombres de archivo con saltos de línea no son soportados (limitación estándar de procesar `find` línea por línea); en la práctica esto es extremadamente raro.

## Autor

Edison Achalma — 2024 (script original), corregido y documentado 2026.