import importlib.util
import pathlib

_ruta = pathlib.Path(__file__).resolve().parents[1] / "app/utils/catalog_utils.py"
_spec = importlib.util.spec_from_file_location("catalog_utils_under_test", _ruta)
cu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cu)


def test_prune_quita_calculados_y_documento_eliminado():
    row = {
        "Nombre": "x",
        "Documentación": ["b.md"],
        "Documentación_0": "a.md",
        "Documentación_1": "b.md",
        "imagen_urls": ["u"],
        "_imagenes": ["u"],
        "images": ["i.jpg"],
    }
    out = cu.prune_derived_row_fields(row, ["Nombre", "Documentación"], ["a.md"])
    assert out == {
        "Nombre": "x",
        "Documentación": ["b.md"],
        "Documentación_1": "b.md",
        "images": ["i.jpg"],
    }


def test_prune_respeta_cabeceras_reales():
    row = {"Documentación_0": "a.md", "imagen_urls": ["u"]}
    out = cu.prune_derived_row_fields(row, ["Documentación_0", "imagen_urls"], ["a.md"])
    assert out == row


def test_prune_no_muta_la_entrada():
    row = {"imagen_urls": ["u"], "Nombre": "x"}
    cu.prune_derived_row_fields(row, ["Nombre"], [])
    assert "imagen_urls" in row


def test_build_row_set_ambas_listas():
    fila = {"a": 1}
    raw = {"data": [{}, {}], "rows": [{}, {}]}
    assert cu.build_row_set(raw, 1, fila) == {"data.1": fila, "rows.1": fila}


def test_build_row_set_sin_rows_escribe_listas_completas():
    fila = {"a": 2}
    raw = {"data": [{"x": 1}]}
    out = cu.build_row_set(raw, 0, fila)
    assert out == {"data": [fila], "rows": [fila], "num_rows": 1, "row_count": 1}
    assert raw["data"] == [{"x": 1}]


def test_build_row_set_rows_mas_corta():
    fila = {"a": 3}
    raw = {"data": [{}, {}], "rows": [{}]}
    out = cu.build_row_set(raw, 1, fila)
    assert out["data"] == [{}, fila] and out["rows"] == out["data"]


def test_build_row_set_documento_vacio():
    fila = {"a": 4}
    out = cu.build_row_set({}, 0, fila)
    assert out["data"] == [fila] and out["num_rows"] == 1


if __name__ == "__main__":
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK", nombre)
