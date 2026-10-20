"""Pruebas de las rutas de administración en la app empaquetada y sobre Atlas con pocos privilegios.

Los módulos se cargan por ruta (sin importar toda la app), como en test_row_media.py.
"""

import importlib.util
import pathlib
import sys
import types

import pytest
from flask import Blueprint, Flask
from pymongo.errors import OperationFailure

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


paths = _cargar("paths_under_test", "app/utils/paths.py")
mongo_admin = _cargar("mongo_admin_under_test", "app/utils/mongo_admin.py")


# ---------- logs_dir ----------
def test_logs_dir_en_desarrollo_devuelve_el_valor_por_defecto(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.logs_dir("/repo/logs") == "/repo/logs"


def test_logs_dir_empaquetada_usa_log_dir_y_no_toca_el_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    destino = tmp_path / "Logs" / "EDF_Catalogo"
    monkeypatch.setenv("LOG_DIR", str(destino))
    assert paths.logs_dir("/Applications/X.app/Contents/Frameworks/app/logs") == str(destino)
    assert destino.is_dir()


def test_logs_dir_empaquetada_sin_log_dir_cae_en_library_logs(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("LOG_DIR", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(paths.os.path, "expanduser", lambda p: str(tmp_path) if p == "~" else p)
    esperado = tmp_path / "Library" / "Logs" / "EDF_Catalogo"
    assert paths.logs_dir("/bundle/logs") == str(esperado)
    assert esperado.is_dir()


# ---------- admin_command ----------
class _Admin:
    def __init__(self, error=None):
        self.error = error

    def command(self, nombre):
        if self.error:
            raise self.error
        return {"cmd": nombre, "version": "7.0"}


class _Cliente:
    def __init__(self, error=None):
        self.admin = _Admin(error)


def test_admin_command_devuelve_el_resultado():
    res, err = mongo_admin.admin_command(_Cliente(), "serverStatus")
    assert err is None and res["cmd"] == "serverStatus"


def test_admin_command_traduce_not_authorized_en_mensaje():
    cli = _Cliente(OperationFailure("not authorized on admin to execute command serverStatus"))
    res, err = mongo_admin.admin_command(cli, "serverStatus")
    assert res is None and "not authorized" in err


# ---------- /api/db/ops con un usuario sin privilegios ----------
def _app_con_ruta_db_ops(monkeypatch, cliente):
    """Carga admin_db_routes con sus dependencias internas sustituidas por stubs."""
    stubs = {
        "app": types.ModuleType("app"),
        "app.audit": types.ModuleType("app.audit"),
        "app.database": types.ModuleType("app.database"),
        "app.decorators": types.ModuleType("app.decorators"),
        "app.utils": types.ModuleType("app.utils"),
        "app.utils.mongo_admin": mongo_admin,
    }
    stubs["app.audit"].audit_log = lambda *a, **k: None
    stubs["app.database"].get_mongo_client = lambda: cliente
    stubs["app.database"].get_mongo_db = lambda: None
    stubs["app.decorators"].admin_required = lambda f: f
    for nombre, mod in stubs.items():
        monkeypatch.setitem(sys.modules, nombre, mod)

    rutas = _cargar("admin_db_routes_under_test", "app/routes/admin/admin_db_routes.py")
    app = Flask(__name__)
    app.secret_key = "test"
    bp = Blueprint("admin", __name__, url_prefix="/admin")
    rutas.register_admin_db_routes(bp)
    app.register_blueprint(bp)
    return app


def test_db_ops_sin_privilegios_no_da_500(monkeypatch):
    cliente = _Cliente(OperationFailure("not authorized on admin to execute command serverStatus"))
    app = _app_con_ruta_db_ops(monkeypatch, cliente)
    resp = app.test_client().get("/admin/api/db/ops")
    assert resp.status_code == 200
    datos = resp.get_json()
    assert datos["success"] is False
    assert datos["unavailable"] is True
    assert "serverStatus no disponible" in datos["error"]
    assert "traceback" not in datos


def test_db_ops_con_privilegios_usa_el_comando_currentop(monkeypatch):
    class AdminOk:
        def command(self, nombre):
            if nombre == "serverStatus":
                return {"opcounters": {"query": 5}, "mem": {"resident": 100}, "connections": {"current": 3}}
            if nombre == "currentOp":
                return {"inprog": [{"opid": 1, "secs_running": 4, "op": "query", "ns": "a.b", "client": "x"}]}
            raise AssertionError(nombre)

    cliente = types.SimpleNamespace(admin=AdminOk())
    app = _app_con_ruta_db_ops(monkeypatch, cliente)
    datos = app.test_client().get("/admin/api/db/ops").get_json()
    assert datos["success"] is True
    assert datos["connections"] == {"current": 3}
    assert datos["slow_ops"][0]["opid"] == 1


# ---------- ids duplicados en plantillas ----------
import re

PLANTILLAS = RAIZ / "app" / "templates"
BLOQUE_VACIO = "{% block multimedia_modal %}{% endblock %}"


MODALES_BASE = {
    "multimediaModal": "multimedia_modal",
    "documentModal": "document_modal",
    "imageModal": "image_modal",
}


def test_modales_de_base_un_solo_id_por_pagina():
    """Si una plantilla que hereda de base.html define su propio modal, debe anular el bloque de base."""
    base = (PLANTILLAS / "base.html").read_text(encoding="utf-8")
    for id_modal, bloque in MODALES_BASE.items():
        assert base.count(f'id="{id_modal}"') == 1, id_modal
        assert "{% block " + bloque + " %}" in base, bloque
    propias = set()
    for p in PLANTILLAS.rglob("*.html"):
        if p.name == "base.html":
            continue
        s = p.read_text(encoding="utf-8")
        if not re.search(r"\{% extends ['\"]base\.html['\"] %\}", s):
            continue
        for id_modal, bloque in MODALES_BASE.items():
            if f'id="{id_modal}"' in s:
                propias.add((p.name, id_modal))
                assert "{% block " + bloque + " %}{% endblock %}" in s, f"{p.relative_to(PLANTILLAS)} duplica #{id_modal}"
    assert ("ver_tabla.html", "documentModal") in propias
    assert ("view.html", "imageModal") in propias


def test_monitor_db_sin_ids_duplicados():
    s = (PLANTILLAS / "admin" / "db_monitor.html").read_text(encoding="utf-8")
    ids = re.findall(r'\bid="([^"]+)"', s)
    repetidos = {i for i in ids if ids.count(i) > 1}
    assert not repetidos, repetidos


# ---------- cabecera compacta de los modales de documento ----------
def test_modal_documentos_cabecera_compacta():
    js = (RAIZ / "app" / "static" / "js" / "modal-functions-UNIFIED.js").read_text(encoding="utf-8")
    assert "function edfDocHeader(" in js
    assert "Visualizando PDF desde S3" not in js      # aviso azul eliminado
    assert 'height="600"' not in js                    # el visor usa el alto de la ventana
    assert "fa-4x text-danger mb-3\"></i>\n          <h5>Documento" not in js
