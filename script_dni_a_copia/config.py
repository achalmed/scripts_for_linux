"""Central configuration for dni-a-copia.

Every user-tunable value lives here. Edit this file to change default
behavior without touching the logic in `lib/`; the most common values can
also be overridden per run via CLI flags (see `lib/cli.py`).

The image-processing constants reproduce a clean, real-size "scanner copy"
of a Peruvian DNI (ISO/IEC 7810 ID-1 card). They were tuned against phone
photos; adjust with care and re-check the output visually.
"""
from __future__ import annotations

import os

from collections import namedtuple

APP_NAME = "dni-a-copia"
VERSION = "1.5.0"

# --- Project exit codes (126/127 are reserved by the shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION = 4
EXIT_DEPENDENCY = 5

# --- Default inputs/outputs -------------------------------------------------
# Personal defaults: running with no flags reproduces the 28250954 copy.
# Override per run with --front/--back/--output-dir/--name.
# NOTE: these paths point at a private archive; do not commit real values to
# a public repository (see README, "Notas y Advertencias").
_DNI_DIR = os.path.join(os.environ.get("PERSONAL_DIR", os.path.expanduser("~/Documents/08 personal")),
                        "01_identidad_y_registro_civil/dni")   # FS2: sin ruta literal (core/env.py → PERSONAL_DIR)
DEFAULT_FRONT = f"{_DNI_DIR}/dni_28250954_frontal.jpeg"
DEFAULT_BACK = f"{_DNI_DIR}/dni_28250954_adversa.jpeg"
DEFAULT_OUTPUT_DIR = _DNI_DIR
DEFAULT_NAME = "dni_28250954_copia"      # base name for the .docx/.pdf
DEFAULT_SAVE_FACES = False               # also drop per-face PNGs next to output
DEFAULT_TO_PDF = False                   # also export the .docx to PDF
DEFAULT_ENHANCE = True                    # restoration stage (de-JPEG + sharpen)
DEFAULT_PRE_CROPPED = False               # input is already the cropped card
                                          # (e.g. the DNIe): skip detection etc.
DEFAULT_GRAYSCALE = False                  # black-and-white (grayscale) output
DEFAULT_ROTATE = "auto"                   # face orientation; see ROTATE_CHOICES
# 'auto': a sideways (portrait) card is rotated 90deg CCW to landscape, an
# already-landscape card is left as-is. Force other senses (CW=270, upside
# down=180) when auto guesses wrong.
ROTATE_CHOICES = ("auto", "0", "90", "180", "270")
DEFAULT_PERSPECTIVE = True                # fix camera keystone via 4-corner warp
CORNER_RADIUS_MM = 2.0                    # physical card corner radius (rounded)

# --- Card size (ISO/IEC 7810 ID-1) and output resolution --------------------
CARD_W_MM = 85.6
CARD_H_MM = 53.98
DEFAULT_DPI = 300           # print-quality and light; matches the real detail
                            # of phone/scan sources. Use --dpi 600 for max.
MIN_DPI = 72
MAX_DPI = 1200
# Perspective-warp at this multiple of the final resolution, then downscale
# with LANCZOS: the downscale anti-aliases the edges (smoother, continuous
# lines) instead of magnifying the source's stair-steps.
SUPERSAMPLE = 1.5

# --- Card detection (HSV saturation segmentation) ---------------------------
SAT_THRESHOLD = 0.20        # teal print has high saturation; gray/shadow ~0
VALUE_MIN = 0.40            # AND bright: excludes dark colored backgrounds
                            # (a black/dark surface can be saturated but dim)
OPEN_ITERATIONS = 2         # remove speckle from the textured background
# For perspective, corners are found on the teal dilated by this much, so the
# quad reaches the card's non-teal header strip (silver/holographic, which
# saturation can't detect and is the same brightness as a white background).
PERSPECTIVE_DILATE_MM = 3.0
MIN_FRAGMENT_FRACTION = 0.02  # keep fragments >=2% of the largest (drop motes)

# --- Deskew (tilt estimation by median of the 4 card edges) -----------------
EDGE_INNER_FRACTION = 0.15  # ignore rounded corners: fit only central 70%
FIT_INLIER_K = 2.5          # robust fit: keep residuals < k*std + 1 px
FIT_MAX_STD = 4.0           # discard an edge whose fit is noisier than this
TILT_MIN_POINTS = 10        # need enough edge samples to trust a fit
DESKEW_MIN_ANGLE_DEG = 0.05  # below this the image is already straight

# --- Laminate rim + finish --------------------------------------------------
LAMINATE_RIM_MM = 1.3       # translucent border kept around the printed area
LAMINATE_RIM_MIN_PX = 6     # floor for low-resolution inputs
RIM_WHITEN = 0.85           # how much the rim background is lightened (0..1)
RIM_WHITEN_MIN_VAL = 0.45   # only lighten already-light rim pixels, so dark
                            # header text/lines in the rim band are preserved
ERODE_RADIUS_PX = 1         # trim anti-aliased edge before compositing
FEATHER_SIGMA = 1.2         # soften the card silhouette against white
# Enhancement (PIL ImageEnhance factors; 1.0 = no change)
ENHANCE_COLOR = 0.82        # <1 lowers saturation (less cold/vivid)
ENHANCE_BRIGHTNESS = 1.07   # scanner-like brighter output
ENHANCE_CONTRAST = 1.06
UNSHARP_RADIUS = 1.5        # legacy sharpen used only when --no-enhance
UNSHARP_PERCENT = 80
UNSHARP_THRESHOLD = 2

# --- Restoration: de-JPEG + denoise + hi-res sharpen (--enhance, default on) -
# Applied BEFORE upscaling so the image scales up clean, not pixelated. Values
# are deliberately mild: enough to remove phone-JPEG artifacts without erasing
# microtext/guilloché or giving a plastic look. It never adds invented detail.
CHROMA_BLUR_RADIUS = 1.2    # smooth Cb/Cr only (kills color bleed, keeps luma)
DENOISE_BILATERAL = True    # edge-preserving denoise (needs scikit-image)
# Applied AFTER upscaling with a small window: gentle enough to keep thin
# features (serial number, microtext) while flattening residual noise.
BILATERAL_SIGMA_COLOR = 0.045  # tonal reach (float image 0..1); higher = smoother
BILATERAL_SIGMA_SPATIAL = 1.2  # spatial reach in px (small = detail-safe)
# Post-upscale sharpen (radius in mm so it scales with DPI; high threshold so
# flat areas/noise are left alone -> crisp edges without halos or amplified
# stair-steps on the line art).
SHARPEN_RADIUS_MM = 0.09
SHARPEN_PERCENT = 72
SHARPEN_THRESHOLD = 3
# Pre-cropped inputs (DNIe/scans) are already clean and sharp, so they get NO
# denoise (it would only soften the crisp text/lines) — just a high-quality
# Lanczos upscale and a definition-oriented unsharp that preserves detail.
PRECROP_SHARPEN_RADIUS_MM = 0.085
PRECROP_SHARPEN_PERCENT = 115
PRECROP_SHARPEN_THRESHOLD = 2

# --- White balance (white-patch on the brightest card pixels) ---------------
WB_PERCENTILE = 97          # top 3% brightest card pixels = white reference
WB_GAIN_MIN = 0.7
WB_GAIN_MAX = 1.6

# --- Drop shadow (expressed in mm so it scales with DPI) --------------------
SHADOW_MARGIN_MM = 1.9      # white room around the card for the shadow
SHADOW_DX_MM = 0.15
SHADOW_DY_MM = 0.22
SHADOW_BLUR_MM = 0.5
SHADOW_OPACITY = 0.15       # very subtle
SHADOW_COLOR = (120, 120, 120)

# --- Page layout (A4 portrait, both faces centered) -------------------------
PAGE_W_MM = 210.0
PAGE_H_MM = 297.0
SIDE_MARGIN_MM = 18.0
GAP_MM = 3.0                # vertical separation between the two faces

# --- PDF export -------------------------------------------------------------
SOFFICE_CANDIDATES = ("libreoffice", "soffice")
# PDF export quality: by default LibreOffice (a) re-encodes images to JPEG and
# (b) downsamples them to ~300 DPI — both degrade the text. Force lossless AND
# disable the resolution reduction so the full 600-DPI image is embedded intact.
PDF_EXPORT_FILTER = (
    'pdf:writer_pdf_Export:{'
    '"UseLosslessCompression":{"type":"boolean","value":true},'
    '"ReduceImageResolution":{"type":"boolean","value":false}'
    '}')

# --- Logging ----------------------------------------------------------------
LOG_FILE = None             # e.g. "dni_a_copia.log" for a persistent audit trail
USE_COLOR = True            # ANSI colors on TTYs; auto-disabled for pipes/NO_COLOR
ANSI_RESET = "\033[0m"
LEVEL_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[32m",
    "WARN": "\033[33m",
    "ERROR": "\033[31m",
}

# --- Derived geometry -------------------------------------------------------
Geometry = namedtuple("Geometry", [
    "card_w_px", "card_h_px", "img_w_px", "img_h_px",
    "img_w_mm", "img_h_mm", "shadow_margin_px",
    "shadow_dx_px", "shadow_dy_px", "shadow_blur_px",
])


def _mm2px(mm: float, dpi: int) -> int:
    """Millimeters to pixels at the given resolution."""
    return round(mm / 25.4 * dpi)


def build_geometry(dpi: int) -> Geometry:
    """Computes all pixel dimensions for a given output resolution.

    The physical card is CARD_W_MM x CARD_H_MM; the rendered canvas adds a
    symmetric SHADOW_MARGIN so the drop shadow has room. `img_*_mm` is the
    size the whole canvas must occupy in the document so that the *card*
    portion prints at exactly its real size.
    """
    card_w = _mm2px(CARD_W_MM, dpi)
    card_h = _mm2px(CARD_H_MM, dpi)
    margin = _mm2px(SHADOW_MARGIN_MM, dpi)
    img_w = card_w + 2 * margin
    img_h = card_h + 2 * margin
    return Geometry(
        card_w_px=card_w, card_h_px=card_h,
        img_w_px=img_w, img_h_px=img_h,
        img_w_mm=CARD_W_MM * img_w / card_w,
        img_h_mm=CARD_H_MM * img_h / card_h,
        shadow_margin_px=margin,
        shadow_dx_px=_mm2px(SHADOW_DX_MM, dpi),
        shadow_dy_px=_mm2px(SHADOW_DY_MM, dpi),
        shadow_blur_px=max(1, _mm2px(SHADOW_BLUR_MM, dpi)),
    )
