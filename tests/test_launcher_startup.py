"""El lanzador debe mostrar ventana al instante y dejar log en fichero (sin importar pywebview)."""
import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "launcher_native_websockets.py"


def _tree():
    return ast.parse(SRC.read_text(encoding="utf-8"))


def test_compila_y_define_funciones_de_arranque():
    names = {n.name for n in ast.walk(_tree()) if isinstance(n, ast.FunctionDef)}
    assert {"_setup_file_logging", "wait_for_server", "_boot", "_error_html", "main"} <= names


def test_ventana_inicial_con_html_y_espera_en_hilo_de_arranque():
    text = SRC.read_text(encoding="utf-8")
    assert '"html": _LOADING_HTML' in text
    assert "_boot,\n            window," in text
    # main() ya no bloquea esperando a Flask antes de crear la ventana
    main_src = text[text.index("def main():"):]
    assert "wait_for_server()" not in main_src


def test_log_a_fichero_solo_en_modo_empaquetado():
    text = SRC.read_text(encoding="utf-8")
    assert 'launcher.log' in text
    assert 'getattr(sys, "frozen", False)' in text.split("def _setup_file_logging")[1][:400]


def test_mimetypes_se_sanea_antes_de_importar_la_app():
    text = SRC.read_text(encoding="utf-8")
    assert "mimetypes.knownfiles" in text
    # debe ejecutarse antes de cualquier import de la app (wsgi/app) y de cargar el .env
    assert text.index("_sandbox_safe_mimetypes()\n") < text.index("from dotenv import load_dotenv")


def test_error_del_hilo_de_flask_se_muestra_en_la_ventana():
    text = SRC.read_text(encoding="utf-8")
    assert "_SERVER_ERROR" in text and "_SERVER_THREAD.is_alive()" in text


def test_sanear_mimetypes_descarta_ficheros_ilegibles(tmp_path):
    import mimetypes
    import types

    ns = {}
    src = SRC.read_text(encoding="utf-8")
    start = src.index("def _sandbox_safe_mimetypes")
    end = src.index("_sandbox_safe_mimetypes()\n", start)
    exec(src[start:end], ns)
    ok = tmp_path / "ok.types"
    ok.write_text("text/plain txt\n")
    bad = tmp_path / "bad.types"
    bad.write_text("x")
    bad.chmod(0)
    viejo = mimetypes.knownfiles
    try:
        mimetypes.knownfiles = [str(ok), str(bad), str(tmp_path / "no_existe")]
        ns["_sandbox_safe_mimetypes"]()
        import os
        if os.geteuid() != 0:  # root lee cualquier fichero
            assert mimetypes.knownfiles == [str(ok)]
        else:
            assert str(ok) in mimetypes.knownfiles
        assert str(tmp_path / "no_existe") not in mimetypes.knownfiles
    finally:
        mimetypes.knownfiles = viejo
