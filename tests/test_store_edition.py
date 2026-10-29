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



def test_spec_mas_declara_que_no_usa_cifrado_no_exento():
    from pathlib import Path

    spec = Path(__file__).resolve().parents[1] / "packaging" / "mas" / "TablaTeca_mas.spec"
    assert '"ITSAppUsesNonExemptEncryption": False' in spec.read_text(encoding="utf-8")


def test_pagina_publica_de_privacidad_y_soporte_existente(store_app):
    c = _entrar(store_app.test_client())
    r = c.get("/privacidad")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "no recopila" in html and "does not collect" in html
    assert c.get("/soporte").status_code == 200


@pytest.mark.parametrize("ext", ["csv", "json"])
def test_backup_csv_json_en_la_tienda_es_descarga_local_sin_drive(store_app, monkeypatch, ext):
    import app.routes.admin.admin_backup_routes as rb

    def _no_debe_llamarse(*a, **k):
        raise AssertionError("la tienda no debe subir nada a Google Drive")

    monkeypatch.setattr(rb, "upload_to_drive", _no_debe_llamarse)
    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "Backup", "headers": "Nombre"})
    import app.database as appdb

    cid = str(appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Backup"})["_id"])
    c.post(f"/catalogs/add-row/{cid}", data={"Nombre": "Ana"})
    r = c.get(f"/admin/backup/{ext}")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("Content-Disposition", "")
    assert f".{ext}" in r.headers["Content-Disposition"]
    assert b"Backup" in r.data


@pytest.mark.parametrize("ext", ["csv", "json"])
def test_backup_sin_datos_en_la_tienda_no_redirige_a_ruta_bloqueada(store_app, monkeypatch, ext):
    import app.routes.admin.admin_backup_routes as rb

    monkeypatch.setattr(rb, "upload_to_drive", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Drive")))
    c = _entrar(store_app.test_client())
    r = c.get(f"/admin/backup/{ext}")
    if r.status_code == 302:
        assert "maintenance" not in r.headers["Location"]
        assert c.get(r.headers["Location"]).status_code == 200
    else:
        assert r.status_code == 200


def test_backup_con_la_cabecera_del_launcher_se_puede_guardar_desde_python(store_app):
    from app.store_edition import launch_headers

    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "Guardar", "headers": "Nombre"})
    import app.database as appdb

    cid = str(appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Guardar"})["_id"])
    c.post(f"/catalogs/add-row/{cid}", data={"Nombre": "Ana"})
    # Cliente sin sesión: como urllib en save_file() del launcher, solo con la cabecera
    r = store_app.test_client().get("/admin/backup/csv", headers=launch_headers())
    assert r.status_code == 200 and b"Guardar" in r.data


def test_el_puente_nativo_guarda_las_copias_con_el_dialogo_del_sistema():
    src = open("app/static/js/edf-native-bridge.js", encoding="utf-8").read()
    assert "/admin/backup/" in src and "edfNativeSave" in src and "BACKUP.test" in src


def test_el_puente_nativo_se_carga_con_version_nueva_para_no_servir_cache_antigua():
    for tpl in ("app/templates/base.html", "app/templates/admin/base.html"):
        src = open(tpl, encoding="utf-8").read()
        assert "edf-native-bridge.js') }}?v=20261029" in src, tpl


def _catalogo_para_exportar():
    h = "8cb8150d9b254f218e9d907f7af638e0"
    filas = [
        {
            "Fecha": "2026-10-28",
            "Nombre": "Nombre 1",
            "Descripción": "Descripción, con coma",
            "Documentación": [f"{h}_manual.pdf", "nota.md"],
            "images": [f"{h}_foto.jpeg"],
        }
    ]
    return {
        "name": "Catálogo 1",
        "description": "d",
        "headers": ["Fecha", "Nombre", "Descripción", "Documentación"],
        "rows": filas,
        "data": filas,
        "owner": "local@tablateca.local",
        "_id": "abc",
        "miniatura": "/static/uploads/x.jpg",
        "row_count": 1,
    }


def test_csv_legible_una_fila_por_registro_sin_campos_tecnicos():
    import csv
    import io

    from app.utils.store_export import catalogos_a_csv

    texto = catalogos_a_csv([_catalogo_para_exportar()])
    assert texto.startswith("﻿")  # BOM para Excel/Numbers
    filas = list(csv.reader(io.StringIO(texto.lstrip("﻿"))))
    assert filas[0] == ["Catálogo", "Fecha", "Nombre", "Descripción", "Documentación", "Imágenes"]
    assert filas[1] == ["Catálogo 1", "2026-10-28", "Nombre 1", "Descripción, con coma", "manual.pdf; nota.md", "foto.jpeg"]
    for tecnico in ("_id", "owner", "row_count", "miniatura", "data", "[{"):
        assert tecnico not in texto


def test_csv_de_varios_catalogos_une_columnas():
    import csv
    import io

    from app.utils.store_export import catalogos_a_csv

    otro = {"name": "Otro", "headers": ["Nombre", "Precio"], "rows": [{"Nombre": "X", "Precio": "5"}], "data": [{"Nombre": "X", "Precio": "5"}]}
    filas = list(csv.reader(io.StringIO(catalogos_a_csv([_catalogo_para_exportar(), otro]).lstrip("﻿"))))
    assert "Precio" in filas[0]
    assert filas[2][0] == "Otro" and filas[2][filas[0].index("Precio")] == "5"
    assert filas[1][filas[0].index("Precio")] == ""


def test_json_legible_sin_campos_tecnicos():
    import json

    from app.utils.store_export import catalogos_a_json

    datos = json.loads(catalogos_a_json([_catalogo_para_exportar()]))
    assert list(datos[0]) == ["name", "description", "headers", "created_at", "updated_at", "rows"]
    assert datos[0]["rows"][0]["Nombre"] == "Nombre 1" and "images" in datos[0]["rows"][0]
    assert "_id" not in datos[0] and "owner" not in datos[0] and "data" not in datos[0]


def test_backup_csv_de_la_tienda_entrega_el_csv_legible(store_app):
    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "Legible", "headers": "Nombre,Notas"})
    import app.database as appdb

    cid = str(appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Legible"})["_id"])
    c.post(f"/catalogs/add-row/{cid}", data={"Nombre": "Ana", "Notas": "ok"})
    cuerpo = c.get("/admin/backup/csv").get_data(as_text=True).lstrip("﻿")
    assert cuerpo.splitlines()[0] == "Catálogo,Nombre,Notas"
    assert "Legible,Ana,ok" in cuerpo


# ----------------------------------------------------------------- Ajustes
def test_validar_perfil():
    from app.store_settings import validar_perfil

    ok, err = validar_perfil({"nombre": " Ana ", "email": "a@b.es", "organizacion": "X"})
    assert not err and ok["nombre"] == "Ana"
    assert validar_perfil({"nombre": ""})[1]
    assert validar_perfil({"nombre": "A", "email": "no-es-correo"})[1]
    assert validar_perfil({"nombre": "A" * 101})[1]
    assert not validar_perfil({"nombre": "A", "email": ""})[1]


def test_es_escribible(tmp_path):
    from app.store_settings import es_escribible

    assert es_escribible(str(tmp_path))
    assert not es_escribible("")
    assert not es_escribible("relativa/ruta")
    assert not es_escribible(str(tmp_path / "no_existe"))
    assert list(tmp_path.iterdir()) == []


def test_marcador_sin_pyobjc_no_falla(tmp_path):
    from app import store_settings as s

    assert s.abrir_marcador("") == ""
    if not os.path.exists("/System/Library"):  # fuera de macOS no hay Foundation
        assert s.crear_marcador(str(tmp_path)) == ""
        assert s.preparar_carpeta(str(tmp_path)) == {"carpeta": str(tmp_path), "marcador": ""}


def test_ajustes_perfil_actualiza_nombre_y_barra(store_app):
    c = _entrar(store_app.test_client())
    assert b"Usuario local" in c.get("/ajustes").data
    r = c.post("/ajustes/perfil", data={"nombre": "Eugenio", "email": "e@x.es", "organizacion": "EDF"})
    assert r.status_code == 302
    html = c.get("/ajustes").get_data(as_text=True)
    assert 'value="Eugenio"' in html and 'value="e@x.es"' in html
    assert "Eugenio</span>" in html


def test_ajustes_perfil_invalido_no_guarda(store_app):
    c = _entrar(store_app.test_client())
    c.post("/ajustes/perfil", data={"nombre": "", "email": "mal"})
    from app import store_settings
    import app.database as appdb

    assert store_settings.cargar(appdb.get_mongo_db())["email"] == ""


def test_ajustes_carpeta_y_copia_zip(store_app, tmp_path):
    import zipfile

    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "Para copia", "headers": "Nombre"})
    destino = tmp_path / "copias"
    destino.mkdir()
    c.post("/ajustes/carpeta", data={"carpeta": str(destino)})
    assert str(destino) in c.get("/ajustes").get_data(as_text=True)
    r = c.post("/ajustes/guardar-copia")
    assert r.status_code == 302
    zips = list(destino.glob("TablaTeca_copia_*.zip"))
    assert len(zips) == 1 and not list(destino.glob("*.parte"))
    with zipfile.ZipFile(zips[0]) as z:
        assert "manifest.json" in z.namelist() and "catalogos.json" in z.namelist()


def test_ajustes_carpeta_inaccesible_se_rechaza(store_app, tmp_path):
    c = _entrar(store_app.test_client())
    c.post("/ajustes/carpeta", data={"carpeta": str(tmp_path / "no_existe")})
    from app import store_settings
    import app.database as appdb

    assert store_settings.cargar(appdb.get_mongo_db())["carpeta"] == ""
    c.post("/ajustes/guardar-copia")  # sin carpeta: no revienta
    assert c.get("/ajustes").status_code == 200


def test_ajustes_olvidar_carpeta(store_app, tmp_path):
    c = _entrar(store_app.test_client())
    c.post("/ajustes/carpeta", data={"carpeta": str(tmp_path)})
    c.post("/ajustes/carpeta/olvidar")
    from app import store_settings
    import app.database as appdb

    assert store_settings.cargar(appdb.get_mongo_db())["carpeta"] == ""


def test_ajustes_no_existe_en_la_edicion_estandar(monkeypatch):
    monkeypatch.delenv("EDF_EDITION", raising=False)
    from app import edition

    assert not edition.is_store()


def test_launcher_expone_choose_folder_y_entitlement_de_marcadores():
    src = open("launcher_native_websockets.py", encoding="utf-8").read()
    assert "def choose_folder" in src and "preparar_carpeta" in src
    plist = open("packaging/mas/entitlements-mas.plist", encoding="utf-8").read()
    assert "com.apple.security.files.bookmarks.app-scope" in plist

# ------------------------------------------------------------- copia ZIP completa
def _zip_bytes(manifest=None, catalogos="[]", archivos=None, nombres_extra=()):
    import io
    import json
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if manifest is not False:
            z.writestr("manifest.json", json.dumps(manifest or {"app": "TablaTeca", "formato": 1}))
        if catalogos is not None:
            z.writestr("catalogos.json", catalogos)
        for n, c in (archivos or {}).items():
            z.writestr(n, c)
        for n in nombres_extra:
            z.writestr(n, b"x")
    return buf.getvalue()


@pytest.fixture()
def zip_app(store_app, tmp_path):
    store_app.config["STORE_BACKUP_DIR"] = str(tmp_path / "copias")
    store_app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    os.makedirs(store_app.config["UPLOAD_FOLDER"])
    return store_app


def _importar(c, datos, confirmo=True, nombre="copia.zip"):
    import io

    form = {"archivo": (io.BytesIO(datos), nombre)}
    if confirmo:
        form["confirmo"] = "1"
    return c.post("/admin/backup/importar", data=form, content_type="multipart/form-data")


def test_zip_exportar_incluye_catalogos_y_archivos(zip_app):
    import io
    import json
    import zipfile

    import app.database as appdb

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Para copia", "headers": "Nombre"})
    with open(os.path.join(zip_app.config["UPLOAD_FOLDER"], "abc_foto.png"), "wb") as f:
        f.write(b"PNGDATA")
    r = c.get("/admin/backup/zip")
    assert r.status_code == 200 and r.mimetype == "application/zip"
    assert "attachment" in r.headers["Content-Disposition"] and ".zip" in r.headers["Content-Disposition"]
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        m = json.loads(z.read("manifest.json"))
        assert m["app"] == "TablaTeca" and m["catalogos"] == 1 and m["archivos"] == 1
        assert z.read("uploads/abc_foto.png") == b"PNGDATA"
        assert "Para copia" in z.read("catalogos.json").decode()
    assert appdb.get_mongo_db()["spreadsheets"].count_documents({}) == 1  # exportar no modifica nada


def test_zip_ida_y_vuelta_restaura_catalogos_y_archivos(zip_app):
    import app.database as appdb

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Original", "headers": "Nombre"})
    col = appdb.get_mongo_db()["spreadsheets"]
    cid = col.find_one({"name": "Original"})["_id"]
    ruta = os.path.join(zip_app.config["UPLOAD_FOLDER"], "k_doc.pdf")
    with open(ruta, "wb") as f:
        f.write(b"%PDF")
    copia = c.get("/admin/backup/zip").data

    col.delete_many({})
    os.remove(ruta)
    c.post("/catalogs/create", data={"name": "Intruso", "headers": "A"})
    r = _importar(c, copia)
    assert r.status_code == 302 and r.headers["Location"].rstrip("/").endswith("/catalogs")
    nombres = [d["name"] for d in col.find()]
    assert nombres == ["Original"]  # sustituye: «Intruso» ya no está
    assert col.find_one({"name": "Original"})["_id"] == cid
    assert open(ruta, "rb").read() == b"%PDF"
    # copia automática del estado anterior
    previas = os.listdir(zip_app.config["STORE_BACKUP_DIR"])
    assert len(previas) == 1 and previas[0].startswith("antes_de_importar_")


def test_zip_importar_reasigna_el_propietario_al_usuario_local(zip_app):
    import json

    import app.database as appdb

    c = _entrar(zip_app.test_client())
    doc = {"_id": {"$oid": "6ae24593a4126a462fe85fab"}, "name": "Ajeno", "headers": ["A"], "rows": [], "data": [],
           "owner": "otro", "created_by": "otro", "email": "otro@x.com", "owner_name": "Otro"}
    _importar(c, _zip_bytes(catalogos=json.dumps([doc])))
    got = appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Ajeno"})
    assert got["owner"] == "tablateca" and got["created_by"] == "tablateca" and got["email"] == "local@tablateca.local"


@pytest.mark.parametrize(
    "nombre",
    ["uploads/../fuera.txt", "../fuera.txt", "/abs.txt", "uploads/sub/dir.txt", "uploads/..\\x.txt", "otra/x.txt", "uploads/.oculto"],
)
def test_zip_rechaza_rutas_peligrosas_y_no_escribe_nada(zip_app, tmp_path, nombre):
    import app.database as appdb

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Intacto", "headers": "A"})
    r = _importar(c, _zip_bytes(nombres_extra=[nombre]))
    assert r.status_code == 302 and "/admin/backup/importar" in r.headers["Location"]
    assert [d["name"] for d in appdb.get_mongo_db()["spreadsheets"].find()] == ["Intacto"]
    assert not (tmp_path / "fuera.txt").exists() and not (tmp_path / "abs.txt").exists()
    assert os.listdir(zip_app.config["UPLOAD_FOLDER"]) == []
    assert not os.path.exists(zip_app.config["STORE_BACKUP_DIR"])  # ni siquiera llega a la copia previa


@pytest.mark.parametrize(
    "datos",
    [
        b"esto no es un zip",
        None,  # sin manifiesto
    ],
)
def test_zip_rechaza_archivos_que_no_son_de_tablateca(zip_app, datos):
    import app.database as appdb

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Intacto", "headers": "A"})
    datos = datos if datos is not None else _zip_bytes(manifest=False)
    assert _importar(c, datos).status_code == 302
    assert [d["name"] for d in appdb.get_mongo_db()["spreadsheets"].find()] == ["Intacto"]


def test_zip_rechaza_otra_app_o_formato_futuro_y_catalogos_corruptos(zip_app):
    import app.database as appdb

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Intacto", "headers": "A"})
    for datos in (
        _zip_bytes(manifest={"app": "Otra", "formato": 1}),
        _zip_bytes(manifest={"app": "TablaTeca", "formato": 99}),
        _zip_bytes(catalogos="{no json"),
        _zip_bytes(catalogos='{"no": "lista"}'),
        _zip_bytes(catalogos=None),
    ):
        assert _importar(c, datos).status_code == 302
        assert [d["name"] for d in appdb.get_mongo_db()["spreadsheets"].find()] == ["Intacto"]


def test_zip_sin_confirmar_no_importa_nada(zip_app):
    import app.database as appdb

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Intacto", "headers": "A"})
    _importar(c, _zip_bytes(catalogos='[{"name": "Nuevo", "headers": []}]'), confirmo=False)
    assert [d["name"] for d in appdb.get_mongo_db()["spreadsheets"].find()] == ["Intacto"]


def test_zip_si_la_sustitucion_falla_se_restauran_los_catalogos_anteriores(zip_app, monkeypatch):
    import app.database as appdb
    from app.storage import local_store

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Anterior", "headers": "A"})
    col_cls = local_store.LocalCollection
    original = col_cls.insert_many
    llamadas = {"n": 0}

    def _falla_la_primera(self, docs, **k):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            raise RuntimeError("disco lleno")
        return original(self, docs, **k)

    monkeypatch.setattr(col_cls, "insert_many", _falla_la_primera)
    r = _importar(c, _zip_bytes(catalogos='[{"name": "Nuevo", "headers": []}]'))
    assert r.status_code == 302 and "/admin/backup/importar" in r.headers["Location"]
    assert [d["name"] for d in appdb.get_mongo_db()["spreadsheets"].find()] == ["Anterior"]


def test_zip_rutas_permitidas_en_la_tienda_y_menu(store_app):
    from app.store_edition import is_blocked_path

    assert not is_blocked_path("/admin/backup/zip") and not is_blocked_path("/admin/backup/importar")
    assert is_blocked_path("/admin/backup/otra")
    c = _entrar(store_app.test_client())
    assert c.get("/admin/backup/importar").status_code == 200
    html = c.get("/admin/").get_data(as_text=True)
    assert "Copia completa (ZIP)" in html and "Importar copia (ZIP)" in html


def test_zip_el_launcher_puede_descargar_la_copia_con_su_cabecera(zip_app):
    from app.store_edition import launch_headers

    r = zip_app.test_client().get("/admin/backup/zip", headers=launch_headers())
    assert r.status_code == 200 and r.mimetype == "application/zip"
    # pero no puede abrir el formulario de importar sin sesión
    assert zip_app.test_client().get("/admin/backup/importar", headers=launch_headers()).status_code != 200

def test_dashboard_de_la_tienda_no_ofrece_buscar_por_propietario(store_app):
    c = _entrar(store_app.test_client())
    html = c.get("/admin/").get_data(as_text=True)
    assert "Usuario propietario" not in html
    assert "nombre o propietario" not in html
    assert 'name="search_type" value="name"' in html
    assert "<th>Propietario</th>" not in html


def test_volver_del_catalogo_en_la_tienda_va_siempre_al_listado(store_app):
    import app.database as appdb

    c = _entrar(store_app.test_client())
    c.post("/catalogs/create", data={"name": "Vuelta", "headers": "Nombre"})
    cid = str(appdb.get_mongo_db()["spreadsheets"].find_one({"name": "Vuelta"})["_id"])
    # el referente es la pantalla de edición: antes «Volver» devolvía a ella
    html = c.get(
        f"/admin/catalogo/spreadsheets/{cid}",
        headers={"Referer": f"http://127.0.0.1/catalogs/{cid}/edit"},
    ).get_data(as_text=True)
    import re

    href = re.search(r'<a href="([^"]*)" class="btn btn-light">\s*<i class="bi bi-arrow-left"></i> Volver', html).group(1)
    assert href.rstrip("/") == "/catalogs"


# ----------------------------------------------------------------- Google Drive (Ajustes)
CRED_OK = (
    b'{"installed": {"client_id": "123-abc.apps.googleusercontent.com", '
    b'"client_secret": "secreto-cliente", "auth_uri": "https://x", "token_uri": "https://y"}}'
)


@pytest.fixture()
def drive_dir(monkeypatch, tmp_path):
    carpeta = tmp_path / "gdrive"
    monkeypatch.setenv("EDF_STORE_DRIVE_DIR", str(carpeta))
    from app import store_drive

    store_drive.cancelar()
    yield carpeta
    store_drive.cancelar()


class _Resp:
    def __init__(self, status=200, cuerpo=None, headers=None):
        self.status_code, self._c, self.headers = status, cuerpo or {}, headers or {}

    def json(self):
        return self._c


class _Google:
    """Sustituye al módulo requests dentro de store_drive y registra las llamadas."""

    def __init__(self, token_status=200, scope="https://www.googleapis.com/auth/drive.file"):
        self.llamadas, self.token_status, self.scope = [], token_status, scope
        self.carpeta_existe = False

    def post(self, url, **kw):
        self.llamadas.append(("post", url, kw))
        if url.endswith("/token"):
            if self.token_status != 200:
                return _Resp(self.token_status, {"error": "invalid_grant"})
            cuerpo = {"access_token": "acceso-1", "expires_in": 3600, "scope": self.scope}
            if kw["data"].get("grant_type") == "authorization_code":
                cuerpo["refresh_token"] = "refresco-secreto"
            return _Resp(200, cuerpo)
        if url.endswith("/revoke"):
            return _Resp(200)
        if "uploadType=resumable" in url or kw.get("params", {}).get("uploadType") == "resumable":
            return _Resp(200, headers={"Location": "https://upload.example/sesion1"})
        return _Resp(200, {"id": "carpeta-nueva"})

    def get(self, url, **kw):
        self.llamadas.append(("get", url, kw))
        return _Resp(200, {"files": [{"id": "carpeta-1"}] if self.carpeta_existe else []})

    def put(self, url, **kw):
        self.llamadas.append(("put", url, {**kw, "cuerpo": kw["data"].read()}))
        return _Resp(200, {"id": "archivo-1", "name": "copia.zip"})


@pytest.fixture()
def google(monkeypatch):
    from app import store_drive

    g = _Google()
    monkeypatch.setattr(store_drive, "requests", g)
    return g


def test_drive_valida_credentials_json():
    from app.store_drive import DriveError, validar_credenciales

    assert validar_credenciales(CRED_OK)["client_secret"] == "secreto-cliente"
    for malo in (
        b"no es json",
        b"[]",
        b'{"web": {"client_id": "a.apps.googleusercontent.com", "client_secret": "s"}}',
        b'{"otra": 1}',
        b'{"installed": {"client_id": "malo", "client_secret": "s"}}',
        b'{"installed": {"client_id": "a.apps.googleusercontent.com"}}',
        b"x" * 30000,
    ):
        with pytest.raises(DriveError):
            validar_credenciales(malo)


@pytest.mark.skipif(os.name != "posix", reason="permisos POSIX")
def test_drive_credenciales_y_token_se_guardan_con_permisos_privados(drive_dir, google):
    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    assert (drive_dir / "credentials.json").stat().st_mode & 0o777 == 0o600


def _autorizar(url_auth):
    """Hace de navegador: devuelve a la app el código con el state de la URL de Google."""
    import urllib.request
    from urllib.parse import parse_qs, urlsplit

    q = parse_qs(urlsplit(url_auth).query)
    destino = q["redirect_uri"][0] + "?" + "code=codigo-1&state=" + q["state"][0]
    urllib.request.urlopen(destino, timeout=5).read()
    return q


def _esperar(cond, segundos=5):
    import time

    limite = time.time() + segundos
    while time.time() < limite:
        if cond():
            return True
        time.sleep(0.05)
    return False


def test_drive_flujo_oauth_con_pkce_y_alcance_minimo(drive_dir, google):
    import base64
    import hashlib

    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    abiertas = []
    url = store_drive.iniciar_autorizacion(abrir=abiertas.append)
    assert abiertas == [url] and store_drive.estado()["esperando"]
    q = _autorizar(url)
    assert q["scope"] == ["https://www.googleapis.com/auth/drive.file"]
    assert q["code_challenge_method"] == ["S256"] and q["access_type"] == ["offline"]
    assert q["redirect_uri"][0].startswith("http://127.0.0.1:")
    assert _esperar(lambda: store_drive.estado()["conectado"])
    canje = [c for c in google.llamadas if c[0] == "post" and c[1].endswith("/token")][0][2]["data"]
    desafio = base64.urlsafe_b64encode(hashlib.sha256(canje["code_verifier"].encode()).digest())
    assert desafio.decode().rstrip("=") == q["code_challenge"][0]
    assert canje["code"] == "codigo-1" and canje["redirect_uri"] == q["redirect_uri"][0]
    e = store_drive.estado()
    assert e["conectado"] and not e["esperando"] and not e["error"]


def test_drive_rechaza_state_ajeno_y_no_guarda_token(drive_dir, google):
    import urllib.error
    import urllib.request
    from urllib.parse import parse_qs, urlsplit

    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    url = store_drive.iniciar_autorizacion(abrir=lambda u: None)
    redirect = parse_qs(urlsplit(url).query)["redirect_uri"][0]
    urllib.request.urlopen(redirect + "?code=x&state=otro", timeout=5).read()
    assert _esperar(lambda: not store_drive.estado()["esperando"])
    e = store_drive.estado()
    assert not e["conectado"] and e["error"]
    assert not any(c[1].endswith("/token") for c in google.llamadas)


def test_drive_rechaza_si_no_se_concede_el_alcance(drive_dir, monkeypatch):
    from app import store_drive

    monkeypatch.setattr(store_drive, "requests", _Google(scope="openid"))
    store_drive.guardar_credenciales(CRED_OK)
    _autorizar(store_drive.iniciar_autorizacion(abrir=lambda u: None))
    assert _esperar(lambda: not store_drive.estado()["esperando"])
    assert not store_drive.estado()["conectado"] and store_drive.estado()["error"]


def test_drive_subir_crea_carpeta_y_envia_el_zip(drive_dir, google, tmp_path):
    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    _autorizar(store_drive.iniciar_autorizacion(abrir=lambda u: None))
    assert _esperar(lambda: store_drive.estado()["conectado"])
    zip_ = tmp_path / "c.zip"
    zip_.write_bytes(b"PK-contenido")
    r = store_drive.subir(str(zip_), "copia.zip")
    assert r == {"id": "archivo-1", "name": "copia.zip"}
    put = [c for c in google.llamadas if c[0] == "put"][0]
    assert put[1] == "https://upload.example/sesion1" and put[2]["cuerpo"] == b"PK-contenido"
    assert put[2]["headers"]["Authorization"] == "Bearer acceso-1"
    # primera vez: busca la carpeta, no existe, la crea
    assert any(c[0] == "post" and c[1] == store_drive.DRIVE_FILES for c in google.llamadas)


def test_drive_reutiliza_la_carpeta_existente(drive_dir, google, tmp_path):
    from app import store_drive

    google.carpeta_existe = True
    store_drive.guardar_credenciales(CRED_OK)
    _autorizar(store_drive.iniciar_autorizacion(abrir=lambda u: None))
    assert _esperar(lambda: store_drive.estado()["conectado"])
    zip_ = tmp_path / "c.zip"
    zip_.write_bytes(b"x")
    store_drive.subir(str(zip_), "c.zip")
    assert not any(c[0] == "post" and c[1] == store_drive.DRIVE_FILES for c in google.llamadas)
    inicio = [c for c in google.llamadas if c[0] == "post" and "upload" in c[1]][0]
    assert "carpeta-1" in inicio[2]["data"]


def test_drive_refresca_el_token_caducado_y_borra_el_permiso_revocado(drive_dir, google, tmp_path):
    import json

    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    caducado = {"refresh_token": "refresco-secreto", "access_token": "viejo", "expires_at": 0}
    (drive_dir / "token.json").write_text(json.dumps(caducado))
    assert store_drive._token_de_acceso() == "acceso-1"
    assert json.loads((drive_dir / "token.json").read_text())["refresh_token"] == "refresco-secreto"

    (drive_dir / "token.json").write_text(json.dumps(caducado))
    google.token_status = 400
    with pytest.raises(store_drive.PermisoCaducado):
        store_drive._token_de_acceso()
    assert not (drive_dir / "token.json").exists() and not store_drive.estado()["conectado"]


def test_drive_desconectar_revoca_y_borra_el_token(drive_dir, google):
    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    _autorizar(store_drive.iniciar_autorizacion(abrir=lambda u: None))
    assert _esperar(lambda: store_drive.estado()["conectado"])
    store_drive.desconectar()
    assert not store_drive.estado()["conectado"] and store_drive.estado()["credenciales"]
    assert any(c[1].endswith("/revoke") for c in google.llamadas)
    store_drive.quitar_credenciales()
    assert not store_drive.estado()["credenciales"]


def test_drive_nuevas_credenciales_invalidan_el_token_anterior(drive_dir, google):
    from app import store_drive

    store_drive.guardar_credenciales(CRED_OK)
    (drive_dir / "token.json").write_text('{"refresh_token": "r", "access_token": "a", "expires_at": 9999999999}')
    assert store_drive.estado()["conectado"]
    store_drive.guardar_credenciales(CRED_OK)
    assert not store_drive.estado()["conectado"]


def test_drive_rutas_de_ajustes_y_el_secreto_nunca_llega_a_la_pagina(zip_app, drive_dir, google, monkeypatch, tmp_path):
    import io

    from app import store_drive

    monkeypatch.setattr(store_drive.webbrowser, "open", lambda u: True)
    c = _entrar(zip_app.test_client())
    html = c.get("/ajustes").get_data(as_text=True)
    assert "credentials.json" in html and "Guardar credenciales" in html

    c.post("/ajustes/drive/credenciales", data={"archivo": (io.BytesIO(b"basura"), "x.json")}, content_type="multipart/form-data")
    assert not store_drive.estado()["credenciales"]
    c.post("/ajustes/drive/credenciales", data={"archivo": (io.BytesIO(CRED_OK), "credentials.json")}, content_type="multipart/form-data")
    assert store_drive.estado()["credenciales"]
    html = c.get("/ajustes").get_data(as_text=True)
    assert "Conectar con Google" in html and "secreto-cliente" not in html

    c.post("/ajustes/drive/conectar")
    assert c.get("/ajustes/drive/estado").get_json()["esperando"] is True
    assert "Esperando la autorización" in c.get("/ajustes").get_data(as_text=True)
    c.post("/ajustes/drive/cancelar")
    assert c.get("/ajustes/drive/estado").get_json()["esperando"] is False

    (drive_dir / "token.json").write_text('{"refresh_token": "refresco-secreto", "access_token": "acceso-1", "expires_at": 9999999999}')
    c.post("/catalogs/create", data={"name": "Para Drive", "headers": "Nombre"})
    html = c.get("/ajustes").get_data(as_text=True)
    assert "Subir copia a Drive ahora" in html and "refresco-secreto" not in html
    r = c.post("/ajustes/drive/subir", follow_redirects=True)
    assert "Copia subida a Google Drive" in r.get_data(as_text=True)
    put = [x for x in google.llamadas if x[0] == "put"][0]
    assert put[2]["cuerpo"][:2] == b"PK"  # es el ZIP de la copia
    assert not any(n.endswith(".zip") for n in os.listdir(drive_dir))  # el temporal se borra

    c.post("/ajustes/drive/desconectar")
    assert not store_drive.estado()["conectado"]


def test_drive_sin_credenciales_no_se_puede_conectar(drive_dir, google):
    from app import store_drive

    with pytest.raises(store_drive.DriveError):
        store_drive.iniciar_autorizacion(abrir=lambda u: None)

class _SinSeekable:
    """Como SpooledTemporaryFile en Python 3.10: lee y se posiciona, pero no tiene seekable()."""

    def __init__(self, datos: bytes):
        import io

        self._f = io.BytesIO(datos)
        self.read, self.seek, self.tell = self._f.read, self._f.seek, self._f.tell


def test_zip_se_importa_aunque_el_upload_no_tenga_seekable_como_en_python_310(zip_app):
    """Regresión: en el paquete (Python 3.10) el restore fallaba con AttributeError: seekable."""
    import app.database as appdb
    from app.store_backup_zip import importar_zip

    c = _entrar(zip_app.test_client())
    c.post("/catalogs/create", data={"name": "Original", "headers": "Nombre"})
    col = appdb.get_mongo_db()["spreadsheets"]
    ruta = os.path.join(zip_app.config["UPLOAD_FOLDER"], "k_doc.pdf")
    with open(ruta, "wb") as f:
        f.write(b"%PDF")
    copia = c.get("/admin/backup/zip").data
    col.delete_many({})
    os.remove(ruta)

    from app.store_edition import ensure_local_user

    res = importar_zip(
        appdb.get_mongo_db(),
        zip_app.config["UPLOAD_FOLDER"],
        _SinSeekable(copia),
        zip_app.config["STORE_BACKUP_DIR"],
        ensure_local_user(appdb.get_mongo_db()),
    )
    assert res["catalogos"] == 1 and res["archivos"] == 1
    assert [d["name"] for d in col.find()] == ["Original"]
    assert open(ruta, "rb").read() == b"%PDF"


def test_zip_sin_seekable_y_corrupto_sigue_dando_mensaje_claro(zip_app):
    import app.database as appdb
    from app.store_backup_zip import ZipInvalido, importar_zip
    from app.store_edition import ensure_local_user

    with pytest.raises(ZipInvalido):
        importar_zip(
            appdb.get_mongo_db(),
            zip_app.config["UPLOAD_FOLDER"],
            _SinSeekable(b"esto no es un zip"),
            zip_app.config["STORE_BACKUP_DIR"],
            ensure_local_user(appdb.get_mongo_db()),
        )


def test_zip_y_ajustes_muestran_sus_mensajes_en_su_propia_pagina(zip_app):
    """Regresión: los flash vivían dentro del bloque content de admin/base.html y estas páginas
    lo sobrescriben; el error se veía después, en otra pantalla."""
    c = _entrar(zip_app.test_client())
    r = _importar(c, b"esto no es un zip")
    assert r.status_code == 302 and r.headers["Location"].endswith("/admin/backup/importar")
    html = c.get(r.headers["Location"]).get_data(as_text=True)
    assert "no es un ZIP válido" in html and html.count("no es un ZIP válido") == 1

    c.post("/ajustes/perfil", data={"nombre": ""})
    html = c.get("/ajustes").get_data(as_text=True)
    assert "El nombre es obligatorio." in html and html.count("El nombre es obligatorio.") == 1
    assert "El nombre es obligatorio." not in c.get("/ajustes").get_data(as_text=True)  # ya consumido
