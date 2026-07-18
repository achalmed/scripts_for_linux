"""Implementación de cada subcomando. `main.py` solo orquesta estas funciones."""
from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path

from config import Settings
from lib import montage, planner, renamer, scanner, validator
from lib.planner import PlanEntry

_REVIEW_STATUSES = {"weak", "dark", "fail", "error"}


def _prepare(folder_arg: str, settings: Settings) -> Path:
    """Valida dependencias, carpeta y parámetros antes de cualquier lógica."""
    validator.require_tesseract()
    validator.validate_crop(settings)
    return validator.validate_folder(folder_arg)


def _progress(logger: logging.Logger):
    """Crea un callback de progreso que reporta avance y velocidad."""
    def report(done: int, total: int) -> None:
        logger.info("Procesadas %d/%d imágenes (%.0f%%)",
                    done, total, 100 * done / total)
    return report


def _write_analysis(results, folder: Path, settings: Settings) -> None:
    """Vuelca el resultado crudo del OCR a JSON para inspección/depuración."""
    payload = [dataclasses.asdict(result) for result in results]
    (folder / settings.analysis_json_name).write_text(
        json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")


def _log_summary(logger: logging.Logger, entries: list[PlanEntry]) -> None:
    """Imprime el bloque de resumen del plan."""
    stats = planner.summarize(entries)
    logger.info("── Resumen ─────────────────────────────")
    logger.info("Total analizadas : %d", stats["total"])
    logger.info("A renombrar      : %d", stats["rename"])
    logger.info("Ya correctas     : %d", stats["keep"])
    logger.info("Sin marca (SKIP) : %d", stats["skip"])
    logger.info("Con sufijo _N    : %d", stats["collision_suffixed"])
    logger.info("────────────────────────────────────────")


def _scan_and_plan(folder: Path, settings: Settings,
                   logger: logging.Logger) -> list[PlanEntry]:
    """Escanea la carpeta y construye el plan, escribiendo también el JSON."""
    results = scanner.scan_folder(folder, settings, _progress(logger))
    _write_analysis(results, folder, settings)
    return planner.build_plan(results)


def cmd_analyze(folder_arg: str, settings: Settings, logger: logging.Logger) -> int:
    """Analiza la carpeta y escribe el plan y el JSON. No cambia nada."""
    folder = _prepare(folder_arg, settings)
    entries = _scan_and_plan(folder, settings, logger)
    planner.write_plan_csv(entries, folder / settings.plan_csv_name)
    _log_summary(logger, entries)
    logger.info("Plan escrito en: %s", folder / settings.plan_csv_name)
    return 0


def cmd_apply(folder_arg: str, settings: Settings, logger: logging.Logger,
              execute: bool, from_plan: str | None) -> int:
    """Renombra según el plan. Sin `execute` solo simula."""
    folder = _prepare(folder_arg, settings)
    if from_plan:
        entries = planner.read_plan_csv(Path(from_plan))
    else:
        entries = _scan_and_plan(folder, settings, logger)
        planner.write_plan_csv(entries, folder / settings.plan_csv_name)
    _log_summary(logger, entries)
    pairs = renamer.apply_plan(entries, folder, settings, execute)
    if execute:
        logger.info("Renombrado aplicado: %d archivos. Log y undo creados.", len(pairs))
    else:
        logger.warning("[SIMULACIÓN] %d se renombrarían. Añade --execute para aplicar.",
                       len(pairs))
    return 0


def _review_items(entries: list[PlanEntry], folder: Path
                  ) -> list[tuple[str, Path]]:
    """Selecciona filas dudosas o con colisión y arma las etiquetas del montaje."""
    stamps = [entry.stamp for entry in entries]
    chosen = [entry for entry in entries
              if entry.status in _REVIEW_STATUSES
              or (entry.stamp and stamps.count(entry.stamp) > 1)]
    return [(f"{entry.old}\n-> {entry.new}\n[{entry.status}]", folder / entry.old)
            for entry in chosen]


def cmd_verify(folder_arg: str, settings: Settings, logger: logging.Logger,
               from_plan: str | None) -> int:
    """Genera montajes PNG de las lecturas dudosas y las colisiones."""
    folder = _prepare(folder_arg, settings)
    entries = (planner.read_plan_csv(Path(from_plan)) if from_plan
               else _scan_and_plan(folder, settings, logger))
    items = _review_items(entries, folder)
    if not items:
        logger.info("No hay lecturas dudosas ni colisiones que revisar.")
        return 0
    outputs = montage.build_montages_chunked(items, folder, "verify_review", settings)
    logger.info("Montajes de revisión: %s", ", ".join(str(path) for path in outputs))
    return 0


def cmd_undo(folder_arg: str, settings: Settings, logger: logging.Logger,
             execute: bool) -> int:
    """Revierte el último renombrado usando el registro guardado."""
    folder = validator.validate_folder(folder_arg)
    pairs = renamer.undo_from_log(folder, settings, execute)
    if execute:
        logger.info("Renombrado revertido: %d archivos.", len(pairs))
    else:
        logger.warning("[SIMULACIÓN] %d se revertirían. Añade --execute.", len(pairs))
    return 0
