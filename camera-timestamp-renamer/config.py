"""Configuración central de camera-timestamp-renamer.

TODO valor ajustable vive aquí. Edita este archivo para cambiar el
comportamiento por defecto sin tocar la lógica en `lib/`. Cualquier campo
puede además sobreescribirse por CLI (ver `lib/cli.py`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

APP_NAME = "camera-timestamp-renamer"
VERSION = "1.1.0"

# --- Códigos de salida del proyecto (126/127 los reserva el shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION = 4
EXIT_DEPENDENCY = 5


@dataclass
class Settings:
    """Parámetros de ejecución. Instancia picklable para multiprocessing.

    Las fracciones de recorte se expresan en 0..1 relativas al tamaño de
    cada imagen, de modo que funcionan igual en cualquier resolución.
    """

    # --- Región de análisis: DÓNDE se lee la marca (esquina, franja...) ---
    crop_left_frac: float = 0.0
    crop_top_frac: float = 0.0
    crop_width_frac: float = 0.40
    crop_height_frac: float = 0.075
    upscale_factor: int = 4  # ampliar el recorte ayuda al OCR

    # --- OCR: barrido de umbrales y opciones de tesseract ---
    bright_thresholds: list = field(  # texto blanco sobre fondo oscuro
        default_factory=lambda: [140, 160, 180, 200, 220, 235])
    dark_thresholds: list = field(  # respaldo: contorno oscuro (sobreexpuestas)
        default_factory=lambda: [70, 100, 130, 160])
    tesseract_psms: list = field(default_factory=lambda: [7, 6])
    tesseract_whitelist: str = "0123456789-: "
    tesseract_lang: Optional[str] = None

    # --- Interpretación y validación del texto reconocido ---
    timestamp_regex: str = (
        r"(\d{4})-(\d{2})-(\d{2})[^\d]*(\d{2})[^\d]*(\d{2})[^\d]*(\d{2})")
    year_min: int = 2015
    year_max: int = 2035
    confident_min_votes: int = 3  # votos mínimos para marcar "confident"

    # --- Archivos que se consideran fotos ---
    image_extensions: tuple = (".jpg", ".jpeg", ".png")

    # --- Videos: se extrae un fotograma y se le aplica el MISMO OCR ---
    video_extensions: tuple = (".mp4", ".mov", ".avi", ".mkv")
    ffmpeg_binary: str = "ffmpeg"
    # Segundos a probar para sacar el fotograma; el primero legible gana. El
    # fotograma en "0" contiene la hora de INICIO de la grabación (la que
    # queremos); los siguientes son respaldo si el primero es negro/transición.
    ffmpeg_frame_times: list = field(default_factory=lambda: ["0", "1", "2"])

    # --- Ejecución ---
    workers: int = 0  # 0 => usar todos los núcleos
    omp_thread_limit: str = "1"  # evita que tesseract sature los núcleos
    progress_every: int = 20
    limit: int = 0  # 0 => sin límite (útil para pruebas rápidas)

    # --- Nombres de salida (se crean dentro de la carpeta objetivo) ---
    plan_csv_name: str = "rename_plan.csv"
    analysis_json_name: str = "analysis.json"
    log_csv_name: str = "_rename_log.csv"
    undo_script_name: str = "_undo_rename.sh"
    temp_prefix: str = ".__ren_tmp_"
    montage_rows_per_image: int = 28


def default_settings() -> Settings:
    """Devuelve la configuración por defecto (punto único de creación)."""
    return Settings()
