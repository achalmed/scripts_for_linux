"""Image restoration for dni-a-copia (visual-only, no invented detail).

A classical restoration chain to give phone photos a clean high-resolution
"scanner" look, in two stages:

  reduce_artifacts()  — at native resolution, BEFORE upscaling:
    * chroma de-JPEG — smooth Cb/Cr in YCbCr, leaving luma (detail/text)
      untouched; removes color bleed and blocky color artifacts.

  restore_highres()   — AFTER upscaling, at the output resolution:
    * bilateral denoise — edge-preserving; flattens residual noise between
      the enlarged pixels while keeping edges/text crisp. Done here (not at
      native res) so thin features — e.g. the serial number — are already
      enlarged and survive the small smoothing window.
    * gentle unsharp — crisp edges without halos (high threshold leaves flat
      areas and noise alone).

Nothing fabricates detail or touches the document data; it only cleans
compression artifacts and rescales.
"""
from __future__ import annotations

from logging import Logger

import numpy as np
from PIL import Image, ImageFilter

import config

try:
    from skimage.restoration import denoise_bilateral
    _HAS_SKIMAGE = True
except ImportError:                      # degrade gracefully to chroma-only
    _HAS_SKIMAGE = False


def reduce_artifacts(image: Image.Image) -> Image.Image:
    """Native-resolution chroma de-JPEG (safe: never blurs luma/detail)."""
    luma, cb, cr = image.convert("YCbCr").split()
    blur = ImageFilter.GaussianBlur(config.CHROMA_BLUR_RADIUS)
    merged = Image.merge("YCbCr", (luma, cb.filter(blur), cr.filter(blur)))
    return merged.convert("RGB")


def restore_highres(image: Image.Image, dpi: int,
                    logger: Logger) -> Image.Image:
    """Denoise + sharpen at the output resolution (after upscaling)."""
    if config.DENOISE_BILATERAL and _HAS_SKIMAGE:
        image = _denoise_bilateral(image)
    elif config.DENOISE_BILATERAL:
        logger.warning("scikit-image no disponible: se omite el denoise "
                       "(instálalo para el completo).")
    return _sharpen(image, dpi)


def _denoise_bilateral(image: Image.Image) -> Image.Image:
    """Edge-preserving denoise with a small window (keeps thin features)."""
    arr = np.asarray(image).astype(np.float32) / 255.0
    smoothed = denoise_bilateral(
        arr, sigma_color=config.BILATERAL_SIGMA_COLOR,
        sigma_spatial=config.BILATERAL_SIGMA_SPATIAL, channel_axis=-1)
    return Image.fromarray((np.clip(smoothed, 0, 1) * 255).astype(np.uint8))


def _sharpen(image: Image.Image, dpi: int) -> Image.Image:
    """Gentle unsharp at the output resolution (radius scales with DPI)."""
    radius = max(1.0, config.SHARPEN_RADIUS_MM / 25.4 * dpi)
    return image.filter(ImageFilter.UnsharpMask(
        radius=radius, percent=config.SHARPEN_PERCENT,
        threshold=config.SHARPEN_THRESHOLD))
