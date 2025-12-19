# File & Folder Tools – Colección de utilidades Bash + Python

![bash](https://img.shields.io/badge/bash-scripts-green) ![python](https://img.shields.io/badge/python-3.8%2B-blue) ![license](https://img.shields.io/github/license/tu-usuario/file-folder-tools)

#readme

**Cuatro scripts imprescindibles** para gestionar archivos y carpetas en proyectos grandes (bibliotecas digitales, cursos, documentación, código, etc.).

| # | Script | Lenguaje | ¿Qué hace? | Uso típico |
|---|------|----------|------------|------------|
| 1 | `count_files_by_extension.sh` | Bash | Analiza recursivamente un directorio y muestra cuántos archivos hay por extensión + tamaño total + Top 5 + estadísticas | Saber qué tipo de archivos dominan tu biblioteca o proyecto |
| 2 | `create_folders_batch.sh` | Bash | Crea cientos de carpetas de golpe desde una lista predefinida o archivo externo | Preparar la estructura de un curso, proyecto o colección |
| 3 | `create_hardlinks.py` | Python 3 | Busca archivos con nombre exacto (ej. `_contenido-inicio.qmd`) y los reemplaza por **hard links** al primero encontrado (ahorra espacio y mantiene sincronía) | Proyectos Quarto, Obsidian, MkDocs, etc. con archivos repetidos |
| 4 | `detect_hardlinks_tree.sh` | Bash | Muestra en forma de árbol todos los enlaces duros existentes en un directorio | Verificar que los hard links se crearon correctamente y gestionarlos |

## 1. count_files_by_extension.sh – Analizador de extensiones

```bash
# Por defecto analiza ~/Documents/biblioteca
./count_files_by_extension.sh

# Analizar cualquier carpeta
./count_files_by_extension.sh "/ruta/a/mi/proyecto"
```

**Salida ejemplo:**
```
EXTENSIÓN            CANTIDAD      TAMAÑO TOTAL
.pdf                    2845         12.45 GB
.epub                   1234          3.21 GB
.qmd                     567          89.4 MB
...

Top 5 extensiones más comunes:
 .pdf          2845 archivos [█████████████████████████]  68.4%
 .epub         1234 archivos [███████████]               29.7%
```

## 2. create_folders_batch.sh – Creador masivo de carpetas

```bash
# Lista predefinida (ideal para cursos)
./create_folders_batch.sh

# Desde un archivo txt (una carpeta por línea)
./create_folders_batch.sh -f mis_carpetas.txt

# En otro directorio + modo verbose + dry-run
./create_folders_batch.sh -p "/ruta/proyecto" -f lista.txt -v -d
```

Soporta subcarpetas (`carpeta/subcarpeta`) y nunca crea duplicados.

## 3. create_hardlinks.py – Hard links automáticos (ahorro brutal de espacio)

Perfecto para proyectos donde el mismo archivo aparece en muchas carpetas (Quarto, Obsidian, cursos con _contenido-inicio.qmd, etc.).

```bash
# Ejemplo típico en un libro/cursos Quarto
python create_hardlinks.py _contenido-inicio.qmd
python create_hardlinks.py _contenido-final.qmd
python create_hardlinks.py header.html
```

- Solo crea hard link si el contenido es idéntico (compara hash SHA-256)
- Excluye por defecto: `_site`, `.git`, `_freeze`, etc.
- Puedes añadir más exclusiones: `--exclude temp build`

**Antes → 500 MB**  
**Después → 3 MB** (¡todos apuntan al mismo archivo físico!)

## 4. detect_hardlinks.sh – Visualizador de enlaces duros

```bash
# Directorio actual
./detect_hardlinks.sh

# Otro directorio
./detect_hardlinks.sh "/home/yo/mi-proyecto"
```

Muestra un árbol bonito como este:

```
Conjunto #1
 Inodo: 1234567 │ Enlaces: 48 │ Tamaño: 2.1K

 ├── 01-introduccion/
 │   └── _contenido-inicio.qmd
 ├── 02-fundamentos/
 │   └── _contenido-inicio.qmd
 ├── 03-avanzado/
 │   └── _contenido-inicio.qmd
 └── 10-anexos/
     └── _contenido-inicio.qmd
```

## Instalación / Uso rápido

```bash
# Clonar el repo
git clone https://github.com/tu-usuario/file-folder-tools.git
cd file-folder-tools

# Dar permisos de ejecución a los bash
chmod +x *.sh

# (Opcional) Python ya viene en casi todos los sistemas
python --version
```

## Licencia

**MIT License** – úsalos, modifícalos y compártelos libremente.

## Autor

Edison Achalma – 2024–2025  
Con mucho cariño para la comunidad de organización digital y software libre

---

**¡Dale una estrella si te ahorran horas de trabajo!**
