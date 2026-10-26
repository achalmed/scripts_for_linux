"""script_registro_tiempo/lib/instalar.py — el .zip del plugin de Super Productivity y el timer de usuario.

El plugin se instala desde la propia aplicación (Ajustes → Plugins → subir .zip): aquí solo se empaqueta. El timer
se renderiza desde `systemd/*.in` con la ruta real de la suite (la carpeta de inicio no se escribe a mano en la
unidad) y se activa con systemctl --user.
"""
from __future__ import annotations

import os
import subprocess
import zipfile
from pathlib import Path

SUITE = Path(__file__).resolve().parent.parent
PLUGIN = SUITE / "plugin-sp"
SYSTEMD = SUITE / "systemd"
ARCHIVOS_PLUGIN = ("manifest.json", "plugin.js", "index.html", "icon.svg")
UNIDADES = ("registro-tiempo.service", "registro-tiempo.timer")


def empaquetar(destino: Path, aplicar: bool) -> list[str]:
    faltan = [a for a in ARCHIVOS_PLUGIN if not (PLUGIN / a).is_file()]
    if faltan:
        raise FileNotFoundError(f"faltan en plugin-sp/: {', '.join(faltan)}")
    if aplicar:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for a in ARCHIVOS_PLUGIN:
                z.write(PLUGIN / a, a)   # en la raíz del zip, como lo espera Super Productivity
    return list(ARCHIVOS_PLUGIN)


def carpeta_unidades() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "systemd" / "user"


def renderizar() -> dict[str, str]:
    return {u: (SYSTEMD / f"{u}.in").read_text(encoding="utf-8").replace("@SUITE@", str(SUITE)) for u in UNIDADES}


def instalar_timer(aplicar: bool) -> list[str]:
    """Escribe las unidades y activa el timer; devuelve las rutas (que escribiría, si simula)."""
    destino = carpeta_unidades()
    unidades = renderizar()
    if aplicar:
        destino.mkdir(parents=True, exist_ok=True)
        for nombre, texto in unidades.items():
            (destino / nombre).write_text(texto, encoding="utf-8")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", "registro-tiempo.timer"], check=True)
    return [str(destino / n) for n in unidades]
