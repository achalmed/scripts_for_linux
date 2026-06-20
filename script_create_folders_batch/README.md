# create_folders_batch.sh

Script de Bash para crear múltiples carpetas de forma masiva, ya sea a partir de una lista predefinida dentro del propio script o desde un archivo de texto externo.

## Descripción

Cuando se necesita preparar de antemano la estructura de carpetas de un proyecto (por ejemplo, los módulos de un curso, las secciones de un repositorio o las entregas de un semestre), crear cada carpeta a mano con `mkdir` es lento y propenso a errores de tipeo. Este script automatiza esa tarea: lee una lista de nombres de carpeta, valida cada uno, evita duplicados y reporta un resumen final con lo creado, lo que ya existía y lo que falló.

Incluye modo de simulación (`dry-run`) para revisar qué se crearía antes de tocar el sistema de archivos, y modo `verbose` para depurar el procesamiento línea por línea.

## Requisitos

- Bash 4 o superior (usa `getopts` extendido y sustitución de procesos).
- Utilidades estándar de GNU/Linux: `mkdir`, `grep`, `sed`. No requiere paquetes adicionales.
- Probado en Kubuntu y Arch Linux; debería funcionar en cualquier distribución con Bash moderno.

## Instalación

```bash
chmod +x create_folders_batch.sh
```

No requiere instalación adicional. Puedes moverlo a un directorio en tu `$PATH` (por ejemplo `~/.local/bin/`) si quieres invocarlo desde cualquier lugar.

## Uso

```bash
./create_folders_batch.sh [opciones]
```

### Opciones

| Opción | Descripción |
|---|---|
| `-f <archivo>` | Lee los nombres de carpeta desde un archivo de texto en lugar de la lista predefinida del script. |
| `-p <ruta>` | Directorio base donde se crearán las carpetas (por defecto: directorio actual `.`). |
| `-v`, `--verbose` | Modo detallado: muestra el procesamiento de cada línea. |
| `-d`, `--dry-run` | Simula la creación sin escribir nada en disco; útil para revisar antes de confirmar. |
| `-h`, `--help` | Muestra la ayuda en pantalla. |

### Ejemplos

```bash
# Usar la lista predefinida en el directorio actual
./create_folders_batch.sh

# Leer la lista desde un archivo externo
./create_folders_batch.sh -f lista_carpetas.txt

# Crear las carpetas en una ruta específica
./create_folders_batch.sh -p /home/usuario/proyectos

# Simular antes de ejecutar (no crea nada)
./create_folders_batch.sh -d -f carpetas.txt

# Modo detallado combinado con archivo y ruta personalizados
./create_folders_batch.sh -v -f mis_carpetas.txt -p /tmp/nuevas_carpetas
```

### Formato del archivo de entrada (`-f`)

Un nombre de carpeta por línea. Se admiten subcarpetas usando `/` en la ruta. Las líneas vacías y las que comienzan con `#` se ignoran (sirven como comentarios):

```
# Módulo 1
carpeta-uno
carpeta-dos

# Módulo 2 con subcarpeta
carpeta-tres/subcarpeta
```

## Flujo de ejecución

1. Valida que el directorio base (`-p`) exista; si no existe, pregunta si se debe crear.
2. Valida que el archivo de entrada (`-f`), si se especificó, exista.
3. Obtiene la lista de carpetas (del archivo o de la lista predefinida).
4. Muestra una vista previa con el conteo total y las primeras carpetas a crear.
5. Pide confirmación antes de proceder (salvo en modo `dry-run`).
6. Crea cada carpeta, detectando duplicados existentes y registrando errores.
7. Imprime un resumen final con totales de creadas, ya existentes y fallidas.

## Notas de la versión corregida

Esta versión corrige un defecto del script original: el mensaje informativo `"Usando lista predefinida de carpetas"` se imprimía por la salida estándar (stdout) junto con la propia lista de carpetas, lo que provocaba que el script intentara crear una carpeta espuria con el texto de ese mensaje como nombre. Ahora todos los mensajes de registro (`log_info`, etc.) se envían explícitamente a la salida de error (stderr) dentro de `get_folders_list()`, separándolos limpiamente de los datos reales.

También se añadió `set -uo pipefail` para detectar variables no definidas y fallos en tuberías de forma más temprana, y se reemplazó el conteo de carpetas basado en `wc -l` (que puede fallar si el archivo de entrada no termina con un salto de línea) por un conteo manual robusto que ignora líneas vacías.

## Personalización

Para editar la lista predefinida de carpetas, modifica directamente el bloque `PREDEFINED_FOLDERS` dentro del script:

```bash
PREDEFINED_FOLDERS=$(cat <<EOF
nombre-carpeta-1
nombre-carpeta-2
EOF
)
```

## Autor

Edison Achalma — 2024 (script original), corregido y documentado 2026.