"""Central configuration for firma-digital.

Every user-tunable value lives here. Edit this file to change default
behavior without touching the logic in `lib/`; the most common values can
also be overridden per run via CLI flags (see `lib/cli.py`).

Values tagged "(× escala)" are base magnitudes measured at scale 1: the
pipeline multiplies them by the working scale so that changing --escala
keeps the visual result consistent.
"""
from __future__ import annotations

APP_NAME = "firma-digital"
VERSION = "1.0.0"

# --- Project exit codes (126/127 are reserved by the shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION = 4
EXIT_DEPENDENCY = 5

# --- Runtime Python dependencies (module name -> pip install hint) ---
# Checked before any work starts so a missing library fails early and
# clearly instead of crashing mid-pipeline.
DEPENDENCIES = {
    "numpy": "pip install numpy",
    "scipy": "pip install scipy",
    "skimage": "pip install scikit-image",
    "PIL": "pip install Pillow",
    "potrace": "pip install potracer",  # 'potrace' module ships in 'potracer'
}

# --- Output naming ---
# Default basename = <stem-de-la-foto> + this suffix. Overridable with --nombre.
SUFIJO_NOMBRE = "_digital"
SUFIJO_FONDO_BLANCO = "_fondo_blanco"

# ======================================================================
# PIPELINE — image preprocessing (lib/preprocess.py)
# ======================================================================
# Blue/violet ink absorbs red light, so the RED channel gives the highest
# ink-vs-paper contrast. Change to 1 (green) or 2 (blue) for other inks.
CANAL_TINTA = 0

# Working scale: the photo is upscaled this many times before processing so
# thin strokes survive thresholding and the trace has sub-pixel detail.
# Higher = sharper but slower (vectorization time grows fast). Overridable.
ESCALA_TRABAJO = 4

# Illumination flattening: the background lighting is estimated with a large
# Gaussian blur and divided out. Base sigma in px at scale 1 (× escala).
SIGMA_FONDO_BASE = 25

# Robust contrast stretch applied to the flattened map, as (low, high)
# percentiles. The high percentile sits well below 100 so faint strokes are
# pushed to full ink without letting a few dark specks saturate the range.
PERCENTILES_ESTIRAMIENTO = (0.5, 90.0)

# ======================================================================
# PIPELINE — binary mask (lib/mask.py)
# ======================================================================
# Otsu picks a global ink/paper threshold; this factor (<1) lowers it a bit
# so faint strokes are not cut. Overridable with --factor-umbral.
FACTOR_UMBRAL_OTSU = 0.90

# Hysteresis: a pixel is ink if it passes the HIGH threshold, or passes the
# LOW threshold AND touches a HIGH pixel. This keeps light stretches of a
# stroke connected instead of dashed. LOW = this fraction of the threshold.
# Overridable with --hist-baja.
FRACCION_HISTERESIS_BAJA = 0.65

# Speckle removal during binarization: connected components smaller than
# this (base px², × escala²) are dropped as noise before smoothing.
AREA_MINIMA_BASE = 15

# Final component filter, AFTER smoothing: components smaller than this
# absolute area (px² at working scale) are removed. The DEFAULT is
# deliberately conservative — it preserves deliberate small marks (dots,
# accents, underscores). For photos with isolated background specks, raise
# it (e.g. 2000) via --area-motas after inspecting the mask with --qa-dir.
AREA_MINIMA_MOTAS = 240

# --- Deskew (Hough-based) ---
# Only near-horizontal long segments vote for the baseline tilt. These are
# the parameters of skimage.probabilistic_hough_line plus the acceptance
# band and the minimum evidence to rotate at all.
HOUGH_UMBRAL = 10
HOUGH_LONGITUD_MIN = 250      # px at working scale
HOUGH_HUECO_MAX = 12
ANGULO_MAX_SEGMENTO = 12.0    # degrees: segments steeper than this are ignored
MIN_SEGMENTOS_ENDEREZAR = 3   # need at least this many segments to trust a tilt
ANGULO_MIN_CORREGIR = 0.5     # below this the signature is treated as level

# --- Smoothing / stroke-width uniformization (base magnitudes, × escala) ---
SUAVIZADO_SIGMA_PRE = 0.7     # Gaussian before morphological closing
CIERRE_RADIO = 1             # disk radius that closes micro-gaps
SUAVIZADO_SIGMA_POST = 0.5    # Gaussian after closing

# ======================================================================
# PIPELINE — vectorization (lib/vectorize.py)
# ======================================================================
# potrace parameters. TURDSIZE drops tiny speckles; ALPHAMAX controls
# corner rounding; OPTTOLERANCE controls Bézier fitting tolerance.
POTRACE_TURDSIZE = 60
POTRACE_ALPHAMAX = 1.15
POTRACE_OPTTOLERANCE = 0.2
POTRACE_OPTICURVE = True
# Points sampled per Bézier segment when rasterizing the vector for the QA
# check (higher = more accurate IoU, slightly slower).
MUESTREO_BEZIER = 24
# The vector must reproduce the mask at least this well (intersection-over-
# union) or the run aborts: a low value means the trace went wrong.
IOU_MINIMO = 0.90

# ======================================================================
# PIPELINE — export (lib/export.py)
# ======================================================================
# Blank margin around the signature, as a fraction of its width.
MARGEN_FRACCION = 0.02
# Physical width the SVG declares (mm). Height follows the aspect ratio.
# ~68 mm inserts at a natural signature size in a document. --ancho-mm.
ANCHO_FISICO_MM = 68.0
# Raster PNG resolution metadata (dots per inch).
PNG_DPI = 600
# Edge anti-aliasing: the boolean raster is blurred then 2×-downscaled; the
# resulting soft alpha is clipped as (alfa - BAJO) / RANGO into [0,1].
ALFA_ANTIALIAS_SIGMA = 1.6
ALFA_UMBRAL_BAJO = 0.25
ALFA_RANGO = 0.5

# ======================================================================
# Logging
# ======================================================================
LOG_FILE = None  # e.g. "firma_digital.log" for a persistent audit trail
USE_COLOR = True  # ANSI colors on TTYs; auto-disabled for pipes and NO_COLOR
ANSI_RESET = "\033[0m"
LEVEL_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[32m",
    "WARN": "\033[33m",
    "ERROR": "\033[31m",
}
