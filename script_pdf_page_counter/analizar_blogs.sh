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