"""Almacén local SQLite con la interfaz mínima de PyMongo que usa la aplicación.

Se usa SOLO en la edición de tienda (``app.edition.is_store()``). Objetivo: que el
resto del código siga hablando "Mongo" sin cambios, pero sin servidor, sin red y sin
cuentas: todo vive en un único fichero SQLite dentro del contenedor de la app.

Diseño:
* Una tabla ``docs(db, coll, id, doc)``; ``doc`` es JSON canónico de ``bson.json_util``,
  que conserva ObjectId, datetime e int/float exactos.
* Las consultas se evalúan en Python. Los datos son locales y pequeños; hay una vía
  rápida por ``_id`` para el caso más frecuente.
* Soporta únicamente lo que la app usa (ver ``tests/test_local_store.py``). Lo que no
  está soportado lanza ``NotImplementedError`` con un mensaje claro, nunca devuelve
  resultados silenciosamente erróneos.
"""

from __future__ import annotations

import copy
import datetime as _dt
import os
import re
import sqlite3
import threading
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from bson import ObjectId, json_util
from pymongo.errors import DuplicateKeyError, OperationFailure
from pymongo.results import (
    DeleteResult,
    InsertManyResult,
    InsertOneResult,
    UpdateResult,
)

DEFAULT_DB_NAME = "tablateca"

_JSON = json_util.CANONICAL_JSON_OPTIONS.with_options(tz_aware=False)
_MISSING = object()


def _dumps(doc: dict) -> str:
    return json_util.dumps(doc, json_options=_JSON)


def _loads(text: str) -> dict:
    return json_util.loads(text, json_options=_JSON)


def _id_key(value: Any) -> str:
    """Clave de texto estable para un ``_id`` (distingue ObjectId de str)."""
    if isinstance(value, ObjectId):
        return "o:" + str(value)
    if isinstance(value, bool):
        return "b:" + str(value)
    if isinstance(value, int):
        return "i:" + str(value)
    if isinstance(value, str):
        return "s:" + value
    return "j:" + json_util.dumps(value, json_options=_JSON)


# --------------------------------------------------------------------------
# Rutas dentro de documentos (a.b.c)
# --------------------------------------------------------------------------


def _resolve(doc: Any, path: str) -> List[Any]:
    """Valores candidatos de ``path`` en ``doc`` (recorre listas de subdocumentos)."""
    current = [doc]
    for part in path.split("."):
        nxt: List[Any] = []
        for item in current:
            if isinstance(item, dict):
                if part in item:
                    nxt.append(item[part])
            elif isinstance(item, list):
                if part.isdigit():
                    idx = int(part)
                    if 0 <= idx < len(item):
                        nxt.append(item[idx])
                else:
                    for sub in item:
                        if isinstance(sub, dict) and part in sub:
                            nxt.append(sub[part])
        current = nxt
        if not current:
            return []
    return current


def _get_one(doc: dict, path: str, default: Any = None) -> Any:
    values = _resolve(doc, path)
    return values[0] if values else default


def _set_path(doc: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    cur: Any = doc
    for i, part in enumerate(parts[:-1]):
        if part == "$" or part.startswith("$["):
            raise NotImplementedError(
                f"Operador posicional no soportado en el almacén local: {path}"
            )
        if isinstance(cur, list):
            cur = cur[int(part)]
            continue
        nxt = cur.get(part)
        if not isinstance(nxt, (dict, list)):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    last = parts[-1]
    if last == "$" or last.startswith("$["):
        raise NotImplementedError(
            f"Operador posicional no soportado en el almacén local: {path}"
        )
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def _unset_path(doc: dict, path: str) -> None:
    parts = path.split(".")
    cur: Any = doc
    for part in parts[:-1]:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)


# --------------------------------------------------------------------------
# Comparaciones
# --------------------------------------------------------------------------


def _norm(value: Any) -> Any:
    if isinstance(value, _dt.datetime) and value.tzinfo is not None:
        return value.astimezone(_dt.timezone.utc).replace(tzinfo=None)
    return value


def _equal(a: Any, b: Any) -> bool:
    return _norm(a) == _norm(b)


def _cmp(a: Any, b: Any) -> Optional[int]:
    a, b = _norm(a), _norm(b)
    num = (int, float)
    if isinstance(a, bool) or isinstance(b, bool):
        if isinstance(a, bool) and isinstance(b, bool):
            return (a > b) - (a < b)
        return None
    if isinstance(a, num) and isinstance(b, num):
        return (a > b) - (a < b)
    if type(a) is type(b) and isinstance(a, (str, _dt.datetime, ObjectId)):
        return (a > b) - (a < b)
    return None


def _regex_flags(options: str) -> int:
    flags = 0
    for ch in options or "":
        if ch == "i":
            flags |= re.IGNORECASE
        elif ch == "m":
            flags |= re.MULTILINE
        elif ch == "s":
            flags |= re.DOTALL
        elif ch == "x":
            flags |= re.VERBOSE
    return flags


def _is_operator_dict(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and bool(value)
        and all(isinstance(k, str) and k.startswith("$") for k in value)
    )


def _match_op(values: List[Any], op: str, arg: Any, cond: dict) -> bool:
    found = bool(values)

    def any_value(pred) -> bool:
        for v in values:
            if pred(v):
                return True
            if isinstance(v, list) and any(pred(x) for x in v):
                return True
        return False

    if op == "$eq":
        return _match_value(values, arg)
    if op == "$ne":
        return not _match_value(values, arg)
    if op in ("$gt", "$gte", "$lt", "$lte"):

        def pred(v):
            c = _cmp(v, arg)
            if c is None:
                return False
            return {"$gt": c > 0, "$gte": c >= 0, "$lt": c < 0, "$lte": c <= 0}[op]

        return any_value(pred)
    if op == "$in":
        return any(_match_value(values, a) for a in arg)
    if op == "$nin":
        return not any(_match_value(values, a) for a in arg)
    if op == "$exists":
        return found == bool(arg)
    if op == "$regex":
        pattern = arg.pattern if isinstance(arg, re.Pattern) else str(arg)
        flags = arg.flags if isinstance(arg, re.Pattern) else 0
        flags |= _regex_flags(cond.get("$options", ""))
        rx = re.compile(pattern, flags)
        return any_value(lambda v: isinstance(v, str) and rx.search(v) is not None)
    if op == "$options":
        return True  # lo consume $regex
    if op == "$not":
        if _is_operator_dict(arg):
            return not all(_match_op(values, o, a, arg) for o, a in arg.items())
        return not _match_value(values, arg)
    if op == "$size":
        return any(isinstance(v, list) and len(v) == arg for v in values)
    if op == "$all":
        return all(_match_value(values, a) for a in arg)
    if op == "$elemMatch":

        def pred(v):
            if not isinstance(v, list):
                return False
            for el in v:
                if isinstance(el, dict) and not _is_operator_dict(arg):
                    if _matches(el, arg):
                        return True
                else:
                    if _is_operator_dict(arg):
                        if all(_match_op([el], o, a, arg) for o, a in arg.items()):
                            return True
                    elif _equal(el, arg):
                        return True
            return False

        return any(pred(v) for v in values)
    raise NotImplementedError(f"Operador de consulta no soportado en el almacén local: {op}")


def _match_value(values: List[Any], expected: Any) -> bool:
    if isinstance(expected, re.Pattern):
        return any(
            isinstance(v, str) and expected.search(v) is not None
            or (isinstance(v, list) and any(isinstance(x, str) and expected.search(x) for x in v))
            for v in values
        )
    if expected is None:
        return not values or any(v is None for v in values)
    for v in values:
        if _equal(v, expected):
            return True
        if isinstance(v, list) and any(_equal(x, expected) for x in v):
            return True
    return False


def _matches(doc: dict, flt: Optional[dict]) -> bool:
    if not flt:
        return True
    for key, cond in flt.items():
        if key == "$and":
            if not all(_matches(doc, sub) for sub in cond):
                return False
        elif key == "$or":
            if not any(_matches(doc, sub) for sub in cond):
                return False
        elif key == "$nor":
            if any(_matches(doc, sub) for sub in cond):
                return False
        elif key.startswith("$"):
            raise NotImplementedError(f"Operador de consulta no soportado en el almacén local: {key}")
        else:
            values = _resolve(doc, key)
            if _is_operator_dict(cond):
                if not all(_match_op(values, op, arg, cond) for op, arg in cond.items()):
                    return False
            elif not _match_value(values, cond):
                return False
    return True


# --------------------------------------------------------------------------
# Ordenación y proyección
# --------------------------------------------------------------------------


def _sort_key(value: Any) -> Tuple[int, Any]:
    value = _norm(value)
    if value is None:
        return (0, 0)
    if isinstance(value, bool):
        return (6, int(value))
    if isinstance(value, (int, float)):
        return (1, value)
    if isinstance(value, str):
        return (2, value)
    if isinstance(value, dict):
        return (3, _dumps(value))
    if isinstance(value, list):
        return (4, _dumps({"v": value}))
    if isinstance(value, ObjectId):
        return (5, str(value))
    if isinstance(value, _dt.datetime):
        return (7, value)
    return (8, str(value))


def _normalize_sort(key_or_list: Any, direction: Optional[int]) -> List[Tuple[str, int]]:
    if isinstance(key_or_list, str):
        return [(key_or_list, 1 if direction is None else int(direction))]
    return [(k, int(d)) for k, d in key_or_list]


def _apply_sort(docs: List[dict], spec: List[Tuple[str, int]]) -> List[dict]:
    out = list(docs)
    for key, direction in reversed(spec):
        out.sort(key=lambda d, k=key: _sort_key(_get_one(d, k)), reverse=direction < 0)
    return out


def _project(doc: dict, projection: Optional[dict]) -> dict:
    if not projection:
        return doc
    flags = {k: bool(v) for k, v in projection.items()}
    include_id = flags.pop("_id", True)
    if not flags:
        result = dict(doc)
        if not include_id:
            result.pop("_id", None)
        return result
    inclusion = any(flags.values())
    if inclusion:
        result: dict = {}
        if include_id and "_id" in doc:
            result["_id"] = doc["_id"]
        for key, on in flags.items():
            if not on:
                continue
            values = _resolve(doc, key)
            if values:
                _set_path(result, key, copy.deepcopy(values[0]))
        return result
    result = copy.deepcopy(doc)
    if not include_id:
        result.pop("_id", None)
    for key in flags:
        _unset_path(result, key)
    return result


# --------------------------------------------------------------------------
# Actualizaciones
# --------------------------------------------------------------------------


def _pull_matches(element: Any, cond: Any) -> bool:
    if _is_operator_dict(cond):
        return all(_match_op([element], op, arg, cond) for op, arg in cond.items())
    if isinstance(cond, dict) and isinstance(element, dict):
        return _matches(element, cond)
    return _equal(element, cond)


def _apply_update(doc: dict, update: dict, inserting: bool = False) -> None:
    if not update or not all(k.startswith("$") for k in update):
        raise ValueError("update debe usar operadores ($set, $inc, ...)")
    for op, fields in update.items():
        if op == "$set":
            for path, value in fields.items():
                _set_path(doc, path, copy.deepcopy(value))
        elif op == "$setOnInsert":
            if inserting:
                for path, value in fields.items():
                    _set_path(doc, path, copy.deepcopy(value))
        elif op == "$unset":
            for path in fields:
                _unset_path(doc, path)
        elif op == "$inc":
            for path, amount in fields.items():
                current = _get_one(doc, path, 0)
                if not isinstance(current, (int, float)) or isinstance(current, bool):
                    raise OperationFailure(f"$inc sobre un campo no numérico: {path}")
                _set_path(doc, path, current + amount)
        elif op in ("$push", "$addToSet"):
            for path, value in fields.items():
                current = _get_one(doc, path, _MISSING)
                if current is _MISSING or current is None:
                    current = []
                    _set_path(doc, path, current)
                if not isinstance(current, list):
                    raise OperationFailure(f"{op} sobre un campo que no es lista: {path}")
                items = value["$each"] if isinstance(value, dict) and "$each" in value else [value]
                for item in items:
                    item = copy.deepcopy(item)
                    if op == "$addToSet" and any(_equal(item, x) for x in current):
                        continue
                    current.append(item)
        elif op == "$pull":
            for path, cond in fields.items():
                current = _get_one(doc, path, _MISSING)
                if isinstance(current, list):
                    current[:] = [x for x in current if not _pull_matches(x, cond)]
        elif op == "$currentDate":
            for path in fields:
                _set_path(doc, path, _dt.datetime.utcnow())
        else:
            raise NotImplementedError(f"Operador de actualización no soportado en el almacén local: {op}")


def _upsert_base(flt: Optional[dict]) -> dict:
    base: dict = {}
    for key, cond in (flt or {}).items():
        if key.startswith("$") or _is_operator_dict(cond):
            continue
        _set_path(base, key, copy.deepcopy(cond))
    return base


# --------------------------------------------------------------------------
# Agregación (lo que usa la app: $match, $group, $sort, $limit, $skip, $count)
# --------------------------------------------------------------------------


def _expr(doc: dict, expr: Any) -> Any:
    if isinstance(expr, str):
        if expr == "$$ROOT":
            return copy.deepcopy(doc)
        if expr.startswith("$"):
            return copy.deepcopy(_get_one(doc, expr[1:]))
        return expr
    if isinstance(expr, dict):
        return {k: _expr(doc, v) for k, v in expr.items()}
    return expr


def _aggregate(docs: List[dict], pipeline: Iterable[dict]) -> List[dict]:
    current = docs
    for stage in pipeline:
        if len(stage) != 1:
            raise ValueError("cada etapa de aggregate debe tener un único operador")
        (name, spec), = stage.items()
        if name == "$match":
            current = [d for d in current if _matches(d, spec)]
        elif name == "$sort":
            current = _apply_sort(current, [(k, int(v)) for k, v in spec.items()])
        elif name == "$limit":
            current = current[: int(spec)]
        elif name == "$skip":
            current = current[int(spec):]
        elif name == "$count":
            current = [{spec: len(current)}]
        elif name == "$group":
            groups: Dict[str, dict] = {}
            order: List[str] = []
            for d in current:
                gid = _expr(d, spec["_id"]) if spec.get("_id") is not None else None
                gkey = _dumps({"k": gid})
                if gkey not in groups:
                    groups[gkey] = {"_id": gid, "_docs": []}
                    order.append(gkey)
                groups[gkey]["_docs"].append(d)
            result: List[dict] = []
            for gkey in order:
                entry = groups[gkey]
                out = {"_id": entry["_id"]}
                for field, acc in spec.items():
                    if field == "_id":
                        continue
                    (aop, aexpr), = acc.items()
                    vals = [_expr(d, aexpr) for d in entry["_docs"]]
                    if aop == "$sum":
                        out[field] = sum(v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool))
                    elif aop == "$push":
                        out[field] = vals
                    elif aop == "$addToSet":
                        uniq: List[Any] = []
                        for v in vals:
                            if not any(_equal(v, u) for u in uniq):
                                uniq.append(v)
                        out[field] = uniq
                    elif aop == "$first":
                        out[field] = vals[0] if vals else None
                    elif aop in ("$min", "$max"):
                        nums = [v for v in vals if v is not None]
                        out[field] = (min if aop == "$min" else max)(nums, key=_sort_key) if nums else None
                    elif aop == "$avg":
                        nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
                        out[field] = sum(nums) / len(nums) if nums else None
                    else:
                        raise NotImplementedError(f"Acumulador no soportado en el almacén local: {aop}")
                result.append(out)
            current = result
        else:
            raise NotImplementedError(f"Etapa de aggregate no soportada en el almacén local: {name}")
    return current


# --------------------------------------------------------------------------
# API tipo PyMongo
# --------------------------------------------------------------------------


class LocalCursor:
    def __init__(self, collection: "LocalCollection", flt: Optional[dict], projection: Optional[dict]):
        self._collection = collection
        self._filter = flt or {}
        self._projection = projection
        self._sort: List[Tuple[str, int]] = []
        self._limit = 0
        self._skip = 0
        self._iter: Optional[Iterator[dict]] = None

    def sort(self, key_or_list: Any, direction: Optional[int] = None) -> "LocalCursor":
        self._sort = _normalize_sort(key_or_list, direction)
        return self

    def limit(self, n: int) -> "LocalCursor":
        self._limit = int(n)
        return self

    def skip(self, n: int) -> "LocalCursor":
        self._skip = int(n)
        return self

    def _results(self) -> List[dict]:
        docs = [d for d in self._collection._all_docs() if _matches(d, self._filter)]
        if self._sort:
            docs = _apply_sort(docs, self._sort)
        if self._skip:
            docs = docs[self._skip:]
        if self._limit > 0:
            docs = docs[: self._limit]
        return [_project(d, self._projection) for d in docs]

    def __iter__(self) -> "LocalCursor":
        self._iter = iter(self._results())
        return self

    def __next__(self) -> dict:
        if self._iter is None:
            self._iter = iter(self._results())
        return next(self._iter)

    def clone(self) -> "LocalCursor":
        other = LocalCursor(self._collection, self._filter, self._projection)
        other._sort, other._limit, other._skip = list(self._sort), self._limit, self._skip
        return other

    def close(self) -> None:
        self._iter = None


class LocalCollection:
    def __init__(self, database: "LocalDatabase", name: str):
        self._database = database
        self.name = name

    # --- metadatos ---
    @property
    def database(self) -> "LocalDatabase":
        return self._database

    @property
    def full_name(self) -> str:
        return f"{self._database.name}.{self.name}"

    def __getitem__(self, sub: str) -> "LocalCollection":
        return LocalCollection(self._database, f"{self.name}.{sub}")

    def create_index(self, *args: Any, **kwargs: Any) -> str:
        return "local_index"

    def index_information(self) -> dict:
        return {"_id_": {"key": [("_id", 1)]}}

    # --- bajo nivel ---
    def _store(self) -> "LocalClient":
        return self._database.client

    def _all_docs(self) -> List[dict]:
        return self._store()._select_all(self._database.name, self.name)

    def _get_by_id(self, value: Any) -> Optional[dict]:
        return self._store()._select_one(self._database.name, self.name, _id_key(value))

    @staticmethod
    def _only_id(flt: Optional[dict]) -> Any:
        if flt and len(flt) == 1 and "_id" in flt and not _is_operator_dict(flt["_id"]):
            return flt["_id"]
        return _MISSING

    # --- lecturas ---
    def find(self, filter: Optional[dict] = None, projection: Optional[dict] = None,
             sort: Any = None, limit: int = 0, skip: int = 0, **_: Any) -> LocalCursor:
        cur = LocalCursor(self, filter, projection)
        if sort:
            cur.sort(sort)
        if limit:
            cur.limit(limit)
        if skip:
            cur.skip(skip)
        return cur

    def find_one(self, filter: Any = None, projection: Optional[dict] = None,
                 sort: Any = None, **_: Any) -> Optional[dict]:
        if filter is not None and not isinstance(filter, dict):
            filter = {"_id": filter}
        only = self._only_id(filter)
        if only is not _MISSING and not sort:
            doc = self._get_by_id(only)
            return _project(doc, projection) if doc is not None else None
        cur = self.find(filter, projection, sort=sort, limit=1)
        return next(iter(cur), None)

    def count_documents(self, filter: Optional[dict] = None, **_: Any) -> int:
        return sum(1 for d in self._all_docs() if _matches(d, filter or {}))

    def estimated_document_count(self, **_: Any) -> int:
        return len(self._all_docs())

    def distinct(self, key: str, filter: Optional[dict] = None) -> list:
        seen: List[Any] = []
        for d in self._all_docs():
            if not _matches(d, filter or {}):
                continue
            for v in _resolve(d, key):
                for x in (v if isinstance(v, list) else [v]):
                    if not any(_equal(x, s) for s in seen):
                        seen.append(x)
        return seen

    def aggregate(self, pipeline: Iterable[dict], **_: Any) -> Iterator[dict]:
        return iter(_aggregate(self._all_docs(), pipeline))

    # --- escrituras ---
    def insert_one(self, document: dict, **_: Any) -> InsertOneResult:
        if "_id" not in document:
            document["_id"] = ObjectId()
        self._store()._insert(self._database.name, self.name, _id_key(document["_id"]), _dumps(document))
        return InsertOneResult(document["_id"], acknowledged=True)

    def insert_many(self, documents: Iterable[dict], **_: Any) -> InsertManyResult:
        ids = []
        for document in documents:
            ids.append(self.insert_one(document).inserted_id)
        return InsertManyResult(ids, acknowledged=True)

    def _update(self, flt: Optional[dict], update: dict, upsert: bool, many: bool) -> UpdateResult:
        store = self._store()
        with store._lock:
            targets = [d for d in self._all_docs() if _matches(d, flt or {})]
            if not many:
                targets = targets[:1]
            matched = len(targets)
            modified = 0
            for doc in targets:
                before = copy.deepcopy(doc)
                _apply_update(doc, update)
                if doc != before:
                    store._replace(self._database.name, self.name, _id_key(doc["_id"]), _dumps(doc))
                    modified += 1
            upserted = None
            if not matched and upsert:
                doc = _upsert_base(flt)
                _apply_update(doc, update, inserting=True)
                if "_id" not in doc:
                    doc["_id"] = ObjectId()
                store._insert(self._database.name, self.name, _id_key(doc["_id"]), _dumps(doc))
                upserted = doc["_id"]
            raw = {"n": matched or (1 if upserted is not None else 0), "nModified": modified}
            if upserted is not None:
                raw["upserted"] = upserted
            return UpdateResult(raw, acknowledged=True)

    def update_one(self, filter: Optional[dict], update: dict, upsert: bool = False, **_: Any) -> UpdateResult:
        return self._update(filter, update, upsert, many=False)

    def update_many(self, filter: Optional[dict], update: dict, upsert: bool = False, **_: Any) -> UpdateResult:
        return self._update(filter, update, upsert, many=True)

    def replace_one(self, filter: Optional[dict], replacement: dict, upsert: bool = False, **_: Any) -> UpdateResult:
        store = self._store()
        with store._lock:
            targets = [d for d in self._all_docs() if _matches(d, filter or {})][:1]
            if targets:
                old = targets[0]
                new = dict(replacement)
                new["_id"] = old["_id"]
                changed = new != old
                if changed:
                    store._replace(self._database.name, self.name, _id_key(old["_id"]), _dumps(new))
                return UpdateResult({"n": 1, "nModified": 1 if changed else 0}, acknowledged=True)
            if upsert:
                new = dict(replacement)
                new.setdefault("_id", ObjectId())
                store._insert(self._database.name, self.name, _id_key(new["_id"]), _dumps(new))
                return UpdateResult({"n": 1, "nModified": 0, "upserted": new["_id"]}, acknowledged=True)
            return UpdateResult({"n": 0, "nModified": 0}, acknowledged=True)

    def find_one_and_update(self, filter: Optional[dict], update: dict, upsert: bool = False,
                            return_document: Any = False, **_: Any) -> Optional[dict]:
        store = self._store()
        with store._lock:
            before = self.find_one(filter)
            self._update(filter, update, upsert, many=False)
            if return_document:
                if before is not None:
                    return self.find_one({"_id": before["_id"]})
                return self.find_one(filter)
            return before

    def _delete(self, flt: Optional[dict], many: bool) -> DeleteResult:
        store = self._store()
        with store._lock:
            targets = [d for d in self._all_docs() if _matches(d, flt or {})]
            if not many:
                targets = targets[:1]
            for doc in targets:
                store._delete(self._database.name, self.name, _id_key(doc["_id"]))
            return DeleteResult({"n": len(targets)}, acknowledged=True)

    def delete_one(self, filter: Optional[dict], **_: Any) -> DeleteResult:
        return self._delete(filter, many=False)

    def delete_many(self, filter: Optional[dict], **_: Any) -> DeleteResult:
        return self._delete(filter, many=True)

    def drop(self) -> None:
        self._store()._drop(self._database.name, self.name)


class LocalDatabase:
    def __init__(self, client: "LocalClient", name: str):
        self.client = client
        self.name = name

    def __getitem__(self, name: str) -> LocalCollection:
        return LocalCollection(self, name)

    def __getattr__(self, name: str) -> LocalCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        return LocalCollection(self, name)

    def get_collection(self, name: str, **_: Any) -> LocalCollection:
        return LocalCollection(self, name)

    def create_collection(self, name: str, **_: Any) -> LocalCollection:
        return LocalCollection(self, name)

    def list_collection_names(self, **_: Any) -> List[str]:
        return self.client._collections(self.name)

    def drop_collection(self, name: str) -> None:
        self.client._drop(self.name, name)

    def command(self, command: Any, *args: Any, **kwargs: Any) -> dict:
        name = command if isinstance(command, str) else next(iter(command))
        if name == "ping":
            return {"ok": 1.0}
        if name == "dbstats":
            names = self.client._collections(self.name)
            objects = sum(len(self.client._select_all(self.name, c)) for c in names)
            size = os.path.getsize(self.client.path) if os.path.exists(self.client.path) else 0
            return {"db": self.name, "collections": len(names), "objects": objects,
                    "dataSize": size, "storageSize": size, "ok": 1.0}
        if name == "serverStatus":
            return {"version": "local-sqlite", "uptime": 0, "ok": 1.0,
                    "connections": {"current": 1, "available": 1}}
        if name == "currentOp":
            return {"inprog": [], "ok": 1.0}
        raise OperationFailure(f"Comando no soportado en el almacén local: {name}")


class LocalClient:
    """Sustituto de ``MongoClient`` respaldado por un fichero SQLite."""

    def __init__(self, path: str, default_db: str = DEFAULT_DB_NAME):
        self.path = path
        self._default_db = default_db
        self._lock = threading.RLock()
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS docs ("
            "db TEXT NOT NULL, coll TEXT NOT NULL, id TEXT NOT NULL, doc TEXT NOT NULL, "
            "PRIMARY KEY (db, coll, id))"
        )
        self.admin = LocalDatabase(self, "admin")

    # --- API tipo MongoClient ---
    def get_database(self, name: Optional[str] = None, **_: Any) -> LocalDatabase:
        return LocalDatabase(self, name or self._default_db)

    def __getitem__(self, name: str) -> LocalDatabase:
        return LocalDatabase(self, name)

    def list_database_names(self) -> List[str]:
        with self._lock:
            rows = self._conn.execute("SELECT DISTINCT db FROM docs").fetchall()
        return sorted({r[0] for r in rows} | {self._default_db})

    def server_info(self) -> dict:
        return {"version": "local-sqlite", "ok": 1.0}

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass

    # --- SQL ---
    def _select_all(self, db: str, coll: str) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT doc FROM docs WHERE db=? AND coll=? ORDER BY rowid", (db, coll)
            ).fetchall()
        return [_loads(r[0]) for r in rows]

    def _select_one(self, db: str, coll: str, key: str) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute(
                "SELECT doc FROM docs WHERE db=? AND coll=? AND id=?", (db, coll, key)
            ).fetchone()
        return _loads(row[0]) if row else None

    def _insert(self, db: str, coll: str, key: str, text: str) -> None:
        with self._lock:
            try:
                self._conn.execute("INSERT INTO docs VALUES (?,?,?,?)", (db, coll, key, text))
            except sqlite3.IntegrityError as exc:
                raise DuplicateKeyError(f"E11000 duplicate key error: _id {key}") from exc

    def _replace(self, db: str, coll: str, key: str, text: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE docs SET doc=? WHERE db=? AND coll=? AND id=?", (text, db, coll, key)
            )

    def _delete(self, db: str, coll: str, key: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM docs WHERE db=? AND coll=? AND id=?", (db, coll, key))

    def _drop(self, db: str, coll: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM docs WHERE db=? AND coll=?", (db, coll))

    def _collections(self, db: str) -> List[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT DISTINCT coll FROM docs WHERE db=? ORDER BY coll", (db,)
            ).fetchall()
        return [r[0] for r in rows]


# --------------------------------------------------------------------------
# Instancia única de la app
# --------------------------------------------------------------------------

_client: Optional[LocalClient] = None
_client_lock = threading.Lock()


def local_db_path() -> str:
    explicit = os.environ.get("EDF_LOCAL_DB")
    if explicit:
        return explicit
    from app.utils.paths import user_data_dir

    return os.path.join(user_data_dir(), "tablateca.sqlite3")


def get_local_client() -> LocalClient:
    global _client
    with _client_lock:
        if _client is None:
            _client = LocalClient(local_db_path())
        return _client


def reset_local_client() -> None:
    """Solo para tests: cierra y olvida la instancia única."""
    global _client
    with _client_lock:
        if _client is not None:
            _client.close()
        _client = None
