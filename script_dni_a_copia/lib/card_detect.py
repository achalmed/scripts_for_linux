"""Card detection, deskew and orientation for dni-a-copia.

Turns a phone photo of one DNI face into an upright, deskewed, cropped
landscape image plus two masks:

  * teal_mask  — the printed (turquoise) area, via HSV-saturation + convex hull
  * card_mask  — the printed area dilated to include the laminate rim

The card is a convex rounded rectangle, so the convex hull of its teal
fragments is its exact silhouette and captures every interior region
(photo, MRZ, fingerprint, inter-strip gaps) that a hole-fill would miss.
"""
from __future__ import annotations

import math
from logging import Logger
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull

import config

WHITE = (255, 255, 255)


def disk(radius: int) -> np.ndarray:
    """Circular structuring element (rounder morphology than a square)."""
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return x * x + y * y <= radius * radius


def card_mask(rgb: np.ndarray) -> np.ndarray:
    """Solid silhouette of the PRINTED (teal) area = convex hull of its
    saturated-and-bright fragments. Used for white balance and the rim.

    Raises:
        ValueError: if no card-like region is found (blank/unreadable image).
    """
    arr = rgb.astype(np.float32)
    mx, mn = arr.max(axis=2), arr.min(axis=2)
    sat = (mx - mn) / (mx + 1e-6)
    val = mx / 255.0
    seed = (sat > config.SAT_THRESHOLD) & (val > config.VALUE_MIN)
    return _hull_of_seed(seed)


def _hull_of_seed(seed: np.ndarray) -> np.ndarray:
    """Opening -> largest fragments -> convex hull (a solid silhouette)."""
    seed = ndimage.binary_opening(seed, structure=np.ones((3, 3)),
                                  iterations=config.OPEN_ITERATIONS)
    keep = _large_fragments(seed)
    ys, xs = np.where(keep)
    if len(xs) < 3:
        raise ValueError("no se detectó una tarjeta en la imagen")
    return _hull_mask(np.column_stack([xs, ys]), keep.shape)


def _large_fragments(seed: np.ndarray) -> np.ndarray:
    """Keeps only components big enough to be card parts (drops motes)."""
    lbl, n = ndimage.label(seed)
    if n == 0:
        raise ValueError("no se detectó una tarjeta en la imagen")
    sizes = ndimage.sum(np.ones_like(lbl), lbl, index=range(1, n + 1))
    threshold = config.MIN_FRAGMENT_FRACTION * sizes.max()
    big = [i + 1 for i, s in enumerate(sizes) if s > threshold]
    return np.isin(lbl, big)


def _hull_mask(points: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    """Rasterizes the convex hull of the given (x, y) points as a mask."""
    hull = ConvexHull(points)
    polygon = [tuple(points[v]) for v in hull.vertices]
    height, width = shape
    canvas = Image.new("L", (width, height), 0)
    ImageDraw.Draw(canvas).polygon(polygon, fill=255)
    return np.asarray(canvas) > 127


def _fit_slope(indep: List[int], dep: List[int]) -> Tuple[float, float]:
    """Robust line fit; returns (slope, residual_std) after outlier rejection."""
    indep_arr = np.asarray(indep, float)
    dep_arr = np.asarray(dep, float)
    slope, intercept = np.polyfit(indep_arr, dep_arr, 1)
    residual = dep_arr - (slope * indep_arr + intercept)
    std = np.std(residual)
    keep = np.abs(residual) < config.FIT_INLIER_K * std + 1.0
    if keep.sum() > 5:
        slope, intercept = np.polyfit(indep_arr[keep], dep_arr[keep], 1)
        std = np.std(dep_arr[keep] - (slope * indep_arr[keep] + intercept))
    return slope, std


def estimate_tilt(mask: np.ndarray) -> float:
    """Tilt in degrees (CCW positive) as the median of the 4 edge angles.

    The median rejects a single defective edge (e.g. a protruding strip)
    that would corrupt a plain average.
    """
    height, width = mask.shape
    angles = _edge_angles_horizontal(mask, width) \
        + _edge_angles_vertical(mask, height)
    if not angles:
        return 0.0
    good = [a for a, s in angles if s < config.FIT_MAX_STD] \
        or [a for a, s in angles]
    return float(np.median(good))


def _edge_angles_horizontal(mask: np.ndarray, width: int) -> list:
    """Angles from the top and bottom edges (fit y as a function of x)."""
    lo, hi = int(width * config.EDGE_INNER_FRACTION), \
        int(width * (1 - config.EDGE_INNER_FRACTION))
    xs, top, bottom = [], [], []
    for x in range(lo, hi):
        col = np.where(mask[:, x])[0]
        if len(col):
            xs.append(x)
            top.append(col[0])
            bottom.append(col[-1])
    if len(xs) <= config.TILT_MIN_POINTS:
        return []
    out = []
    for dep in (top, bottom):
        slope, std = _fit_slope(xs, dep)
        out.append((-math.degrees(math.atan(slope)), std))
    return out


def _edge_angles_vertical(mask: np.ndarray, height: int) -> list:
    """Angles from the left and right edges (fit x as a function of y)."""
    lo, hi = int(height * config.EDGE_INNER_FRACTION), \
        int(height * (1 - config.EDGE_INNER_FRACTION))
    ys, left, right = [], [], []
    for y in range(lo, hi):
        row = np.where(mask[y, :])[0]
        if len(row):
            ys.append(y)
            left.append(row[0])
            right.append(row[-1])
    if len(ys) <= config.TILT_MIN_POINTS:
        return []
    out = []
    for dep in (left, right):
        slope, std = _fit_slope(ys, dep)
        out.append((math.degrees(math.atan(slope)), std))
    return out


def deskew(img: Image.Image) -> Tuple[Image.Image, float]:
    """Straightens the card; verifies the residual and picks the best sense.

    Returns the (possibly rotated) image and the angle actually applied.
    """
    theta = estimate_tilt(card_mask(np.asarray(img)))
    if abs(theta) < config.DESKEW_MIN_ANGLE_DEG:
        return img, 0.0
    best_img, best_residual, best_angle = img, abs(theta), 0.0
    for angle in (-theta, theta):  # try both senses, keep the flatter result
        candidate = img.rotate(angle, resample=Image.BICUBIC,
                               expand=True, fillcolor=WHITE)
        residual = abs(estimate_tilt(card_mask(np.asarray(candidate))))
        if residual < best_residual:
            best_img, best_residual, best_angle = candidate, residual, angle
    return best_img, best_angle


def _bbox(mask: np.ndarray) -> Tuple[int, int, int, int]:
    """(y0, y1, x0, x1) of the True region."""
    ys, xs = np.where(mask)
    return ys.min(), ys.max(), xs.min(), xs.max()


def _dilation_px(mask: np.ndarray, millimeters: float) -> int:
    """A width in mm expressed in native pixels, scaled to the card long side."""
    y0, y1, x0, x1 = _bbox(mask)
    long_side = max(y1 - y0, x1 - x0) + 1
    scaled = round(millimeters / config.CARD_W_MM * long_side)
    return max(config.LAMINATE_RIM_MIN_PX, scaled)


_ROTATIONS = {
    90: Image.Transpose.ROTATE_90,     # counter-clockwise
    180: Image.Transpose.ROTATE_180,
    270: Image.Transpose.ROTATE_270,   # clockwise
}


def _decide_rotation(width: int, height: int, rotate: str) -> int:
    """Rotation (deg CCW) to bring the card upright landscape.

    'auto': a taller-than-wide card is sideways -> turn 90deg CCW; an already
    wider card is left as-is. Clockwise / upside-down can't be told apart from
    the shape, so force them with --rotate (270 / 180).
    """
    if rotate != "auto":
        return int(rotate)
    return 90 if height > width else 0


def _orient(image: Image.Image, angle: int) -> Image.Image:
    """Rotates by a right angle (0/90/180/270 deg CCW) without resampling."""
    return image if angle == 0 else image.transpose(_ROTATIONS[angle])


def _fit_line(indep: list, dep: list) -> Tuple[float, float]:
    """Robust line dep = m*indep + b, with one outlier-rejection pass."""
    x = np.asarray(indep, float)
    y = np.asarray(dep, float)
    m, b = np.polyfit(x, y, 1)
    resid = y - (m * x + b)
    keep = np.abs(resid) < 2.5 * np.std(resid) + 1.0
    if keep.sum() > 5:
        m, b = np.polyfit(x[keep], y[keep], 1)
    return m, b


def _find_card_quad(mask: np.ndarray) -> Tuple[np.ndarray, ...]:
    """Four card corners (UL, UR, LR, LL) as the intersections of straight
    lines fitted to the 4 edges.

    Fitting the edges (over the central 70%, skipping the rounded corners) and
    intersecting them locates the true corners far more precisely than extreme
    points on the rounded arcs — which is what leaves a residual tilt.
    """
    h, w = mask.shape
    xs, y_top, y_bot = [], [], []
    for x in range(int(w * 0.15), int(w * 0.85)):
        col = np.where(mask[:, x])[0]
        if len(col):
            xs.append(x)
            y_top.append(col[0])
            y_bot.append(col[-1])
    ys, x_left, x_right = [], [], []
    for y in range(int(h * 0.15), int(h * 0.85)):
        row = np.where(mask[y, :])[0]
        if len(row):
            ys.append(y)
            x_left.append(row[0])
            x_right.append(row[-1])
    mt, bt = _fit_line(xs, y_top)      # top:    y = mt*x + bt
    mb, bb = _fit_line(xs, y_bot)      # bottom: y = mb*x + bb
    ml, bl = _fit_line(ys, x_left)     # left:   x = ml*y + bl
    mr, br = _fit_line(ys, x_right)    # right:  x = mr*y + br

    def corner(m_h, b_h, m_v, b_v):    # intersect horizontal & vertical edge
        x = (m_v * b_h + b_v) / (1 - m_v * m_h)
        return np.array([x, m_h * x + b_h])

    return (corner(mt, bt, ml, bl), corner(mt, bt, mr, br),
            corner(mb, bb, mr, br), corner(mb, bb, ml, bl))


def _warp_to_rectangle(img: Image.Image, corners: Tuple[np.ndarray, ...],
                       target_long: int = None) -> Image.Image:
    """Perspective-warps the card quad to a true, ID-1-proportioned rectangle.

    Removes keystone (opposite sides become equal) AND fixes the aspect to the
    known ID-1 ratio, so no anisotropic stretch is introduced downstream. The
    long side is `target_long` if given (supersampled render), else the longer
    detected edge; the card's orientation in the photo is preserved.
    """
    ul, ur, lr, ll = corners

    def dist(a, b):
        return float(np.hypot(a[0] - b[0], a[1] - b[1]))

    edge_w = max(dist(ul, ur), dist(ll, lr))     # top/bottom edges
    edge_h = max(dist(ul, ll), dist(ur, lr))     # left/right edges
    long_px = target_long or round(max(edge_w, edge_h))
    short_px = round(long_px * config.CARD_H_MM / config.CARD_W_MM)
    if edge_w >= edge_h:                          # landscape in the photo
        w, h = long_px, short_px
    else:                                         # sideways (portrait)
        h, w = long_px, short_px
    quad = (ul[0], ul[1], ll[0], ll[1],          # PIL QUAD order: UL, LL, LR, UR
            lr[0], lr[1], ur[0], ur[1])
    return img.transform((w, h), Image.Transform.QUAD, quad,
                         resample=Image.BICUBIC)


def _rounded_mask(width: int, height: int, radius: int) -> np.ndarray:
    """Boolean rounded-rectangle mask (card silhouette after warp)."""
    canvas = Image.new("L", (width, height), 0)
    ImageDraw.Draw(canvas).rounded_rectangle(
        [0, 0, width - 1, height - 1], radius=radius, fill=255)
    return np.asarray(canvas) > 127


def extract_face(path: Path, logger: Logger, rotate: str = "auto",
                 perspective: bool = True, target_px: int = None
                 ) -> Tuple[Image.Image, np.ndarray, np.ndarray]:
    """Loads one DNI face, rectifies it and returns it upright + its masks.

    With `perspective` the card is warped from its 4 detected corners to a true
    rectangle (removes camera keystone: both sides end up equal). Otherwise
    only rotational deskew + an axis-aligned crop are applied. `target_px` sets
    the warped long side (supersampled), for anti-aliasing on the later downscale.
    """
    img = Image.open(path).convert("RGB")
    if perspective:
        teal = card_mask(np.asarray(img))
        # dilate enough to reach the non-teal header strip before finding corners
        outline = ndimage.binary_dilation(
            teal, structure=disk(_dilation_px(teal, config.PERSPECTIVE_DILATE_MM)))
        return _rectify_perspective(img, outline, path, rotate, logger, target_px)
    return _rectify_axis_aligned(img, path, rotate, logger)


def _rectify_perspective(img: Image.Image, outline: np.ndarray, path: Path,
                         rotate: str, logger: Logger, target_px: int = None):
    """4-corner homography -> flat rectangle; masks recomputed on the result."""
    warped = _warp_to_rectangle(img, _find_card_quad(outline), target_px)
    angle = _decide_rotation(warped.size[0], warped.size[1], rotate)
    crop = _orient(warped, angle)
    logger.info("%s: perspectiva corregida %dx%d, orientación=%d°",
                path.name, warped.size[0], warped.size[1], angle)
    teal_l = card_mask(np.asarray(crop))
    radius = max(1, round(config.CORNER_RADIUS_MM / config.CARD_W_MM
                          * crop.size[0]))
    card_l = _rounded_mask(crop.size[0], crop.size[1], radius)
    return crop, teal_l, card_l


def _rectify_axis_aligned(img: Image.Image, path: Path, rotate: str,
                          logger: Logger):
    """Rotational deskew + axis-aligned crop (no keystone correction)."""
    img, applied = deskew(img)
    teal = card_mask(np.asarray(img))
    card = ndimage.binary_dilation(
        teal, structure=disk(_dilation_px(teal, config.LAMINATE_RIM_MM)))
    y0, y1, x0, x1 = _bbox(card)
    angle = _decide_rotation(x1 - x0, y1 - y0, rotate)
    logger.info("%s: giro deskew=%+.2f°, residual=%+.2f°, orientación=%d°",
                path.name, applied, estimate_tilt(teal), angle)
    pad = 3
    box = (max(0, x0 - pad), max(0, y0 - pad),
           min(img.size[0], x1 + pad), min(img.size[1], y1 + pad))
    crop = _orient(img.crop(box), angle)
    teal_l = _crop_orient_mask(teal, box, angle)
    card_l = _crop_orient_mask(card, box, angle)
    return crop, teal_l, card_l


def _crop_orient_mask(mask: np.ndarray, box: Tuple[int, int, int, int],
                      angle: int) -> np.ndarray:
    """Crops a boolean mask to `box` and applies the same right-angle turn."""
    as_img = Image.fromarray((mask * 255).astype(np.uint8)).crop(box)
    return np.asarray(_orient(as_img, angle)) > 127
