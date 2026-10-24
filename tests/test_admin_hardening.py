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


# ---------- backups y credenciales de Drive fuera del .app ----------
def test_backups_dir_desarrollo_y_empaquetada(monkeypatch, tmp_path):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.backups_dir("/repo") == "/repo/backups"            # desarrollo: sin cambios

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths, "user_data_dir", lambda: str(tmp_path))
    destino = paths.backups_dir("/Applications/X.app/Contents/Frameworks")
    assert destino == str(tmp_path / "backups") and (tmp_path / "backups").is_dir()


def test_drive_config_dir_desarrollo_y_empaquetada(monkeypatch, tmp_path):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.drive_config_dir("/repo/tools/db_utils") == "/repo/tools/db_utils"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths, "user_data_dir", lambda: str(tmp_path))
    assert paths.drive_config_dir("/bundle/tools/db_utils") == str(tmp_path / "google_drive")


def test_rutas_de_backups_y_drive_no_apuntan_al_bundle():
    """El listado/descarga/borrado/subida de backups y las credenciales de Drive no pueden usar la ruta del código."""
    mant = (RAIZ / "app" / "routes" / "maintenance_routes.py").read_text(encoding="utf-8")
    assert 'project_root / "backups"' not in mant
    assert mant.count("backups_dir(") >= 5
    for nombre in ("google_drive_utils.py", "google_drive_utils_v2.py"):
        s = (RAIZ / "tools" / "db_utils" / nombre).read_text(encoding="utf-8")
        assert 'os.path.dirname(__file__), "credentials.json"' not in s
        assert 'os.path.dirname(__file__), "token.pickle"' not in s
        assert "script_dir = os.path.dirname(os.path.abspath(__file__))" not in s
        assert "def _config_dir()" in s


def test_monitor_db_muestra_nd_y_aviso_sin_serverstatus():
    from jinja2 import DictLoader, Environment

    src = (PLANTILLAS / "admin" / "db_monitor.html").read_text(encoding="utf-8")
    # solo el bloque de contenido (el script usa Chart.js por CDN y no forma parte de esta comprobación)
    env = Environment(loader=DictLoader({"admin/base.html": "{% block content %}{% endblock %}", "m.html": src}))
    env.globals["url_for"] = lambda *a, **k: "/x"
    t = env.get_template("m.html")
    base = {"is_connected": True, "error": None, "stats": {}, "slow_ops": []}

    sin_permisos = t.render(status={**base, "server_status": {"error": "serverStatus no disponible: not authorized"}})
    assert "Métricas en tiempo real no disponibles" in sin_permisos
    assert 'id="currentOps">N/D<' in sin_permisos and 'id="memoryUsage">N/D<' in sin_permisos

    con_permisos = t.render(status={**base, "server_status": {"version": "7.0"}})
    assert "Métricas en tiempo real no disponibles" not in con_permisos
    assert 'id="currentOps">—<' in con_permisos


def test_acciones_masivas_backups_locales_usan_delegacion():
    """Los botones masivos del modal de backups locales deben tener manejador
    delegado (antes estaban en una función que nunca se invocaba)."""
    js = (RAIZ / "app/static/js/dashboard.js").read_text(encoding="utf-8")
    assert '$(document).on("click", "#deleteSelectedLocalBackups"' in js
    assert '$(document).on("click", "#uploadSelectedLocalBackups"' in js
    assert "_initializeLocalBackupsMassiveActions" not in js


def test_tamano_backups_no_muestra_na_para_ficheros_pequenos():
    js = (RAIZ / "app/static/js/dashboard.js").read_text(encoding="utf-8")
    assert "function formatFileSize(" in js
    assert "formatFileSize(backup.size)" in js
    assert "formatFileSize(backup.file_size)" in js
    assert "backup.size_mb ?" not in js


def test_create_and_upload_respalda_todas_las_colecciones():
    src = (RAIZ / "app/routes/admin/admin_backup_routes.py").read_text(encoding="utf-8")
    assert '["catalogs", "users"]' not in src
    assert "db.list_collection_names()" in src
    assert 'startswith("system.")' in src


def test_listas_backups_destruyen_datatable_antes_de_vaciar_tbody():
    """Vaciar el tbody con un DataTable activo hace que destroy() restaure las
    filas antiguas (los backups eliminados reaparecían tras refrescar)."""
    js = (RAIZ / "app/static/js/dashboard.js").read_text(encoding="utf-8")
    assert "function resetDataTable(" in js
    for body in ("#localBackupsTableBody", "#driveBackupsTableBody"):
        assert f'$("{body}").empty()' not in js.replace(
            "$(bodySelector).empty()", ""
        ), body
    assert js.count('resetDataTable("#localBackupsTable"') == 2
    assert js.count('resetDataTable("#driveBackupsTable"') == 2
    # Si Drive queda vacío, la tabla anterior se oculta
    assert '$("#driveBackupsContent").hide();\n          $("#driveBackupsEmpty").show();' in js


def _dashboard_js():
    return (RAIZ / "app/static/js/dashboard.js").read_text(encoding="utf-8")


def test_datatables_sin_language_url_y_destroy_tolerante():
    """language.url hace asíncrona la inicialización; un refresco intermedio
    lanzaba excepción en destroy() y la lista no se actualizaba."""
    js = _dashboard_js()
    assert "cdn.datatables.net" not in js
    assert js.count('"language": DT_LANG_ES') == 2
    i = js.index("function resetDataTable(")
    cuerpo = js[i : i + 700]
    assert "try {" in cuerpo and "catch (err)" in cuerpo


def test_seleccion_drive_se_poda_y_borrado_masivo_tolerante():
    js = _dashboard_js()
    assert "selectedBackups.delete(id)" in js  # poda de IDs inexistentes
    assert "selectedBackups.delete(fileId)" in js  # borrado individual
    assert "Promise.allSettled(deletePromises)" in js
    assert "Promise.all(deletePromises)" not in js
    i = js.index("Promise.allSettled(deletePromises)")
    assert "loadDriveBackups();" in js[i : i + 900]  # siempre refresca


def test_resultado_de_backup_se_vuelve_a_mostrar():
    js = _dashboard_js()
    assert "function showBackupResult(" in js
    assert '$("#backupResult").html(' not in js
    assert '.stop(true, true).show().html(html)' in js
    assert js.count('$("#backupResult").fadeOut(') == 1  # solo en el helper
    assert "window.loadLocalBackups = loadLocalBackups;" in js


def test_subida_a_drive_conserva_el_nombre_del_backup():
    src = (RAIZ / "app/routes/maintenance_routes.py").read_text(encoding="utf-8")
    i = src.index("def upload_file(self, filename: str, file_content: bytes)")
    bloque = src[i : i + 2200]
    assert "NamedTemporaryFile" not in bloque
    assert "os.path.basename(filename)" in bloque
    assert "shutil.rmtree(temp_dir" in bloque


def test_imports_de_subida_a_drive_apuntan_a_funciones_que_existen():
    """El import dentro de upload_backup_to_drive fallaba siempre (la función
    no existía en el módulo) y se mostraba como 'Google Drive no disponible'."""
    import ast

    src = (RAIZ / "app/routes/admin/admin_backup_routes.py").read_text(encoding="utf-8")
    arbol = ast.parse(src)
    fn = next(
        n
        for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef) and n.name == "upload_backup_to_drive"
    )
    imports = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("google_drive_utils")
    ]
    assert imports, "no se encontró el import de Google Drive"
    for imp in imports:
        modulo = RAIZ / "tools" / "db_utils" / f"{imp.module}.py"
        assert modulo.exists(), modulo
        definidas = {
            n.name
            for n in ast.parse(modulo.read_text(encoding="utf-8")).body
            if isinstance(n, ast.FunctionDef)
        }
        for alias in imp.names:
            assert alias.name in definidas, f"{imp.module} no define {alias.name}"


def _cargar_models_database(monkeypatch):
    """Carga app/models/database.py aislado (sin importar el paquete app)."""
    for nombre in ("app", "app.models", "app.models.user_schema"):
        monkeypatch.setitem(sys.modules, nombre, types.ModuleType(nombre))
    sys.modules["app.models.user_schema"].normalize_user_doc = lambda d: d
    spec = importlib.util.spec_from_file_location(
        "edf_models_database_test", RAIZ / "app" / "models" / "database.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_mongo_valida_certificado_tls_por_defecto(monkeypatch):
    monkeypatch.delenv("MONGO_TLS_INSECURE", raising=False)
    mod = _cargar_models_database(monkeypatch)
    import certifi

    opts = mod._tls_options("mongodb+srv://u:p@cluster.example.mongodb.net/db")
    assert opts == {"tlsCAFile": certifi.where()}
    assert "tlsAllowInvalidCertificates" not in opts
    # Mongo local sin TLS: sin opciones
    assert mod._tls_options("mongodb://localhost:27017/") == {}


def test_mongo_salida_insegura_solo_explicita(monkeypatch):
    monkeypatch.setenv("MONGO_TLS_INSECURE", "1")
    mod = _cargar_models_database(monkeypatch)
    opts = mod._tls_options("mongodb+srv://u:p@cluster.example.mongodb.net/db")
    assert opts["tlsAllowInvalidCertificates"] is True


def test_get_mongo_client_no_pasa_tls_inseguro(monkeypatch):
    monkeypatch.delenv("MONGO_TLS_INSECURE", raising=False)
    monkeypatch.setenv("MONGO_URI", "mongodb+srv://u:p@cluster.example.mongodb.net/db")
    mod = _cargar_models_database(monkeypatch)
    llamadas = {}

    class FalsoCliente:
        def __init__(self, uri, **kwargs):
            llamadas["kwargs"] = kwargs

    monkeypatch.setattr(mod, "MongoClient", FalsoCliente)
    mod.client = None
    mod.get_mongo_client()
    assert "tlsAllowInvalidCertificates" not in llamadas["kwargs"]
    assert "tlsCAFile" in llamadas["kwargs"]


def test_mongo_uri_con_flag_inseguro_se_ignora(monkeypatch):
    monkeypatch.delenv("MONGO_TLS_INSECURE", raising=False)
    mod = _cargar_models_database(monkeypatch)
    uri = "mongodb+srv://u:p@c.example.mongodb.net/db?tlsAllowInvalidCertificates=true"
    assert mod._tls_options(uri)["tlsAllowInvalidCertificates"] is False
    monkeypatch.setenv("MONGO_TLS_INSECURE", "1")
    assert mod._tls_options(uri)["tlsAllowInvalidCertificates"] is True


def test_pymongo_kwarg_prevalece_sobre_uri():

    uri = "mongodb://h/db?tls=true&tlsAllowInvalidCertificates=true"
    from pymongo import MongoClient

    c = MongoClient(uri, tlsAllowInvalidCertificates=False, connect=False)
    assert c.options.pool_options._ssl_context.verify_mode.name == "CERT_REQUIRED"
    c.close()


# --- Tablas de filas de catálogo: layout responsive (admin y usuario) ---

_PLANTILLAS_TABLA = ("app/templates/ver_tabla.html", "app/templates/admin/ver_catalogo.html")


def test_tablas_catalogo_sin_anchos_fijos_ni_reglas_posicionales():
    import re

    for ruta in _PLANTILLAS_TABLA + ("app/static/css/ver_tabla_improvements.css",):
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        assert not re.search(r"min-width:\s*1[4-6]00px", texto), ruta
        assert "#tablaFilas th:nth-child" not in texto, ruta
        assert "#tablaFilas td:nth-child(1" not in texto, ruta
        assert "td:nth-last-child" not in texto, ruta


def test_tablas_catalogo_celdas_con_data_label_y_clases():
    for ruta in _PLANTILLAS_TABLA:
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        for clase in ("col-num", "col-imagenes", "col-acciones"):
            assert f'class="{clase}"' in texto, (ruta, clase)
        assert 'data-label="{{ header|e }}"' in texto, ruta
        assert 'data-label="Acciones"' in texto, ruta


def test_vista_usuario_emite_su_css():
    # base.html no define {% block head %}: el CSS debe ir dentro de content
    base = (RAIZ / "app/templates/base.html").read_text(encoding="utf-8")
    assert "{% block head %}" not in base
    texto = (RAIZ / "app/templates/ver_tabla.html").read_text(encoding="utf-8")
    assert "{% block head %}" not in texto.replace(
        "{# base.html no define {% block head %}", ""
    )
    inicio = texto.index("{% block content %}")
    assert texto.index("ver_tabla_improvements.css") > inicio


def test_css_tarjetas_no_fuerza_display_de_filas():
    # la búsqueda y la paginación ocultan filas con style.display
    css = (RAIZ / "app/static/css/ver_tabla_improvements.css").read_text(encoding="utf-8")
    bloque = css[css.index("@media (width <= 768px)", css.index("11. LAYOUT")):]
    assert "#tablaFilas tbody tr {" in bloque
    regla_tr = bloque[bloque.index("#tablaFilas tbody tr {"):].split("}")[0]
    assert "display" not in regla_tr


def test_navbar_admin_colapsa_por_debajo_de_xl():
    base = (RAIZ / "app/templates/admin/base.html").read_text(encoding="utf-8")
    assert "navbar-expand-xl" in base and "navbar-expand-lg" not in base
    assert "max-width: 1199.98px" in base
