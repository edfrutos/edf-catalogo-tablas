"""Almacén local SQLite (edición de tienda): interfaz tipo PyMongo."""

import datetime as dt
import re
import threading

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.storage.local_store import LocalClient


@pytest.fixture()
def db(tmp_path):
    client = LocalClient(str(tmp_path / "t.sqlite3"))
    yield client.get_database()
    client.close()


def test_insert_find_roundtrip_conserva_tipos(db):
    now = dt.datetime(2026, 10, 26, 12, 30, 5)
    oid = ObjectId()
    res = db.users.insert_one({"email": "a@x.com", "n": 3, "f": 1.5, "when": now, "ref": oid, "ok": True})
    doc = db.users.find_one({"_id": res.inserted_id})
    assert doc["when"] == now and doc["when"].tzinfo is None
    assert doc["ref"] == oid and isinstance(doc["ref"], ObjectId)
    assert isinstance(doc["n"], int) and isinstance(doc["f"], float) and doc["ok"] is True


def test_insert_asigna_id_y_duplicado_falla(db):
    doc = {"a": 1}
    db.c.insert_one(doc)
    assert isinstance(doc["_id"], ObjectId)
    with pytest.raises(DuplicateKeyError):
        db.c.insert_one({"_id": doc["_id"], "a": 2})


def test_id_str_y_objectid_no_colisionan(db):
    oid = ObjectId()
    db.c.insert_one({"_id": oid})
    db.c.insert_one({"_id": str(oid)})
    assert db.c.count_documents({}) == 2


def test_operadores_de_consulta_usados_por_la_app(db):
    db.users.insert_many([
        {"email": "Ana@Gmail.com", "username": "ana", "role": "user", "age": 20},
        {"email": "bob@x.com", "username": "bob", "role": "admin", "age": 40, "last_login": 1},
        {"email": "eve@x.com", "username": "eve", "role": "user", "age": 30},
    ])
    f = db.users.find
    assert [d["username"] for d in f({"email": {"$regex": "^ana@gmail.com$", "$options": "i"}})] == ["ana"]
    assert {d["username"] for d in f({"$or": [{"username": "bob"}, {"username": "eve"}]})} == {"bob", "eve"}
    assert [d["username"] for d in f({"last_login": {"$exists": False}})] == ["ana", "eve"]
    assert [d["username"] for d in f({"role": {"$ne": "user"}})] == ["bob"]
    assert {d["username"] for d in f({"username": {"$in": ["ana", "eve"]}})} == {"ana", "eve"}
    assert [d["username"] for d in f({"age": {"$gt": 25}, "role": "user"})] == ["eve"]
    assert [d["username"] for d in f({"$and": [{"age": {"$gte": 30}}, {"role": "user"}]})] == ["eve"]
    assert db.users.count_documents({"role": "user"}) == 2
    assert [d["username"] for d in f({"email": re.compile("^BOB", re.I)})] == ["bob"]


def test_igualdad_con_lista_y_rutas_con_punto(db):
    db.s.insert_one({"name": "c1", "tags": ["a", "b"], "meta": {"owner": {"id": 7}}, "rows": [{"k": 1}, {"k": 2}]})
    assert db.s.count_documents({"tags": "a"}) == 1
    assert db.s.count_documents({"meta.owner.id": 7}) == 1
    assert db.s.count_documents({"rows.k": 2}) == 1
    assert db.s.count_documents({"rows.k": 3}) == 0
    assert db.s.count_documents({"nope": None}) == 1


def test_find_sort_skip_limit_proyeccion(db):
    for i, name in enumerate(["c", "a", "b", "d"]):
        db.t.insert_one({"name": name, "i": i, "extra": "x"})
    names = lambda cur: [d["name"] for d in cur]  # noqa: E731
    assert names(db.t.find().sort("name", 1)) == ["a", "b", "c", "d"]
    assert names(db.t.find().sort("name", -1).limit(2)) == ["d", "c"]
    assert names(db.t.find().sort([("name", 1)]).skip(1).limit(2)) == ["b", "c"]
    only = list(db.t.find({}, {"name": 1, "_id": 0}).sort("name", 1))
    assert only[0] == {"name": "a"}
    without = db.t.find_one({"name": "a"}, {"extra": 0})
    assert "extra" not in without and without["name"] == "a"
    assert db.t.find_one({"name": "zzz"}) is None
    assert db.t.find_one({}, sort=[("name", -1)])["name"] == "d"


def test_sort_mezcla_de_tipos_y_faltantes_no_rompe(db):
    db.t.insert_many([{"v": "b"}, {"v": 3}, {}, {"v": None}, {"v": dt.datetime(2026, 1, 1)}])
    assert len(list(db.t.find().sort("v", 1))) == 5
    assert len(list(db.t.find().sort("v", -1))) == 5


def test_update_set_inc_push_pull_unset(db):
    r = db.c.insert_one({"name": "x", "n": 1, "rows": [], "tags": ["a", "b"]})
    _id = r.inserted_id
    u = db.c.update_one({"_id": _id}, {"$set": {"name": "y", "meta.k": 5}, "$inc": {"n": 2}})
    assert (u.matched_count, u.modified_count) == (1, 1)
    db.c.update_one({"_id": _id}, {"$push": {"rows": {"a": 1}}})
    db.c.update_one({"_id": _id}, {"$push": {"rows": {"$each": [{"a": 2}, {"a": 3}]}}})
    db.c.update_one({"_id": _id}, {"$pull": {"tags": "a", "rows": {"a": 2}}})
    db.c.update_one({"_id": _id}, {"$unset": {"meta.k": ""}})
    d = db.c.find_one({"_id": _id})
    assert d["name"] == "y" and d["n"] == 3 and d["tags"] == ["b"]
    assert d["rows"] == [{"a": 1}, {"a": 3}] and d["meta"] == {}


def test_update_sin_cambios_no_cuenta_modificado_y_sin_match(db):
    r = db.c.insert_one({"a": 1})
    u = db.c.update_one({"_id": r.inserted_id}, {"$set": {"a": 1}})
    assert (u.matched_count, u.modified_count) == (1, 0)
    u = db.c.update_one({"_id": ObjectId()}, {"$set": {"a": 1}})
    assert (u.matched_count, u.modified_count) == (0, 0)


def test_upsert_y_set_on_insert(db):
    u = db.c.update_one({"email": "n@x.com"}, {"$set": {"n": 1}, "$setOnInsert": {"role": "user"}}, upsert=True)
    assert u.upserted_id is not None
    d = db.c.find_one({"email": "n@x.com"})
    assert d["n"] == 1 and d["role"] == "user"
    db.c.update_one({"email": "n@x.com"}, {"$set": {"n": 2}, "$setOnInsert": {"role": "admin"}}, upsert=True)
    d = db.c.find_one({"email": "n@x.com"})
    assert d["n"] == 2 and d["role"] == "user" and db.c.count_documents({}) == 1


def test_update_many_delete_one_delete_many(db):
    db.c.insert_many([{"g": 1, "v": 0}, {"g": 1, "v": 0}, {"g": 2, "v": 0}])
    assert db.c.update_many({"g": 1}, {"$set": {"v": 9}}).modified_count == 2
    assert db.c.delete_one({"g": 1}).deleted_count == 1
    assert db.c.delete_many({}).deleted_count == 2
    assert db.c.count_documents({}) == 0


def test_update_con_documento_de_reemplazo_se_rechaza(db):
    r = db.c.insert_one({"a": 1})
    with pytest.raises(ValueError):
        db.c.update_one({"_id": r.inserted_id}, {"a": 2})


def test_inc_sobre_campo_inexistente_lo_crea(db):
    r = db.c.insert_one({})
    db.c.update_one({"_id": r.inserted_id}, {"$inc": {"hits": 1}})
    assert db.c.find_one({"_id": r.inserted_id})["hits"] == 1


def test_aggregate_duplicados_como_en_admin_routes(db):
    db.users.insert_many([{"email": "a@x"}, {"email": "a@x"}, {"email": "b@x"}])
    out = list(db.users.aggregate([
        {"$group": {"_id": "$email", "count": {"$sum": 1}, "docs": {"$push": "$$ROOT"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]))
    assert len(out) == 1 and out[0]["_id"] == "a@x" and out[0]["count"] == 2 and len(out[0]["docs"]) == 2


def test_etapa_no_soportada_falla_claro(db):
    db.c.insert_one({"a": 1})
    with pytest.raises(NotImplementedError):
        list(db.c.aggregate([{"$lookup": {}}]))
    with pytest.raises(NotImplementedError):
        db.c.find({"a": {"$where": "1"}}).__iter__().__next__()
    with pytest.raises(NotImplementedError):
        db.c.update_one({"a": 1}, {"$set": {"rows.$.x": 1}})


def test_comandos_y_metadatos_de_cliente(tmp_path):
    client = LocalClient(str(tmp_path / "t.sqlite3"))
    assert client.admin.command("ping")["ok"] == 1.0
    database = client.get_database()
    database.users.insert_one({"a": 1})
    database.spreadsheets.insert_one({"a": 1})
    assert database.list_collection_names() == ["spreadsheets", "users"]
    assert database.command("ping")["ok"] == 1.0
    stats = database.command("dbstats")
    assert stats["collections"] == 2 and stats["objects"] == 2
    with pytest.raises(OperationFailure):
        database.command("dropDatabase")
    database.users.drop()
    assert database.list_collection_names() == ["spreadsheets"]
    assert database["spreadsheets"] is not None and database.get_collection("spreadsheets").name == "spreadsheets"
    assert database.users.database.name == database.name
    client.close()


def test_persistencia_entre_aperturas(tmp_path):
    path = str(tmp_path / "p.sqlite3")
    c1 = LocalClient(path)
    c1.get_database().c.insert_one({"_id": "k", "v": 1})
    c1.close()
    c2 = LocalClient(path)
    assert c2.get_database().c.find_one({"_id": "k"})["v"] == 1
    c2.close()


def test_find_one_por_id_vias_rapida_y_lenta_coinciden(db):
    r = db.c.insert_one({"a": 1})
    assert db.c.find_one({"_id": r.inserted_id}) == db.c.find_one({"_id": {"$in": [r.inserted_id]}})
    assert db.c.find_one(r.inserted_id)["a"] == 1


def test_find_one_and_update(db):
    r = db.c.insert_one({"n": 1})
    before = db.c.find_one_and_update({"_id": r.inserted_id}, {"$inc": {"n": 1}})
    assert before["n"] == 1
    after = db.c.find_one_and_update({"_id": r.inserted_id}, {"$inc": {"n": 1}}, return_document=True)
    assert after["n"] == 3


def test_concurrencia_de_incrementos(db):
    r = db.c.insert_one({"n": 0})

    def work():
        for _ in range(25):
            db.c.update_one({"_id": r.inserted_id}, {"$inc": {"n": 1}})

    threads = [threading.Thread(target=work) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert db.c.find_one({"_id": r.inserted_id})["n"] == 100
