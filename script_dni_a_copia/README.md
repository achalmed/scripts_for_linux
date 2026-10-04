---
tipo: readme
estado: activo
---
# script_dni_a_copia/ — dos fotos de un DNI a una copia limpia a tamaño real, en DOCX o PDF
<!-- suite:inicio -->
**Suite `dni_a_copia`** · objetivo *personal* · estado *activo* · python · interfaz cli

Convierte dos fotografías de un DNI (anverso y reverso) en una copia limpia a tamaño real lista para imprimir.

- Escribe en: archivos · simula por defecto: no
- Depende de: python3, opencv

Comandos:

```bash
main.py --front anverso.jpg --back reverso.jpg [-o <carpeta>] [--to-pdf]
main.py --front anverso.jpg --back reverso.jpg --dry-run
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-03); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Toma dos imágenes de un DNI peruano (anverso y reverso) y arma una hoja A4 con las dos caras centradas a su tamaño
físico (ISO/IEC 7810 ID-1, 85,6 × 53,98 mm), como si se hubieran escaneado:

1. **Detecta la tarjeta** por color saturado y brillante (el turquesa impreso) y toma su envolvente convexa.
2. **Rectifica**: corrige la perspectiva con las cuatro esquinas (`--no-perspective` la quita y deja solo el
   enderezado por rotación) y orienta la cara (`--rotate`).
3. **Compone** sobre blanco conservando el borde del laminado, con una sombra tenue, y corrige el color (balance de
   blancos y realce suave).
4. **Restaura** (activa por defecto; `--no-enhance` la quita): suaviza la crominancia, reescala con Lanczos a los
   DPI pedidos, quita ruido con un filtro bilateral si está `scikit-image` y aplica un realce final.
5. **Exporta** a Word y, con `--to-pdf`, a PDF con LibreOffice sin compresión con pérdida ni reducción de resolución.

Con `--pre-cropped` la imagen se toma como la tarjeta ya recortada y plana (DNIe o escaneo): se omiten detección,
perspectiva, orientación y color, y solo se reescala, se realza (salvo `--no-enhance`), se redondean las esquinas y se añade la sombra.

- **Qué escribe**, en `--output-dir`: `<nombre>.docx`; con `--to-pdf`, `<nombre>.pdf`; con `--save-caras`,
  `<nombre>_anverso.png` y `<nombre>_reverso.png` (cada cara a tamaño real, con los DPI en el PNG). Sobrescribe sin
  preguntar. El perfil temporal de LibreOffice se borra al terminar. No escribe log en disco (`LOG_FILE = None`).
- **Qué no hace:** no lee ni altera los datos del documento; la restauración es solo visual y no inventa detalle.
- **Simulación:** no simula por defecto; `-d`/`--dry-run` procesa las imágenes pero no escribe ningún archivo.

## Uso

```bash
python3 main.py --front frente.jpg --back reverso.jpg -o ~/copias -n dni_copia --to-pdf
python3 main.py --front frente.jpg --back reverso.jpg -o ~/copias -n dni_copia --dry-run --verbose
python3 main.py --front dnie_a.png --back dnie_r.png -o ~/copias -n dnie_copia --pre-cropped
python3 main.py --front frente.jpg --back reverso.jpg -o ~/copias -n dni_bn --bn --save-caras
```

**Pasar siempre `--front`, `--back`, `-o` y `-n`.** Los valores por defecto de `config.py` apuntan a las imágenes,
la carpeta y el nombre de un DNI concreto (bajo `PERSONAL_DIR`), no a valores de ejemplo: sin esas opciones, la
herramienta lee esas imágenes o deja la salida en esa carpeta con ese nombre (ver `docs/decisiones.md` §Pendientes).

| opción | qué hace | por defecto (`config.py`) |
|---|---|---|
| `--front IMG` | imagen del anverso | la del DNI de `config.py` |
| `--back IMG` | imagen del reverso | la del DNI de `config.py` |
| `-o`, `--output-dir DIR` | carpeta de salida; la crea si no existe | la del DNI de `config.py` |
| `-n`, `--name NOMBRE` | nombre base de los archivos | el del DNI de `config.py` |
| `--dpi N` | resolución, entre 72 y 1200 | `300` (`DEFAULT_DPI`) |
| `--to-pdf` | exporta también a PDF | no |
| `--no-enhance` | desactiva la restauración | restauración activa |
| `--rotate MODO` | `auto`, `0`, `90`, `180` o `270` (grados antihorarios) | `auto` |
| `--no-perspective` | sin corrección de perspectiva | corrección activa |
| `--pre-cropped` | la imagen ya es la tarjeta recortada y plana | no |
| `--grayscale`, `--bn` | salida en escala de grises | no |
| `--save-caras` | guarda además el PNG de cada cara | no |
| `-d`, `--dry-run` | simula | no |
| `-v`, `--verbose` | nivel DEBUG | no |
| `--version` | imprime la versión | — |
| `-h`, `--help` | ayuda | — |

Al imprimir, escala al 100 % («tamaño real»), nunca «ajustar a la página». Códigos de salida: 0 hecho · 1 no se
detectó la tarjeta o falló LibreOffice · 2 DPI fuera de rango o salida que no es carpeta · 3 imagen inexistente ·
4 sin permisos · 5 falta LibreOffice con `--to-pdf` · 130 interrumpido.

Requisitos: Python 3 con `numpy`, `scipy`, `Pillow` y `python-docx` (`requirements.txt`); `scikit-image`
recomendado (sin él no hay filtro bilateral); LibreOffice (`libreoffice` o `soffice`) solo para `--to-pdf`.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | orquesta: argumentos → validación → cada cara (detectar o pre-recortada, componer) → PNG → Word → PDF |
| `config.py` | rutas y nombre por defecto, tamaño ID-1, DPI, umbrales de detección, laminado, sombra, restauración, página A4, filtro de exportación PDF |
| `requirements.txt` | paquetes de Python |
| `lib/__init__.py` | marca `lib/` como paquete |
| `lib/cli.py` | parser `argparse` y ejemplos |
| `lib/logger.py` | envoltorio del logger común (carpeta core del espacio de trabajo, py-common) |
| `lib/validator.py` | paquetes, LibreOffice, imágenes de entrada, carpeta de salida y rango de DPI |
| `lib/card_detect.py` | máscara de la tarjeta, inclinación, esquinas y homografía, orientación y recorte |
| `lib/card_render.py` | balance de blancos, borde del laminado, composición sobre blanco, sombra, acabado de la pre-recortada |
| `lib/enhance.py` | suavizado de crominancia, reescalado, filtro bilateral y realce |
| `lib/docx_builder.py` | Word A4 con las dos caras centradas y exportación a PDF con LibreOffice |

## Límite honesto

- **Los valores por defecto son de un DNI real**: el número y las rutas de una persona viven en `config.py` y en la
  ayuda de `lib/cli.py`, en un repositorio público. Retirarlos es decisión del autor (ver `docs/decisiones.md`
  §Pendientes); mientras tanto, la salida y el nombre se pasan siempre por opción.
- **La ayuda dice «600 dpi por defecto» y es 300** (`DEFAULT_DPI`): manda `config.py` (ver `docs/decisiones.md`
  §Pendientes).
- **La detección exige color saturado y brillante y las cuatro esquinas visibles**: el DNIe no es turquesa y va
  siempre con `--pre-cropped`; una esquina tapada o deformada, con `--no-perspective`; un fondo muy oscuro o una
  foto con poca tarjeta acaban en «no se detectó una tarjeta» (código 1).
- **`--rotate auto` solo distingue vertical de horizontal** (si es más alta que ancha gira 90°); al revés o en
  sentido horario se fuerza con `--rotate 180` o `--rotate 270`. Con `--pre-cropped`, `--rotate` y `--no-perspective`
  no tienen efecto.
- **Sin un paquete obligatorio no sale el mensaje de dependencias**: `main.py` importa Pillow, numpy y scipy antes de
  validar, así que falta un paquete y Python termina con su propia traza.
- **`--dry-run` no es rápido**: procesa las dos imágenes completas y solo se ahorra la escritura.
- **El centrado vertical se hace con márgenes simétricos**: LibreOffice ignora `w:vAlign`; Word sí lo respeta.
- **Las imágenes de un documento de identidad no deben salir de la máquina**; la herramienta no las envía a ningún
  sitio, pero tampoco cifra ni borra la salida.
- Probada en Linux; en macOS o Windows el procesado debería funcionar, la exportación a PDF depende de encontrar
  LibreOffice en el `PATH`.
