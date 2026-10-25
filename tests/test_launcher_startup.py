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
