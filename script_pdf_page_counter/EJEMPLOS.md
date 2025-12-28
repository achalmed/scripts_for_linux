# 📘 Ejemplos de Uso - Edison Achalma

Casos de uso específicos para el análisis de tus blogs y publicaciones.

## 🎯 Casos Comunes

### 1. Analizar solo el blog website-achalma

```bash
# Solo archivos index.pdf
python3 pdf_page_counter.py website-achalma/_site

# Todos los PDFs
python3 pdf_page_counter.py website-achalma/_site --todos -o website_achalma_completo.xlsx
```

### 2. Analizar todos tus blogs a la vez

```bash
python3 pdf_page_counter.py \
  actus-mercator/_site \
  aequilibria/_site \
  axiomata/_site \
  dialectica-y-mercado/_site \
  epsilon-y-beta/_site \
  methodica/_site \
  notas/_site \
  numerus-scriptum/_site \
  optimums/_site \
  pecunia-fluxus/_site \
  res-publica/_site \
  website-achalma/_site \
  -o analisis_todos_blogs.xlsx
```

### 3. Analizar solo blogs económicos

```bash
python3 pdf_page_counter.py \
  actus-mercator/_site \
  aequilibria/_site \
  dialectica-y-mercado/_site \
  pecunia-fluxus/_site \
  -o blogs_economia.xlsx
```

### 4. Script de análisis completo (Linux/Mac)

Crea un archivo `analizar_blogs.sh`:

```bash
#!/bin/bash

echo "Analizando todos los blogs..."
echo "=============================="

cd /ruta/a/publicaciones

python3 pdf_page_counter.py \
  actus-mercator/_site \
  aequilibria/_site \
  apa/_site \
  axiomata/_site \
  borradores/_site \
  chaska/_site \
  "dialectica-y-mercado/_site" \
  "epsilon-y-beta/_site" \
  methodica/_site \
  notas/_site \
  "numerus-scriptum/_site" \
  optimums/_site \
  "pecunia-fluxus/_site" \
  "practicas preprofesionales/_site" \
  "propuesta bicentenario/_site" \
  "res-publica/_site" \
  "taller unsch como elaborar tesis de pregrado/_site" \
  website-achalma/_site \
  -o "reporte_completo_$(date +%Y%m%d).xlsx"

echo ""
echo "✅ Análisis completado!"
echo "📊 Reporte generado: reporte_completo_$(date +%Y%m%d).xlsx"
```

Dar permisos y ejecutar:
```bash
chmod +x analizar_blogs.sh
./analizar_blogs.sh
```

### 5. Script de análisis completo (Windows)

Crea un archivo `analizar_blogs.bat`:

```batch
@echo off
echo Analizando todos los blogs...
echo ==============================

cd C:\ruta\a\publicaciones

python pdf_page_counter.py ^
  actus-mercator/_site ^
  aequilibria/_site ^
  apa/_site ^
  axiomata/_site ^
  borradores/_site ^
  chaska/_site ^
  dialectica-y-mercado/_site ^
  epsilon-y-beta/_site ^
  methodica/_site ^
  notas/_site ^
  numerus-scriptum/_site ^
  optimums/_site ^
  pecunia-fluxus/_site ^
  "practicas preprofesionales/_site" ^
  "propuesta bicentenario/_site" ^
  res-publica/_site ^
  "taller unsch como elaborar tesis de pregrado/_site" ^
  website-achalma/_site ^
  -o reporte_completo.xlsx

echo.
echo ✅ Análisis completado!
echo 📊 Reporte generado: reporte_completo.xlsx
pause
```

## 📊 Análisis por Categorías

### Blogs de Economía
```bash
python3 pdf_page_counter.py \
  actus-mercator/_site \
  aequilibria/_site \
  dialectica-y-mercado/_site \
  pecunia-fluxus/_site \
  -o economia.xlsx
```

### Blogs de Metodología
```bash
python3 pdf_page_counter.py \
  apa/_site \
  methodica/_site \
  "taller unsch como elaborar tesis de pregrado/_site" \
  -o metodologia.xlsx
```

### Blogs de Matemáticas y Análisis
```bash
python3 pdf_page_counter.py \
  axiomata/_site \
  epsilon-y-beta/_site \
  numerus-scriptum/_site \
  optimums/_site \
  -o matematicas.xlsx
```

## 🔄 Automatización con Cron (Linux/Mac)

Para ejecutar análisis automático cada semana:

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar cada lunes a las 9 AM
0 9 * * 1 /ruta/a/analizar_blogs.sh
```

## 📅 Análisis Comparativo

Genera reportes con fecha para comparar evolución:

```bash
# Enero
python3 pdf_page_counter.py website-achalma/_site -o stats_2025_01.xlsx

# Febrero
python3 pdf_page_counter.py website-achalma/_site -o stats_2025_02.xlsx

# Marzo
python3 pdf_page_counter.py website-achalma/_site -o stats_2025_03.xlsx
```

## 🎨 Personalización

### Modificar el script para agregar más columnas

Puedes modificar el script para incluir:
- Fecha de creación del archivo
- Tamaño del archivo
- Fecha de última modificación

### Crear reportes por blog automáticamente

```bash
#!/bin/bash

BLOGS=(
    "actus-mercator"
    "aequilibria"
    "website-achalma"
)

for blog in "${BLOGS[@]}"; do
    echo "Procesando $blog..."
    python3 pdf_page_counter.py "${blog}/_site" -o "${blog}_reporte.xlsx"
done

echo "✅ Todos los reportes generados!"
```

## 📈 Análisis de Productividad

### Contar publicaciones por mes
Puedes usar los reportes generados para:
1. Ver cuántos documentos produces por mes
2. Calcular páginas totales por período
3. Identificar blogs más activos
4. Planificar contenido futuro

### Estadísticas rápidas
```bash
# Ver solo el total
python3 pdf_page_counter.py website-achalma/_site | grep "Total de páginas"

# Contar archivos
python3 pdf_page_counter.py website-achalma/_site | grep "Total de archivos"
```

## 🚀 Tips Avanzados

### 1. Usar con find para mayor control
```bash
find /ruta/a/publicaciones -name "index.pdf" -type f | wc -l
```

### 2. Combinar con otros comandos
```bash
# Generar reporte y enviarlo por email
python3 pdf_page_counter.py _site && \
  mail -s "Reporte PDF" tu@email.com < conteo_paginas_pdf.xlsx
```

### 3. Crear alias útiles
```bash
# En ~/.bashrc o ~/.zshrc
alias count-pdfs='python3 ~/scripts/pdf_page_counter.py'
alias count-all='python3 ~/scripts/pdf_page_counter.py --todos'

# Uso:
# count-pdfs _site
# count-all _site -o reporte.xlsx
```

## ⚡ Optimización

Para grandes cantidades de archivos:
- Procesa un blog a la vez
- Usa SSD para mayor velocidad
- Cierra otras aplicaciones pesadas
- Considera usar modo batch nocturno

## 📝 Notas para tu Flujo de Trabajo

Como economista e informático trabajando en la Universidad Nacional de San Cristóbal de Huamanga:

1. **Respaldos**: Guarda los reportes Excel como histórico
2. **Organización**: Usa nombres con fecha: `reporte_YYYYMMDD.xlsx`
3. **Documentación**: Anota cambios importantes en cada período
4. **Automatización**: Configura análisis semanal o mensual
5. **Análisis**: Usa los datos para planificar publicaciones futuras

---

¿Necesitas más ejemplos? Contacta con achalmaedison en cualquier plataforma.
