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
