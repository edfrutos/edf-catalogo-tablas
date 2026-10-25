"""Los logs no deben contener contraseñas ni otros secretos."""
import logging

from werkzeug.datastructures import ImmutableMultiDict

from app.utils.log_safety import REDACTED, redact


def test_redact_oculta_claves_sensibles():
    data = {
        "email": "a@b.c", "password": "d3v3L0p3r", "confirm_password": "x",
        "csrf_token": "t", "api_key": "k", "nueva_contraseña": "y", "nombre": "n",
    }
    out = redact(data)
    assert out["email"] == "a@b.c" and out["nombre"] == "n"
    for k in ("password", "confirm_password", "csrf_token", "api_key", "nueva_contraseña"):
        assert out[k] == REDACTED


def test_redact_con_formulario_de_flask_y_anidados():
    out = redact(ImmutableMultiDict([("username", "u"), ("password", "p")]))
    assert out == {"username": "u", "password": REDACTED}
    assert redact({"a": [{"token": "z", "ok": 1}]}) == {"a": [{"token": REDACTED, "ok": 1}]}
    assert redact(None) is None


def test_registro_no_escribe_la_contrasena_en_el_log():
    from app import create_app

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    registros = []

    class _Captura(logging.Handler):
        def emit(self, record):
            registros.append(record.getMessage())

    # Se engancha directamente al logger de la ruta: el logging unificado de la app
    # puede cortar la propagación hacia caplog y volver el test inútil.
    logger = logging.getLogger("app.routes.auth_routes")
    handler = _Captura(level=logging.DEBUG)
    nivel, logger.level = logger.level, logging.DEBUG
    logger.addHandler(handler)
    secreto = "S3cretoÚnico-98765"
    try:
        with app.test_client() as c:
            try:
                c.post("/register", data={
                    "username": "u", "nombre": "n", "email": "u@example.com",
                    "password": secreto, "confirm_password": secreto,
                })
            except Exception:
                pass  # sin MongoDB falla más adelante; lo que importa es el log
    finally:
        logger.removeHandler(handler)
        logger.level = nivel

    assert any("[REGISTER]" in r for r in registros), "el test no llegó al log de registro"
    assert not any(secreto in r for r in registros)
