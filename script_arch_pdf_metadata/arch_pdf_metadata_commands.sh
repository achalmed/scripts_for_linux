# ══════════════════════════════════════════════════════════════════════════════
# ARCH LINUX — Ver Metadatos de PDFs desde el Terminal
# Edison Achalma | Universidad Nacional de San Cristóbal de Huamanga
# ══════════════════════════════════════════════════════════════════════════════
#
# ADVERTENCIA: este archivo es una REFERENCIA DE COMANDOS, no un script para
# ejecutar de corrido con `bash arch_pdf_metadata_commands.sh`. Cada bloque es
# independiente y usa "archivo.pdf" como marcador de posición que debes
# reemplazar por la ruta real de tu PDF. Copia y pega el comando que necesites.
# ══════════════════════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────────────────────
# 1. INSTALACIÓN DE HERRAMIENTAS
# ──────────────────────────────────────────────────────────────────────────────

# exiftool — la herramienta más completa para metadatos XMP/DocInfo
sudo pacman -S perl-image-exiftool

# pdfinfo — parte de poppler, rápido para DocInfo básico
sudo pacman -S poppler

# pdftk — para inspección avanzada (en AUR)
yay -S pdftk          # o: paru -S pdftk

# qpdf — inspector de estructura PDF
sudo pacman -S qpdf

# mutool — parte de mupdf, muy rápido
sudo pacman -S mupdf-tools


# ──────────────────────────────────────────────────────────────────────────────
# 2. EXIFTOOL — VER METADATOS XMP COMPLETOS (recomendado)
# ──────────────────────────────────────────────────────────────────────────────

# Ver TODOS los metadatos del PDF (XMP + DocInfo + estructura)
exiftool archivo.pdf

# Ver solo metadatos XMP (los que incrusta el script de Zotero)
exiftool -XMP:all archivo.pdf

# Ver campos Dublin Core específicos
exiftool -dc:all archivo.pdf

# Ver solo los campos más útiles: título, autor, fecha, DOI, resumen
exiftool -Title -Author -Creator -Date -Description -Subject -Keywords archivo.pdf

# Ver metadatos en formato JSON (útil para scripts)
exiftool -json archivo.pdf

# Ver metadatos en formato XML completo
exiftool -xmlformat archivo.pdf

# Procesar múltiples PDFs a la vez
exiftool *.pdf

# Ver metadatos de todos los PDFs en un directorio de forma recursiva
exiftool -r /ruta/a/directorio/*.pdf

# Ejemplo con ruta típica de Zotero en Linux:
exiftool ~/Zotero/storage/XXXXXXXX/articulo.pdf

# Filtrar solo líneas no vacías (más limpio)
exiftool archivo.pdf | grep -v "^$"

# Ver solo campos que contienen información XMP (los del script de Zotero)
exiftool archivo.pdf | grep -E "Title|Author|Creator|Description|Subject|Keywords|Date|DOI|Publisher|Source|Modify"


# ──────────────────────────────────────────────────────────────────────────────
# 3. PDFINFO — VER DocInfo BÁSICO (rápido)
# ──────────────────────────────────────────────────────────────────────────────

# Información básica del PDF (título, autor, palabras clave, fechas)
pdfinfo archivo.pdf

# Con metadatos XMP también
pdfinfo -meta archivo.pdf

# Mostrar el XML XMP completo incrustado
pdfinfo -meta archivo.pdf | grep -A 1000 "Metadata:"


# ──────────────────────────────────────────────────────────────────────────────
# 4. QPDF — INSPECCIÓN AVANZADA DE ESTRUCTURA PDF
# ──────────────────────────────────────────────────────────────────────────────

# Ver información general (chequeo de validez estructural del PDF)
qpdf --check archivo.pdf

# Extraer el flujo XMP (si existe) — vía JSON de qpdf + grep
# (corregido: qpdf no tiene la opción --show-object; --json es la forma
# correcta de inspeccionar objetos de metadatos)
qpdf --json=latest archivo.pdf | grep -i "xmp\|metadata\|title\|author" | head -40


# ──────────────────────────────────────────────────────────────────────────────
# 5. MUTOOL — VER METADATOS CON MUPDF
# ──────────────────────────────────────────────────────────────────────────────

# Información del PDF (DocInfo básico: título, autor, fechas)
mutool info archivo.pdf

# Ver el diccionario Info del trailer (metadatos DocInfo, NO es XMP)
mutool show archivo.pdf trailer/Info

# Ver el flujo XMP real (si existe) — está en trailer/Root/Metadata,
# no en trailer/Info (corregido: el comando original mostraba el lugar
# equivocado para datos XMP)
mutool show archivo.pdf trailer/Root/Metadata


# ──────────────────────────────────────────────────────────────────────────────
# 6. GREP DIRECTO — SIN INSTALAR NADA (para emergencias)
# ──────────────────────────────────────────────────────────────────────────────
# Los metadatos XMP son texto XML legible dentro del PDF binario.
# Se puede extraer con strings + grep sin instalar herramientas extra.

# Ver si el PDF tiene paquete XMP
strings archivo.pdf | grep -c "xpacket"

# Extraer el bloque XMP completo
strings archivo.pdf | grep -A 200 "xpacket begin" | grep -B 200 "xpacket end"

# Buscar título
strings archivo.pdf | grep -i "dc:title" -A 3

# Buscar autores
strings archivo.pdf | grep -i "dc:creator" -A 10

# Buscar DOI
strings archivo.pdf | grep -i "dc:identifier\|doi:"

# Buscar palabras clave / etiquetas
strings archivo.pdf | grep -i "pdf:Keywords\|dc:subject" -A 5


# ──────────────────────────────────────────────────────────────────────────────
# 7. PYTHON — LECTURA PROGRAMÁTICA CON pypdf
# ──────────────────────────────────────────────────────────────────────────────
# pip install pypdf

python3 << 'EOF'
from pypdf import PdfReader
import sys

pdf_path = "archivo.pdf"   # <- cambia esto
reader = PdfReader(pdf_path)
meta = reader.metadata

print("=" * 50)
print("  METADATOS DocInfo (estándar PDF)")
print("=" * 50)
print(f"  Título    : {meta.title    or '-'}")
print(f"  Autor     : {meta.author   or '-'}")
print(f"  Asunto    : {meta.subject  or '-'}")
print(f"  Keywords  : {meta.get('/Keywords') or '-'}")
print(f"  Creator   : {meta.creator  or '-'}")
print(f"  Producer  : {meta.producer or '-'}")
print(f"  CreationDate: {meta.creation_date or '-'}")
print(f"  ModDate   : {meta.modification_date or '-'}")
print()

# Si hay XMP disponible
if reader.xmp_metadata:
    xmp = reader.xmp_metadata
    print("=" * 50)
    print("  METADATOS XMP")
    print("=" * 50)
    # Nota: dc_title y dc_description son diccionarios {idioma: texto}
    # (ej. {'x-default': 'Mi título'}), no strings simples; el resto de
    # campos dc_* suelen ser listas.
    print(f"  dc:title       : {xmp.dc_title}")
    print(f"  dc:creator     : {xmp.dc_creator}")
    print(f"  dc:description : {xmp.dc_description}")
    print(f"  dc:subject     : {xmp.dc_subject}")
    print(f"  dc:publisher   : {xmp.dc_publisher}")
    print(f"  dc:date        : {xmp.dc_date}")
    print(f"  dc:identifier  : {xmp.dc_identifier}")
    print(f"  dc:type        : {xmp.dc_type}")
    print(f"  dc:source      : {xmp.dc_source}")
else:
    print("  (sin metadatos XMP en este PDF)")
EOF


# ──────────────────────────────────────────────────────────────────────────────
# 8. SCRIPT BASH — REVISAR TODOS LOS PDFs DE ZOTERO
# ──────────────────────────────────────────────────────────────────────────────

# Ver metadatos de TODOS los PDFs en el directorio de Zotero
find ~/Zotero/storage -name "*.pdf" -exec echo "=== {} ===" \; \
  -exec exiftool -Title -Author -Date -Keywords {} \; 2>/dev/null

# Solo los que SÍ tienen título (procesados por el script de Zotero)
find ~/Zotero/storage -name "*.pdf" | while IFS= read -r f; do
  title=$(exiftool -s3 -Title "$f" 2>/dev/null)
  if [ -n "$title" ]; then
    echo "✅ $title"
    echo "   $f"
  fi
done

# Solo los que NO tienen metadatos (pendientes de procesar)
find ~/Zotero/storage -name "*.pdf" | while IFS= read -r f; do
  title=$(exiftool -s3 -Title "$f" 2>/dev/null)
  if [ -z "$title" ]; then
    echo "⚠️  Sin metadatos: $f"
  fi
done


# ──────────────────────────────────────────────────────────────────────────────
# 9. ALIAS ÚTILES — agregar a ~/.bashrc o ~/.zshrc
# ──────────────────────────────────────────────────────────────────────────────

# Pegar en ~/.bashrc o ~/.zshrc:

alias pdfmeta='exiftool -Title -Author -Date -Keywords -Description -Subject'
# Uso: pdfmeta archivo.pdf

alias pdfxmp='exiftool -XMP:all'
# Uso: pdfxmp archivo.pdf

alias pdfinfo-full='pdfinfo -meta'
# Uso: pdfinfo-full archivo.pdf

# Función para buscar PDFs de Zotero por título
pdfzotero() {
  find ~/Zotero/storage -name "*.pdf" -exec exiftool -s3 -Title {} \; 2>/dev/null \
    | grep -i "$1"
}
# Uso: pdfzotero "nombre del artículo"
# Nota: si necesitas también la ruta del archivo encontrado, usa en su lugar:
#   find ~/Zotero/storage -name "*.pdf" | while IFS= read -r f; do
#     exiftool -s3 -Title "$f" | grep -qi "$1" && echo "$f"
#   done