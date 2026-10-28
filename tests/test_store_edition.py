"""Edición de tienda: conmutador, no-regresión de la edición estándar y flujo local."""

import os

import pytest

from app import edition


# ----------------------------------------------------------------- conmutador
def test_por_defecto_es_standard(monkeypatch):
    monkeypatch.delenv("EDF_EDITION", raising=False)
    assert edition.current_edition() == "standard" and not edition.is_store()


@pytest.mark.parametrize("value", ["store", "STORE", " store "])
def test_store_se_activa_con_la_variable(monkeypatch, value):
    monkeypatch.setenv("EDF_EDITION", value)
    assert edition.is_store()


@pytest.mark.parametrize("value", ["", "tienda", "1", "true", "standard", "storex"])
def test_valores_desconocidos_nunca_activan_tienda(monkeypatch, value):
    monkeypatch.setenv("EDF_EDITION", value)
    assert not edition.is_store()


def test_marcador_solo_cuenta_empaquetado(monkeypatch, tmp_path):
    (tmp_path / "EDITION").write_text("store")
    monkeypatch.delenv("EDF_EDITION", raising=False)
    monkeypatch.setattr("sys.frozen", False, raising=False)
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)
    assert not edition.is_store()
    monkeypatch.setattr("sys.frozen", True, raising=False)
    assert edition.is_store()


def test_la_variable_gana_al_marcador(monkeypatch, tmp_path):
    (tmp_path / "EDITION").write_text("store")
    monkeypatch.setenv("EDF_EDITION", "standard")
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)
    assert not edition.is_store()


# ----------------------------------------- la edición estándar no cambia nada
def test_standard_sin_mongo_uri_sigue_fallando_igual(monkeypatch, tmp_path):
    monkeypatch.delenv("EDF_EDITION", raising=False)
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.setenv("EDF_LOCAL_DB", str(tmp_path / "no_debe_existir.sqlite3"))
    import app.database as appdb

    assert appdb.initialize_db() is False
    assert "MONGO_URI" in (appdb.get_last_error() or "")
    assert not (tmp_path / "no_debe_existir.sqlite3").exists()


def test_standard_usa_pymongo_no_el_almacen_local(monkeypatch, tmp_path):
    monkeypatch.delenv("EDF_EDITION", raising=False)
    monkeypatch.setenv("EDF_LOCAL_DB", str(tmp_path / "no_debe_existir.sqlite3"))
    import app.models.database as mdb
    from app.storage.local_store import LocalClient

    monkeypatch.setattr(mdb, "client", None)
    cli = mdb.get_mongo_client()
    try:
        assert not isinstance(cli, LocalClient)
        assert type(cli).__module__.startswith("pymongo")
    finally:
        cli.close()
    assert not (tmp_path / "no_debe_existir.sqlite3").exists()


def test_standard_no_registra_el_inicio_de_sesion_automatico():
    src = open(os.path.join(os.path.dirname(edition.__file__), "__init__.py"), encoding="utf-8").read()
    assert "if is_store():" in src and "init_store_edition" in src
    # el módulo de tienda solo se importa dentro de esa rama
    assert src.count("from app.store_edition import") == 1


# ------------------------------------------------------------ flujo en tienda
@pytest.fixture()
def store_app(monkeypatch, tmp_path):
    for var in ("MONGO_URI", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "USE_S3"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("EDF_EDITION", "store")
    monkeypatch.setenv("EDF_LOCAL_DB", str(tmp_path / "t.sqlite3"))
    from app.storage import local_store

    local_store.reset_local_client()
    import app as app_pkg

    application = app_pkg.create_app(testing=True)
    application.config["TESTING"] = True
    yield application
    local_store.reset_local_client()
    import app.database as appdb

    appdb._mongo_client = appdb._mongo_db = None
    appdb._is_connected = False


def _entrar(client):
    """Entra como lo hace el launcher: con la URL que lleva el token de arranque."""
    from app.store_edition import entry_path

    r = client.get(entry_path())
    assert r.status_code == 302 and r.headers["Location"].endswith("/")
    return client


def test_tienda_entra_con_el_token_y_usa_sqlite(store_app):
    import app.database as appdb
    from app.storage.local_store import LocalClient

    assert isinstance(appdb.get_mongo_client(), LocalClient)
    c = _entrar(store_app.test_client())
    assert c.get("/", follow_redirects=True).status_code == 200
    with c.session_transaction() as s:
        assert s["logged_in"] is True and s["role"] == "admin"
    users = appdb.get_mongo_db()["users"]
    assert users.count_documents({"email": "local@tablateca.local"}) == 1
    _entrar(store_app.test_client())
    assert users.count_documents({}) == 1  # no duplica el usuario local


# ------------------------------------------------ el puerto local no se regala
def test_sin_token_no_hay_sesion_ni_datos(store_app):
    import app.database as appdb

    c = store_app.test_client()
    assert c.get("/").status_code == 403
    assert c.get("/admin/").status_code == 403
    assert c.post("/catalogs/create", data={"name": "X", "headers": "A"}).status_code == 403
    db = appdb.get_mongo_db()
    assert db["spreadsheets"].count_documents({}) == 0
    assert db["users"].count_documents({}) == 0  # ni siquiera se crea el usuario local


@pytest.mark.parametrize("token", ["", "x", "A" * 43])
def test_token_incorrecto_se_rechaza(store_app, token):
    import app.database as appdb

    c = store_app.test_client()
    assert c.get(f"/_store/enter?t={token}").status_code == 403
    assert c.get("/_store/enter").status_code == 403
    assert appdb.get_mongo_db()["users"].count_documents({}) == 0
    assert c.get("/").status_code == 403


def test_host_no_local_se_rechaza_incluso_con_token(store_app):
    from app.store_edition import entry_path

    c = store_app.test_client()
    assert c.get(entry_path(), base_url="http://evil.example:5004").status_code == 403
    assert c.get(entry_path(), base_url="http://127.0.0.1.evil.example").status_code == 403
    r = c.get(entry_path(), base_url="http://127.0.0.1:5004")
    assert r.status_code == 302
    assert c.get("/", base_url="http://127.0.0.1:5004", follow_redirects=True).status_code == 200
    # La misma sesión (cookie de 127.0.0.1) con otro nombre de host no entra
    assert c.get("/", base_url="http://evil.example:5004").status_code == 403


@pytest.mark.parametrize(
    "host,esperado",
    [
        ("127.0.0.1", True),
        ("127.0.0.1:5004", True),
        ("localhost:5004", True),
        ("[::1]:5004", True),
        ("evil.example", False),
        ("evil.example:5004", False),
        ("127.0.0.1.evil.example", False),
        ("localhost.evil.example:5004", False),
        ("", False),
    ],
)
def test_host_local_solo_acepta_loopback(store_app, host, esperado):
    from app.store_edition import _host_is_local

    with store_app.test_request_context("/", headers={"Host": host}):
        assert _host_is_local() is esperado


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "http://evil.example"},
        {"Origin": "null"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
    ],
)
def test_escrituras_de_otro_origen_se_rechazan_aunque_haya_sesion(store_app, headers):
    import app.database as appdb

    c = _entrar(store_app.test_client())
    r = c.post("/catalogs/create", data={"name": "Intruso", "headers": "A"}, headers=headers)
    assert r.status_code == 403
    assert appdb.get_mongo_db()["spreadsheets"].count_documents({"name": "Intruso"}) == 0


def test_escritura_del_mismo_origen_funciona(store_app):
    import app.database as appdb

    c = _entrar(store_app.test_client())
    r = c.post(
        "/catalogs/create",
        data={"name": "Propio", "headers": "A"},
        headers={"Origin": "http://localhost", "Sec-Fetch-Site": "same-origin"},
    )
    assert r.status_code in (200, 302)
    assert appdb.get_mongo_db()["spreadsheets"].count_documents({"name": "Propio"}) == 1


@pytest.mark.parametrize("path", ["/login", "/register", "/welcome", "/auth/login", "/auth/register"])
def test_pantallas_de_cuenta_redirigen_a_inicio(store_app, path):
    r = _entrar(store_app.test_client()).get(path)
    assert r.status_code == 302 and r.headers["Location"].endswith("/")


def test_crear_catalogo_anadir_editar_ver_y_borrar(store_app, tmp_path):
    import app.database as appdb

    c = _entrar(store_app.test_client())
    r = c.post("/catalogs/create", data={"name": "Mi tabla", "headers": "Nombre,Notas"})
    assert r.status_code in (200, 302), r.status_code
    sheet = appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Mi tabla"})
    assert sheet is not None and sheet["headers"] == ["Nombre", "Notas"]
    cid = str(sheet["_id"])

    r = c.post(f"/catalogs/add-row/{cid}", data={"Nombre": "Ana", "Notas": "primera"})
    assert r.status_code in (200, 302)
    sheet = appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Mi tabla"})
    assert sheet["rows"][0]["Nombre"] == "Ana"

    assert c.get(f"/catalogs/{cid}", follow_redirects=True).status_code == 200
    assert c.get(f"/admin/catalogo/spreadsheets/{cid}").status_code == 200

    r = c.post(f"/catalogs/edit-row/{cid}/0", data={"Nombre": "Ana María", "Notas": "editada"})
    assert r.status_code in (200, 302)
    sheet = appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Mi tabla"})
    assert sheet["rows"][0]["Nombre"] == "Ana María"

    r = c.post(f"/catalogs/delete/{cid}")
    assert r.status_code in (200, 302)
    assert appdb.get_mongo_db()["spreadsheets"].count_documents({"name": "Mi tabla"}) == 0


def test_los_datos_sobreviven_a_reiniciar(store_app, tmp_path):
    from app.storage import local_store

    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "Persistente", "headers": "A"})
    local_store.reset_local_client()
    again = local_store.LocalClient(str(tmp_path / "t.sqlite3"))
    try:
        assert again.get_database()["spreadsheets"].count_documents({"name": "Persistente"}) == 1
    finally:
        again.close()


def test_descargas_del_launcher_llevan_cabecera_y_solo_leen(store_app):
    from app.store_edition import launch_headers

    c = store_app.test_client()
    # Con la cabecera se supera la puerta (la ruta decide después: 404 = no existe el fichero)
    assert c.get("/imagenes_subidas/no-existe.png", headers=launch_headers()).status_code != 403
    assert c.get("/imagenes_subidas/no-existe.png").status_code == 403
    assert c.get("/imagenes_subidas/no-existe.png", headers={"X-EDF-Launch": "otro"}).status_code == 403
    r = c.post("/catalogs/create", data={"name": "X", "headers": "A"}, headers=launch_headers())
    assert r.status_code == 403  # la cabecera no autoriza escrituras


# --------------------------------------------------------------- el launcher
def _launcher_ns(monkeypatch, store):
    import ast
    import pathlib

    src = (pathlib.Path(__file__).resolve().parents[1] / "launcher_native_websockets.py").read_text()
    tree = ast.parse(src)
    wanted = {"_store_edition", "_start_url", "_launch_headers"}
    code = "\n".join(ast.get_source_segment(src, n) for n in tree.body
                     if isinstance(n, ast.FunctionDef) and n.name in wanted)
    ns = {"PORT": 5004}
    exec(code, ns)  # noqa: S102 - solo funciones del propio launcher
    if store:
        monkeypatch.setenv("EDF_EDITION", "store")
    else:
        monkeypatch.delenv("EDF_EDITION", raising=False)
    return ns


def test_launcher_abre_la_tienda_con_el_token(monkeypatch):
    from app.store_edition import LAUNCH_TOKEN

    ns = _launcher_ns(monkeypatch, store=True)
    assert ns["_start_url"]() == f"http://127.0.0.1:5004/_store/enter?t={LAUNCH_TOKEN}"


def test_launcher_en_edicion_estandar_abre_la_url_de_siempre(monkeypatch):
    ns = _launcher_ns(monkeypatch, store=False)
    assert ns["_start_url"]() == "http://127.0.0.1:5004"


def test_launcher_envia_la_cabecera_en_la_tienda_y_no_en_la_estandar(monkeypatch):
    from app.store_edition import LAUNCH_TOKEN

    ns = _launcher_ns(monkeypatch, store=True)
    assert ns["_launch_headers"]() == {"X-EDF-Launch": LAUNCH_TOKEN}
    ns = _launcher_ns(monkeypatch, store=False)
    assert ns["_launch_headers"]() == {}


# ------------------------------------------- tienda sin S3: filas con multimedia
def _catalogo_con_media(db):
    rows = [
        {
            "Nombre": "Con medios",
            "Multimedia": ["foto1.png"],
            "Documentación": ["manual1.pdf"],
            "images": ["foto1.png"],
        }
    ]
    res = db["spreadsheets"].insert_one(
        {
            "name": "Con medios",
            "headers": ["Nombre", "Multimedia", "Documentación"],
            "rows": rows,
            "data": rows,
            "owner": "local@tablateca.local",
        }
    )
    return str(res.inserted_id)


def test_tienda_ver_catalogo_con_imagenes_y_documentos_sin_s3(store_app):
    """Regresión: 'expected string or bytes-like object' al abrir un catálogo con
    medios, porque get_s3_url llamaba a boto3 sin bucket (TypeError)."""
    import app.database as appdb

    cid = _catalogo_con_media(appdb.get_mongo_db())
    c = _entrar(store_app.test_client())

    r = c.get(f"/admin/catalogo/spreadsheets/{cid}")
    assert r.status_code == 200, (r.status_code, r.headers.get("Location"))
    assert b"foto1.png" in r.data
    assert c.get("/catalogs/", follow_redirects=True).status_code == 200


def test_get_s3_url_sin_bucket_devuelve_none(monkeypatch):
    import app.routes.s3_utils as s3u

    monkeypatch.setattr(s3u, "S3_BUCKET_NAME", None)
    assert s3u.get_s3_url("foto1.png") is None
    monkeypatch.setattr(s3u, "S3_BUCKET_NAME", "")
    assert s3u.get_s3_url("foto1.png") is None


def test_get_s3_url_con_bucket_sigue_firmando(monkeypatch):
    """No regresión de la edición estándar: con bucket configurado se firma."""
    import app.routes.s3_utils as s3u

    class FakeS3:
        def generate_presigned_url(self, op, Params, ExpiresIn):
            return f"https://s3.test/{Params['Bucket']}/{Params['Key']}?e={ExpiresIn}"

    monkeypatch.setattr(s3u, "S3_BUCKET_NAME", "bucket")
    monkeypatch.setattr(s3u, "s3_client", FakeS3())
    assert s3u.get_s3_url("a.png", 60) == "https://s3.test/bucket/a.png?e=60"


# ------------------------------------------------ miniatura del catálogo (listado)
@pytest.mark.parametrize(
    "row, esperado",
    [
        ({"images": ["a.png"]}, "/static/uploads/a.png"),
        ({"images": [["a.png", "b.png"]]}, "/static/uploads/a.png"),
        ({"images": ["/imagenes_subidas/a.png"]}, "/static/uploads/a.png"),
        ({"images": ["/static/uploads/a.png"]}, "/static/uploads/a.png"),
        ({"images": [], "Multimedia": ["v.mp4", "f.JPG"]}, "/static/uploads/f.JPG"),
        ({"imagenes": "a.png"}, "/static/uploads/a.png"),
        ({"images": ["N/A"], "Multimedia": ["v.mp4"]}, None),
        ({"images": ["/logout"]}, "/static/uploads/logout"),
        ({"images": ["//evil.example/x.png"]}, "/static/uploads/x.png"),
        ({"images": ["/imagenes_subidas/../.."]}, None),
        ({"images": ["/imagenes_subidas/%2e%2e/%2e%2e/logout"]}, "/static/uploads/logout"),
        ({"images": ["../../logout"]}, "/static/uploads/logout"),
        ({"images": ["..", "%2e%2e", "/", "\\..\\x.png"]}, "/static/uploads/x.png"),
        
        ({"Nombre": "sin imagen"}, None),
    ],
)
def test_miniatura_de_fila(store_app, row, esperado):
    from app.routes.catalogs_routes import _miniatura_de_fila

    with store_app.test_request_context("/"):
        assert _miniatura_de_fila(row) == esperado


def test_listado_muestra_miniatura_valida_y_la_sirve(store_app):
    import app.database as appdb

    cid = _catalogo_con_media(appdb.get_mongo_db())
    c = _entrar(store_app.test_client())
    r = c.get("/catalogs/")
    assert r.status_code == 200
    assert b"/static/uploads/foto1.png" in r.data
    # y con rutas con barra inicial (antes salía /static/uploads//imagenes_subidas/..)
    db = appdb.get_mongo_db()
    db["spreadsheets"].update_one(
        {"name": "Con medios"},
        {"$set": {"data": [{"images": ["/imagenes_subidas/zz.png"]}]}},
    )
    r = c.get("/catalogs/")
    assert b'src="/static/uploads/zz.png"' in r.data
    assert b"uploads//" not in r.data


@pytest.mark.parametrize(
    "valor",
    ["%2e%2e", "..", "%252e%252e", "/imagenes_subidas/%2e%2e", "a/..", "javascript:alert(1)", "data:image/png;base64,AA"],
)
def test_miniatura_nunca_emite_rutas_de_escape(store_app, valor):
    from app.routes.catalogs_routes import _miniatura_de_fila

    with store_app.test_request_context("/"):
        assert _miniatura_de_fila({"images": [valor]}) is None


def test_miniatura_solo_usa_url_bajo_uploads(store_app):
    from app.routes.catalogs_routes import _miniatura_de_fila

    malos = ["/logout", "//evil.example/x.png", "../../logout", "/imagenes_subidas/%2e%2e/%2e%2e/logout", "\\..\\logout"]
    with store_app.test_request_context("/"):
        for v in malos:
            url = _miniatura_de_fila({"images": [v]})
            assert url is None or (url.startswith("/static/uploads/") and "/.." not in url and "//" not in url[1:]), (v, url)


# ------------------------------------------ miniatura subida: no puede quedar vacía
def _png():
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d"
        "49444154789c6360000002000001e221bc330000000049454e44ae426082"
    )


def test_subir_miniatura_en_la_tienda_guarda_el_contenido_y_se_sirve(store_app):
    import io

    import app.database as appdb

    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "M", "headers": "Nombre"})
    cid = str(appdb.get_mongo_db()["spreadsheets"].find_one({"name": "M"})["_id"])
    r = c.post(
        f"/catalogs/{cid}/edit",
        data={"name": "M", "headers": "Nombre", "miniatura": "", "miniatura_file": (io.BytesIO(_png()), "m.jpeg")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 302
    mini = appdb.get_mongo_db()["spreadsheets"].find_one({"name": "M"})["miniatura"]
    assert mini.startswith("/static/uploads/miniatura_")
    resp = c.get(mini)
    assert resp.status_code == 200 and resp.data == _png()
    # y el listado la usa
    assert mini.encode() in c.get("/catalogs/").data
    os.remove(os.path.join(store_app.config["UPLOAD_FOLDER"], os.path.basename(mini)))


def test_listado_ignora_miniatura_local_vacia_o_inexistente_y_usa_la_imagen_de_la_fila(store_app):
    import app.database as appdb

    up = store_app.config["UPLOAD_FOLDER"]
    os.makedirs(up, exist_ok=True)
    vacio = os.path.join(up, "miniatura_vacia_test.jpeg")
    open(vacio, "wb").close()
    try:
        db = appdb.get_mongo_db()
        for mini in ("/static/uploads/miniatura_vacia_test.jpeg", "/static/uploads/no_existe_test.jpeg"):
            db["spreadsheets"].delete_many({})
            db["spreadsheets"].insert_one(
                {"name": "X", "headers": ["Nombre"], "rows": [], "miniatura": mini,
                 "data": [{"images": ["real.png"]}], "owner": "local@tablateca.local"}
            )
            c = _entrar(store_app.test_client())
            html = c.get("/catalogs/").data
            assert b'src="/static/uploads/real.png"' in html, mini
            assert mini.encode() not in html
    finally:
        os.remove(vacio)


def test_miniatura_rota_solo_se_evalua_en_la_tienda(monkeypatch, tmp_path):
    from flask import Flask

    from app.routes.catalogs_routes import _miniatura_local_rota

    a = Flask(__name__)
    a.config["UPLOAD_FOLDER"] = str(tmp_path)
    monkeypatch.delenv("EDF_EDITION", raising=False)
    with a.app_context():
        assert _miniatura_local_rota("/static/uploads/no_existe.jpeg") is False
    monkeypatch.setenv("EDF_EDITION", "store")
    with a.app_context():
        assert _miniatura_local_rota("/static/uploads/no_existe.jpeg") is True
        assert _miniatura_local_rota("https://x/y.png") is False
        (tmp_path / "ok.png").write_bytes(b"x")
        assert _miniatura_local_rota("/static/uploads/ok.png") is False


# ------------------------------------------------ modal de imagen: el indicador se oculta
def test_modal_de_imagen_oculta_el_indicador_al_cargar_o_fallar():
    """Regresión: el spinner del modal de imagen giraba para siempre junto a la imagen.
    (Comprobado además en Chromium: oculto tras imagen válida y tras imagen rota.)"""
    import re

    src = open(
        os.path.join(os.path.dirname(__file__), "..", "app", "static", "js", "modal-functions-UNIFIED.js"),
        encoding="utf-8",
    ).read()
    cuerpo = src[src.index("function showImageModal") : src.index("function showMultimediaModal")]
    assert "setSpinner(true)" in cuerpo
    assert re.search(r"onload = function\(\) \{\s*setSpinner\(false\)", cuerpo)
    assert re.search(r"onerror = function\(\) \{\s*setSpinner\(false\)", cuerpo)
    # el src se asigna después de los manejadores
    assert cuerpo.index("modalImage.onload") < cuerpo.index("modalImage.src = imageSrc")


# ------------------------------------------------------- visor de PDF (pdf.js local)
def test_visor_pdf_usa_pdfjs_local_con_respaldo_de_iframe():
    base = os.path.join(os.path.dirname(__file__), "..", "app", "static", "js")
    for f in ("pdf.min.js", "pdf.worker.min.js", "LICENSE"):
        assert os.path.getsize(os.path.join(base, "vendor", "pdfjs", f)) > 1000, f
    js = open(os.path.join(base, "modal-functions-UNIFIED.js"), encoding="utf-8").read()
    # los dos caminos de PDF (S3 y local) montan pdf.js, ya no un iframe fijo
    import re as _re

    assert len(_re.findall(r"edfMountPdf\(modalContent, \w+\);", js)) == 2
    cuerpo = js[js.index("function showDocumentModal") : js.index("function edfEscapeHtml")]
    assert "<iframe" not in cuerpo.split("fileExtension === 'md'")[0].split("if (fileExtension === 'pdf')")[1]
    # sin CDN: todo desde /static y sin eval
    assert "/static/js/vendor/pdfjs/pdf.min.js" in js and "isEvalSupported: false" in js
    assert "cdn" not in js[js.index("function edfEnsurePdfJs") : js.index("function showMarkdownInModal")].lower()
    # y el respaldo al visor integrado existe
    assert "document.createElement('iframe')" in js


def test_visor_pdf_fuentes_y_cmaps_locales_con_respaldo_del_sistema():
    """Los PDF con fuentes CID no embebidas (p. ej. ReportLab/HeiseiMin-W3) solo se ven con
    CMaps locales y la fuente del sistema: no hay que desactivar FontFace ni useSystemFonts."""
    base = os.path.join(os.path.dirname(__file__), "..", "app", "static", "js")
    js = open(os.path.join(base, "modal-functions-UNIFIED.js"), encoding="utf-8").read()
    for clave in (
        "standardFontDataUrl: '/static/js/vendor/pdfjs/standard_fonts/'",
        "cMapUrl: '/static/js/vendor/pdfjs/cmaps/'",
        "cMapPacked: true",
    ):
        assert clave in js, clave
    cfg = js[js.index("getDocument({") : js.index(".promise;", js.index("getDocument({"))]
    assert "disableFontFace: true" not in cfg
    assert "useSystemFonts: false" not in cfg
    pdfjs = os.path.join(base, "vendor", "pdfjs")
    assert os.path.getsize(os.path.join(pdfjs, "standard_fonts", "LiberationSans-Regular.ttf")) > 1000
    assert os.path.getsize(os.path.join(pdfjs, "cmaps", "90ms-RKSJ-H.bcmap")) > 100


def test_ver_catalogo_tabla_fuera_de_la_barra_de_botones(store_app):
    """Regresión: faltaba un </div> en la barra de acciones del admin y la tabla de
    filas quedaba dentro de la fila flex (más estrecha que la tarjeta)."""
    from html.parser import HTMLParser

    import app.database as appdb

    cid = _catalogo_con_media(appdb.get_mongo_db())
    c = _entrar(store_app.test_client())
    html = c.get(f"/admin/catalogo/spreadsheets/{cid}").get_data(as_text=True)

    class _P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.pila, self.dentro_barra, self.ok_tabla = [], False, False

        def handle_starttag(self, tag, attrs):
            if tag != "div":
                return
            cls = dict(attrs).get("class", "") or ""
            self.pila.append(cls)
            if "table-responsive-custom" in cls:
                # ningún ancestro puede ser la barra de botones (d-flex gap-2)
                self.ok_tabla = not any("d-flex" in x and "gap-2" in x for x in self.pila[:-1])

        def handle_endtag(self, tag):
            if tag == "div" and self.pila:
                self.pila.pop()

    p = _P()
    p.feed(html)
    assert "table-responsive-custom" in html
    assert p.ok_tabla


# ------------------------------------------------- assets locales (sin CDN, offline)
_HOSTS_CDN = ("cdn.jsdelivr.net", "cdnjs.cloudflare.com", "code.jquery.com", "fonts.googleapis.com", "fonts.gstatic.com", "unpkg.com")


def test_assets_base_locales_y_presentes():
    raiz = os.path.join(os.path.dirname(__file__), "..", "app")
    for rel in (
        "templates/base.html",
        "templates/admin/base.html",
        "templates/partials/_assets_head.html",
    ):
        txt = open(os.path.join(raiz, rel), encoding="utf-8").read()
        assert not [h for h in _HOSTS_CDN if h in txt], rel
    vendor = os.path.join(raiz, "static", "vendor")
    for rel in (
        "bootstrap/css/bootstrap.min.css",
        "bootstrap/js/bootstrap.bundle.min.js",
        "bootstrap-icons/bootstrap-icons.min.css",
        "bootstrap-icons/fonts/bootstrap-icons.woff2",
        "fontawesome/css/all.min.css",
        "fontawesome/webfonts/fa-solid-900.woff2",
        "jquery/jquery-3.7.1.min.js",
    ):
        assert os.path.getsize(os.path.join(vendor, rel)) > 1000, rel


def test_tienda_paginas_sin_recursos_externos_y_assets_servidos(store_app):
    import re as _re

    import app.database as appdb

    cid = _catalogo_con_media(appdb.get_mongo_db())
    c = _entrar(store_app.test_client())
    for url in ("/admin/", "/catalogs/", f"/admin/catalogo/spreadsheets/{cid}"):
        html = c.get(url, follow_redirects=True).get_data(as_text=True)
        assert not [h for h in _HOSTS_CDN if h in html], url
        assert "/static/vendor/bootstrap/css/bootstrap.min.css" in html, url
    for ruta in (
        "/static/vendor/bootstrap/css/bootstrap.min.css",
        "/static/vendor/bootstrap/js/bootstrap.bundle.min.js",
        "/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2",
        "/static/vendor/fontawesome/webfonts/fa-solid-900.woff2",
        "/static/vendor/jquery/jquery-3.7.1.min.js",
    ):
        assert c.get(ruta).status_code == 200, ruta


# ------------------------------------------ tienda sin paneles de administración
@pytest.mark.parametrize(
    "ruta,bloqueada",
    [
        ("/admin/", False),
        ("/admin/dashboard", False),
        ("/admin/catalogo/spreadsheets/abc", False),
        ("/admin/catalogo/spreadsheets/abc/editar", False),
        ("/catalogs/", False),
        ("/api/health", False),
        ("/admin/backup/csv", False),
        ("/admin/backup/json", False),
        ("/admin/backup/csv/", False),
        ("/admin/backup/upload-to-drive/x.json", True),
        ("/admin/backup/create-and-upload", True),
        ("/admin/backups/list", True),
        ("/admin/usuarios", True),
        ("/admin/usuarios/create", True),
        ("/admin/password-management", True),
        ("/admin/db-status", True),
        ("/admin/db/backup", True),
        ("/admin/drive-backups", True),
        ("/admin/maintenance/local-backups", True),
        ("/admin/logs", True),
        ("/admin/logs/tail", True),
        ("/admin/system-status", True),
        ("/admin/api/system_status", True),
        ("/admin/s3-link", True),
        ("/admin/tools/", True),
        ("/dev-template/readme", True),
        ("/perfil", True),
        ("/logout", True),
        ("/api/system/check-update", True),
        ("/api/config/drive", True),
    ],
)
def test_is_blocked_path(ruta, bloqueada):
    from app.store_edition import is_blocked_path

    assert is_blocked_path(ruta) is bloqueada


def test_tienda_paneles_de_admin_dan_404_y_lo_demas_funciona(store_app):
    import app.database as appdb

    cid = _catalogo_con_media(appdb.get_mongo_db())
    c = _entrar(store_app.test_client())
    for ruta in (
        "/admin/usuarios",
        "/admin/logs",
        "/admin/logs/tail",
        "/admin/system-status",
        "/admin/api/system_status",
        "/admin/drive-backups",
        "/admin/maintenance/local-backups",
        "/admin/tools/",
        "/admin/db-status",
        "/admin/backups/list",
        "/dev-template/readme",
        "/perfil",
        "/logout",
        "/api/system/check-update",
    ):
        assert c.get(ruta).status_code == 404, ruta
    for ruta in (
        "/admin/",
        f"/admin/catalogo/spreadsheets/{cid}",
        "/catalogs/",
        "/admin/backup/csv",
        "/admin/backup/json",
    ):
        assert c.get(ruta, follow_redirects=True).status_code == 200, ruta


def test_tienda_navegacion_sin_enlaces_de_administracion(store_app):
    import app.database as appdb

    cid = _catalogo_con_media(appdb.get_mongo_db())
    c = _entrar(store_app.test_client())
    prohibido = (
        "/admin/usuarios",
        "/admin/logs",
        "/admin/system",
        "/admin/maintenance",
        "/admin/tools",
        "/admin/db",
        "/perfil",
        "/logout",
        "/dev-template",
        "/admin/drive",
        "check-update",
        "api/system_status",
        "js/dashboard.js",
        "Cerrar Sesión",
        "Gestión de Usuarios",
    )
    for url in ("/admin/", f"/admin/catalogo/spreadsheets/{cid}", "/catalogs/"):
        html = c.get(url, follow_redirects=True).get_data(as_text=True)
        assert "Usuario local" in html, url
        assert [x for x in prohibido if x in html] == [], url


def test_edicion_estandar_conserva_menus_de_administracion(store_app):
    """Con is_store_edition ausente/False las plantillas siguen mostrando todo."""
    from flask import render_template, session

    store_app.jinja_env.globals["is_store_edition"] = False
    with store_app.test_request_context("/catalogs/"):
        session["role"] = "admin"
        session["username"] = "admin"
        html = render_template("navbar.html")
    assert "Contacto" in html and "Admin" in html and "Scripts" in html and "Cerrar Sesión" in html


def test_guardar_catalogo_desde_el_editor_admin_no_redirige_a_ruta_bloqueada(store_app):
    """Regresión: tras guardar (p. ej. la miniatura) se iba a /admin/catalogos-usuario/<id> -> 404."""
    import app.database as appdb

    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "M2", "headers": "Nombre"})
    cid = str(appdb.get_mongo_db()["spreadsheets"].find_one({"name": "M2"})["_id"])
    r = c.post(
        f"/admin/catalogo/spreadsheets/{cid}/editar",
        data={"name": "M2 editado", "description": "d", "headers": "Nombre"},
    )
    assert r.status_code == 302
    destino = r.headers["Location"]
    assert "catalogos-usuario" not in destino
    assert c.get(destino).status_code == 200
    assert appdb.get_mongo_db()["spreadsheets"].find_one({"_id": __import__("bson").ObjectId(cid)})["name"] == "M2 editado"

