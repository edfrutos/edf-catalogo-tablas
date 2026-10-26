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


def test_tienda_entra_sin_login_y_usa_sqlite(store_app, tmp_path):
    import app.database as appdb
    from app.storage.local_store import LocalClient

    assert isinstance(appdb.get_mongo_client(), LocalClient)
    c = store_app.test_client()
    r = c.get("/", follow_redirects=True)
    assert r.status_code == 200
    with c.session_transaction() as s:
        assert s["logged_in"] is True and s["role"] == "admin"
    users = appdb.get_mongo_db()["users"]
    assert users.count_documents({"email": "local@tablateca.local"}) == 1
    c.get("/", follow_redirects=True)
    assert users.count_documents({}) == 1  # no duplica el usuario local


@pytest.mark.parametrize("path", ["/login", "/register", "/welcome", "/auth/login", "/auth/register"])
def test_pantallas_de_cuenta_redirigen_a_inicio(store_app, path):
    r = store_app.test_client().get(path)
    assert r.status_code == 302 and r.headers["Location"].endswith("/")


def test_crear_catalogo_anadir_editar_ver_y_borrar(store_app, tmp_path):
    import app.database as appdb

    c = store_app.test_client()
    c.get("/")
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
    import app.database as appdb
    from app.storage import local_store

    c = store_app.test_client()
    c.get("/")
    c.post("/catalogs/create", data={"name": "Persistente", "headers": "A"})
    local_store.reset_local_client()
    again = local_store.LocalClient(str(tmp_path / "t.sqlite3"))
    try:
        assert again.get_database()["spreadsheets"].count_documents({"name": "Persistente"}) == 1
    finally:
        again.close()
