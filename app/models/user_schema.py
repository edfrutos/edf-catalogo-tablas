# Script: user_schema.py
# Descripción: Capa de compatibilidad de esquema para la colección `users`.
# Autor: EDF Developer - 2026-09-03
"""Compatibilidad de esquema para la colección ``users``.

La colección ``users`` de ``edf_catalogotablas`` está compartida con el cliente
.NET, que escribe los campos en PascalCase (``Name``, ``Username``, ``Role``,
``IsActive``, ``CreatedAt``, ``LastLoginAt``, ``Phone``...). La app Flask trabaja
en snake_case (``nombre``, ``username``, ``role``, ``is_active``...).

Este módulo centraliza la traducción para que el resto de la app no tenga que
conocer ambas convenciones:

* :func:`normalize_user_doc` — al **leer**: garantiza las claves snake_case a
  partir de las que existan (snake_case tiene prioridad; si no, PascalCase).
  No borra las claves PascalCase, así el cliente .NET sigue viéndolas.
* :func:`build_user_set` — al **escribir**: dado un ``$set`` en snake_case,
  añade el espejo PascalCase para que el cliente .NET no se quede desincronizado.
"""

from __future__ import annotations

from typing import Any

# Clave canónica (snake_case que usa Flask) -> orígenes posibles, por prioridad.
USER_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "username": ("username", "Username"),
    "nombre": ("nombre", "name", "Name"),
    "name": ("name", "Name", "nombre"),
    "role": ("role", "Role"),
    "is_active": ("is_active", "active", "IsActive"),
    "active": ("active", "is_active", "IsActive"),
    "created_at": ("created_at", "CreatedAt"),
    "last_login": ("last_login", "lastLoginAt", "LastLoginAt", "ultimo_login"),
    "phone": ("phone", "Phone", "telefono"),
    "company": ("company", "Company", "empresa"),
    "address": ("address", "Address", "direccion"),
    "occupation": ("occupation", "Occupation", "ocupacion"),
}

# snake_case -> PascalCase que espera el cliente .NET (para espejar al escribir).
SNAKE_TO_PASCAL: dict[str, str] = {
    "username": "Username",
    "nombre": "Name",
    "name": "Name",
    "role": "Role",
    "is_active": "IsActive",
    "active": "IsActive",
    "created_at": "CreatedAt",
    "last_login": "LastLoginAt",
    "phone": "Phone",
    "company": "Company",
    "address": "Address",
    "occupation": "Occupation",
}

_MISSING = object()


def _first_present(doc: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Devuelve el primer valor no vacío entre ``keys`` dentro de ``doc``."""
    for key in keys:
        value = doc.get(key, _MISSING)
        if value is not _MISSING and value is not None and value != "":
            return value
    return None


def normalize_user_doc(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    """Devuelve una copia de ``doc`` con las claves canónicas snake_case
    garantizadas. No modifica el original ni borra las claves PascalCase.

    Si ``doc`` es ``None`` o vacío se devuelve tal cual.
    """
    if not doc:
        return doc

    out = dict(doc)
    for canonical, sources in USER_FIELD_ALIASES.items():
        current = out.get(canonical)
        if current is None or current == "":
            value = _first_present(doc, sources)
            if value is not None:
                out[canonical] = value

    # `role` siempre normalizado a minúsculas (el .NET usa "Admin"/"User").
    role = out.get("role")
    if isinstance(role, str):
        out["role"] = role.strip().lower()

    # `is_active` / `active` como booleano coherente.
    for flag in ("is_active", "active"):
        if flag in out and not isinstance(out[flag], bool):
            out[flag] = str(out[flag]).strip().lower() in ("1", "true", "yes", "on")

    return out


def build_user_set(updates: dict[str, Any]) -> dict[str, Any]:
    """Dado un ``dict`` de actualizaciones en snake_case, devuelve otro que
    incluye además el espejo PascalCase para el cliente .NET.

    Ejemplo::

        col.update_one({"_id": _id}, {"$set": build_user_set({"role": "admin"})})
        # -> $set: {"role": "admin", "Role": "admin"}
    """
    result: dict[str, Any] = dict(updates)
    for snake, pascal in SNAKE_TO_PASCAL.items():
        if snake in updates and pascal not in result:
            result[pascal] = updates[snake]
    return result
