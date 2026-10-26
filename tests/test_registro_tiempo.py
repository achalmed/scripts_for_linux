# tests/test_registro_tiempo.py — la suite script_registro_tiempo sobre fuentes sintéticas, y su plugin con una API simulada.
"""Pruebas de script_registro_tiempo.

Cada fuente se fabrica en una carpeta temporal (base de KOReader, base de Zotero, sync-data.json de Super
Productivity comprimido como lo escribe la 18.10) y las rutas se pasan por las variables que respeta core/env.py, así
nada lee ni toca los datos del autor. El plugin se prueba con Node sobre un PluginAPI de mentira.
"""
from __future__ import annotations

import base64
import gzip
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SUITE = REPO / "script_registro_tiempo"
sys.path.insert(0, str(SUITE))
# Cada suite tiene su paquete `lib` y su `config`: si otra prueba ya importó los suyos, se apartan para cargar estos.
for _m in [m for m in sys.modules if m in ("lib", "config") or m.startswith("lib.")]:
    del sys.modules[_m]

from lib import clasificar, informe, koreader, plan, registro, superproductivity, zotero  # noqa: E402

HOY = date(2026, 10, 25)


def _ms(dia: str, hora: int) -> int:
    return int(datetime.fromisoformat(f"{dia}T{hora:02d}:00").timestamp() * 1000)


def fabricar_koreader(ruta: Path) -> None:
    con = sqlite3.connect(ruta)
    con.executescript("CREATE TABLE book (id INTEGER PRIMARY KEY, title TEXT);"
                      "CREATE TABLE page_stat_data (id_book INT, page INT, start_time INT, duration INT, total_pages INT);")
    con.execute("INSERT INTO book VALUES (1, 'Economía y sociedad')")
    for i in range(30):   # 30 páginas de 60 s el 24 de octubre a las 9:00
        con.execute("INSERT INTO page_stat_data VALUES (1, ?, ?, 60, 300)", (i, _ms("2026-10-24", 9) // 1000 + i * 60))
    con.commit()
    con.close()


def fabricar_zotero(ruta: Path, segundos: int) -> None:
    con = sqlite3.connect(ruta)
    con.executescript(
        "CREATE TABLE items (itemID INTEGER PRIMARY KEY, key TEXT);"
        "CREATE TABLE itemNotes (itemID INT, note TEXT);"
        "CREATE TABLE deletedItems (itemID INT);"
        "CREATE TABLE fields (fieldID INT, fieldName TEXT);"
        "CREATE TABLE itemData (itemID INT, fieldID INT, valueID INT);"
        "CREATE TABLE itemDataValues (valueID INT, value TEXT);")
    con.execute("INSERT INTO items VALUES (1, 'ABCD1234'), (2, 'NOTA0001')")
    con.execute("INSERT INTO fields VALUES (1, 'title')")
    con.execute("INSERT INTO itemDataValues VALUES (1, 'Pobreza y desigualdad')")
    con.execute("INSERT INTO itemData VALUES (1, 1, 1)")
    nota = ('<div class="zotero-note znv1">ABCD1234\n{"readingTime":{"page":3,"data":{"1":%d}}}</div>' % segundos)
    con.execute("INSERT INTO itemNotes VALUES (2, ?)", (nota,))
    con.commit()
    con.close()


def fabricar_sp(ruta: Path, comprimido: bool = True) -> None:
    estado = {
        "project": {"entities": {"P1": {"id": "P1", "title": "Tesis"}, "PR": {"id": "PR", "title": "Registro automático"}}},
        "tag": {"entities": {"T1": {"id": "T1", "title": "escritura"}}},
        "task": {"entities": {
            "madre": {"id": "madre", "title": "Capítulo 2", "projectId": "P1", "subTaskIds": ["hija"],
                      "timeSpentOnDay": {"2026-10-24": 5400000}, "tagIds": []},
            "hija": {"id": "hija", "title": "Redactar 2.1", "projectId": "P1", "parentId": "madre", "subTaskIds": [],
                     "timeSpentOnDay": {"2026-10-24": 5400000}, "tagIds": ["T1", "TODAY"],
                     "isDone": True, "doneOn": _ms("2026-10-24", 18)},
            "externa": {"id": "externa", "title": "Lectura en KOReader", "projectId": "PR", "subTaskIds": [],
                        "timeSpentOnDay": {"2026-10-24": 1800000}, "tagIds": []}}},
    }
    datos = {"version": 2, "state": estado, "archiveYoung": {"task": {"entities": {}}}}
    texto = json.dumps(datos)
    if comprimido:
        texto = "pf_C2__" + base64.b64encode(gzip.compress(texto.encode())).decode()
    ruta.write_text(texto, encoding="utf-8")


USUARIO = {
    "categorias": {
        "redes": {"dominios": ["facebook.com"], "titulos": ["Facebook"], "a_sp": True, "tarea_sp": "Redes sociales",
                  "vigilar": True},
        "lectura": {"apps": ["okular", "calibre"]},
    },
    "fuentes_a_sp": {"koreader": "Lectura en KOReader", "zotero": "Lectura en Zotero"},
    "metas_semanales_horas": {"Tesis": 6, "Lectura": 1},
    "limites_semanales_horas": {"Redes sociales": 0.5},
    "estructura_sp": {"proyectos": [{"titulo": "Tesis"}], "archivar": ["Bloomberg"]},
}


# --------------------------------------------------------------------------- fuentes

def test_koreader_minutos_por_dia(tmp_path):
    ruta = tmp_path / "statistics.sqlite3"
    fabricar_koreader(ruta)
    dias = koreader.leer(ruta, "2026-10-20")
    assert dias["2026-10-24"]["total_min"] == 30
    assert dias["2026-10-24"]["libros"] == {"Economía y sociedad": 30}
    assert koreader.leer(ruta, "2026-10-25") == {}


def test_zotero_primera_pasada_no_inventa_y_luego_cuenta_lo_crecido(tmp_path):
    ruta = tmp_path / "zotero.sqlite"
    fabricar_zotero(ruta, 600)
    actual = zotero.acumulados(ruta)
    assert actual == {"ABCD1234": {"seg": 600, "titulo": "Pobreza y desigualdad"}}
    assert zotero.diferencia({}, actual) == {}
    assert zotero.diferencia({"items": {"ABCD1234": {"seg": 300}}}, actual) == {"Pobreza y desigualdad": 5.0}


def test_sp_cuenta_hojas_excluye_registro_y_etiqueta_hoy(tmp_path):
    ruta = tmp_path / "sync-data.json"
    fabricar_sp(ruta)
    dias = superproductivity.leer(ruta, "2026-10-20", "Registro automático")
    d = dias["2026-10-24"]
    assert d["total_min"] == 90                          # la madre no suma otra vez lo de su hija
    assert d["proyectos"] == {"Tesis": 90}               # lo importado de fuera no vuelve como trabajo de SP
    assert d["etiquetas"] == {"escritura": 90}
    assert d["hechas"] == ["Redactar 2.1"]


def test_sp_plano_y_cifrado(tmp_path):
    ruta = tmp_path / "sync-data.json"
    fabricar_sp(ruta, comprimido=False)
    assert superproductivity.leer(ruta, "2026-10-20", "Registro automático")["2026-10-24"]["total_min"] == 90
    ruta.write_text("pf_CE2__xxxx", encoding="utf-8")
    with pytest.raises(superproductivity.Cifrado):
        superproductivity.leer(ruta, "2026-10-20", "Registro automático")


def test_clasificar_reparte_navegador_por_dominio():
    dia = {"ventanas": [("zen", "Inicio — Zen", 50.0), ("okular", "libro.pdf", 20.0), ("konsole", "~", 5.0)],
           "dominios": {"m.facebook.com": 30.0, "duolingo.com": 20.0}}
    r = clasificar.resumir(dia, USUARIO["categorias"], "(?i)zen|firefox")
    assert r["categorias"] == {"redes": 30.0, "lectura": 20.0, "sin_clasificar": 25.0}
    sin_web = clasificar.resumir({"ventanas": [("zen", "Facebook — Zen", 40.0)]}, USUARIO["categorias"], "(?i)zen")
    assert sin_web["categorias"] == {"redes": 40.0}


# --------------------------------------------------------------------------- salidas

def test_para_sp_solo_lo_marcado():
    hist = {"2026-10-24": {"koreader": {"total_min": 30}, "zotero": {"total_min": 0.5},
                           "aw": {"categorias": {"redes": 12.0, "lectura": 40.0}}}}
    r = registro.para_sp(hist, USUARIO)
    assert r["tareas"] == {"Lectura en KOReader": {"2026-10-24": 1800000}, "Redes sociales": {"2026-10-24": 720000}}
    assert r["estructura"]["archivar"] == ["Bloomberg"]


def test_informe_semanal_tiene_resumen_y_metas():
    hist = {"2026-10-20": {"sp": {"total_min": 120, "proyectos": {"Tesis": 120}, "hechas": ["a", "b"]},
                           "koreader": {"total_min": 30, "libros": {"Economía y sociedad": 30}},
                           "aw": {"categorias": {"redes": 45}}}}
    texto = informe.semana(date(2026, 10, 19), hist, USUARIO, {"KOReader": "prueba"})
    assert texto.startswith("---\nid: 20261019000000\ntipo: tablero")
    assert "semana 2026-W43" in texto
    assert "| Tesis | 6 h | 2 h 00 | 33 % |" in texto
    assert "| Lectura | 1 h | 30 min | 50 % |" in texto
    assert "| Redes sociales | 0.5 h | 45 min | excedido |" in texto
    sin_aw = informe.semana(date(2026, 10, 19), {"2026-10-20": {"sp": {"total_min": 10}}}, USUARIO, {})
    assert "| Redes sociales | 0.5 h | — | sin medir |" in sin_aw
    assert "| Redes sociales |" in texto and "**2**" in texto


def test_historial_fusiona_sin_perder_otros_dias(tmp_path):
    registro.escribir_json(tmp_path / "2026-10.json", {"version": 1, "dias": {"2026-10-01": {"x": 1}}})
    meses = registro.fusionar(tmp_path, {"2026-10-24": {"y": 2}, "2026-11-01": {"z": 3}})
    assert meses[tmp_path / "2026-10.json"]["dias"] == {"2026-10-01": {"x": 1}, "2026-10-24": {"y": 2}}
    assert meses[tmp_path / "2026-11.json"]["dias"] == {"2026-11-01": {"z": 3}}


# --------------------------------------------------------------------------- planificar

@pytest.mark.parametrize("texto, esperado", [
    ("Preparar clase de microeconomía +docencia 45m @2026-07-08",
     dict(titulo="Preparar clase de microeconomía", proyecto="docencia", estimado_ms=2700000, dia="2026-07-08")),
    ("Leer paper de Acemoglu #lectura 30m", dict(titulo="Leer paper de Acemoglu", etiquetas=["lectura"], estimado_ms=1800000)),
    ("- [ ] Deep work: tesis #tesis #escritura @07:30 0m/1h30m",
     dict(titulo="Deep work: tesis", etiquetas=["tesis", "escritura"], estimado_ms=5400000, dia="2026-10-25", hora="07:30")),
    ("Revisar +Maestría-en-Gestión-Pública @mañana", dict(titulo="Revisar", proyecto="Maestría en Gestión Pública", dia="2026-10-26")),
])
def test_plan_linea(texto, esperado):
    t = plan.linea(texto, HOY)
    for campo, valor in esperado.items():
        assert getattr(t, campo) == valor, campo


def test_plan_subtareas_y_cuerpo():
    tareas = plan.leer("<!-- comentario -->\nTesis: capítulo 2 +tesis 2h\n  - Releer 2.1 25m\n  - Redactar 2.2 #nueva 1h\n", HOY)
    assert len(tareas) == 1 and [s.titulo for s in tareas[0].subtareas] == ["Releer 2.1", "Redactar 2.2"]
    cuerpo, avisos = plan.cuerpo(tareas[0].subtareas[1], {"tesis": "P1"}, {"escritura": "T1"})
    assert cuerpo == {"title": "Redactar 2.2", "timeEstimate": 3600000}
    assert avisos == ["«Redactar 2.2»: la etiqueta «nueva» no existe; se omite"]


# --------------------------------------------------------------------------- de punta a punta

@pytest.fixture
def entorno(tmp_path):
    tareas = tmp_path / "tareas"
    tareas.mkdir()
    fabricar_koreader(tmp_path / "statistics.sqlite3")
    fabricar_zotero(tmp_path / "zotero.sqlite", 600)
    fabricar_sp(tareas / "sync-data.json")
    import yaml
    (tareas / "registro-tiempo.yml").write_text(yaml.safe_dump(USUARIO, allow_unicode=True), encoding="utf-8")
    env = dict(os.environ, TASKS_DIR=str(tareas), KOREADER_STATS=str(tmp_path / "statistics.sqlite3"),
               ZOTERO_DB=str(tmp_path / "zotero.sqlite"), XDG_STATE_HOME=str(tmp_path / "estado"),
               XDG_CONFIG_HOME=str(tmp_path / "config"), NO_COLOR="1", PYTHONDONTWRITEBYTECODE="1")
    return tmp_path, tareas, env


def _correr(env, *args):
    return subprocess.run([sys.executable, str(SUITE / "main.py"), *args], env=env, capture_output=True, text=True,
                          timeout=60)


def test_recoger_simula_sin_escribir_y_aplica(entorno):
    raiz, tareas, env = entorno
    antes = sorted(p.name for p in tareas.rglob("*"))
    r = _correr(env, "recoger", "--dias", "3", "--sin-aw", "--sin-sp")
    assert r.returncode == 0, r.stderr
    assert sorted(p.name for p in tareas.rglob("*")) == antes and not (raiz / "estado").exists()
    assert "[SIMULACIÓN]" in r.stderr

    r = _correr(env, "recoger", "--dias", "3", "--sin-aw", "--sin-sp", "--aplicar")
    assert r.returncode == 0, r.stderr
    mes = json.loads((tareas / "registro" / "datos" / f"{date.today():%Y-%m}.json").read_text(encoding="utf-8"))
    assert (tareas / "registro" / "datos" / "zotero-instantanea.json").is_file()
    assert list((tareas / "registro").glob("*-semana.md"))
    para_sp = json.loads((raiz / "estado" / "registro-tiempo" / "para-sp.json").read_text(encoding="utf-8"))
    assert para_sp["proyecto"] == "Registro automático" and "dias" in mes


def test_plugin_zip_y_timer_simulan(entorno):
    raiz, _, env = entorno
    assert _correr(env, "plugin").returncode == 0 and not (raiz / "estado").exists()
    r = _correr(env, "plugin", "--aplicar")
    assert r.returncode == 0
    import zipfile
    with zipfile.ZipFile(raiz / "estado" / "registro-tiempo" / "registro-tiempo-sp.zip") as z:
        assert sorted(z.namelist()) == ["icon.svg", "index.html", "manifest.json", "plugin.js"]
    r = _correr(env, "timer")
    assert r.returncode == 0 and not (raiz / "config").exists()
    assert "registro-tiempo.timer" in r.stderr


@pytest.fixture
def sp_falso():
    """Un servidor que responde como la API REST local de Super Productivity 18.10 (las rutas que usa la suite)."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    estado = {"tareas": [], "proyectos": [{"id": "PT", "title": "Tesis"}], "etiquetas": [{"id": "TE", "title": "escritura"}]}

    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _responder(self, codigo, datos):
            cuerpo = json.dumps({"ok": True, "data": datos}).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(cuerpo)

        def _cuerpo(self):
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")

        def do_GET(self):
            ruta = self.path.split("?")[0]
            if ruta == "/health":
                return self._responder(200, {"server": "up", "rendererReady": True})
            if ruta == "/tasks":
                return self._responder(200, estado["tareas"])
            if ruta == "/projects":
                return self._responder(200, estado["proyectos"])
            if ruta == "/tags":
                return self._responder(200, estado["etiquetas"])
            self._responder(404, None)

        def do_POST(self):
            assert self.headers.get("Origin") is None   # SP rechaza las peticiones con Origin de la web
            t = {"id": f"t{len(estado['tareas']) + 1}", **self._cuerpo()}
            estado["tareas"].append(t)
            self._responder(201, t)

        def do_PATCH(self):
            tid = self.path.rsplit("/", 1)[-1]
            t = next(x for x in estado["tareas"] if x["id"] == tid)
            t.update(self._cuerpo())
            self._responder(200, t)

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_port}", estado
    servidor.shutdown()


def test_entrega_a_sp_y_planificar(entorno, sp_falso):
    raiz, _, env = entorno
    url, estado = sp_falso
    env = dict(env, SP_REST_URL=url)
    for _ in range(2):   # la segunda pasada actualiza la misma portadora, no crea otra
        r = _correr(env, "recoger", "--dias", "3", "--sin-aw", "--aplicar")
        assert r.returncode == 0, r.stderr
    portadoras = [t for t in estado["tareas"] if t["title"] == "Datos del registro de tiempo"]
    assert len(portadoras) == 1 and '"version":1' in portadoras[0]["notes"]
    assert "projectId" not in portadoras[0]          # sin el proyecto aún: va a la bandeja y el plugin la mueve

    plan_txt = raiz / "plan.txt"
    plan_txt.write_text("Redactar 3.2 +Tesis #escritura #nueva 1h30m @2026-10-26\n  - Releer 3.1 15m\n", encoding="utf-8")
    r = _correr(env, "planificar", str(plan_txt))
    assert r.returncode == 0 and len(estado["tareas"]) == 1, r.stderr   # simular no crea
    assert "la etiqueta «nueva» no existe" in r.stderr
    r = _correr(env, "planificar", str(plan_txt), "--aplicar")
    assert r.returncode == 0, r.stderr
    madre = next(t for t in estado["tareas"] if t["title"] == "Redactar 3.2")
    hija = next(t for t in estado["tareas"] if t["title"] == "Releer 3.1")
    assert madre["projectId"] == "PT" and madre["tagIds"] == ["TE"] and madre["dueDay"] == "2026-10-26"
    assert hija["parentId"] == madre["id"] and "projectId" not in hija and hija["timeEstimate"] == 900000


@pytest.mark.skipif(shutil.which("node") is None, reason="falta node para probar el plugin")
def test_plugin_contra_api_simulada():
    r = subprocess.run(["node", str(Path(__file__).with_name("plugin_registro_tiempo.test.mjs"))],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
