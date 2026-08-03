"""Color correction and "scanner copy" finish for dni-a-copia.

Takes an upright DNI face (plus its teal/card masks) and produces the
final page image: natural color, the real laminate rim kept but with its
background whitened, the card composited on white at real ID-1 size, and a
very subtle drop shadow so the card reads as a scan without a hard cutout.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from scipy import ndimage

import config
from lib import enhance
from lib.card_detect import disk, _rounded_mask

WHITE = (255, 255, 255)


def white_balance(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """White-patch balance: the brightest card pixels become neutral.

    Scaling each channel so the bright reference turns gray removes the
    cold/blue cast of phone photos without desaturating the whole card.
    """
    values = rgb.astype(np.float32)
    card_pixels = values[mask]
    luminance = card_pixels.mean(axis=1)
    threshold = np.percentile(luminance, config.WB_PERCENTILE)
    reference = card_pixels[luminance >= threshold].mean(axis=0)
    gain = np.clip(reference.mean() / (reference + 1e-6),
                   config.WB_GAIN_MIN, config.WB_GAIN_MAX)
    return np.clip(values * gain, 0, 255).astype(np.uint8)


def _color_grade(image: Image.Image) -> Image.Image:
    """Gentle color/brightness/contrast for a clean scan look (no sharpen)."""
    image = ImageEnhance.Color(image).enhance(config.ENHANCE_COLOR)
    image = ImageEnhance.Brightness(image).enhance(config.ENHANCE_BRIGHTNESS)
    return ImageEnhance.Contrast(image).enhance(config.ENHANCE_CONTRAST)


def _legacy_sharpen(image: Image.Image) -> Image.Image:
    """Native-resolution unsharp — the pre-restoration look (--no-enhance)."""
    return image.filter(ImageFilter.UnsharpMask(
        radius=config.UNSHARP_RADIUS, percent=config.UNSHARP_PERCENT,
        threshold=config.UNSHARP_THRESHOLD))


def _whiten_rim(arr: np.ndarray, teal_mask: np.ndarray,
                card_region: np.ndarray) -> np.ndarray:
    """Lightens the rim band's background to white — but only already-light
    pixels, so dark header text/lines that fall in the band are preserved."""
    inner = ndimage.binary_dilation(teal_mask, structure=disk(1))
    light = arr.mean(axis=2) > config.RIM_WHITEN_MIN_VAL * 255
    target = (card_region & ~inner) & light
    arr[target] = arr[target] * (1 - config.RIM_WHITEN) + 255.0 * config.RIM_WHITEN
    return arr


def _composite_on_white(arr: np.ndarray, card_region: np.ndarray,
                        geom: config.Geometry) -> tuple:
    """Places the card on white (feathered edge) at real ID-1 pixel size.

    Returns the resized card image and its silhouette (alpha) mask.
    """
    trimmed = ndimage.binary_erosion(
        card_region, structure=disk(config.ERODE_RADIUS_PX))
    alpha = ndimage.gaussian_filter(
        trimmed.astype(np.float32), sigma=config.FEATHER_SIGMA)
    blended = np.clip(arr * alpha[..., None] + 255.0 * (1 - alpha[..., None]),
                      0, 255).astype(np.uint8)
    size = (geom.card_w_px, geom.card_h_px)
    card_img = Image.fromarray(blended).resize(size, Image.LANCZOS)
    silhouette = Image.fromarray(
        (alpha * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    return card_img, silhouette


def _add_shadow(card_img: Image.Image, silhouette: Image.Image,
                geom: config.Geometry) -> Image.Image:
    """Composites the card on a white page with a very subtle drop shadow."""
    page = Image.new("RGB", (geom.img_w_px, geom.img_h_px), WHITE)
    shadow = Image.new("L", page.size, 0)
    shadow.paste(silhouette, (geom.shadow_margin_px + geom.shadow_dx_px,
                              geom.shadow_margin_px + geom.shadow_dy_px))
    shadow = shadow.filter(ImageFilter.GaussianBlur(geom.shadow_blur_px))
    shadow = shadow.point(lambda v: int(v * config.SHADOW_OPACITY))
    page = Image.composite(
        Image.new("RGB", page.size, config.SHADOW_COLOR), page, shadow)
    page.paste(card_img, (geom.shadow_margin_px, geom.shadow_margin_px),
               silhouette)
    return page


def _define_sharpen(image: Image.Image, dpi: int) -> Image.Image:
    """Definition-oriented unsharp for clean inputs (no denoise, no softening)."""
    radius = max(1.0, config.PRECROP_SHARPEN_RADIUS_MM / 25.4 * dpi)
    return image.filter(ImageFilter.UnsharpMask(
        radius=radius, percent=config.PRECROP_SHARPEN_PERCENT,
        threshold=config.PRECROP_SHARPEN_THRESHOLD))


def render_precropped(card_img: Image.Image, geom: config.Geometry,
                      dpi: int, enhance_on: bool, logger) -> Image.Image:
    """Render an already-cropped, flat card (e.g. the DNIe) to the final page.

    The whole input IS the card, so there is no detection, perspective, white
    balance or desaturation (those are for the teal phone photos). Crucially,
    there is NO denoise either: a clean scan is already sharp, and denoising
    would only soften its text/lines. Just a high-quality Lanczos upscale, a
    definition unsharp, rounded corners and a subtle shadow — detail and colors
    are preserved (and edges sharpened), never reduced.
    """
    card = card_img.resize((geom.card_w_px, geom.card_h_px), Image.LANCZOS)
    if enhance_on:
        card = _define_sharpen(card, dpi)
    radius = max(1, round(config.CORNER_RADIUS_MM / config.CARD_W_MM
                          * geom.card_w_px))
    silhouette = Image.fromarray(
        (_rounded_mask(geom.card_w_px, geom.card_h_px, radius) * 255)
        .astype(np.uint8))
    return _add_shadow(card, silhouette, geom)


def render_face(crop: Image.Image, teal_mask: np.ndarray,
                card_region: np.ndarray, geom: config.Geometry,
                dpi: int, enhance_on: bool, logger) -> Image.Image:
    """Full finish pipeline for one face -> final page image.

    With `enhance_on` the restoration chain runs: de-JPEG/denoise before the
    upscale and a gentle sharpen after it. Without it, the previous
    native-resolution unsharp is used instead (unchanged legacy look).
    """
    image = Image.fromarray(white_balance(np.asarray(crop), teal_mask))
    if enhance_on:
        image = enhance.reduce_artifacts(image)          # chroma de-JPEG (native)
    image = _color_grade(image)
    if not enhance_on:
        image = _legacy_sharpen(image)
    arr = _whiten_rim(np.asarray(image).astype(np.float32),
                      teal_mask, card_region)
    card_img, silhouette = _composite_on_white(arr, card_region, geom)
    if enhance_on:
        card_img = enhance.restore_highres(card_img, dpi, logger)  # denoise+sharpen
    return _add_shadow(card_img, silhouette, geom)
