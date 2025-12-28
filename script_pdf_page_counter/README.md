# 📘 Ejemplos de Uso Detallados - PDF Page Counter

Ejemplos prácticos y casos de uso específicos para el análisis de tus blogs académicos.

**Autor:** Edison Achalma  
**Universidad:** Universidad Nacional de San Cristóbal de Huamanga

---

## 🎯 Ejemplos Básicos

### 1. Ver todos los blogs disponibles

```bash
python3 pdf_page_counter.py --listar
```

**Cuándo usar:** Antes de ejecutar cualquier análisis, para verificar qué blogs están configurados y disponibles.

---

### 2. Analizar todos los blogs (por defecto)

```bash
python3 pdf_page_counter.py
```

**Resultado:**
- Procesa todos los blogs en `BLOGS_ESTANDAR`
- Procesa los blogs en `BLOGS_WEBSITE_ACHALMA`
- Solo busca archivos `index.pdf`
- Genera archivo con timestamp automático

---

### 3. Analizar un solo blog

```bash
python3 pdf_page_counter.py -b actus-mercator
```

**Cuándo usar:** 
- Verificar un blog específico
- Después de actualizar contenido de un blog
- Análisis rápido

---

### 4. Analizar múltiples blogs específicos

```bash
python3 pdf_page_counter.py -b actus-mercator aequilibria axiomata
```

**Cuándo usar:**
- Análisis por categoría (ej: solo blogs de economía)
- Reportes parciales
- Comparación entre blogs relacionados

---

### 5. Buscar todos los PDFs (no solo index.pdf)

```bash
python3 pdf_page_counter.py --todos
```

**Cuándo usar:**
- Análisis completo de recursos
- Incluir documentos adicionales (no solo index.pdf)
- Auditoría completa de contenido

---

## 📊 Análisis por Categoría

### Blogs de Economía

```bash
python3 pdf_page_counter.py \
  -b actus-mercator aequilibria dialectica-y-mercado pecunia-fluxus \
  -o economia_$(date +%Y%m%d).xlsx
```

**Blogs incluidos:**
- `actus-mercator`: Comercio y negocios
- `aequilibria`: Equilibrio económico
- `dialectica-y-mercado`: Dialéctica económica
- `pecunia-fluxus`: Flujos monetarios

---

### Blogs de Metodología y APA

```bash
python3 pdf_page_counter.py \
  -b methodica \
  -o metodologia_$(date +%Y%m%d).xlsx
```

**Notas:**
- No incluye `apa` porque no es un blog (carpeta de recursos)
- No incluye `taller unsch...` porque no es blog estándar

---

### Blogs de Matemáticas y Análisis

```bash
python3 pdf_page_counter.py \
  -b axiomata epsilon-y-beta numerus-scriptum optimums \
  -o matematicas_$(date +%Y%m%d).xlsx
```

**Blogs incluidos:**
- `axiomata`: Axiomas matemáticos
- `epsilon-y-beta`: Análisis epsilon-delta
- `numerus-scriptum`: Números y escritura matemática
- `optimums`: Optimización

---

### Website Achalma (Blog personal + Teaching)

```bash
python3 pdf_page_counter.py \
  -b blog teching \
  -o website_achalma_$(date +%Y%m%d).xlsx
```

**Blogs incluidos:**
- `blog`: Blog personal en website-achalma
- `teching`: Contenido educativo (economía preuniversitaria, etc.)

---

## 🤖 Scripts de Automatización

### Script 1: Análisis Completo Mensual (Linux/Mac)

Crea `analisis_mensual.sh`:

```bash
#!/bin/bash

# ============================================================================
# Script de Análisis Mensual de Blogs
# Autor: Edison Achalma
# ============================================================================

# Configuración
SCRIPT_DIR="/home/achalmaedison/Documents/scripts/scripts_for_linux/script_pdf_page_counter"
FECHA=$(date +%Y%m%d)
MES=$(date +%Y_%m)

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$SCRIPT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   ANÁLISIS MENSUAL DE BLOGS - $(date '+%B %Y')${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Activar entorno conda
echo "🐍 Activando entorno conda..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate pdf_counter

# 1. Análisis general (solo index.pdf)
echo ""
echo "📊 1/4 - Análisis general..."
python3 pdf_page_counter.py -o "reporte_general_${MES}.xlsx"

# 2. Análisis completo (todos los PDFs)
echo ""
echo "📊 2/4 - Análisis completo..."
python3 pdf_page_counter.py --todos -o "reporte_completo_${MES}.xlsx"

# 3. Análisis por categoría: Economía
echo ""
echo "📊 3/4 - Análisis de blogs de economía..."
python3 pdf_page_counter.py \
  -b actus-mercator aequilibria dialectica-y-mercado pecunia-fluxus \
  -o "reporte_economia_${MES}.xlsx"

# 4. Análisis de website-achalma
echo ""
echo "📊 4/4 - Análisis de website-achalma..."
python3 pdf_page_counter.py \
  -b blog teching \
  -o "reporte_website_${MES}.xlsx"

# Resumen
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ ANÁLISIS COMPLETADO${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📁 Archivos generados en: $SCRIPT_DIR/excel_databases/"
echo ""
echo "   • reporte_general_${MES}.xlsx"
echo "   • reporte_completo_${MES}.xlsx"
echo "   • reporte_economia_${MES}.xlsx"
echo "   • reporte_website_${MES}.xlsx"
echo ""

# Desactivar entorno
conda deactivate
```

**Uso:**
```bash
chmod +x analisis_mensual.sh
./analisis_mensual.sh
```

---

### Script 2: Análisis Rápido por Blog (Linux/Mac)

Crea `analizar_blog.sh`:

```bash
#!/bin/bash

# Script para analizar un blog específico rápidamente
# Uso: ./analizar_blog.sh nombre_del_blog

if [ $# -eq 0 ]; then
    echo "❌ Error: Debes especificar el nombre del blog"
    echo "Uso: $0 nombre_del_blog"
    echo ""
    echo "Ejemplos:"
    echo "  $0 actus-mercator"
    echo "  $0 blog"
    exit 1
fi

BLOG=$1
FECHA=$(date +%Y%m%d_%H%M%S)
SCRIPT_DIR="/home/achalmaedison/Documents/scripts/scripts_for_linux/script_pdf_page_counter"

cd "$SCRIPT_DIR"

# Activar entorno
source ~/miniconda3/etc/profile.d/conda.sh
conda activate pdf_counter

# Ejecutar análisis
python3 pdf_page_counter.py -b "$BLOG" -o "${BLOG}_${FECHA}.xlsx"

# Desactivar entorno
conda deactivate
```

**Uso:**
```bash
chmod +x analizar_blog.sh
./analizar_blog.sh actus-mercator
```

---

### Script 3: Automatización con Cron

```bash
# Editar crontab
crontab -e

# Añadir estas líneas:

# Análisis general el primer día de cada mes a las 8 AM
0 8 1 * * cd ~/Documents/scripts/scripts_for_linux/script_pdf_page_counter && ~/miniconda3/condabin/conda run -n pdf_counter python3 pdf_page_counter.py -o reporte_mensual_$(date +\%Y\%m).xlsx

# Análisis semanal todos los lunes a las 9 AM
0 9 * * 1 cd ~/Documents/scripts/scripts_for_linux/script_pdf_page_counter && ~/miniconda3/condabin/conda run -n pdf_counter python3 pdf_page_counter.py -o reporte_semanal_$(date +\%Y\%m\%d).xlsx
```

---

## 📈 Análisis Comparativo

### Comparar crecimiento mensual

```bash
#!/bin/bash

# Script para generar reportes mensuales y comparar

MESES=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12")
ANIO="2025"

for MES in "${MESES[@]}"; do
    echo "Generando reporte para $ANIO-$MES..."
    python3 pdf_page_counter.py -o "historico_${ANIO}_${MES}.xlsx"
    
    # Esperar para no sobrecargar
    sleep 2
done

echo "✅ Reportes históricos generados"
echo "📊 Puedes comparar los archivos en excel_databases/"
```

---

## 🔄 Workflows Recomendados

### Workflow 1: Análisis Post-Publicación

```bash
# Después de publicar contenido nuevo en un blog

# 1. Verificar el blog
python3 pdf_page_counter.py -b nombre-del-blog -o verificacion_$(date +%Y%m%d).xlsx

# 2. Revisar el Excel generado
# 3. Comparar con análisis anterior
```

---

### Workflow 2: Auditoría Trimestral

```bash
# Script: auditoria_trimestral.sh

#!/bin/bash

TRIMESTRE=$(date +%Y_Q$(($(date +%-m)/3+1)))

# Análisis completo con todos los PDFs
python3 pdf_page_counter.py --todos -o "auditoria_${TRIMESTRE}.xlsx"

# Análisis por categorías
python3 pdf_page_counter.py \
  -b actus-mercator aequilibria dialectica-y-mercado pecunia-fluxus \
  -o "auditoria_economia_${TRIMESTRE}.xlsx"

python3 pdf_page_counter.py \
  -b axiomata epsilon-y-beta numerus-scriptum optimums \
  -o "auditoria_matematicas_${TRIMESTRE}.xlsx"

echo "✅ Auditoría trimestral completada"
```

---

### Workflow 3: Preparación de Informe Académico

```bash
# Para preparar estadísticas para un informe académico

# 1. Análisis general
python3 pdf_page_counter.py -o informe_general.xlsx

# 2. Análisis por área (para incluir en el informe)
python3 pdf_page_counter.py \
  -b actus-mercator aequilibria \
  -o informe_economia.xlsx

python3 pdf_page_counter.py \
  -b blog teching \
  -o informe_docencia.xlsx

# 3. Los archivos Excel se pueden insertar directamente en el informe
```

---

## 💡 Tips Avanzados

### Tip 1: Crear Alias Personalizados

Añade a tu `~/.bashrc` o `~/.zshrc`:

```bash
# Aliases para PDF Counter
alias count-all='conda activate pdf_counter && cd ~/Documents/scripts/scripts_for_linux/script_pdf_page_counter && python3 pdf_page_counter.py'

alias count-blog='conda activate pdf_counter && cd ~/Documents/scripts/scripts_for_linux/script_pdf_page_counter && python3 pdf_page_counter.py -b'

alias count-list='conda activate pdf_counter && cd ~/Documents/scripts/scripts_for_linux/script_pdf_page_counter && python3 pdf_page_counter.py --listar'

alias count-economia='conda activate pdf_counter && cd ~/Documents/scripts/scripts_for_linux/script_pdf_page_counter && python3 pdf_page_counter.py -b actus-mercator aequilibria dialectica-y-mercado pecunia-fluxus'
```

**Uso después de recargar el shell:**
```bash
source ~/.bashrc  # o source ~/.zshrc

# Ahora puedes usar:
count-list
count-all
count-blog actus-mercator
count-economia
```

---

### Tip 2: Integración con Git

```bash
# Script para análisis antes de commit

#!/bin/bash
# pre-commit-stats.sh

# Generar estadísticas antes de hacer commit
python3 pdf_page_counter.py -o pre_commit_$(date +%Y%m%d).xlsx

# Añadir al commit
git add excel_databases/pre_commit_$(date +%Y%m%d).xlsx
git commit -m "docs: actualizar estadísticas de páginas"
```

---

### Tip 3: Enviar Reportes por Email

```bash
#!/bin/bash
# enviar_reporte.sh

FECHA=$(date +%Y%m%d)
REPORTE="excel_databases/reporte_${FECHA}.xlsx"

# Generar reporte
python3 pdf_page_counter.py -o "reporte_${FECHA}.xlsx"

# Enviar por email (requiere configurar mail/sendmail)
echo "Reporte de páginas PDF adjunto" | mail -s "Reporte Mensual - $FECHA" \
  -A "$REPORTE" \
  tu_email@unsch.edu.pe
```

---

## 🎓 Casos de Uso Académicos

### 1. Informe de Productividad Docente

```bash
# Generar estadísticas para informe anual

python3 pdf_page_counter.py \
  -b blog teching \
  -o productividad_docente_2025.xlsx
```

**Uso del reporte:**
- Número total de materiales educativos
- Páginas totales de contenido generado
- Comparación año a año

---

### 2. Análisis de Publicaciones Científicas

```bash
# Blogs de investigación

python3 pdf_page_counter.py \
  -b res-publica chaska \
  -o publicaciones_cientificas_2025.xlsx
```

---

### 3. Estadísticas para Memoria Institucional

```bash
# Reporte completo para memoria anual

python3 pdf_page_counter.py \
  --todos \
  -o memoria_institucional_2025.xlsx
```

---

## 🚀 Optimización y Performance

### Para grandes volúmenes de archivos

Si tienes muchos archivos, procesa por partes:

```bash
# Procesar blogs en lotes

# Lote 1: Economía
python3 pdf_page_counter.py \
  -b actus-mercator aequilibria \
  -o lote1_economia.xlsx

# Lote 2: Matemáticas  
python3 pdf_page_counter.py \
  -b axiomata numerus-scriptum \
  -o lote2_matematicas.xlsx

# etc...
```

---

## 📝 Notas Importantes

1. **Nombres de archivos:** El script genera nombres con timestamp automático si no especificas `-o`

2. **Directorio de salida:** Todos los Excel se guardan en `excel_databases/` en el directorio del script

3. **Blogs de website-achalma:** Usa los nombres `blog` y `teching`, no `website-achalma/_site/blog`

4. **Añadir nuevos blogs:** Edita `BLOGS_ESTANDAR` en el script principal

5. **Conda vs pip:** El script detecta automáticamente qué método usaste

---

## 🆘 Solución de Problemas Específicos

### El script no encuentra un blog específico

```bash
# 1. Verificar que el blog está en la lista
python3 pdf_page_counter.py --listar

# 2. Si no aparece, añádelo en el script:
# Editar pdf_page_counter.py línea ~43
```

### Error: "conda: command not found"

```bash
# Instalar Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# O usar pip
pip3 install PyPDF2 openpyxl --break-system-packages
```

---

**¿Más ejemplos? Escríbeme en cualquiera de mis plataformas:**

- GitHub: @achalmed
- LinkedIn: achalmaedison  
- Email: Ver perfil en Gravatar

---

**¡Feliz análisis de datos! 📊✨**