"""Vectorization: from the boolean mask to Bézier curves (SVG paths).

Single responsibility: fit smooth outlines to the stroke mask with potrace
and provide a raster round-trip so the caller can measure how faithfully
the vector reproduces the mask (IoU) before trusting it.
"""
from __future__ import annotations

from logging import Logger
from typing import List, Tuple

import numpy as np
import potrace
from skimage.draw import polygon as sk_polygon

import config

# potracer exposes turn-policy constants under two different names across
# versions; fall back to MINORITY's integer value if neither is present.
_TURNPOLICY = getattr(potrace, "TURNPOLICY_MINORITY",
                      getattr(potrace, "POTRACE_TURNPOLICY_MINORITY", 4))


def _pxy(point) -> Tuple[float, float]:
    """Reads an (x, y) pair from a potrace point (attr or tuple form)."""
    return (point.x, point.y) if hasattr(point, "x") else (point[0], point[1])


def _bezier_segment(start, segment, t: np.ndarray) -> Tuple[list, str]:
    """Samples one cubic Bézier into points and its SVG 'C' command."""
    p0 = np.array(start)
    c1 = np.array(_pxy(segment.c1))
    c2 = np.array(_pxy(segment.c2))
    end = np.array(_pxy(segment.end_point))
    curve = (((1 - t) ** 3)[:, None] * p0
             + (3 * (1 - t) ** 2 * t)[:, None] * c1
             + (3 * (1 - t) * t ** 2)[:, None] * c2
             + (t ** 3)[:, None] * end)
    command = (f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} "
               f"{end[0]:.2f} {end[1]:.2f}")
    return [tuple(point) for point in curve], command


def _sample_curve(curve, t: np.ndarray) -> Tuple[list, str]:
    """Turns one potrace curve into (polygon points, SVG path string)."""
    start = _pxy(curve.start_point)
    points = [start]
    parts = [f"M {start[0]:.2f} {start[1]:.2f}"]
    for segment in curve.segments:
        if segment.is_corner:
            corner, end = _pxy(segment.c), _pxy(segment.end_point)
            parts.append(f"L {corner[0]:.2f} {corner[1]:.2f} "
                         f"L {end[0]:.2f} {end[1]:.2f}")
            points += [corner, end]
        else:
            sampled, command = _bezier_segment(points[-1], segment, t)
            points += sampled
            parts.append(command)
    parts.append("Z")
    return points, " ".join(parts)


def trace(mask: np.ndarray, logger: Logger) -> Tuple[List[np.ndarray], List[str]]:
    """Traces the mask with potrace into polygons (for QA) and SVG paths.

    Returns:
        (polygons, svg_paths): the sampled outline points per curve, and the
        matching SVG path 'd' strings, sharing the mask's coordinate system.
    """
    logger.info("Vectorizando con potrace (puede tardar varios minutos)...")
    # potracer treats nonzero pixels as WHITE; trace the INVERTED mask so the
    # ink becomes the foreground being outlined (otherwise it traces paper).
    bitmap = potrace.Bitmap(np.logical_not(mask))
    path = bitmap.trace(
        turdsize=config.POTRACE_TURDSIZE, turnpolicy=_TURNPOLICY,
        alphamax=config.POTRACE_ALPHAMAX,
        opticurve=1 if config.POTRACE_OPTICURVE else 0,
        opttolerance=config.POTRACE_OPTTOLERANCE)
    t = np.linspace(0, 1, config.MUESTREO_BEZIER + 1)[1:]
    polygons, svg_paths = [], []
    for curve in path:
        points, path_d = _sample_curve(curve, t)
        polygons.append(np.array(points))
        svg_paths.append(path_d)
    logger.info("Vectorización: %d curvas.", len(polygons))
    return polygons, svg_paths


def rasterize(polygons: List[np.ndarray],
              shape: Tuple[int, int]) -> np.ndarray:
    """Fills the traced polygons with even-odd rule (holes via XOR)."""
    canvas = np.zeros(shape, dtype=bool)
    for poly in polygons:
        rr, cc = sk_polygon(poly[:, 1], poly[:, 0], shape=shape)
        canvas[rr, cc] ^= True
    return canvas


def compute_iou(raster: np.ndarray, mask: np.ndarray) -> float:
    """Intersection-over-union between the vector raster and the mask."""
    union = np.logical_or(raster, mask).sum()
    if not union:
        return 0.0
    return float(np.logical_and(raster, mask).sum() / union)
