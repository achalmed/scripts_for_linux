"""Photo preprocessing: from a phone photo to a clean float ink map.

Single responsibility: turn the source image into a 2-D float array in
[0, 1] where 1 means ink and 0 means paper, correcting the two artifacts
a phone photo always has — uneven lighting and low ink/paper contrast.
"""
from __future__ import annotations

from logging import Logger
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image
from scipy import ndimage

import config


def _extract_channel_upscaled(source: Path, escala: int,
                              canal: int) -> np.ndarray:
    """Reads one color channel and upscales it (Lanczos) by `escala`.

    The red channel is used by default because blue/violet ink absorbs red
    light, so it is darkest there — the cleanest ink/paper separation.
    """
    rgb = np.asarray(Image.open(source).convert("RGB"))
    canal_img = rgb[:, :, canal].astype(np.float64) / 255.0
    height, width = canal_img.shape
    upscaled = Image.fromarray((canal_img * 255).astype(np.uint8)).resize(
        (width * escala, height * escala), Image.LANCZOS)
    return np.asarray(upscaled).astype(np.float64) / 255.0


def _flatten_illumination(gris: np.ndarray, sigma: float) -> np.ndarray:
    """Removes lighting gradients by dividing out a blurred background.

    A large Gaussian blur estimates the page's local brightness (shadows,
    vignetting); dividing by it leaves the strokes on a flat white field.
    """
    fondo = ndimage.gaussian_filter(gris, sigma=sigma)
    return np.clip(gris / np.maximum(fondo, 1e-6), 0, 2)


def _stretch_percentiles(plano: np.ndarray,
                         percentiles: Tuple[float, float]) -> np.ndarray:
    """Robust contrast stretch between the given (low, high) percentiles."""
    lo, hi = np.percentile(plano, percentiles)
    return np.clip((plano - lo) / (hi - lo), 0, 1)


def load_ink_map(source: Path, escala: int, logger: Logger) -> np.ndarray:
    """Builds the ink map (1=ink, 0=paper) from the source photo.

    Args:
        source: Path to the signature photo.
        escala: Working upscale factor.
        logger: Progress logger.

    Returns:
        A float64 array in [0, 1]; larger values are more likely ink.
    """
    logger.info("Cargando foto y corrigiendo iluminación (escala %d×)...",
                escala)
    gris = _extract_channel_upscaled(source, escala, config.CANAL_TINTA)
    plano = _flatten_illumination(gris, config.SIGMA_FONDO_BASE * escala)
    plano = _stretch_percentiles(plano, config.PERCENTILES_ESTIRAMIENTO)
    tinta = 1.0 - plano
    logger.debug("Mapa de tinta: %s px, rango [%.3f, %.3f]",
                 tinta.shape, float(tinta.min()), float(tinta.max()))
    return tinta
