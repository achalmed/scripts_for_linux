---
tipo: readme
estado: activo
---
# script_firma_digital/ — foto de una firma a SVG y PNG limpios: canal rojo, histéresis y potrace
<!-- suite:inicio -->
**Suite `firma_digital`** · objetivo *personal* · estado *activo* · python · interfaz cli

Convierte la foto de una firma en SVG y PNG limpios (canal rojo, histéresis, potrace).

- Escribe en: archivos · simula por defecto: no
- Depende de: python3, opencv, potrace

Comandos:

```bash
main.py firma.jpg [-o <carpeta>] [-n <nombre>]
main.py firma.jpg --dry-run
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-03); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Convierte la foto de una firma manuscrita (tomada con el celular) en una firma digital limpia, en cinco pasos:

1. **Mapa de tinta** (`lib/preprocess.py`): toma el canal rojo (`CANAL_TINTA = 0`, el que mejor separa la tinta azul o
   violeta), reescala por `--escala` con Lanczos, divide por un fondo gaussiano para aplanar la iluminación y estira
   el contraste por percentiles.
2. **Máscara** (`lib/mask.py`): umbral de Otsu multiplicado por `--factor-umbral`, histéresis con `--hist-baja`,
   quita componentes menores que `--area-motas`, endereza con segmentos de Hough casi horizontales y suaviza.
3. **Vector** (`lib/vectorize.py`): traza la máscara con potrace (el módulo `potrace` del paquete `potracer`) y
   compara el vector rasterizado con la máscara; si el IoU baja de 0,90 (`IOU_MINIMO`) aborta con código 1.
4. **Recorte**: encuadra el contenido con un margen del 2 % y lo centra.
5. **Exportación** (`lib/export.py`): SVG con el ancho físico de `--ancho-mm` y dos PNG a 600 ppp con la tinta en
   negro, uno con fondo transparente y otro con fondo blanco.

La limpieza es geométrica sobre los trazos reales: no redibuja ni completa partes de la firma.

- **Qué escribe**, en `--output-dir` (por defecto, la carpeta de la foto) y con el nombre base de `-n` (por defecto,
  `<foto>_digital`): `<base>.svg`, `<base>.png` (transparente) y `<base>_fondo_blanco.png`. Con `--solo-mascara`, solo
  los dos PNG, hechos desde la máscara. Con `--qa-dir DIR`: `<base>_qa_tinta.png`, `<base>_qa_mascara.png` y, si se
  vectorizó, `<base>_qa_vector.png`. Sobrescribe sin preguntar; crea las carpetas que falten. No escribe log en disco.
- **Simulación:** no simula por defecto; `-d`/`--dry-run` construye la máscara (para informar del ángulo y la
  cobertura), no vectoriza ni escribe. Sin las bibliotecas instaladas, la simulación solo lista los archivos que
  generaría.

## Uso

```bash
python3 main.py firma.jpg                                    # SVG + dos PNG junto a la foto
python3 main.py firma.jpg -o ~/firmas -n firma_digital
python3 main.py firma.jpg --solo-mascara --qa-dir ./qa       # rápido: revisar la máscara antes de vectorizar
python3 main.py firma_ruidosa.jpg --area-motas 2000 --qa-dir ./qa
python3 main.py firma_clara.jpg --factor-umbral 0.85         # tinta tenue
python3 main.py firma.jpg --dry-run
```

Para una firma nueva conviene iterar con `--solo-mascara --qa-dir`: subir `--area-motas` si quedan motas, bajar
`--factor-umbral` (o `--hist-baja`) si se pierden trazos tenues, y vectorizar cuando la máscara esté bien.

| opción | qué hace | por defecto (`config.py`) |
|---|---|---|
| `FOTO` | foto de la firma (JPG, PNG…) | obligatoria |
| `-o`, `--output-dir DIR` | carpeta de salida | la de la foto |
| `-n`, `--nombre NOMBRE` | nombre base sin extensión | `<foto>_digital` (`SUFIJO_NOMBRE`) |
| `--solo-mascara` | no vectoriza: solo los dos PNG desde la máscara | no |
| `--qa-dir DIR` | guarda imágenes de control | — |
| `--escala N` | factor de reescalado de trabajo (entero ≥ 1) | `4` (`ESCALA_TRABAJO`) |
| `--factor-umbral F` | multiplicador del umbral de Otsu, en (0, 1] | `0.9` (`FACTOR_UMBRAL_OTSU`) |
| `--hist-baja F` | umbral bajo de la histéresis como fracción, en (0, 1] | `0.65` (`FRACCION_HISTERESIS_BAJA`) |
| `--area-motas N` | área mínima en px² a escala de trabajo para conservar un componente | `240` (`AREA_MINIMA_MOTAS`) |
| `--ancho-mm MM` | ancho físico declarado en el SVG | `68.0` (`ANCHO_FISICO_MM`) |
| `--sin-enderezar` | no corrige la inclinación | corrige |
| `-d`, `--dry-run` | simula | no |
| `-v`, `--verbose` | nivel DEBUG | no |
| `--version` | imprime la versión | — |
| `-h`, `--help` | ayuda | — |

Códigos de salida: 0 hecho · 1 el vector no reproduce la máscara · 2 falta la foto, es una carpeta o una opción es
inválida · 3 foto inexistente · 4 sin permisos · 5 falta una biblioteca · 130 interrumpido.

Requisitos: Python 3 con `numpy`, `scipy`, `scikit-image`, `Pillow` y `potracer` (`requirements.txt`). Ningún binario
del sistema: ni OpenCV ni el `potrace` nativo.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | orquesta: argumentos → validación → mapa de tinta → máscara → vector con control de IoU → recorte y exportación; importa las bibliotecas pesadas tras validar |
| `config.py` | dependencias, sufijos de nombre, canal de tinta, escala, umbrales, Hough, potrace, IoU mínimo, margen, ancho y ppp |
| `requirements.txt` | paquetes de Python |
| `lib/__init__.py` | marca `lib/` como paquete |
| `lib/cli.py` | parser `argparse` con validadores de tipo y ejemplos |
| `lib/logger.py` | envoltorio del logger común (carpeta core del espacio de trabajo, py-common) |
| `lib/validator.py` | bibliotecas, foto de entrada, carpetas de salida y de control |
| `lib/preprocess.py` | canal, reescalado, aplanado de iluminación y contraste |
| `lib/mask.py` | Otsu e histéresis, motas, enderezado por Hough, suavizado |
| `lib/vectorize.py` | trazado potrace, curvas Bézier a rutas SVG, rasterizado e IoU |
| `lib/export.py` | encuadre, SVG, PNG con antialias e imágenes de control |

## Límite honesto

- **Vectorizar tarda minutos**: `potracer` es potrace en Python puro y trabaja a escala 4. Para iterar, `--solo-mascara`;
  bajar `--escala` a 3 o 2 acelera a costa de nitidez.
- **`--area-motas` es conservador a propósito** (240 px²): conserva puntos, tildes y subrayados a costa de alguna mota
  en fotos ruidosas; al subirlo, revisar con `--qa-dir` que no se pierdan marcas reales.
- **El enderezado deja un residual de 2–3° en firmas sin línea base recta**: solo corrige si encuentra al menos tres
  segmentos casi horizontales y la inclinación supera 0,5°. Si gira de más, `--sin-enderezar`.
- **Tinta azul o violeta**: el canal rojo es el que la separa; para otro color hay que cambiar `CANAL_TINTA` en
  `config.py` (no hay opción).
- **Una foto por ejecución**; no procesa carpetas.
- **«La vectorización no reproduce la máscara»** indica una máscara mala (foto tenue o ruidosa): revisarla con
  `--solo-mascara --qa-dir` y ajustar `--factor-umbral` o `--area-motas` antes de vectorizar de nuevo.
- Escrita en Python puro; probada en Linux, sin probar en macOS ni Windows.
