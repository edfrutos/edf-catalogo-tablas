"""
Utilidades comunes para catálogos.

Objetivo:
- Centralizar la compatibilidad entre `data` y `rows`.
- Considerar `data` como fuente principal.
- Mantener `rows` solo como compatibilidad con código/plantillas antiguas.
"""

from __future__ import annotations

from typing import Any


def normalize_catalog_rows(catalog: dict[str, Any]) -> dict[str, Any]:
    """
    Normaliza un catálogo para que siempre tenga:

    - data
    - rows
    - row_count
    - num_rows

    Regla principal:
    - Si `data` existe y es lista, manda `data`.
    - Si `data` no existe o no es lista, pero `rows` sí, se usa `rows`.
    - `rows` se sincroniza desde `data` para compatibilidad.
    """

    data = catalog.get("data")
    rows = catalog.get("rows")

    if isinstance(data, list):
        normalized_rows = data
    elif isinstance(rows, list):
        normalized_rows = rows
        catalog["data"] = normalized_rows
    else:
        normalized_rows = []
        catalog[""] = normalized_rows

    catalog["rows"] = normalized_rows
    catalog["row_count"] = len(normalized_rows)
    catalog["num_rows"] = len(normalized_rows)

    return catalog


def get_catalog_rows(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Devuelve las filas normalizadas de un catálogo.

    Siempre usa `data` como fuente preferente.
    """

    normalize_catalog_rows(catalog)
    rows = catalog.get("data", [])

    if isinstance(rows, list):
        return rows

    return []


def sync_row_update_paths(update_data: dict[str, Any]) -> dict[str, Any]:
    """
    Cuando se actualiza una ruta tipo:

        data.3.Nombre

    añade también:

        rows.3.Nombre

    Y viceversa.

    Esto mantiene compatibilidad mientras existan ambas estructuras.
    """

    extra_updates: dict[str, Any] = {}

    for key, value in list(update_data.items()):
        if key.startswith("data."):
            rows_key = key.replace("data.", "rows.", 1)
            extra_updates.setdefault(rows_key, value)

        elif key.startswith("rows."):
            data_key = key.replace("rows.", "data.", 1)
            extra_updates.setdefault(data_key, value)

    update_data.update(extra_updates)
    return update_data


def sync_row_push_paths(row: Any) -> dict[str, Any]:
    """Devuelve un $push compatible para añadir una fila a data y rows."""
    return {"data": row, "rows": row}


_DERIVED_ROW_FIELDS = (
    "imagen_urls",
    "_imagenes",
    "processed_documents",
    "processed_images",
)


def prune_derived_row_fields(
    row: dict[str, Any],
    headers: list[str] | None,
    removed_docs: list[Any] | None = None,
) -> dict[str, Any]:
    """
    Devuelve una copia de la fila sin campos calculados solo para pintar pantallas.

    - Elimina imagen_urls, _imagenes, processed_documents y processed_images
      (salvo que sean cabeceras reales del catalogo).
    - Elimina Documentacion_N / Documentos_N solo si su valor es uno de los
      documentos eliminados en esta peticion (y no es una cabecera real).
    """
    headers_set = set(headers or [])
    removed = {v for v in (removed_docs or []) if isinstance(v, str)}
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if key not in headers_set:
            if key in _DERIVED_ROW_FIELDS:
                continue
            is_doc_aux = key.startswith("Documentación_") or key.startswith("Documentos_")
            if is_doc_aux and isinstance(value, str) and value in removed:
                continue
        cleaned[key] = value
    return cleaned


def build_row_set(
    raw_doc: dict[str, Any], row_index: int, row: dict[str, Any]
) -> dict[str, Any]:
    """
    Construye el $set para guardar una fila manteniendo `data` y `rows` sincronizadas.

    Si ambas listas existen y contienen la posicion, actualiza solo esa fila en las
    dos. En caso contrario escribe las dos listas completas a partir de `data`
    (o de `rows`), sin modificar `raw_doc`.
    """
    data = raw_doc.get("data")
    rows = raw_doc.get("rows")
    needed = row_index + 1
    if (
        isinstance(data, list)
        and isinstance(rows, list)
        and len(data) >= needed
        and len(rows) >= needed
    ):
        return sync_row_update_paths({f"data.{row_index}": row})

    base = data if isinstance(data, list) else (rows if isinstance(rows, list) else [])
    merged = list(base)
    while len(merged) <= row_index:
        merged.append({})
    merged[row_index] = row
    return {
        "data": merged,
        "rows": merged,
        "num_rows": len(merged),
        "row_count": len(merged),
    }
