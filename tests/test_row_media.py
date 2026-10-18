import importlib.util
import pathlib

_ruta = pathlib.Path(__file__).resolve().parents[1] / "app/utils/row_media.py"
_spec = importlib.util.spec_from_file_location("row_media_under_test", _ruta)
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)

UUID = "a" * 32


def test_as_list_acepta_texto_lista_y_vacios():
    assert rm.as_list(None) == []
    assert rm.as_list("") == []
    assert rm.as_list(" a.md ") == ["a.md"]
    assert rm.as_list(["a", "", None, " b "]) == ["a", "b"]
    assert rm.as_list(5) == []


def test_media_key_unifica_rutas_del_mismo_archivo():
    k = rm.media_key("/admin/s3/x.md")
    assert k == rm.media_key("/static/uploads/x.md") == rm.media_key("x.md")
    assert rm.media_key("https://ejemplo.com/a/x.md") == "https://ejemplo.com/a/x.md"
    assert rm.media_key("https://b.s3.eu-central-1.amazonaws.com/x.md") == "x.md"


def test_subir_segundo_documento_conserva_el_primero():
    row = {"Documentación": ["a.md"]}
    up = rm.documents_update(row, "Documentación", added=["b.pdf"])
    assert up == {"Documentación": ["a.md", "b.pdf"]}


def test_documentos_heredados_se_integran_y_se_vacian():
    row = {
        "Documentación": ["b.md"],
        "Documentación_3": "a.md",
        "Documentación_4": "b.md",
    }
    up = rm.documents_update(row, "Documentación", added=["c.pdf"])
    assert up["Documentación"] == ["b.md", "a.md", "c.pdf"]
    assert up["Documentación_3"] == ""
    assert up["Documentación_4"] == ""


def test_eliminar_documento_tambien_en_campo_heredado():
    row = {"Documentación": ["a.md", "b.md"], "Documentación_2": "a.md"}
    up = rm.documents_update(row, "Documentación", removed=["/admin/s3/a.md"])
    assert up["Documentación"] == ["b.md"]
    assert up["Documentación_2"] == ""


def test_documentos_otro_campo_base():
    row = {"Documentos": "x.txt", "Documentos_1": "y.txt"}
    assert rm.collect_documents(row, "Documentos") == ["x.txt", "y.txt"]
    assert rm.collect_documents(row, "Documentación") == []


def test_multimedia_antiguo_texto_pasa_a_lista_y_acumula():
    row = {"Multimedia": "v1.mp4"}
    assert rm.multimedia_update(row, added=["v2.mp4"]) == ["v1.mp4", "v2.mp4"]


def test_multimedia_eliminar_uno_conserva_el_resto():
    row = {"Multimedia": ["v1.mp4", "v2.mp4", "a.mp3"]}
    assert rm.multimedia_update(row, removed=["v1.mp4"]) == ["v2.mp4", "a.mp3"]


def test_multimedia_no_duplica_si_se_sube_el_mismo_nombre():
    row = {"Multimedia": ["/admin/s3/v1.mp4"]}
    assert rm.multimedia_update(row, added=["v1.mp4"]) == ["/admin/s3/v1.mp4"]


def test_display_name_quita_prefijo_uuid_y_ruta():
    assert rm.display_name(f"/admin/s3/{UUID}_Informe final.md") == "Informe final.md"
    assert rm.display_name(f"{UUID}_a.pdf") == "a.pdf"
    assert rm.display_name("https://ejemplo.com/docs/guia.md?x=1") == "guia.md"
    assert rm.display_name("normal.txt") == "normal.txt"


def test_doc_base_for():
    assert rm.doc_base_for("Documentación") == "Documentación"
    assert rm.doc_base_for("Documentos_4") == "Documentos"
    assert rm.doc_base_for("Nombre") is None
