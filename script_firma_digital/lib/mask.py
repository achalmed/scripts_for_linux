"""Binary mask construction: from the float ink map to a clean stroke mask.

Single responsibility: decide which pixels are ink. Combines hysteresis
thresholding (keeps faint stroke stretches connected), speckle removal,
Hough-based deskewing and morphological smoothing into one boolean mask
ready to be vectorized.
"""
from __future__ import annotations

from logging import Logger
from typing import Tuple

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.filters import apply_hysteresis_threshold, threshold_otsu
from skimage.morphology import binary_closing, disk, remove_small_holes
from skimage.transform import probabilistic_hough_line

import config


def _despeckle_by_area(mask: np.ndarray, min_area: float) -> np.ndarray:
    """Drops connected components smaller than `min_area` pixels."""
    labels, count = ndimage.label(mask)
    if not count:
        return mask
    areas = ndimage.sum(mask, labels, range(1, count + 1))
    keep = np.flatnonzero(areas >= min_area) + 1
    return np.isin(labels, keep)


def _binarize(ink_map: np.ndarray, umbral: float, frac_baja: float,
              area_minima: float) -> np.ndarray:
    """Hysteresis threshold + speckle/hole cleanup into a boolean mask."""
    mask = apply_hysteresis_threshold(ink_map, umbral * frac_baja, umbral)
    mask = _despeckle_by_area(mask, area_minima)
    return remove_small_holes(mask, area_threshold=int(area_minima))


def _dominant_angle(mask: np.ndarray) -> Tuple[float, int]:
    """Length-weighted tilt of the near-horizontal strokes, in degrees.

    Only segments flatter than ANGULO_MAX_SEGMENTO vote, so tall ascenders
    do not drag the estimate. Runs on a 2×-downsampled mask for speed.
    Returns (angle, number_of_voting_segments); positive angle slopes down
    to the right.
    """
    segments = probabilistic_hough_line(
        mask[::2, ::2], threshold=config.HOUGH_UMBRAL,
        line_length=config.HOUGH_LONGITUD_MIN,
        line_gap=config.HOUGH_HUECO_MAX, rng=42)
    weights, angles = [], []
    for (x0, y0), (x1, y1) in segments:
        angle = np.degrees(np.arctan2(y1 - y0, x1 - x0))
        angle = (angle + 90) % 180 - 90  # fold into (-90, 90]
        if abs(angle) < config.ANGULO_MAX_SEGMENTO:
            weights.append(np.hypot(x1 - x0, y1 - y0))
            angles.append(angle)
    if not weights:
        return 0.0, 0
    return float(np.average(angles, weights=weights)), len(weights)


def _rotate_ink_map(ink_map: np.ndarray, angle: float) -> np.ndarray:
    """Rotates the continuous ink map (bicubic) so re-thresholding is clean."""
    rotated = Image.fromarray((ink_map * 255).astype(np.uint8)).rotate(
        angle, resample=Image.BICUBIC, expand=True, fillcolor=0)
    return np.asarray(rotated).astype(np.float64) / 255.0


def _deskew(ink_map: np.ndarray, mask: np.ndarray, umbral: float,
            frac_baja: float, area_minima: float, logger: Logger) -> np.ndarray:
    """Rotates the signature level, verifying the sign by residual tilt.

    Both rotation directions are tried and the one that leaves the smallest
    residual tilt wins; this sidesteps sign-convention mistakes. If neither
    improves on the original, the mask is returned unrotated.
    """
    angle, votes = _dominant_angle(mask)
    if abs(angle) < config.ANGULO_MIN_CORREGIR \
            or votes < config.MIN_SEGMENTOS_ENDEREZAR:
        logger.info("Enderezado omitido (inclinación %.2f°, %d segmentos).",
                    angle, votes)
        return mask
    candidates = []
    for sign in (+1, -1):
        rotated = _binarize(_rotate_ink_map(ink_map, sign * angle),
                            umbral, frac_baja, area_minima)
        residual, _ = _dominant_angle(rotated)
        candidates.append((abs(residual), sign * angle, residual, rotated))
    best = min(candidates, key=lambda item: item[0])
    if best[0] >= abs(angle):
        logger.info("Enderezado omitido: ninguna rotación mejora %.2f°.", angle)
        return mask
    logger.info("Enderezado: %+.2f° (inclinación %.2f° -> residual %+.2f°).",
                best[1], angle, best[2])
    return best[3]


def _smooth_and_uniformize(mask: np.ndarray, escala: int,
                           area_minima: float) -> np.ndarray:
    """Smooths edges, closes micro-gaps and evens out stroke width."""
    pre = ndimage.gaussian_filter(
        mask.astype(np.float64), sigma=config.SUAVIZADO_SIGMA_PRE * escala) > 0.5
    closed = binary_closing(pre, disk(int(config.CIERRE_RADIO * escala)))
    post = ndimage.gaussian_filter(
        closed.astype(np.float64),
        sigma=config.SUAVIZADO_SIGMA_POST * escala) > 0.5
    return remove_small_holes(post, area_threshold=int(area_minima))


def build_clean_mask(ink_map: np.ndarray, escala: int, factor_umbral: float,
                     frac_baja: float, area_motas: int, enderezar: bool,
                     logger: Logger) -> np.ndarray:
    """Turns the ink map into a clean, level, denoised boolean stroke mask.

    Args:
        ink_map: Float ink map from preprocess.load_ink_map.
        escala: Working scale (magnitudes tagged "× escala" use it).
        factor_umbral: Multiplier applied to the Otsu threshold.
        frac_baja: Low/high ratio of the hysteresis threshold.
        area_motas: Final min component area (px²) to keep after smoothing.
        enderezar: Whether to deskew.
        logger: Progress logger.

    Returns:
        A boolean array; True where the signature ink is.
    """
    umbral = threshold_otsu(ink_map) * factor_umbral
    area_minima = config.AREA_MINIMA_BASE * escala * escala
    mask = _binarize(ink_map, umbral, frac_baja, area_minima)
    logger.info("Umbral Otsu×%.2f = %.3f; %d px de tinta iniciales.",
                factor_umbral, umbral, int(mask.sum()))
    if enderezar:
        mask = _deskew(ink_map, mask, umbral, frac_baja, area_minima, logger)
    mask = _smooth_and_uniformize(mask, escala, area_minima)
    mask = _despeckle_by_area(mask, area_motas)
    logger.info("Máscara final: %d×%d, %d px de tinta.",
                mask.shape[1], mask.shape[0], int(mask.sum()))
    return mask
