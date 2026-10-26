"""Regresión: Multimedia/documentos como lista dentro de lista rompían las plantillas
('list object' has no attribute 'lower') y dejaban el catálogo con Error 500."""
from pathlib import Path

import pytest
from flask import Flask

from app.filters import init_app as init_filters
from app.utils.row_media import as_list, collect_multimedia, flatten_media

ROOT = Path(__file__).resolve().parent.parent


def test_flatten_media_casos():
    assert flatten_media(None) == []
    assert flatten_media("") == []
    assert flatten_media("  a.jpg ") == ["a.jpg"]
    assert flatten_media(["a.jpg", "", None, 3]) == ["a.jpg"]
    assert flatten_media([["a.jpg", "b.png"], ["c.mp4"], "d.pdf"]) == ["a.jpg", "b.png", "c.mp4", "d.pdf"]
    assert flatten_media([[["x"]], [[]]]) == ["x"]
    assert flatten_media({"a": 1}) == []


def test_as_list_y_collect_multimedia_no_pierden_los_anidados():
    assert as_list([["a.jpg"], "b.png"]) == ["a.jpg", "b.png"]
    assert collect_multimedia({"Multimedia": [["a.jpg", "b.jpg"], "a.jpg"]}) == ["a.jpg", "b.jpg"]


def _env():
    app = Flask(__name__)
    init_filters(app)
    return app.jinja_env


# La construcción que fallaba en producción, tal y como estaba en las plantillas
_ANTES = (
    "{% set raw = row.get('Multimedia','') %}"
    "{% set l = ([raw] if raw is string else raw) if raw else [] %}"
    "{% for m in l %}{{ m.lower() }},{% endfor %}"
)
_AHORA = (
    "{% set raw = row.get('Multimedia','') %}"
    "{% set l = raw|media_list %}"
    "{% for m in l %}{{ m.lower() }},{% endfor %}"
)


def test_la_construccion_antigua_fallaba_con_listas_anidadas():
    from jinja2.exceptions import UndefinedError

    with pytest.raises(UndefinedError, match="lower"):
        _env().from_string(_ANTES).render(row={"Multimedia": [["A.JPG", "B.PNG"]]})


@pytest.mark.parametrize("valor,esperado", [
    ("A.JPG", "a.jpg,"),
    (["A.JPG", "B.PNG"], "a.jpg,b.png,"),
    ([["A.JPG", "B.PNG"]], "a.jpg,b.png,"),
    ([], ""),
    (None, ""),
])
def test_filtro_media_list_acepta_todas_las_formas(valor, esperado):
    assert _env().from_string(_AHORA).render(row={"Multimedia": valor}) == esperado


@pytest.mark.parametrize("plantilla,viejo", [
    ("app/templates/admin/ver_catalogo.html", "([multimedia_raw] if multimedia_raw is string else multimedia_raw)"),
    ("app/templates/ver_tabla.html", "([multimedia_raw] if multimedia_raw is string else multimedia_raw)"),
])
def test_plantillas_usan_el_filtro(plantilla, viejo):
    text = (ROOT / plantilla).read_text(encoding="utf-8")
    assert "multimedia_raw|media_list" in text
    assert viejo not in text
