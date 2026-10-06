# tests/test_simulacion.py — cada suite que escribe, en simulación sobre un HOME temporal, no escribe nada (ola 4, L1b).
"""Prueba de simulación de las suites de scripts_for_linux.

Para cada suite que escribe (``escribe_en`` distinto de ``[ninguno]`` en su ``suite.yml``) y admite
simulación (``--dry-run``, ``--simulate``, ``-d``, ``-n``, ``--check`` o «sin ``--execute``»), la
ejecuta sobre un ``HOME`` temporal y una carpeta de trabajo temporal con entradas mínimas, y compara
un listado con tamaño y mtime de la carpeta temporal y del propio repo antes y después: nada se crea,
nada se modifica, nada se borra.

Las suites que necesitan red, GUI o hardware se marcan ``skip`` con su motivo o se
prueban solo con ``--help`` (que tampoco debe escribir).

Se corre con ``tests/run.sh`` (fija ``--basetemp`` fuera de /tmp y ``-p no:cacheprovider``).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
FS = REPO / "scripts_filesystem_studio" / "backend"
GIT = REPO / "scripts_git_studio" / "backend"

# Carpetas que no forman parte del contenido que una suite podría tocar: el propio git y los
# cachés que crea pytest al importar este archivo.
IGNORAR = {".git", ".pytest_cache"}


def instantanea(raiz: Path) -> dict[str, tuple[int, int, str]]:
    """{ruta relativa: (tamaño, mtime_ns, tipo)} de todo lo que cuelga de ``raiz`` (sin seguir enlaces)."""
    foto: dict[str, tuple[int, int, str]] = {}
    for dirpath, dirnames, filenames in os.walk(raiz, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR]
        for nombre in dirnames + filenames:
            p = Path(dirpath) / nombre
            st = p.lstat()
            tipo = "l" if p.is_symlink() else ("d" if p.is_dir() else "f")
            # el mtime de una carpeta cambia si se crea o borra algo dentro: también cuenta
            foto[str(p.relative_to(raiz))] = (0 if tipo == "d" else st.st_size, st.st_mtime_ns, tipo)
    return foto


def diferencias(antes: dict, despues: dict) -> list[str]:
    nuevas = sorted(set(despues) - set(antes))
    borradas = sorted(set(antes) - set(despues))
    cambiadas = sorted(k for k in set(antes) & set(despues) if antes[k] != despues[k])
    return [f"+ {k}" for k in nuevas] + [f"- {k}" for k in borradas] + [f"~ {k}" for k in cambiadas]


@pytest.fixture
def entorno(tmp_path: Path):
    """HOME, XDG_* y carpeta de trabajo temporales; devuelve (home, trabajo, env)."""
    home = tmp_path / "home"
    trabajo = tmp_path / "trabajo"
    for d in (home, trabajo, home / ".config", home / ".cache", home / ".local" / "share", home / ".local" / "state"):
        d.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("LOG_FILE", "SGDP_USB", "GITHUB_TOKEN"))}
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_STATE_HOME": str(home / ".local" / "state"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "TERM": env.get("TERM") or "dumb",
        "NO_COLOR": "1",
        "LC_ALL": "C.UTF-8",
    })
    return home, trabajo, env


def correr_sin_escribir(cmd: list[str], raiz_tmp: Path, cwd: Path, env: dict, *, rc_esperado=(0,), entrada="",
                        timeout=120) -> subprocess.CompletedProcess:
    """Corre ``cmd`` y falla si cambió algo en ``raiz_tmp`` o en el repo, o si el código de salida no es el esperado."""
    antes_tmp, antes_repo = instantanea(raiz_tmp), instantanea(REPO)
    r = subprocess.run(cmd, cwd=cwd, env=env, input=entrada, capture_output=True, text=True, timeout=timeout)
    salida = f"\n--- stdout ---\n{r.stdout[-3000:]}\n--- stderr ---\n{r.stderr[-3000:]}"
    cambios = diferencias(antes_tmp, instantanea(raiz_tmp)) + [f"repo: {c}" for c in diferencias(antes_repo, instantanea(REPO))]
    assert not cambios, "la simulación escribió:\n" + "\n".join(cambios) + salida
    assert r.returncode in rc_esperado, f"código de salida {r.returncode}{salida}"
    return r


def requiere(*binarios: str):
    falta = [b for b in binarios if shutil.which(b) is None]
    return pytest.mark.skipif(bool(falta), reason=f"falta en PATH: {', '.join(falta)}")


def requiere_modulos(*modulos: str):
    import importlib.util
    falta = [m for m in modulos if importlib.util.find_spec(m) is None]
    return pytest.mark.skipif(bool(falta), reason=f"faltan módulos de Python: {', '.join(falta)}")


PY = sys.executable


# --------------------------------------------------------------------------- multimedia

@requiere("ffmpeg")
def test_audio_converter_dry_run(entorno):
    home, trabajo, env = entorno
    (trabajo / "notas").mkdir()
    (trabajo / "notas" / "PTT-prueba.opus").write_bytes(b"OggS" + b"\0" * 60)
    correr_sin_escribir([PY, str(REPO / "script_audio_converter" / "main.py"), "notas", "-r", "--dry-run"],
                        home.parent, trabajo, env)


def test_whisper_transcriber_dry_run(entorno):
    home, trabajo, env = entorno
    (trabajo / "entrevista.mp3").write_bytes(b"ID3" + b"\0" * 60)
    correr_sin_escribir([PY, str(REPO / "script_whisper_transcriber" / "main.py"), "entrevista.mp3",
                         "-l", "es", "-m", "tiny", "--dry-run"], home.parent, trabajo, env)


def test_video_downloader_help(entorno):
    """La simulación (``--simulate <url>``) consulta la red con yt-dlp: aquí solo ``--help``."""
    home, trabajo, env = entorno
    correr_sin_escribir(["bash", str(REPO / "script_video_downloader" / "main.sh"), "--help"],
                        home.parent, trabajo, env)


@pytest.mark.skip(reason="red: --simulate <url> consulta el sitio con yt-dlp; ver test_video_downloader_help")
def test_video_downloader_simulate():
    pass


@requiere("exiftool")
@requiere_modulos("PIL", "numpy")
@pytest.mark.parametrize("sub", ["apply", "undo", "fix-names", "embed-date"])
def test_photo_metadata_sin_execute(entorno, sub):
    """Los subcomandos que escriben simulan si no se les da ``--execute``."""
    home, trabajo, env = entorno
    fotos = trabajo / "fotos"
    fotos.mkdir()
    (fotos / "IMG_0001.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    (fotos / "VID_0001.mp4").write_bytes(b"\0" * 32)
    (fotos / "20260101_120000.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    # registro de un renombrado anterior, para que `undo` tenga algo que revertir
    (fotos / "_rename_log.csv").write_text("old,new\nTapo_0002.jpg,20260101_120000.jpg\n", encoding="utf-8")
    correr_sin_escribir([PY, str(REPO / "scripts_photo_metadata_suite" / "main.py"), sub, "fotos"],
                        home.parent, trabajo, env)


@pytest.mark.skip(reason="datos externos: sync-digikam lee la base de digiKam del usuario (aun en copia)")
def test_photo_metadata_sync_digikam():
    pass


# --------------------------------------------------------------------------- sistema de archivos

def test_create_folders_batch_dry_run(entorno):
    home, trabajo, env = entorno
    (trabajo / "lista.txt").write_text("uno\ndos/tres\n# comentario\n", encoding="utf-8")
    (trabajo / "base").mkdir()
    correr_sin_escribir(["bash", str(FS / "script_create_folders_batch" / "main.sh"), "-d", "-y", "--no-color",
                         "-f", "lista.txt", "-p", "base"], home.parent, trabajo, env)


@pytest.mark.xfail(strict=True, reason="pendiente en estado.md: con -d y un -p inexistente, mkdir -p crea la base")
def test_create_folders_batch_dry_run_base_inexistente(entorno):
    home, trabajo, env = entorno
    (trabajo / "lista.txt").write_text("uno\n", encoding="utf-8")
    correr_sin_escribir(["bash", str(FS / "script_create_folders_batch" / "main.sh"), "-d", "-y", "--no-color",
                         "-f", "lista.txt", "-p", "no-existe"], home.parent, trabajo, env)


def test_hardlinks_creator_dry_run(entorno):
    home, trabajo, env = entorno
    for sitio in ("a", "b", "c"):
        (trabajo / "arbol" / sitio).mkdir(parents=True)
        (trabajo / "arbol" / sitio / "_metadata.yml").write_text("igual: sí\n", encoding="utf-8")
    correr_sin_escribir([PY, str(FS / "script_hardlinks-creator" / "main.py"), "_metadata.yml",
                         "-d", str(trabajo / "arbol"), "--auto", "--dry-run", "--no-color"],
                        home.parent, trabajo, env)


def test_hardlinks_detector_solo_lee(entorno):
    """No tiene simulación: solo escribe lo que se le pide con ``-o`` o ``--report``; sin ellas, lee."""
    home, trabajo, env = entorno
    (trabajo / "arbol").mkdir()
    (trabajo / "arbol" / "x.txt").write_text("x\n", encoding="utf-8")
    os.link(trabajo / "arbol" / "x.txt", trabajo / "arbol" / "y.txt")
    for formato in ("tree", "csv", "json"):
        correr_sin_escribir(["bash", str(FS / "script_hardlinks-detector" / "main.sh"), "arbol", "-f", formato,
                             "--no-color"], home.parent, trabajo, env)


@requiere("tree")
def test_proyect_tree_dry_run(entorno):
    home, trabajo, env = entorno
    (trabajo / "proyecto" / "src").mkdir(parents=True)
    (trabajo / "proyecto" / "src" / "a.py").write_text("print(1)\n", encoding="utf-8")
    for formato in ("txt", "md", "json"):
        correr_sin_escribir(["bash", str(FS / "script_proyect_tree" / "main.sh"), "--dry-run", "-t", ".",
                             "-f", formato, "--no-color"], home.parent, trabajo / "proyecto", env)


def test_sync_usb_dry_run(entorno):
    """Dos carpetas temporales hacen de laptop y de USB; la clave es de prueba y llega por el entorno."""
    home, trabajo, env = entorno
    local, usb = trabajo / "local", trabajo / "usb"
    (local / "SGDP" / "2026").mkdir(parents=True)
    (local / "SGDP" / "2026" / "oficio.txt").write_text("local\n", encoding="utf-8")
    (usb / "SGDP").mkdir(parents=True)
    (usb / "SGDP" / "otro.txt").write_text("usb\n", encoding="utf-8")
    env = dict(env, SGDP_USB_CLAVE="clave-de-prueba", SGDP_USB_CLAVE_ESPERADA="clave-de-prueba")
    correr_sin_escribir([PY, str(REPO / "script_sync_usb" / "main.py"), "--local", str(local / "SGDP"),
                         "--usb", str(usb), "--dry-run"], home.parent, trabajo, env)


# --------------------------------------------------------------------------- git

def _repo_git(ruta: Path, env: dict) -> None:
    ruta.mkdir(parents=True)
    g = ["git", "-C", str(ruta), "-c", "user.name=prueba", "-c", "user.email=prueba@example.invalid"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(ruta)], check=True, env=env)
    (ruta / "a.txt").write_text("uno\n", encoding="utf-8")
    subprocess.run(g + ["add", "a.txt"], check=True, env=env)
    subprocess.run(g + ["commit", "-q", "-m", "inicio"], check=True, env=env)
    (ruta / "a.txt").write_text("dos\n", encoding="utf-8")            # cambio sin confirmar


@requiere("git")
def test_git_sync_respos_check(entorno):
    """``sync.sh --check`` sobre un repo temporal sin remoto con un cambio sin confirmar: no commitea ni toca nada."""
    home, trabajo, env = entorno
    _repo_git(trabajo / "repos" / "uno", env)
    config = trabajo / "repos-config.yml"
    config.write_text(
        f"base_directory: {trabajo / 'repos'}\n"
        "default_commit_message: chore: prueba\n"
        "repositories:\n"
        "  - name: uno\n"
        "    branch: main\n"
        "    enabled: true\n",
        encoding="utf-8")
    r = correr_sin_escribir(["bash", str(GIT / "script_git_sync_respos" / "sync.sh"), "--check", "--config",
                             str(config)], home.parent, trabajo, env)
    assert "uno" in r.stdout + r.stderr


@requiere("git")
def test_git_download_respos_dry_run(entorno):
    """``-n`` en modo ``list`` (sin API): ni clona ni crea la carpeta destino."""
    home, trabajo, env = entorno
    correr_sin_escribir(["bash", str(GIT / "script_git_download_respos" / "main.sh"), "-u", "prueba", "-m", "list",
                         "-r", "uno,dos", "-n", "-o", str(trabajo / "destino")], home.parent, trabajo, env)


# --------------------------------------------------------------------------- GUI

@pytest.mark.skip(reason="GUI (PySide6): filesystem_studio y git_studio escriben por sus backends, probados arriba")
def test_gui_studios():
    pass
