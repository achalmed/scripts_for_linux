# firma-digital

<!-- suite:inicio -->
**Suite `firma_digital`** · objetivo *personal* · estado *activo* · python · interfaz cli

Convierte la foto de una firma en SVG y PNG limpios (canal rojo, histéresis, potrace).

- Escribe en: archivos · simula por defecto: no
- Depende de: python3, opencv, potrace

Comandos:

```bash
main.py firma.jpg [--salida firma.svg]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-15); no se edita a mano.</sub>
<!-- suite:fin -->

> Convierte la foto de una firma manuscrita (tomada con el celular) en una firma
> digital limpia y profesional: **SVG vectorial** escalable sin pérdida y **PNG**
> de alta resolución con fondo transparente, listos para PDF, Word, LibreOffice,
> formularios electrónicos y procesos de firma.

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Requisitos](#️-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Arquitectura](#️-arquitectura)
- [Bugs Corregidos](#-bugs-corregidos)
- [Solución de Problemas](#-solución-de-problemas)
- [Cómo Contribuir](#-cómo-contribuir)
- [Notas y Advertencias](#️-notas-y-advertencias)

## 📖 Descripción

Una firma fotografiada con el celular llega con tres problemas: iluminación
despareja (sombras, viñeteo), bajo contraste tinta/papel y grano del papel. Esta
herramienta los corrige y entrega una firma digital autónoma:

1. **Limpia** la iluminación y el ruido del papel.
2. **Refuerza** los trazos tenues sin romperlos (umbral por histéresis).
3. **Endereza** la firma midiendo la inclinación real de sus trazos.
4. **Suaviza** y uniformiza el grosor.
5. **Vectoriza** con potrace a curvas Bézier (SVG escalable).
6. **Exporta** un SVG y dos PNG (transparente y con fondo blanco) a 600 ppp,
   recortados y centrados, con la tinta en negro puro.

Todo el proceso es limpieza geométrica sobre los trazos reales: **no redibuja ni
inventa** partes de la firma, para no alterar su identidad ni su validez visual.

El diseño del pipeline (canal rojo para tinta azul, aplanado de iluminación,
histéresis, enderezado por Hough, máscara invertida para potrace) proviene de la
digitalización real de varias firmas y está documentado paso a paso en el código.

## ⚙️ Requisitos

### Sistema Operativo

- Linux (probado en Ubuntu/Debian). Debería funcionar en macOS y Windows con
  Python 3.9+; sin dependencias de binarios del sistema.

### Dependencias

Todas son librerías de Python puro (ninguna necesita `apt`/compilación):

- `numpy` >= 1.20 — cálculo numérico del pipeline.
- `scipy` >= 1.7 — filtros gaussianos y componentes conexos.
- `scikit-image` >= 0.19 — Otsu, histéresis, morfología, Hough.
- `Pillow` >= 9.0 — lectura/escritura de imágenes y rotación.
- `potracer` >= 0.0.4 — vectorización potrace en Python puro (módulo `potrace`).

### Para Python

- Python >= 3.9
- pip

## 🚀 Instalación

### Paso 1: Situarse en la herramienta

```bash
cd scripts_for_linux/script_firma_digital
```

### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 3: Permiso de ejecución (opcional)

```bash
chmod +x main.py
```

## 💻 Uso

### Sintaxis

```bash
python3 main.py FOTO [OPCIONES]
```

Sin `--output-dir`, los archivos se escriben junto a la foto; el nombre base por
defecto es `<foto>_digital`.

### Opciones disponibles

| Flag                 | Descripción                                                        | Requerido |
| -------------------- | ------------------------------------------------------------------ | --------- |
| `FOTO`               | Foto de la firma a procesar (JPG, PNG...)                          | Sí        |
| `-o, --output-dir`   | Carpeta de salida (por defecto: la de la foto)                     | No        |
| `-n, --nombre`       | Nombre base de las salidas (por defecto: `<foto>_digital`)         | No        |
| `--solo-mascara`     | Solo el PNG ráster limpio, sin vectorizar (mucho más rápido)       | No        |
| `--qa-dir`           | Guarda imágenes de control (tinta, máscara, vector) para revisar   | No        |
| `--escala`           | Factor de reescalado de trabajo (por defecto: 4)                   | No        |
| `--factor-umbral`    | Multiplicador del umbral de Otsu, <1 conserva trazos tenues (0.9)  | No        |
| `--hist-baja`        | Umbral bajo de la histéresis, fracción del umbral (0.65)           | No        |
| `--area-motas`       | Área mínima (px²) para conservar un componente (240)               | No        |
| `--ancho-mm`         | Ancho físico del SVG en milímetros (68.0)                          | No        |
| `--sin-enderezar`    | No corregir la inclinación                                         | No        |
| `-d, --dry-run`      | Simular: mostrar el plan sin vectorizar ni escribir               | No        |
| `-v, --verbose`      | Salida detallada (DEBUG)                                            | No        |
| `--version`          | Mostrar versión                                                    | No        |
| `-h, --help`         | Mostrar ayuda                                                      | No        |

### Ejemplos de uso

```bash
# Conversión completa: SVG + PNG transparente + PNG fondo blanco
python3 main.py firma.jpg

# Elegir carpeta y nombre de salida
python3 main.py firma.jpg -o ~/firmas -n firma_juan_digital

# Foto con motas de fondo aisladas: subir el filtro de componentes pequeños
python3 main.py firma_ruidosa.jpg --area-motas 2000 --qa-dir ./qa

# Solo la versión ráster limpia (rápido, ~1 min, sin vectorizar)
python3 main.py firma.jpg --solo-mascara

# Firma muy tenue: bajar el umbral para no perder trazos claros
python3 main.py firma_clara.jpg --factor-umbral 0.85

# Simulación: ver el plan (ángulo detectado, cobertura, archivos)
python3 main.py firma.jpg --dry-run
```

### Flujo recomendado para una firma nueva

1. `--solo-mascara --qa-dir ./qa` para obtener rápido la máscara y revisarla.
2. Si hay motas de fondo, subir `--area-motas` (p. ej. 2000) y repetir.
3. Si se perdieron trazos tenues, bajar `--factor-umbral` (p. ej. 0.85).
4. Cuando la máscara esté bien, ejecutar sin `--solo-mascara` para el SVG.

## 🗂️ Arquitectura

```
script_firma_digital/
├── main.py              # Punto de entrada: orquesta las fases
├── config.py            # Configuración: TODO valor ajustable vive aquí
├── requirements.txt     # Dependencias de Python
├── README.md
└── lib/
    ├── __init__.py      # Marca lib/ como paquete
    ├── logger.py        # Logging centralizado a stderr (con color)
    ├── validator.py     # Validación de dependencias, entrada y directorios
    ├── cli.py           # Definición de argumentos (argparse)
    ├── preprocess.py    # Foto -> mapa de tinta (canal, iluminación, contraste)
    ├── mask.py          # Mapa de tinta -> máscara limpia (histéresis, enderezado)
    ├── vectorize.py     # Máscara -> curvas Bézier (potrace) + control IoU
    └── export.py        # Recorte, SVG y PNGs (transparente y fondo blanco)
```

### Descripción de módulos

| Archivo             | Responsabilidad                                                        |
| ------------------- | ---------------------------------------------------------------------- |
| `main.py`           | Orquestación de fases; importa el pipeline pesado de forma diferida    |
| `config.py`         | Constantes del pipeline, códigos de salida, catálogo de dependencias   |
| `lib/logger.py`     | Logger con niveles INFO/WARN/ERROR y color automático en terminal      |
| `lib/validator.py`  | Comprobaciones tempranas con mensajes accionables y códigos de salida  |
| `lib/cli.py`        | Parser de argumentos con validadores de tipo y ejemplos de uso         |
| `lib/preprocess.py` | Extrae el canal, reescala, aplana la iluminación y estira el contraste |
| `lib/mask.py`       | Binariza por histéresis, quita motas, endereza y suaviza               |
| `lib/vectorize.py`  | Traza con potrace, genera paths SVG y mide la fidelidad (IoU)          |
| `lib/export.py`     | Calcula el recorte, escribe el SVG y renderiza los PNG con antialias   |

## 🐛 Bugs Corregidos

Bugs reales encontrados en los scripts ad-hoc originales y corregidos en esta
reestructuración:

### Bug #1: Enderezado que se iba a ángulos extremos

- **Descripción**: la primera versión estimaba la inclinación minimizando la
  altura del recuadro del contenido. Con firmas de trazos verticales altos
  (bucles, astas) esa métrica premia rotaciones grandes y erróneas.
- **Impacto**: firmas giradas hasta el extremo del rango de búsqueda; resultado
  inutilizable.
- **Corrección**: se mide la inclinación con `probabilistic_hough_line` sobre los
  segmentos casi horizontales, promediando por longitud, y se prueban ambos
  signos de rotación quedándose con el menor residual (`lib/mask.py::_deskew`).

### Bug #2: Polaridad de potrace invertida

- **Descripción**: `potrace.Bitmap(mask)` interpreta los píxeles distintos de
  cero como **blanco**, así que trazar la máscara sin invertir vectorizaba el
  fondo, no la tinta.
- **Impacto**: IoU de 0.0008 (vector vacío/basura); SVG inservible.
- **Corrección**: se traza `np.logical_not(mask)` para que la tinta sea el primer
  plano (`lib/vectorize.py::trace`, comentado en el código).

### Bug #3: Fallo de `reshape` con dimensiones impares

- **Descripción**: el antialias reducía la imagen 2× con un `reshape` cuyas
  dimensiones se calculaban desde el `viewBox` y no desde el array realmente
  recortado; con lados impares lanzaba `ValueError: cannot reshape`.
- **Impacto**: caída del script (código 1) tras minutos de vectorización.
- **Corrección**: las dimensiones pares se derivan del propio array recortado
  antes del `reshape` (`lib/export.py::_alpha_from_raster`).

### Checklist de paridad funcional

Toda la funcionalidad de los scripts originales está preservada:

| Funcionalidad original (scripts ad-hoc)     | Dónde vive ahora            |
| ------------------------------------------- | --------------------------- |
| Extracción del canal rojo                   | `lib/preprocess.py`         |
| Reescalado 4× (Lanczos)                     | `lib/preprocess.py`         |
| Aplanado de iluminación (÷ fondo gaussiano) | `lib/preprocess.py`         |
| Estiramiento de percentiles                 | `lib/preprocess.py`         |
| Umbral Otsu + histéresis                    | `lib/mask.py`               |
| Eliminación de motas por área               | `lib/mask.py`               |
| Enderezado por segmentos Hough              | `lib/mask.py`               |
| Suavizado + cierre morfológico              | `lib/mask.py`               |
| Filtro final de componentes pequeños        | `lib/mask.py` (`--area-motas`) |
| Vectorización con potrace (máscara invert.) | `lib/vectorize.py`          |
| Bézier -> path SVG                          | `lib/vectorize.py`          |
| Control de calidad IoU                      | `lib/vectorize.py`          |
| Recorte + margen + centrado                 | `lib/export.py`             |
| PNG transparente desde el vector            | `lib/export.py`             |
| PNG con fondo blanco                        | `lib/export.py`             |
| SVG con `fill-rule="evenodd"`               | `lib/export.py`             |
| Metadatos a 600 ppp                         | `lib/export.py`             |

## 🔧 Solución de Problemas

### Error: "Falta la dependencia '...'"

```bash
pip install -r requirements.txt
```

### La vectorización tarda varios minutos

Es normal: `potracer` es potrace en Python puro y trabaja sobre la imagen a 4×.
Para iterar rápido usa `--solo-mascara` (no vectoriza). Bajar `--escala` a 3 o 2
también acelera, a costa de algo de nitidez.

### "La vectorización no reproduce la máscara (IoU ...)"

La máscara salió mal (foto muy tenue o con mucho ruido). Revísala con
`--solo-mascara --qa-dir ./qa` y ajusta `--factor-umbral` (bájalo para tinta
tenue) o `--area-motas` (súbelo si hay ruido de fondo) antes de vectorizar.

### La firma quedó con motas de fondo

Sube `--area-motas` (p. ej. `--area-motas 2000`). Revisa antes con `--qa-dir`
para no eliminar marcas reales pequeñas (puntos, tildes, subrayados).

### La firma perdió trazos tenues

Baja `--factor-umbral` (p. ej. `0.85`) y/o `--hist-baja` (p. ej. `0.55`).

### La firma quedó inclinada o se giró de más

Usa `--sin-enderezar` para desactivar la corrección, o revisa el ángulo detectado
con `--dry-run`. Firmas muy orgánicas dejan un residual de 2–3°, que es natural.

## 🤝 Cómo Contribuir

### Para agregar un nuevo paso al pipeline

1. Crea o extiende un módulo en `lib/` con responsabilidad única.
2. Expón sus valores ajustables en `config.py` (nunca los hardcodees en `lib/`).
3. Si necesita una opción de línea de comandos, agrégala en `lib/cli.py`.
4. Llámalo desde la fase correspondiente en `main.py` (solo orquestación).
5. Actualiza este README.

### Estándares de código

- Máximo ~30 líneas por función; una responsabilidad por función.
- Nombres descriptivos en inglés técnico; comentarios para el "por qué".
- Mensajes al usuario (CLI, logs) en español.
- Verifica sintaxis con `python3 -m py_compile` y, si está, `ruff check .`.

## ⚠️ Notas y Advertencias

- **`--area-motas` por defecto es conservador (240 px²)**: preserva marcas
  pequeñas deliberadas (puntos, tildes, subrayados), a costa de dejar alguna mota
  de fondo en fotos ruidosas. Es una decisión de diseño para no alterar la
  identidad de la firma; súbelo explícitamente cuando la foto lo requiera. Revisa
  siempre con `--qa-dir` antes de subirlo mucho.
- **El enderezado deja un residual en firmas orgánicas**: si la firma no tiene una
  línea base recta larga, el residual típico es de 2–3°. Es esperado; forzar más
  la haría ver artificial. Se corrige solo si hay ≥3 segmentos casi horizontales
  y la inclinación supera 0.5°.
- **Velocidad**: `potracer` (Python puro) tarda varios minutos en la escala 4×.
  Se eligió por no tener dependencias del sistema. Si tienes el binario nativo
  `potrace` instalado, una futura versión podría usarlo para acelerar mucho; hoy
  no se usa.
- **Canal de tinta**: por defecto se usa el canal rojo, óptimo para tinta
  azul/violeta (la más común en bolígrafos). Para tinta de otro color, ajusta
  `CANAL_TINTA` en `config.py`.
- **`--dry-run` no vectoriza**: para que la simulación sea rápida, construye la
  máscara (para reportar ángulo y cobertura) pero se detiene antes del trazado
  lento y de escribir archivos. Sin las dependencias instaladas, muestra solo un
  plan superficial con los nombres de archivo que generaría.
- **Supuestos asumidos** (esta reestructuración se hizo en modo directo, sin
  checkpoint de confirmación): lenguaje Python (el pipeline es científico), una
  sola foto por ejecución, ancho físico del SVG por defecto de 68 mm (tamaño
  natural de firma), y salidas junto a la foto salvo `--output-dir`.
```
