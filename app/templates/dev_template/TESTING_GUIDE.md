# Guía práctica para diseñar tus propios tests en Flask/MongoDB

## 1. Estructura recomendada para tests

- **`tests/conftest.py`**: Define fixtures reutilizables como `app`, `client`, mocks de usuarios, y conexiones a MongoDB.
- **`tests/integration/`**: Tests que validan flujos completos, endpoints REST, integración de módulos.
- **`tests/unit/`**: (Opcional) Tests de funciones aisladas, lógica de negocio, helpers.
- **`tests/app/routes/`**: Tests específicos de rutas o blueprints.

---

## 2. Cómo escribir un buen test

### a) Nombra los tests de forma descriptiva

```python
def test_login_success(client):
    ...
def test_create_catalog_requires_admin(client):
    ...
```

### b) Usa el fixture `client` para simular peticiones HTTP

```python
def test_list_users(client):
    response = client.get('/api/users/list')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert 'users' in data
```

### c) Prepara el contexto necesario

- Si tu endpoint requiere autenticación, simula login o usa un mock de usuario admin.
- Si necesitas datos en la base, crea los mínimos necesarios antes del test (setup) y límpialos después (teardown).

### d) Verifica distintos escenarios

- Éxito (200, 201)
- Error de permisos (401, 403)
- Error de datos no encontrados (404)
- Validaciones de entrada (422, 400)

### e) Comprueba el contenido de la respuesta

- Que existan claves esperadas en el JSON.
- Que los valores tengan el tipo y formato correcto.
- Que los cambios en la base se reflejen tras la petición.

---

## 3. Ejemplo de test completo

```python
def test_create_and_delete_catalog(client):
    # Crear catálogo
    payload = {"nombre": "test_temp", "descripcion": "catálogo temporal"}
    response = client.post('/api/catalogs/create', json=payload)
    assert response.status_code in (201, 403, 401)
    if response.status_code == 201:
        data = response.get_json()
        catalog_id = data.get('id')
        # Borrar catálogo
        del_resp = client.delete(f'/api/catalogs/delete/{catalog_id}')
        assert del_resp.status_code in (200, 204)
```

---

## 4. Consejos útiles

- **Mantén los tests independientes**: cada test debe poder ejecutarse solo, sin depender del orden de otros.
- **Usa fixtures para preparar datos**: por ejemplo, un fixture que cree un usuario de prueba y lo limpie después.
- **Aprovecha los asserts**: no solo status_code, también contenido y estructura del JSON.
- **Documenta los tests**: un docstring breve ayuda a entender el propósito.
- **Cubre casos límite**: entradas vacías, ids inexistentes, permisos insuficientes.

---

## 5. Recursos recomendados

- [Documentación oficial de pytest](https://docs.pytest.org/en/stable/)
- [Testing Flask Applications](https://flask.palletsprojects.com/en/3.0.x/testing/)
- [pytest-mock para mocks avanzados](https://pytest-mock.readthedocs.io/en/latest/)
- [PyMongo Testing](https://pymongo.readthedocs.io/en/stable/examples/tls.html)
