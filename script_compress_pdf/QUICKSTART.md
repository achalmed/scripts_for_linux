# Guía Rápida de Uso - PDF Compressor v2.0

## 🚀 Inicio Rápido (5 minutos)

### 1. Instalar (solo una vez)

```bash
cd ~/Downloads  # o donde hayas descargado los archivos
chmod +x install.sh
./install.sh
```

Selecciona la opción **1** (instalación en carpeta fija con wrapper global)

### 2. Tu primer compresión

```bash
# Desde cualquier lugar
pdf-compress ~/Documents/mi_libro.pdf
```

¡Listo! Encontrarás `mi_libro_compressed.pdf` junto al original.

## 📊 Casos de Uso Comunes

### Para bibliotecas digitales completas

```bash
# Comprimir toda tu biblioteca recursivamente
pdf-compress -m ebook -r ~/Documents/biblioteca
```

**Resultado típico:** 
- 🔥 Reduce 60-85% el tamaño
- 📱 Perfecta calidad para tablets/e-readers
- ⚡ Procesa automáticamente subdirectorios
- 💾 Archivos comprimidos quedan junto a originales

### Para compartir por email/WhatsApp

```bash
# Máxima compresión
pdf-compress -m screen ~/Documents/presentacion.pdf
```

**Resultado típico:**
- 🔥 Reduce 80-95% el tamaño
- 📧 Perfecto para enviar por email
- 📱 Calidad suficiente para lectura rápida

### Para PDFs escaneados

```bash
# Usa el método OCR (requiere ocrmypdf instalado)
pdf-compress -m ocr ~/Documents/escaneados/documento.pdf
```

**Resultado típico:**
- 🔥 Reduce 50-80% el tamaño
- 📄 Optimización especial para imágenes escaneadas
- ✨ Excelente calidad

## 🎯 Métodos Disponibles

| Comando | Reducción | Calidad | Uso |
|---------|-----------|---------|-----|
| `-m screen` | 80-95% | OK | Web, email, máxima compresión |
| `-m ebook` | 60-85% | ⭐ Buena | **RECOMENDADO** - Lectura digital |
| `-m printer` | 40-70% | Muy buena | Para imprimir después |
| `-m prepress` | 20-50% | Excelente | Impresión profesional |
| `-m ocr` | 50-80% | ⭐ Excelente | **Para escaneados** |

## 💡 Tips Pro

### Comprimir solo si vale la pena

```bash
# Solo comprime si reduce al menos 20%
pdf-compress -m ebook -r -t 20 ~/Documents/biblioteca
```

### Ver qué método funciona mejor

```bash
# Prueba todos los métodos en un archivo
./test_compression.sh ~/Documents/libro.pdf
```

### Modo verbose (ver detalles)

```bash
pdf-compress -v -m ebook ~/Documents/libro.pdf
```

### Forzar sobrescritura

```bash
pdf-compress -f -m ebook ~/Documents/libro.pdf
```

## 🔧 Solución de Problemas Rápidos

### "Error: Faltan las siguientes dependencias: ghostscript"

```bash
sudo pacman -S ghostscript
```

### "Permission denied"

```bash
chmod +x /usr/local/bin/pdf-compress
```

### El PDF comprimido es más grande (v2.0 ya NO debería pasar)

- El script automáticamente descarta el archivo si es más grande
- Prueba con `-m screen` para máxima compresión
- El PDF original puede estar ya muy optimizado

## 📍 Ubicación de Archivos

Después de la instalación recomendada (opción 1):

```
📁 /home/achalmaedison/Documents/scripts/scripts_for_linux/script_compress_pdf/
├── compress_pdf.sh      # Script principal
├── README.md            # Documentación completa
├── LICENSE              # Licencia MIT
└── test_compression.sh  # Script de prueba

📁 /usr/local/bin/
└── pdf-compress         # Wrapper para ejecutar desde cualquier lugar
```

## 🎓 Ejemplos del Día a Día

### Comprimir tu carpeta de documentos académicos

```bash
pdf-compress -m ebook -r ~/Documents/Universidad
```

### Preparar PDFs para subir a Google Drive

```bash
pdf-compress -m screen -r ~/Documents/ParaSubir
```

### Optimizar toda tu biblioteca antes de respaldar

```bash
pdf-compress -m ebook -r -t 15 ~/Documents/biblioteca
```

## 📞 Ayuda Rápida

```bash
pdf-compress --help        # Ver ayuda completa
pdf-compress -v archivo    # Modo verbose (detallado)
```

## ✅ Verificación de Instalación

```bash
# Verificar que el wrapper funciona
which pdf-compress

# Debería mostrar: /usr/local/bin/pdf-compress

# Verificar que el script principal existe
ls ~/Documents/scripts/scripts_for_linux/script_compress_pdf/compress_pdf.sh

# Probar con un archivo
pdf-compress ~/Documents/cualquier_pdf.pdf
```

## 🌟 Recuerda

- Los archivos comprimidos se guardan **junto al original** con sufijo `_compressed`
- El script **nunca borra el original**
- Si la compresión falla o aumenta el tamaño, el archivo comprimido se descarta automáticamente
- Usa `-r` para procesar subdirectorios recursivamente
- Usa `-m ebook` para el mejor balance calidad/tamaño

## 📖 Más Información

Para documentación completa, ejemplos avanzados y troubleshooting detallado:

```bash
less ~/Documents/scripts/scripts_for_linux/script_compress_pdf/README.md
```

O visita el README.md completo en el repositorio.

---

**¡Eso es todo!** Con estos comandos básicos ya puedes comprimir tus PDFs efectivamente. 🎉

**Autor:** Edison Achalma  
**Versión:** 2.0  
**Fecha:** Enero 2026
