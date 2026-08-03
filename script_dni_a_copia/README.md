# dni-a-copia

> Arma una copia limpia, a tamaño real y **alta resolución**, del anverso y
> reverso de un DNI a partir de dos fotos de celular: endereza, recorta, blanquea
> el fondo (conservando el marco de laminado), **restaura la calidad** (quita
> artefactos JPEG, reduce ruido y reescala con nitidez), corrige el color y
> centra ambas caras en una hoja A4 → Word y, opcionalmente, PDF listo para
> imprimir.

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

Herramienta CLI que convierte dos fotografías (anverso y reverso) de un DNI
peruano —normalmente tomadas con celular, torcidas y con fondo— en una copia de
aspecto profesional, como si se hubiera escaneado en alta calidad:

1. **Segmenta** la tarjeta por saturación (el turquesa impreso destaca sobre el
   fondo gris) y calcula su **envolvente convexa** como silueta sólida.
2. **Rectifica la geometría**: corrige la **perspectiva** (keystone) con una
   homografía de 4 esquinas — los lados opuestos quedan iguales y proporción
   ID-1 exacta — y endereza cualquier inclinación residual. Desactivable con
   `--no-perspective` (cae a solo deskew rotacional).
3. Conserva el **marco de laminado** translúcido pero **blanquea su fondo**,
   compone la tarjeta sobre blanco con borde suavizado y añade una **sombra muy
   sutil** para separarla del papel sin que parezca un recorte.
4. Corrige el **color** (balance de blancos "white-patch" + realce suave) para
   un turquesa natural, sin dominante azul.
5. **Restaura la calidad** (etapa `--enhance`, activa por defecto): de-JPEG de
   crominancia antes de escalar, *upscaling* Lanczos a alta resolución (600 dpi
   por defecto), denoise bilateral que preserva bordes y realce final suave.
   Es restauración clásica: limpia artefactos y reescala **sin inventar detalle**
   ni alterar ningún dato del documento.
6. Lleva cada cara a su **tamaño físico exacto** (ISO/IEC 7810 ID-1,
   85.6 × 53.98 mm) y las **centra** —horizontal y verticalmente— en A4.
7. Exporta a **Word** y, con `--to-pdf`, también a **PDF**.

## ⚙️ Requisitos

### Sistema Operativo

- Linux (probado). macOS/Windows deberían funcionar salvo la exportación a PDF.

### Dependencias

- Python >= 3.9
- `numpy`, `scipy`, `Pillow`, `python-docx` (ver `requirements.txt`)
- `scikit-image` — recomendada; habilita el denoise bilateral de `--enhance`
  (sin ella, la restauración degrada a de-JPEG de crominancia + realce)
- **LibreOffice** — solo para `--to-pdf` (`libreoffice`/`soffice` en el PATH)

## 🚀 Instalación

```bash
cd script_dni_a_copia
pip install -r requirements.txt
# PDF opcional:
sudo apt install libreoffice
```

## 💻 Uso

### Sintaxis

```bash
python3 main.py [OPCIONES]
```

### Opciones disponibles

| Flag                | Descripción                                          | Requerido |
| ------------------- | ---------------------------------------------------- | --------- |
| `--front IMG`       | Imagen del anverso                                   | No¹       |
| `--back IMG`        | Imagen del reverso                                   | No¹       |
| `-o, --output-dir`  | Directorio de salida del Word/PDF                    | No        |
| `-n, --name NOMBRE` | Nombre base de los archivos de salida                | No        |
| `--dpi N`           | Resolución de las imágenes (72–1200; def. 300)       | No        |
| `--to-pdf`          | Además del Word, exporta a PDF (LibreOffice)         | No        |
| `--no-enhance`      | Desactiva la restauración (de-JPEG/denoise/realce)   | No        |
| `--rotate MODO`     | Orientación: `auto` (def.) o grados CCW 0/90/180/270 | No        |
| `--no-perspective`  | Desactiva la corrección de perspectiva (keystone)   | No        |
| `--pre-cropped`     | La imagen ya es el DNI recortado y plano (DNIe/scan)| No        |
| `--grayscale`,`--bn`| Salida en blanco y negro (escala de grises)         | No        |
| `--save-caras`      | Guarda cada cara recortada a tamaño real (PNG @ DPI) | No        |
| `-d, --dry-run`     | Simula: muestra qué se generaría sin escribir nada   | No        |
| `-v, --verbose`     | Salida detallada (nivel DEBUG)                       | No        |
| `--version`         | Muestra la versión y sale                            | No        |
| `-h, --help`        | Muestra la ayuda y sale                              | No        |

¹ Tienen valores por defecto (los archivos del DNI 28250954); ver Notas.

### Ejemplos de uso

```bash
# Reproducir la copia por defecto (DNI 28250954) -> Word
python3 main.py

# Cualquier DNI, con salida y nombre propios, y PDF
python3 main.py --front frente.jpg --back reverso.jpg \
    -o ~/copias -n dni_juan --to-pdf

# Archivos más ligeros (menor resolución) o acabado anterior (sin restaurar)
python3 main.py --dpi 450 --to-pdf
python3 main.py --no-enhance

# Simulación detallada (no escribe nada)
python3 main.py --dry-run --verbose
```

> **Al imprimir/exportar:** usa escala **100 % / "Tamaño real"** (no "Ajustar a
> página") para que el DNI salga exactamente a su tamaño físico.

## 🗂️ Arquitectura

Sigue el patrón modular del repo: `main` orquesta, `lib/` implementa, `config`
centraliza todo valor ajustable.

```
script_dni_a_copia/
├── main.py            # Orquestación: valida -> procesa caras -> Word -> (PDF)
├── config.py          # TODO valor editable + geometría derivada (build_geometry)
├── requirements.txt
├── README.md
└── lib/
    ├── logger.py      # Logging INFO/WARN/ERROR (consola + archivo opcional)
    ├── validator.py   # Valida args, entradas, dependencias, permisos
    ├── cli.py         # argparse (flags + ejemplos)
    ├── card_detect.py # Segmentación + deskew + recorte/orientación
    ├── card_render.py # White balance + acabado (laminado, composición, sombra)
    ├── enhance.py     # Restauración: de-JPEG + denoise + realce hi-res
    └── docx_builder.py# Construye el Word y exporta a PDF
```

### Descripción de módulos

| Archivo              | Responsabilidad                                              |
| -------------------- | ----------------------------------------------------------- |
| `main.py`            | Orquesta las fases; no contiene lógica de negocio           |
| `config.py`          | Tamaño ID-1, DPI, umbrales, laminado, sombra, restauración, layout, rutas |
| `lib/logger.py`      | Logging con colores en TTY y archivo opcional               |
| `lib/validator.py`   | Chequeos previos con códigos de salida                      |
| `lib/cli.py`         | Definición de todas las flags                               |
| `lib/card_detect.py` | `card_mask`, `estimate_tilt`, `deskew`, `extract_face`      |
| `lib/card_render.py` | `white_balance`, `render_face` y sus etapas                 |
| `lib/enhance.py`     | `reduce_artifacts` (de-JPEG), `restore_highres` (denoise+realce) |
| `lib/docx_builder.py`| `build_document`, `export_pdf`                              |

## 🐛 Bugs Corregidos

Migración desde el script monolítico `build_copia.py`:

### Bug #1: Parámetro que ocultaba una función global
- **Descripción**: en `finish(...)` el parámetro `card_mask` sombreaba la
  función global `card_mask()`.
- **Impacto**: bomba de tiempo de mantenimiento; cualquier llamada futura a la
  función dentro de esa scope habría usado el array.
- **Corrección**: parámetro renombrado a `card_region`.

### Bug #2: `card_mask` reventaba sin región saturada
- **Descripción**: con 0 componentes, `sizes.max()` lanzaba `ValueError`, y
  `ConvexHull` fallaba con menos de 3 puntos.
- **Impacto**: crash con traza críptica ante una imagen en blanco/ilegible.
- **Corrección**: se validan componentes y nº de puntos y se lanza un error de
  dominio claro ("no se detectó una tarjeta").

### Bug #3: Sin validación de entradas ni dependencias
- **Descripción**: archivos inexistentes o librerías faltantes provocaban trazas
  crudas; sin códigos de salida.
- **Corrección**: `lib/validator.py` con mensajes accionables y códigos 3/4/5.

### Bug #4: Todo se ejecutaba al importar (sin `main`)
- **Descripción**: el pipeline corría en el ámbito del módulo y una función se
  definía después del código que ya se había ejecutado.
- **Corrección**: orquestación en `main()` bajo `if __name__ == "__main__":`.

### Bug #5: Rutas absolutas hardcodeadas (scratch efímero)
- **Descripción**: rutas fijas, incluida una carpeta temporal de sesión que no
  existiría en ejecuciones futuras (crash al guardar).
- **Corrección**: rutas y tunables en `config.py`, sobreescribibles por flags;
  archivos temporales de LibreOffice con `tempfile` y limpieza garantizada.

### Bug #6: `print()` en vez de logging con niveles
- **Corrección**: `lib/logger.py` (INFO/WARN/ERROR, `--verbose`, salida a stderr).

## 🔧 Solución de Problemas

### `Faltan dependencias de Python`
```bash
pip install -r requirements.txt
```

### `Falta LibreOffice para exportar a PDF`
```bash
sudo apt install libreoffice   # o quita --to-pdf y convierte el .docx aparte
```

### `no se detectó una tarjeta en la imagen`
La foto no tiene suficiente turquesa reconocible (muy oscura, recortada o el DNI
ocupa muy poco). Reencuadra la foto con la tarjeta bien visible sobre un fondo
claro y uniforme.

### El PDF no sale a tamaño real
Imprime/exporta a escala **100 %**, nunca "Ajustar a página".

## 🤝 Cómo Contribuir

### Para agregar un nuevo módulo o flag
1. Crea `lib/nuevo_modulo.py` con funciones de responsabilidad única (< 30 líneas).
2. Añade los valores ajustables en `config.py` (nunca hardcodeados en `lib/`).
3. Si aporta una opción, declárala en `lib/cli.py` y consúmela en `main.py`.
4. Actualiza este README.

### Estándares de código
- Máximo 30 líneas por función; nombres descriptivos en inglés técnico.
- Comentarios sobre el "por qué", no el "qué".
- Mensajes al usuario en español; código y docstrings en inglés.

## ⚠️ Notas y Advertencias

- **Datos personales**: `config.py` trae como valores por defecto las rutas de un
  DNI real (número 28250954) para comodidad de un uso concreto. Si versionas este
  repositorio en un remoto público, **cambia esos defaults o no los subas**
  (p. ej. añádelos a `.gitignore` o reemplázalos por rutas de ejemplo). Las
  imágenes del DNI nunca deben salir de la máquina.
- **Orientación**: la herramienta asume que ambas fotos están en vertical con la
  tarjeta girada 90° (caso típico de foto de celular) y las gira 90° antihorario.
  Si tus fotos vienen en otra orientación, gíralas antes o ajusta
  `extract_face`.
- **Decisión de diseño**: el centrado vertical se logra con márgenes
  superior/inferior simétricos (LibreOffice ignora `w:vAlign`; MS Word sí lo
  respeta, y se deja activado por compatibilidad).
- **Restauración = solo visual**: la etapa `--enhance` limpia artefactos de
  compresión, reduce ruido y reescala; **no inventa detalle** ni modifica dato
  alguno del documento. Está calibrada suave para conservar microtexto, huella y
  demás elementos de seguridad; si algún elemento se ve demasiado suave, baja
  `BILATERAL_SIGMA_*` en `config.py` o usa `--no-enhance`.
- **Rendimiento y tamaño**: a 600 dpi con restauración, procesar ambas caras
  toma ~15 s y el `.docx` pesa varios MB (el PDF re-comprime y queda pequeño).
  Baja `--dpi` (p. ej. 450) si necesitas archivos más ligeros.
- **Orientación**: por defecto (`--rotate auto`) la herramienta detecta si la
  tarjeta viene de lado (vertical → gira 90° CCW) o ya horizontal (no gira). Los
  otros sentidos (horario, boca abajo) no se pueden deducir sin leer el
  contenido: fuérzalos con `--rotate 270` o `--rotate 180`.
- **Fondos oscuros**: la detección exige color **saturado y brillante**
  (`SAT_THRESHOLD` + `VALUE_MIN`), de modo que una superficie oscura pero con
  algo de color (no negro puro) no se confunde con la tarjeta.
- **Perspectiva**: la corrección asume que las 4 esquinas de la tarjeta se
  detectan bien (borde saturado visible). Si una esquina tiene un parche que
  tapa el borde y sale deformada, usa `--no-perspective` para esa imagen.
- **Dos tipos de entrada**: fotos de celular del DNI azul (tarjeta pequeña sobre
  un fondo, con perspectiva → detección + rectificación), y **DNIe/escaneos ya
  recortados y planos** (`--pre-cropped`: se omite detección/perspectiva/color y
  se preservan los colores originales). El DNIe no es turquesa, así que la
  detección por saturación no aplica: usa siempre `--pre-cropped` con él.
- **Peso de archivo**: los PDF/DOCX salen sin pérdida a la resolución elegida.
  A 300 dpi (por defecto) rondan 1.5–3 MB; a 600 dpi se cuadruplican sin aportar
  detalle real (el origen suele tener ~220 dpi efectivos). Usa 300 salvo que
  necesites 600 por algún requisito.
- **Historial de cambios**:
  - **v1.5.0** — salida en blanco y negro (`--grayscale`/`--bn`) y `--save-caras`
    ahora exporta cada cara recortada al tamaño real (PNG con DPI = 85.6×54 mm),
    lista para subir por separado.
  - **v1.4.1** — DPI por defecto 300 (peso ~1/4, misma nitidez real) y PDF de
    exportación sin pérdida y sin submuestreo (`UseLosslessCompression`,
    `ReduceImageResolution=false`): el PDF ya no recomprime ni baja resolución.
  - **v1.4.0** — modo `--pre-cropped` para imágenes ya recortadas y planas
    (DNIe/escaneos): tamaño real + esquinas + sombra + realce, sin alterar color.
  - **v1.3.1** — esquinas por intersección de rectas ajustadas a los bordes
    (alineación exacta a 0°) y warp con supersampling (`SUPERSAMPLE`) para
    anti-aliasing de las líneas.
  - **v1.3.0** — corrección de perspectiva (keystone) por homografía de 4
    esquinas a proporción ID-1 exacta (`--no-perspective` para desactivar).
  - **v1.2.0** — auto-orientación de las caras (`--rotate`) y detección robusta
    ante fondos oscuros/no uniformes (piso de brillo `VALUE_MIN`).
  - **v1.1.0** — etapa de restauración (`--enhance`, por defecto) y DPI por
    defecto 600 para acabado de escáner de alta resolución.
  - **v1.0.0** — reestructuración 1:1 del script original + exportación
    integrada a PDF (`--to-pdf`).
