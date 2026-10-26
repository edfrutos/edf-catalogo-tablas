"""Edición de la aplicación.

* ``standard`` (por defecto): comportamiento de siempre (MongoDB, cuentas, S3).
* ``store``: edición Mac App Store, totalmente local (SQLite, sin cuentas, archivos
  en el contenedor de la app).

La edición se decide, por este orden, con:
1. la variable de entorno ``EDF_EDITION``;
2. un fichero ``EDITION`` junto a la app empaquetada (lo añade el spec de la tienda);
3. ``standard``.

Cualquier valor desconocido cae en ``standard``: nunca activa el modo tienda por error.
"""

import os
import sys

STANDARD = "standard"
STORE = "store"


def _marker_edition() -> str:
    if not getattr(sys, "frozen", False):
        return ""
    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    try:
        with open(os.path.join(base, "EDITION"), encoding="utf-8") as fh:
            return fh.read().strip().lower()
    except OSError:
        return ""


def current_edition() -> str:
    value = (os.environ.get("EDF_EDITION") or _marker_edition() or STANDARD).strip().lower()
    return STORE if value == STORE else STANDARD


def is_store() -> bool:
    return current_edition() == STORE
