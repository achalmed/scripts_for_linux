# 📊 Contador de Páginas PDF

Script en Python para contar recursivamente el número de páginas de archivos PDF en directorios y generar un reporte en Excel.

## 🎯 Características

- ✅ Búsqueda recursiva de archivos PDF
- ✅ Dos modos de operación:
  - **Modo Index**: Solo busca archivos llamados `index.pdf`
  - **Modo Todos**: Busca todos los archivos `.pdf`
- ✅ Genera reporte en formato Excel (.xlsx)
- ✅ Muestra progreso en tiempo real
- ✅ Cálculo automático de totales
- ✅ Formato profesional con estilos
- ✅ Manejo de errores robusto

## 📋 Requisitos

- Python 3.6 o superior
- Bibliotecas necesarias:
  - `PyPDF2`: Para leer archivos PDF
  - `openpyxl`: Para crear archivos Excel

## 🔧 Instalación

### 1. Instalar dependencias

```bash
conda create -n pdf_page_counter python=3.11
conda activate pdf_page_counter
conda install PyPDF2 openpyxl
```

usar `pip` (no ideal, pero funciona)

```bash
pip install PyPDF2 openpyxl --break-system-packages
```

### 2. Descargar el script

Guarda el archivo `pdf_page_counter.py` en tu sistema.

### 3. Dar permisos de ejecución (Linux/Mac)

```bash
chmod +x pdf_page_counter.py
```

## 🚀 Uso

### Uso básico (solo archivos index.pdf)

```bash
python3 pdf_page_counter.py _site
```

Este comando:
- Busca recursivamente todos los archivos llamados `index.pdf` en la carpeta `_site`
- Cuenta las páginas de cada uno
- Genera un archivo `conteo_paginas_pdf.xlsx` con los resultados

### Buscar todos los archivos PDF

```bash
python3 pdf_page_counter.py _site --todos
```

O usando la forma corta:

```bash
python3 pdf_page_counter.py _site -t
```

### Especificar archivo de salida personalizado

```bash
python3 pdf_page_counter.py _site -o mi_reporte.xlsx
```

### Buscar en múltiples directorios

```bash
python3 pdf_page_counter.py _site blog publicaciones
```

### Combinar opciones

```bash
python3 pdf_page_counter.py _site blog --todos -o reporte_completo.xlsx
```

## 📊 Formato del Reporte Excel

El archivo Excel generado contiene:

| Columna | Descripción |
|---------|-------------|
| **Ruta del Archivo** | Ruta relativa del archivo PDF desde el directorio base |
| **Número de Páginas** | Cantidad de páginas del documento |

Características adicionales:
- Encabezados con formato destacado (fondo azul, texto blanco)
- Fila de **TOTAL** al final con la suma automática
- Ancho de columnas ajustado automáticamente
- Alineación centrada para números

### Ejemplo de salida:

```
Ruta del Archivo                                          | Número de Páginas
---------------------------------------------------------|------------------
posts/2021-10-01-gestion-publica/index.pdf              | 12
posts/2021-10-01-reformas-modernizacion/index.pdf       | 8
posts/2023-05-11-cualidades-servidores/index.pdf        | 15
---------------------------------------------------------|------------------
TOTAL                                                     | 35
```

## 🖥️ Salida en Terminal

Durante la ejecución, verás algo como:

```
📊 Contador de Páginas PDF
======================================================================
🔍 Buscando PDFs en: _site
📋 Modo: Solo index.pdf
======================================================================
✓ posts/2021-10-01-gestion-publica/index.pdf: 12 página(s)
✓ posts/2021-10-01-reformas-modernizacion/index.pdf: 8 página(s)
✓ posts/2023-05-11-cualidades-servidores/index.pdf: 15 página(s)

======================================================================
📄 Total de archivos encontrados: 3
📑 Total de páginas: 35

✅ Archivo Excel creado: conteo_paginas_pdf.xlsx

✨ Proceso completado exitosamente!
```

## 🔍 Opciones de Línea de Comandos

```
usage: pdf_page_counter.py [-h] [-t] [-o OUTPUT] directorios [directorios ...]

Contador de páginas PDF recursivo

positional arguments:
  directorios           Directorio(s) donde buscar archivos PDF

optional arguments:
  -h, --help            Muestra este mensaje de ayuda
  -t, --todos           Buscar todos los archivos PDF (no solo index.pdf)
  -o OUTPUT, --output OUTPUT
                        Nombre del archivo Excel de salida 
                        (default: conteo_paginas_pdf.xlsx)
```

## 📁 Estructura de Directorios Soportada

El script funciona con cualquier estructura de directorios. Ejemplos:

### Estructura simple:
```
_site/
├── blog/
│   └── post1/
│       └── index.pdf
└── publicaciones/
    └── paper1/
        └── index.pdf
```

### Estructura compleja:
```
publicaciones/
├── actus-mercator/
│   └── _site/
│       └── posts/
│           └── 2021-10-01-gestion-publica/
│               └── index.pdf
├── aequilibria/
│   └── _site/
│       └── posts/
└── dialectica-y-mercado/
    └── _site/
        └── posts/
```

## ⚠️ Manejo de Errores

El script maneja varios tipos de errores:

1. **Archivo PDF corrupto**: Se marca como 0 páginas y muestra advertencia
2. **Directorio no existe**: Muestra error y termina
3. **Dependencias no instaladas**: Muestra instrucciones de instalación
4. **Sin permisos de lectura**: Muestra advertencia y continúa

## 💡 Casos de Uso

### Caso 1: Contar páginas solo de archivos index.pdf en _site
```bash
python3 pdf_page_counter.py _site
```

### Caso 2: Contar páginas de todos los PDFs en múltiples blogs
```bash
python3 pdf_page_counter.py \
  actus-mercator/_site \
  aequilibria/_site \
  dialectica-y-mercado/_site \
  --todos \
  -o reporte_todos_blogs.xlsx
```

### Caso 3: Análisis de un solo blog
```bash
python3 pdf_page_counter.py res-publica/_site -o res_publica_stats.xlsx
```

## 🐛 Solución de Problemas

### Error: "No module named 'PyPDF2'"
```bash
pip install PyPDF2 openpyxl --break-system-packages
```

### Error: "Permission denied"
En Linux/Mac, da permisos de ejecución:
```bash
chmod +x pdf_page_counter.py
```

### El script no encuentra archivos
- Verifica que la ruta del directorio sea correcta
- Asegúrate de estar en el directorio correcto
- Usa rutas absolutas si es necesario: `/ruta/completa/a/_site`

### PDFs con 0 páginas
- Puede ser un archivo corrupto
- Verifica manualmente el PDF
- El script continuará con los demás archivos

## 📝 Notas Adicionales

- El script respeta la estructura de directorios y muestra rutas relativas
- Los archivos se procesan en el orden que encuentra el sistema
- El proceso puede tomar tiempo con muchos archivos grandes
- El archivo Excel se sobrescribe si ya existe (úsalo con `-o` para cambiar nombre)

## 🤝 Contribuciones

Mejoras sugeridas para futuras versiones:
- [ ] Agregar gráficos al Excel
- [ ] Soporte para otros formatos (DOCX, PPTX)
- [ ] Modo estadístico (promedio, mediana, etc.)
- [ ] Exportar a CSV o JSON
- [ ] Interfaz gráfica (GUI)

## 📄 Licencia

Este script es de uso libre para fines educativos y profesionales.

## ✍️ Autor

**Edison Achalma**
- Universidad Nacional de San Cristóbal de Huamanga
- Economista
---

💡 **Tip**: Agrega este script a tu PATH para usarlo desde cualquier directorio:
```bash
sudo cp pdf_page_counter.py /usr/local/bin/pdf-counter
sudo chmod +x /usr/local/bin/pdf-counter
# Ahora puedes usar: pdf-counter _site
```
