"""Escaneo paralelo de una carpeta de imágenes con reporte de progreso."""
from __future__ import annotations

import os
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Optional

from config import Settings
from lib.ocr import OcrResult, extract_timestamp


def find_images(folder: Path, settings: Settings) -> list[Path]:
    """Lista los archivos de imagen de la carpeta (orden determinista)."""
    extensions = set(settings.image_extensions)
    images = [entry for entry in folder.iterdir()
              if entry.is_file() and entry.suffix.lower() in extensions]
    images.sort()
    return images[:settings.limit] if settings.limit else images


def _worker(task: tuple) -> OcrResult:
    """Procesa una imagen aislando fallos para no abortar todo el lote."""
    path, settings = task
    try:
        return extract_timestamp(path, settings)
    except (OSError, ValueError) as exc:
        # Una imagen corrupta o ilegible no debe detener el escaneo completo.
        return OcrResult(str(path), None, "error", {"error": str(exc)})


def scan_folder(folder: Path, settings: Settings,
                on_progress: Optional[Callable[[int, int], None]] = None
                ) -> list[OcrResult]:
    """Escanea todas las imágenes en paralelo y devuelve un resultado por foto.

    Args:
        folder: Carpeta a escanear.
        settings: Configuración de ejecución.
        on_progress: Callback opcional (procesadas, total) para mostrar avance.

    Returns:
        Lista de OcrResult, una por imagen encontrada.
    """
    # Un solo hilo por proceso de tesseract evita saturar los núcleos
    # (cada worker ya usa un núcleo); sin esto el lote se vuelve ~10x lento.
    os.environ["OMP_THREAD_LIMIT"] = settings.omp_thread_limit
    images = find_images(folder, settings)
    total = len(images)
    workers = settings.workers or os.cpu_count() or 1
    results: list[OcrResult] = []
    with Pool(workers) as pool:
        tasks = ((path, settings) for path in images)
        for done, result in enumerate(
                pool.imap_unordered(_worker, tasks, chunksize=2), start=1):
            results.append(result)
            if on_progress and (done % settings.progress_every == 0 or done == total):
                on_progress(done, total)
    return results
