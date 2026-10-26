"""script_registro_tiempo/lib/validator.py — el archivo del usuario y el entorno, antes de procesar."""
from __future__ import annotations

from pathlib import Path

import yaml

CLAVES = ("categorias", "fuentes_a_sp", "metas_semanales_horas", "limites_semanales_horas", "estructura_sp",
          "navegadores_regex")


def cargar_usuario(ruta: Path) -> tuple[dict, list[str]]:
    """(configuración, avisos). Sin archivo, configuración vacía: la pasada mide y no clasifica."""
    if not ruta.is_file():
        return {}, [f"no existe {ruta}: se mide sin categorías ni metas (copia el ejemplo del README)"]
    try:
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"{ruta} no es YAML válido: {e}") from e
    if not isinstance(datos, dict):
        raise ValueError(f"{ruta} debe ser un mapa con las claves {', '.join(CLAVES)}")
    avisos = [f"clave desconocida en {ruta.name}: {k}" for k in datos if k not in CLAVES]
    for nombre, regla in (datos.get("categorias") or {}).items():
        if not isinstance(regla, dict):
            raise ValueError(f"categoría «{nombre}»: debe ser un mapa (dominios, apps, titulos, a_sp, tarea_sp)")
        if regla.get("a_sp") and not regla.get("tarea_sp"):
            avisos.append(f"categoría «{nombre}» va a SP sin tarea_sp: se usará su nombre")
    return datos, avisos
