# arch_pdf_metadata_commands.sh

Referencia de comandos de terminal para inspeccionar y extraer metadatos (XMP y DocInfo) de archivos PDF en Arch Linux, con énfasis en flujos de trabajo de Zotero.

## Descripción

Este archivo **no es un script para ejecutar de corrido**: es una colección organizada de comandos de referencia, agrupados por herramienta, pensados para copiar y pegar según la necesidad. Cada bloque usa `archivo.pdf` como marcador de posición que debes reemplazar por la ruta real de tu PDF.

Cubre dos tipos de metadatos distintos que suelen confundirse:

- **DocInfo** — el diccionario clásico `/Info` del PDF (Título, Autor, Producer, fechas de creación/modificación). Es el formato más antiguo y limitado.
- **XMP (Extensible Metadata Platform)** — un paquete de metadatos en XML/RDF incrustado en el PDF, con vocabulario Dublin Core (`dc:title`, `dc:creator`, `dc:identifier`, etc.). Es el formato que usan extensiones como el script de Zotero para incrustar metadatos enriquecidos (DOI, resumen, etiquetas).

## Herramientas cubiertas

| Herramienta | Paquete (pacman/AUR) | Uso principal |
|---|---|---|
| `exiftool` | `perl-image-exiftool` | La más completa: lee XMP, DocInfo y estructura interna. Recomendada como primera opción. |
| `pdfinfo` | `poppler` | Rápida, ideal para DocInfo básico; con `-meta` también muestra el bloque XMP crudo. |
| `pdftk` | AUR (`yay -S pdftk` / `paru -S pdftk`) | Inspección y manipulación avanzada de formularios y campos. |
| `qpdf` | `qpdf` | Inspector de estructura interna del PDF; útil para diagnóstico y validación. |
| `mutool` | `mupdf-tools` | Muy rápido, parte del proyecto MuPDF; permite inspeccionar objetos internos directamente. |
| `strings` + `grep` | incluido en `binutils`/`coreutils` | Método de emergencia sin instalar nada: extrae el bloque XMP como texto plano del binario. |
| `pypdf` (Python) | `pip install pypdf` | Lectura programática para integrarse en scripts propios. |

## Instalación de herramientas

```bash
sudo pacman -S perl-image-exiftool poppler qpdf mupdf-tools
yay -S pdftk          # o: paru -S pdftk
pip install pypdf --user
```

## Cómo usar este archivo

1. Abre el archivo y ubica el bloque numerado correspondiente a lo que necesitas (instalación, exiftool, pdfinfo, qpdf, mutool, grep directo, Python, recorrido masivo de Zotero, o alias).
2. Copia el comando, reemplaza `archivo.pdf` por tu ruta real y ejecútalo en tu terminal.
3. Para flujos repetitivos, considera agregar los alias de la sección 9 a tu `~/.bashrc` o `~/.zshrc`.

### Ejemplo rápido (el más usado en la práctica)

```bash
exiftool -Title -Author -Creator -Date -Description -Subject -Keywords archivo.pdf
```

### Revisar todos los PDFs de tu biblioteca Zotero de una vez

```bash
find ~/Zotero/storage -name "*.pdf" -exec echo "=== {} ===" \; \
  -exec exiftool -Title -Author -Date -Keywords {} \; 2>/dev/null
```

### Detectar qué PDFs aún no tienen metadatos (pendientes de procesar)

```bash
find ~/Zotero/storage -name "*.pdf" | while IFS= read -r f; do
  title=$(exiftool -s3 -Title "$f" 2>/dev/null)
  if [ -z "$title" ]; then
    echo "⚠️  Sin metadatos: $f"
  fi
done
```

## Alias sugeridos para `~/.bashrc` o `~/.zshrc`

```bash
alias pdfmeta='exiftool -Title -Author -Date -Keywords -Description -Subject'
alias pdfxmp='exiftool -XMP:all'
alias pdfinfo-full='pdfinfo -meta'

pdfzotero() {
  find ~/Zotero/storage -name "*.pdf" -exec exiftool -s3 -Title {} \; 2>/dev/null \
    | grep -i "$1"
}
```

Uso: `pdfmeta archivo.pdf`, `pdfxmp archivo.pdf`, `pdfzotero "palabra del título"`.

## Notas de la versión corregida

Al revisar el archivo original se detectaron y corrigieron tres comandos con errores de sintaxis o de fondo:

1. **`qpdf --show-object=1 archivo.pdf`** — esta opción no existe en `qpdf`; el comando fallaría con un error de argumento inválido. Se reemplazó por `qpdf --check archivo.pdf` (valida la integridad estructural del PDF) y se corrigió el comando de extracción de metadatos vía JSON a `qpdf --json=latest archivo.pdf | grep ...`, que sí es sintaxis válida.
2. **`mutool show archivo.pdf trailer/Info`** anunciado como forma de "extraer el XML XMP completo** — esto es incorrecto: `trailer/Info` apunta al diccionario DocInfo clásico, no al paquete XMP. El paquete XMP real, cuando existe, vive en `trailer/Root/Metadata`. Se añadió el comando correcto (`mutool show archivo.pdf trailer/Root/Metadata`) manteniendo el original para referencia de DocInfo.
3. **Manejo de rutas con espacios** — los bucles `find ... | while read f` del bloque 8 y la función `pdfzotero` no protegían contra el "comerse" backslashes o espacios al inicio/fin de nombres de archivo. Se cambió a `while IFS= read -r f` para un manejo robusto, consistente con las buenas prácticas usadas en los otros scripts de esta colección.

Adicionalmente, se documentó que en el bloque de Python, los campos `xmp.dc_title` y `xmp.dc_description` de `pypdf` retornan **diccionarios por idioma** (ej. `{'x-default': 'Mi título'}`), no cadenas de texto simples, mientras que la mayoría de los demás campos `dc_*` retornan listas. Esto es importante al programar lógica que dependa de estos valores.

## Limitaciones

- El método de `strings | grep` (sección 6) solo funciona si el PDF no comprime el flujo XMP; muchos PDFs modernos sí lo comprimen, en cuyo caso no aparecerá texto legible y será necesario usar `exiftool` o `pdfinfo -meta`.
- `qpdf --check` valida la estructura del PDF, no garantiza la presencia de metadatos; úsalo como diagnóstico complementario, no como sustituto de `exiftool`.

## Autor

Edison Achalma | Universidad Nacional de San Cristóbal de Huamanga — documentación original, corregida y ampliada 2026.