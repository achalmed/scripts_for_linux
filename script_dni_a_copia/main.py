#!/usr/bin/env python3
"""dni-a-copia — copia limpia, a tamaño real, de un DNI (anverso + reverso).

Orchestration only — the logic lives in lib/:

  1. Parse arguments             (lib/cli.py)
  2. Init logging                (lib/logger.py)
  3. Validate deps/inputs/flags  (lib/validator.py)
  4. Detect + deskew each face   (lib/card_detect.py)
  5. Render the scanner finish   (lib/card_render.py)
  6. Build Word (+ optional PDF) (lib/docx_builder.py)
  7. Summary; exit non-zero on failure.

Turns two phone photos of a DNI into an A4 sheet where both faces are
straightened, cleaned onto white (laminate rim kept), color-corrected and
centered at exact ISO/IEC 7810 ID-1 size. Version: 1.0.0
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run from any CWD

from PIL import Image

import config
from lib import validator
from lib.card_detect import extract_face
from lib.card_render import render_face, render_precropped
from lib.cli import build_argument_parser
from lib.docx_builder import build_document, export_pdf
from lib.logger import setup_logger


def _process_face(path: Path, geom: config.Geometry, dpi: int, enhance_on: bool,
                  rotate: str, perspective: bool, pre_cropped: bool,
                  grayscale: bool, logger):
    """Detects, rectifies and renders one face into its final page image."""
    if pre_cropped:
        logger.info("%s: pre-recortado (sin detección/perspectiva)", path.name)
        card = Image.open(path).convert("RGB")
        face = render_precropped(card, geom, dpi, enhance_on, logger)
    else:
        target_px = round(geom.card_w_px * config.SUPERSAMPLE)  # supersampled warp
        crop, teal_mask, card_region = extract_face(path, logger, rotate,
                                                    perspective, target_px)
        face = render_face(crop, teal_mask, card_region, geom,
                           dpi, enhance_on, logger)
    if grayscale:
        face = face.convert("L").convert("RGB")   # black-and-white output
    return face


def _save_faces(front, back, out_dir: Path, name: str, geom: config.Geometry,
                dpi: int, logger) -> None:
    """Writes each face cropped to the real card size (no shadow margin), tagged
    with the DPI so the PNG represents exactly 85.6 x 54 mm — ready to upload
    as a separate image."""
    box = (geom.shadow_margin_px, geom.shadow_margin_px,
           geom.shadow_margin_px + geom.card_w_px,
           geom.shadow_margin_px + geom.card_h_px)
    for image, suffix in ((front, "anverso"), (back, "reverso")):
        target = out_dir / f"{name}_{suffix}.png"
        image.crop(box).save(target, dpi=(dpi, dpi))
        logger.info("Cara (tamaño real) guardada: %s", target)


def main() -> int:
    args = build_argument_parser().parse_args()
    logger = setup_logger(config.APP_NAME, args.verbose, config.LOG_FILE)
    if args.dry_run:
        logger.info("Modo simulación: no se escribirá nada.")

    validator.validate_dependencies(args.to_pdf, args.dry_run, logger)
    dpi = validator.validate_dpi(args.dpi, logger)
    front_path, back_path = validator.validate_inputs(
        args.front, args.back, logger)
    out_dir = validator.validate_output_dir(
        args.output_dir, args.dry_run, logger)

    geom = config.build_geometry(dpi)
    logger.info("Procesando las dos caras del DNI%s...",
                " (restauración activa)" if args.enhance else "")
    front_img = _process_face(front_path, geom, dpi, args.enhance, args.rotate,
                              args.perspective, args.pre_cropped,
                              args.grayscale, logger)
    back_img = _process_face(back_path, geom, dpi, args.enhance, args.rotate,
                             args.perspective, args.pre_cropped,
                             args.grayscale, logger)
    logger.info("Tarjeta a tamaño real: %.1f x %.1f mm (@ %d dpi).",
                config.CARD_W_MM, config.CARD_H_MM, dpi)

    if args.save_caras and not args.dry_run:
        _save_faces(front_img, back_img, out_dir, args.name, geom, dpi, logger)
    elif args.save_caras:
        logger.info("[SIMULACIÓN] Se guardarían las PNG de cada cara.")

    docx_path = out_dir / f"{args.name}.docx"
    build_document(front_img, back_img, geom, docx_path, args.dry_run, logger)
    if args.to_pdf:
        export_pdf(docx_path, out_dir, args.dry_run, logger)

    logger.info("Listo.%s Imprime a escala 100%% para tamaño real.",
                " (simulación)" if args.dry_run else "")
    return config.EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        # Domain failure from card detection (e.g. no card in the image).
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(config.EXIT_GENERAL)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.", file=sys.stderr)
        sys.exit(130)  # convención del shell para SIGINT
