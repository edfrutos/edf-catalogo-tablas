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
        ({"images": ["/imagenes_subidas/a.png"]}, "/imagenes_subidas/a.png"),
        ({"images": ["/static/uploads/a.png"]}, "/static/uploads/a.png"),
        ({"images": [], "Multimedia": ["v.mp4", "f.JPG"]}, "/static/uploads/f.JPG"),
        ({"imagenes": "a.png"}, "/static/uploads/a.png"),
        ({"images": ["N/A"], "Multimedia": ["v.mp4"]}, None),
        ({"images": ["/logout"]}, None),
        ({"images": ["//evil.example/x.png"]}, None),
        ({"images": ["/imagenes_subidas/../../logout"]}, None),
        ({"images": ["/logout", "ok.png"]}, "/static/uploads/ok.png"),
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
    # y con rutas propias con barra inicial (antes salía /static/uploads//imagenes_subidas/..)
    db = appdb.get_mongo_db()
    db["spreadsheets"].update_one(
        {"name": "Con medios"},
        {"$set": {"data": [{"images": ["/imagenes_subidas/zz.png"]}]}},
    )
    r = c.get("/catalogs/")
    assert b'src="/imagenes_subidas/zz.png"' in r.data
    assert b"uploads//" not in r.data
