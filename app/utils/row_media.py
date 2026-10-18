"""Lógica compartida para documentos y multimedia de una fila.

Antes cada ruta de edición (propietario, admin, catálogos) tenía su propia
versión de esta lógica y divergían: unas sobrescribían el valor anterior,
otras lo conservaban. Aquí hay una única implementación, sin dependencias de
Flask ni de MongoDB, para que sea fácil de probar.

Modelo de datos:
- Documentos: lista en el campo principal (``Documentación`` o ``Documentos``)
  más campos auxiliares heredados ``Documentación_N`` / ``Documentos_N`` (texto).
- Multimedia: lista de nombres de archivo o URLs. Se acepta el formato antiguo
  (un único texto).
"""

from __future__ import annotations

import re
from typing import Any, Iterable
from urllib.parse import unquote

DOC_BASES = ("Documentación", "Documentos")

_UUID_PREFIX = re.compile(r"^[0-9a-fA-F]{32}_")
_EXTERNAL_PREFIXES = ("http://", "https://")
_OWN_PREFIXES = (
    "/admin/s3/",
    "/s3/",
    "/static/uploads/",
    "/imagenes_subidas/",
)


def as_list(value: Any) -> list[str]:
    """Normaliza un valor (None, texto o lista) a lista de textos no vacíos."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def media_key(item: str) -> str:
    """Clave de comparación de un elemento.

    ``/admin/s3/abc_x.md``, ``/static/uploads/abc_x.md`` y ``abc_x.md`` son el
    mismo archivo. Las URL externas se comparan completas.
    """
    item = (item or "").strip()
    if item.lower().startswith(_EXTERNAL_PREFIXES):
        # Los enlaces de nuestro propio bucket se tratan como archivo propio.
        if ".amazonaws.com/" not in item:
            return item
    clean = item.split("?", 1)[0].split("#", 1)[0]
    return unquote(clean.rsplit("/", 1)[-1])


def dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = media_key(item)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def display_name(item: str) -> str:
    """Nombre legible para mostrar o descargar (sin ruta ni prefijo uuid)."""
    name = media_key(item)
    if item.lower().startswith(_EXTERNAL_PREFIXES) and ".amazonaws.com/" not in item:
        name = unquote(item.split("?", 1)[0].rsplit("/", 1)[-1]) or item
    return _UUID_PREFIX.sub("", name) or name


def doc_base_for(header: str) -> str | None:
    """Devuelve ``Documentación``/``Documentos`` para un campo de documentos."""
    for base in DOC_BASES:
        if header == base or header.startswith(f"{base}_"):
            return base
    return None


def aux_doc_keys(row: dict, base: str) -> list[str]:
    return [k for k in row if isinstance(k, str) and k.startswith(f"{base}_")]


def collect_documents(row: dict, base: str) -> list[str]:
    """Todos los documentos de una fila para un campo base, sin duplicados.

    Une la lista principal y los campos auxiliares heredados.
    """
    items = as_list(row.get(base))
    for key in aux_doc_keys(row, base):
        items.extend(as_list(row.get(key)))
    return dedupe(items)


def collect_multimedia(row: dict) -> list[str]:
    return dedupe(as_list(row.get("Multimedia")))


def apply_changes(
    existing: Iterable[str],
    added: Iterable[str] = (),
    removed: Iterable[str] = (),
) -> list[str]:
    """existing - removed + added, conservando el orden y sin duplicados."""
    removed_keys = {media_key(r) for r in removed if isinstance(r, str)}
    kept = [x for x in dedupe(existing) if media_key(x) not in removed_keys]
    return dedupe([*kept, *as_list(list(added))])


def documents_update(
    row: dict,
    base: str,
    added: Iterable[str] = (),
    removed: Iterable[str] = (),
) -> dict[str, Any]:
    """Cambios a guardar para los documentos de ``base``.

    Devuelve ``{base: lista_final}`` y vacía los campos auxiliares heredados
    (su contenido ya está dentro de la lista), para que no reaparezcan al
    borrar ni se dupliquen al añadir.
    """
    final = apply_changes(collect_documents(row, base), added, removed)
    update: dict[str, Any] = {base: final}
    for key in aux_doc_keys(row, base):
        if row.get(key):
            update[key] = ""
    return update


def multimedia_update(
    row: dict,
    added: Iterable[str] = (),
    removed: Iterable[str] = (),
) -> list[str]:
    return apply_changes(collect_multimedia(row), added, removed)
