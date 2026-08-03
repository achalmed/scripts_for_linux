"""Export: crop, center and write the SVG and PNG deliverables.

Single responsibility: take a final boolean raster (the vector's raster in
full mode, or the mask in --solo-mascara mode) and produce the files —
a scalable SVG (full mode only), a transparent high-res PNG and a
white-background PNG — plus optional QA images.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image
from scipy import ndimage

import config

BBox = Tuple[int, int, int, int]  # (x0, x1, y0, y1)


def content_bbox(raster: np.ndarray,
                 margen_frac: float) -> Tuple[BBox, int]:
    """Bounding box of the ink plus a proportional margin.

    Returns (bbox, ref_width) where ref_width is the ink width without the
    margin — the reference used to convert pixels to millimeters.
    """
    ys, xs = np.nonzero(raster)
    ref_width = int(xs.max() - xs.min())
    margin = int(round(ref_width * margen_frac))
    x0 = max(int(xs.min()) - margin, 0)
    x1 = min(int(xs.max()) + margin + 1, raster.shape[1])
    y0 = max(int(ys.min()) - margin, 0)
    y1 = min(int(ys.max()) + margin + 1, raster.shape[0])
    return (x0, x1, y0, y1), ref_width


def write_svg(svg_paths: List[str], bbox: BBox, ref_width: int,
              ancho_mm: float, out_path: Path) -> Tuple[float, float]:
    """Writes the SVG with a physical size and even-odd fill.

    Returns the declared (width_mm, height_mm).
    """
    x0, x1, y0, y1 = bbox
    view_w, view_h = x1 - x0, y1 - y0
    mm_per_px = ancho_mm / ref_width
    width_mm, height_mm = view_w * mm_per_px, view_h * mm_per_px
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{width_mm:.1f}mm" height="{height_mm:.1f}mm" '
           f'viewBox="{x0} {y0} {view_w} {view_h}">\n'
           f'<path d="{" ".join(svg_paths)}" fill="#000000" '
           f'fill-rule="evenodd" stroke="none"/>\n</svg>\n')
    out_path.write_text(svg, encoding="utf-8")
    return width_mm, height_mm


def _alpha_from_raster(raster: np.ndarray, bbox: BBox) -> np.ndarray:
    """Anti-aliased alpha: blur the cropped raster, then 2×-downscale.

    Dimensions are trimmed to even before the reshape-downscale so odd
    crop sizes never raise a reshape error.
    """
    x0, x1, y0, y1 = bbox
    cropped = raster[y0:y1, x0:x1].astype(np.float64)
    blurred = ndimage.gaussian_filter(cropped, config.ALFA_ANTIALIAS_SIGMA)
    even_h = (cropped.shape[0] // 2) * 2
    even_w = (cropped.shape[1] // 2) * 2
    downscaled = blurred[:even_h, :even_w].reshape(
        even_h // 2, 2, even_w // 2, 2).mean(axis=(1, 3))
    return np.clip((downscaled - config.ALFA_UMBRAL_BAJO) / config.ALFA_RANGO,
                   0, 1)


def render_pngs(raster: np.ndarray, bbox: BBox, out_png: Path,
                out_png_white: Path) -> Tuple[int, int]:
    """Writes the transparent PNG and the white-background PNG.

    Returns the (width, height) in pixels of the rendered images.
    """
    alpha = _alpha_from_raster(raster, bbox)
    alpha_u8 = (alpha * 255).astype(np.uint8)
    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)  # RGB stays black (0)
    rgba[..., 3] = alpha_u8
    Image.fromarray(rgba, "RGBA").save(out_png, dpi=(config.PNG_DPI,
                                                     config.PNG_DPI))
    Image.fromarray(255 - alpha_u8).convert("RGB").save(
        out_png_white, dpi=(config.PNG_DPI, config.PNG_DPI))
    return alpha.shape[1], alpha.shape[0]


def _save_downscaled(image_u8: np.ndarray, out_path: Path,
                     factor: int = 3) -> None:
    """Saves a large diagnostic array shrunk by `factor` for quick viewing."""
    img = Image.fromarray(image_u8)
    width, height = img.size
    img.resize((max(width // factor, 1), max(height // factor, 1)),
               Image.LANCZOS).save(out_path)


def save_qa_images(qa_dir: Path, base: str, ink_map: np.ndarray,
                   mask: np.ndarray,
                   vector_raster: Optional[np.ndarray]) -> None:
    """Dumps ink map, clean mask and (if traced) vector raster for review."""
    _save_downscaled((np.clip(ink_map, 0, 1) * 255).astype(np.uint8),
                     qa_dir / f"{base}_qa_tinta.png")
    _save_downscaled(((~mask) * 255).astype(np.uint8),
                     qa_dir / f"{base}_qa_mascara.png")
    if vector_raster is not None:
        _save_downscaled(((~vector_raster) * 255).astype(np.uint8),
                         qa_dir / f"{base}_qa_vector.png")
