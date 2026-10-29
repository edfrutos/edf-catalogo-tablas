"""Exportación legible de catálogos (CSV/JSON) para la edición de tienda.

El documento interno de un catálogo mezcla datos de usuario con campos técnicos
(``_id``, ``owner``, ``data``/``rows`` duplicados...). Aquí se exporta solo lo que
tiene sentido para el usuario: una fila por registro y una columna por campo.
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Iterable

from app.utils.catalog_utils import get_catalog_rows

_PREFIJO_HASH = re.compile(r"^[0-9a-f]{32}_")
COLUMNA_CATALOGO = "Catálogo"
COLUMNA_IMAGENES = "Imágenes"


def _nombre_legible(valor: Any) -> str:
    """Quita el prefijo hexadecimal con el que se guardan los archivos subidos."""
    return _PREFIJO_HASH.sub("", str(valor))


def _celda(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (list, tuple)):
        return "; ".join(_nombre_legible(v) for v in valor)
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False, default=str)
    return str(valor)


def _cabeceras(catalogo: dict[str, Any]) -> list[str]:
    cabeceras = catalogo.get("headers") or []
    return [str(h) for h in cabeceras] if isinstance(cabeceras, list) else []


def catalogos_a_csv(catalogos: Iterable[dict[str, Any]]) -> str:
    """Un único CSV: columna «Catálogo» + unión ordenada de las cabeceras + una fila por registro."""
    catalogos = list(catalogos)
    columnas: list[str] = []
    hay_imagenes = False
    for cat in catalogos:
        for h in _cabeceras(cat):
            if h not in columnas:
                columnas.append(h)
        hay_imagenes = hay_imagenes or any(
            isinstance(f, dict) and f.get("images") for f in get_catalog_rows(cat)
        )
    cabecera = [COLUMNA_CATALOGO, *columnas] + ([COLUMNA_IMAGENES] if hay_imagenes else [])

    salida = io.StringIO()
    escritor = csv.writer(salida, lineterminator="\n")
    escritor.writerow(cabecera)
    for cat in catalogos:
        nombre = str(cat.get("name", ""))
        for fila in get_catalog_rows(cat):
            if not isinstance(fila, dict):
                continue
            registro = [nombre, *(_celda(fila.get(c)) for c in columnas)]
            if hay_imagenes:
                registro.append(_celda(fila.get("images")))
            escritor.writerow(registro)
    # BOM: Excel y Numbers reconocen UTF-8 (acentos) al abrir el archivo
    return "﻿" + salida.getvalue()


def catalogos_a_json(catalogos: Iterable[dict[str, Any]]) -> str:
    """JSON sin campos técnicos: nombre, descripción, cabeceras, fechas y filas."""
    resultado = []
    for cat in catalogos:
        cabeceras = _cabeceras(cat)
        filas = []
        for fila in get_catalog_rows(cat):
            if not isinstance(fila, dict):
                continue
            filas.append(
                {k: v for k, v in fila.items() if k in cabeceras or k == "images"}
            )
        resultado.append(
            {
                "name": cat.get("name", ""),
                "description": cat.get("description", ""),
                "headers": cabeceras,
                "created_at": cat.get("created_at"),
                "updated_at": cat.get("updated_at"),
                "rows": filas,
            }
        )
    return json.dumps(resultado, indent=2, ensure_ascii=False, default=str)
