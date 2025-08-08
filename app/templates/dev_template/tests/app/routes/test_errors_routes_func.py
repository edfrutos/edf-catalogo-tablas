import pytest

def test_404_error_handler(client):
    resp = client.get("/ruta_que_no_existe")
    # Debe devolver 404 y mostrar mensaje de error personalizado
    assert resp.status_code == 404
    # Validar el contenido real de la plantilla 404
    assert b"p\xc3\xa1gina no encontrada" in resp.data.lower() or b"pagina no encontrada" in resp.data.lower()
