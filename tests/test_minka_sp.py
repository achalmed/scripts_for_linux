# tests/test_minka_sp.py — las tareas de Minka en Super Productivity (script_registro_tiempo, orden `minka`).
"""Pruebas de la orden `minka` de script_registro_tiempo.

La parte pura (`lib/minka.py::plan`) con tareas fabricadas, y de punta a punta con dos servidores de mentira: uno que
responde como `GET /api/tareas/mias.json` de Minka y otro como la API REST local de Super Productivity 18.10. La
dirección llega por un .env temporal (`MINKA_ENV`), así nada lee ni toca los datos del autor ni los del despacho.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

REPO = Path(__file__).resolve().parent.parent
SUITE = REPO / "script_registro_tiempo"
sys.path.insert(0, str(SUITE))
for _m in [m for m in sys.modules if m in ("lib", "config") or m.startswith("lib.")]:
    del sys.modules[_m]

from lib import minka  # noqa: E402

TOKEN = "s" * 43


def f(id_, titulo=None, estado="por_hacer", dia=None, en=None, actualizado="2026-10-25T10:00:00-05:00"):
    cerrada = estado in ("hecha", "cancelada")
    return {"id": id_, "titulo": titulo or f"Informe {id_}", "estado": estado,
            "estado_nombre": {"por_hacer": "Por hacer", "en_curso": "En curso", "hecha": "Hecha",
                              "cancelada": "Cancelada"}[estado],
            "cerrada": cerrada, "prioridad": "normal", "vence_dia": dia, "vence_en": en, "enlace": f"/tareas?tarea={id_}",
            "actualizado_en": actualizado, "cerrada_en": actualizado if cerrada else None}


def feed(*tareas, completo=True):
    return {"version": 1, "zona": "America/Lima", "completo": completo, "cerradas_dias": 30, "tareas": list(tareas)}


# --------------------------------------------------------------------------- dirección

def test_conexion_desde_la_direccion_del_calendario():
    base, token = minka.conexion({"MINKA_SUSCRIPCION": f"https://ejemplo.test/qillqa/api/agenda.ics?token={TOKEN}&solo_mias=true"})
    assert (base, token) == ("https://ejemplo.test/qillqa", TOKEN)
    assert minka.conexion({"MINKA_URL": "http://127.0.0.1:8032/", "MINKA_TOKEN": TOKEN}) == ("http://127.0.0.1:8032", TOKEN)
    assert minka.conexion({}) is None
    with pytest.raises(ValueError):
        minka.conexion({"MINKA_SUSCRIPCION": "https://ejemplo.test/otra/cosa?token=x"})


def test_leer_env(tmp_path):
    ruta = tmp_path / ".env"
    ruta.write_text("# comentario\nMINKA_SUSCRIPCION='https://ejemplo.test/api/agenda.ics?token=abc'\n\nSIN_IGUAL\n")
    assert minka.leer_env(ruta) == {"MINKA_SUSCRIPCION": "https://ejemplo.test/api/agenda.ics?token=abc"}
    assert minka.leer_env(tmp_path / "no-existe") == {}


# --------------------------------------------------------------------------- plan

def test_plan_crea_las_abiertas_con_su_plazo_y_no_las_cerradas():
    p = minka.plan(feed(f(1, dia="2026-10-28"), f(2, en="2026-10-29T15:00:00-05:00"), f(3), f(4, estado="hecha")),
                   [], [], "PT")
    por_titulo = {c["title"]: c for c in p["crear"]}
    assert sorted(por_titulo) == ["Informe 1", "Informe 2", "Informe 3"]
    assert por_titulo["Informe 1"]["dueDay"] == "2026-10-28" and "dueWithTime" not in por_titulo["Informe 1"]
    assert por_titulo["Informe 2"]["dueWithTime"] == 1793304000000 and "dueDay" not in por_titulo["Informe 2"]
    assert "dueDay" not in por_titulo["Informe 3"] and por_titulo["Informe 3"]["projectId"] == "PT"
    notas = por_titulo["Informe 1"]["notes"]
    assert minka.MARCA + "1" in notas and "Plazo: 2026-10-28" in notas and "Por hacer" in notas
    assert "/tareas?tarea=" not in notas and "http" not in notas   # ni el servidor del despacho ni enlaces


def _en_sp(f_, sid="t1", **extra):
    return {"id": sid, "title": f_["titulo"], "notes": minka.notas(f_), "isDone": False, "projectId": "PT",
            **minka.campos_plazo(f_), **extra}


def test_plan_no_repite_y_cierra_lo_cerrado():
    abierta = f(1, dia="2026-10-28")
    assert minka.plan(feed(abierta), [_en_sp(abierta)], [], "PT") == {"crear": [], "cambiar": [], "avisos": []}
    cerrada = f(1, estado="hecha", dia="2026-10-28")
    (tid, cambios, _), = minka.plan(feed(cerrada), [_en_sp(abierta)], [], "PT")["cambiar"]
    assert tid == "t1" and cambios["isDone"] is True and "Hecha" in cambios["notes"]
    # Ya archivada en SP: nada que hacer.
    assert minka.plan(feed(cerrada), [], [_en_sp(cerrada, isDone=True)], "PT")["crear"] == []


def test_plan_titulo_estado_y_plazo_cambiados_en_minka():
    antes = f(1, dia="2026-10-28")
    nota_propia = "Llamar antes a la oficina.\n\n" + minka.notas(antes)
    t = _en_sp(antes, notes=nota_propia)
    ahora = f(1, titulo="Informe final", estado="en_curso", en="2026-10-30T09:30:00-05:00")
    (_, cambios, _), = minka.plan(feed(ahora), [t], [], "PT")["cambiar"]
    assert cambios["title"] == "Informe final"
    assert cambios["dueWithTime"] == 1793370600000 and cambios["dueDay"] is None
    assert cambios["notes"].startswith("Llamar antes a la oficina.\n\n" + minka.SEPARADOR)   # lo del autor se queda
    assert "En curso" in cambios["notes"] and "Plazo: 2026-10-30 09:30" in cambios["notes"]
    # Si Minka quita el plazo, también se quita en SP.
    (_, cambios, _), = minka.plan(feed(f(1)), [_en_sp(antes)], [], "PT")["cambiar"]
    assert cambios["dueDay"] is None and "Plazo:" not in cambios["notes"]


def test_plan_respeta_lo_replanificado_en_sp():
    """Si el autor movió la tarea a otro día en SP y el plazo de Minka no cambió, no se le devuelve al plazo."""
    f_ = f(1, dia="2026-10-28")
    t = _en_sp(f_, dueDay="2026-10-27")
    assert minka.plan(feed(f_), [t], [], "PT")["cambiar"] == []


def test_plan_hecha_en_sp_y_abierta_en_minka():
    f_ = f(1, actualizado="2026-10-25T10:00:00-05:00")   # 15:00 UTC
    hecha_despues = _en_sp(f_, isDone=True, doneOn=1792944000000)   # 2026-10-25 16:00 UTC
    p = minka.plan(feed(f_), [hecha_despues], [], "PT")
    assert p["cambiar"] == [] and "ciérrela allá" in p["avisos"][0]
    hecha_antes = _en_sp(f_, isDone=True, doneOn=1792936800000)    # 14:00 UTC: Minka la reabrió después
    (_, cambios, _), = minka.plan(feed(f_), [hecha_antes], [], "PT")["cambiar"]
    assert cambios == {"isDone": False}


def test_plan_lo_que_ya_no_es_suyo_se_marca_hecho_si_la_lista_es_completa():
    t = _en_sp(f(9))
    p = minka.plan(feed(f(1)), [t], [], "PT")
    assert ("t1", {"isDone": True}, "Informe 9") in p["cambiar"] and "ya no está" in p["avisos"][0]
    assert minka.plan(feed(f(1), completo=False), [t], [], "PT")["cambiar"] == []


def test_recoger_no_lleva_al_vault_los_titulos_del_despacho(tmp_path):
    from lib import superproductivity
    hoy_ms = 1792936800000
    estado = {"task": {"entities": {
        "a": {"id": "a", "title": "Informe 1", "isDone": True, "doneOn": hoy_ms, "notes": minka.notas(f(1)), "tagIds": []},
        "b": {"id": "b", "title": "Leer a Hayek", "isDone": True, "doneOn": hoy_ms, "notes": "", "tagIds": []},
    }}, "project": {"entities": {}}, "tag": {"entities": {}}}
    ruta = tmp_path / "sync-data.json"
    ruta.write_text(json.dumps(estado), encoding="utf-8")
    dias = superproductivity.leer(ruta, "2026-10-01", "Registro automático")
    hechas = [h for d in dias.values() for h in d["hechas"]]
    assert sorted(hechas) == sorted([superproductivity.TAREA_MINKA, "Leer a Hayek"])


# --------------------------------------------------------------------------- de punta a punta

def _servidor(manejador):
    s = ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


@pytest.fixture
def servidores():
    estado = {"feed": feed(f(1, dia="2026-10-28"), f(2)), "sp": [], "proyectos": [{"id": "PT", "title": "Trabajo"}],
              "cabeceras": []}

    class Minka(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            estado["cabeceras"].append(self.headers.get("X-Minka-Token"))
            ok = urlsplit(self.path).path == "/api/tareas/mias.json" and self.headers.get("X-Minka-Token") == TOKEN
            self.send_response(200 if ok else 401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(estado["feed"] if ok else {"detail": "no"}).encode())

    class SP(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _responder(self, codigo, datos):
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "data": datos}).encode())

        def _cuerpo(self):
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")

        def do_GET(self):
            ruta = urlsplit(self.path).path
            if ruta == "/tasks":
                return self._responder(200, estado["sp"])
            if ruta == "/projects":
                return self._responder(200, estado["proyectos"])
            if ruta == "/tags":
                return self._responder(200, [])
            self._responder(404, None)

        def do_POST(self):
            t = {"id": f"t{len(estado['sp']) + 1}", "isDone": False, **self._cuerpo()}
            estado["sp"].append(t)
            self._responder(201, t)

        def do_PATCH(self):
            t = next(x for x in estado["sp"] if x["id"] == self.path.rsplit("/", 1)[-1])
            t.update(self._cuerpo())
            self._responder(200, t)

    m, s = _servidor(Minka), _servidor(SP)
    yield f"http://127.0.0.1:{m.server_port}", f"http://127.0.0.1:{s.server_port}", estado
    m.shutdown()
    s.shutdown()


def _entorno(tmp_path, url_minka, url_sp, token=TOKEN):
    tareas = tmp_path / "tareas"
    tareas.mkdir(exist_ok=True)
    (tareas / "registro-tiempo.yml").write_text("rutina: []\n", encoding="utf-8")
    env_minka = tmp_path / "minka.env"
    env_minka.write_text(f"MINKA_SUSCRIPCION={url_minka}/api/agenda.ics?token={token}&solo_mias=true\n")
    return dict(os.environ, TASKS_DIR=str(tareas), XDG_STATE_HOME=str(tmp_path / "estado"), MINKA_ENV=str(env_minka),
                SP_REST_URL=url_sp, NO_COLOR="1", PYTHONDONTWRITEBYTECODE="1")


def _correr(env, *args):
    return subprocess.run([sys.executable, str(SUITE / "main.py"), *args], env=env, capture_output=True, text=True,
                          timeout=60)


def test_minka_simula_aplica_y_cierra(tmp_path, servidores):
    url_minka, url_sp, estado = servidores
    env = _entorno(tmp_path, url_minka, url_sp)
    r = _correr(env, "minka")
    assert r.returncode == 0, r.stderr
    assert estado["sp"] == [] and "[SIMULACIÓN] crearía «Informe 1» (Plazo: 2026-10-28)" in r.stderr
    assert TOKEN not in r.stderr and estado["cabeceras"] == [TOKEN]   # el token va en la cabecera, no al registro
    for _ in range(2):   # la segunda pasada no duplica
        r = _correr(env, "minka", "--aplicar")
        assert r.returncode == 0, r.stderr
    assert [(t["title"], t["projectId"], t.get("dueDay")) for t in estado["sp"]] == [
        ("Informe 1", "PT", "2026-10-28"), ("Informe 2", "PT", None)]
    # Se cierra en Minka → hecha en SP.
    estado["feed"] = feed(f(1, estado="hecha", dia="2026-10-28"), f(2))
    r = _correr(env, "minka", "--aplicar")
    assert r.returncode == 0, r.stderr
    assert [t["isDone"] for t in estado["sp"]] == [True, False]


def test_minka_desde_el_timer_calla_lo_que_falta(tmp_path, servidores):
    url_minka, url_sp, estado = servidores
    env = _entorno(tmp_path, url_minka, url_sp, token="revocado-" + "x" * 30)
    r = _correr(env, "minka", "--desde-timer")
    assert r.returncode == 0 and "WARNING" not in r.stderr and estado["sp"] == []
    r = _correr(env, "minka", "--aplicar")
    assert r.returncode != 0 and "revocó" in r.stderr
    env = dict(env, MINKA_ENV=str(tmp_path / "no-existe.env"))
    assert _correr(env, "minka", "--desde-timer").returncode == 0
    assert _correr(env, "minka").returncode == 2
