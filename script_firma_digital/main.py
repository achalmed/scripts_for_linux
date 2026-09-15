#!/usr/bin/env python3
"""script_firma_digital/main.py — convierte la foto de una firma en SVG + PNG limpios.

Orchestration only — the pipeline lives in lib/:

  1. Parse arguments            (lib/cli.py)
  2. Init logging               (lib/logger.py)
  3. Validate deps / input / dirs (lib/validator.py)
  4. Preprocess  -> ink map     (lib/preprocess.py)
  5. Build clean stroke mask    (lib/mask.py)
  6. Vectorize (unless --solo-mascara), with an IoU fidelity check
                                (lib/vectorize.py)
  7. Crop, center and export SVG + PNGs (lib/export.py)
  8. Summary.

The heavy scientific libraries are imported lazily (step 4 onward) so the
dependency check in step 3 can report a friendly message instead of an
ImportError when a library is missing.
"""
from __future__ import annotations

import sys
from collections import namedtuple
from logging import Logger
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run from any CWD

import config
from lib import validator
from lib.cli import build_argument_parser
from lib.logger import setup_logger

Rutas = namedtuple("Rutas", "base svg png blanco")


def _build_paths(args, input_path: Path, output_dir: Path) -> Rutas:
    """Derives the output basename and the SVG/PNG paths."""
    base = args.nombre or (input_path.stem + config.SUFIJO_NOMBRE)
    return Rutas(
        base=base,
        svg=output_dir / f"{base}.svg",
        png=output_dir / f"{base}.png",
        blanco=output_dir / f"{base}{config.SUFIJO_FONDO_BLANCO}.png",
    )


def _report_shallow_plan(paths: Rutas, solo_mascara: bool,
                         logger: Logger) -> None:
    """Dry-run plan when the scientific libraries are missing (no mask)."""
    files = [paths.png.name, paths.blanco.name]
    if not solo_mascara:
        files.insert(0, paths.svg.name)
    logger.info("[SIMULACIÓN] Sin dependencias no se puede analizar la foto; "
                "se generaría: %s.", ", ".join(files))


def _vectorize_checked(mask, logger: Logger):
    """Traces the mask and validates fidelity. Returns (svg_paths, raster).

    Returns (None, None) when the vector fails the IoU check so the caller
    can abort with a non-zero exit code.
    """
    from lib import vectorize
    polygons, svg_paths = vectorize.trace(mask, logger)
    vector_raster = vectorize.rasterize(polygons, mask.shape)
    iou = vectorize.compute_iou(vector_raster, mask)
    logger.info("Fidelidad vector/máscara (IoU): %.4f.", iou)
    if iou < config.IOU_MINIMO:
        logger.error("La vectorización no reproduce la máscara (IoU %.4f < "
                     "%.2f); revisa la foto o baja --factor-umbral.",
                     iou, config.IOU_MINIMO)
        return None, None
    return svg_paths, vector_raster


def run_conversion(args, input_path: Path, output_dir: Path,
                   qa_dir, logger: Logger) -> int:
    """Runs the full pipeline and writes the deliverables. Returns exit code."""
    from lib import export, preprocess
    from lib import mask as mask_mod

    ink_map = preprocess.load_ink_map(input_path, args.escala, logger)
    mask = mask_mod.build_clean_mask(
        ink_map, args.escala, args.factor_umbral, args.hist_baja,
        args.area_motas, not args.sin_enderezar, logger)
    paths = _build_paths(args, input_path, output_dir)

    if args.dry_run:
        kind = "PNG ráster" if args.solo_mascara else "SVG + PNG"
        logger.info("[SIMULACIÓN] Máscara lista; se generaría %s con base "
                    "'%s'. No se escribe nada.", kind, paths.base)
        return config.EXIT_OK

    svg_paths, vector_raster = None, None
    if not args.solo_mascara:
        svg_paths, vector_raster = _vectorize_checked(mask, logger)
        if vector_raster is None:
            return config.EXIT_GENERAL

    final_raster = vector_raster if vector_raster is not None else mask
    bbox, ref_width = export.content_bbox(final_raster, config.MARGEN_FRACCION)
    if svg_paths is not None:
        width_mm, height_mm = export.write_svg(
            svg_paths, bbox, ref_width, args.ancho_mm, paths.svg)
        logger.info("SVG: %s (%.0f×%.0f mm).", paths.svg.name,
                    width_mm, height_mm)
    px_w, px_h = export.render_pngs(final_raster, bbox, paths.png, paths.blanco)
    logger.info("PNG: %s y %s (%d×%d px @ %d ppp).", paths.png.name,
                paths.blanco.name, px_w, px_h, config.PNG_DPI)
    if qa_dir is not None:
        export.save_qa_images(qa_dir, paths.base, ink_map, mask, vector_raster)
        logger.info("Imágenes de control en '%s'.", qa_dir)
    logger.info("Listo.")
    return config.EXIT_OK


def main() -> int:
    args = build_argument_parser().parse_args()
    logger = setup_logger(config.APP_NAME, args.verbose, config.LOG_FILE)
    if args.dry_run:
        logger.info("Modo simulación: no se vectorizará ni se escribirá nada.")
    deps_ok = validator.validate_dependencies(args.dry_run, logger)
    input_path = validator.validate_input(args.entrada, logger)
    output_dir = validator.resolve_output_dir(
        args.output_dir, input_path, args.dry_run, logger)
    qa_dir = validator.resolve_qa_dir(args.qa_dir, args.dry_run, logger)
    if args.dry_run and not deps_ok:
        _report_shallow_plan(_build_paths(args, input_path, output_dir),
                             args.solo_mascara, logger)
        return config.EXIT_OK
    return run_conversion(args, input_path, output_dir, qa_dir, logger)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.", file=sys.stderr)
        sys.exit(130)  # convención del shell para SIGINT
