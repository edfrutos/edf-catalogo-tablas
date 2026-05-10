# Instalación y entorno

## Requisitos

- Python 3.10 recomendado.
- Entorno virtual `.venv`.
- MongoDB configurado.
- Variables de entorno en `.env`.

## Activación del entorno

```bash
cd /Users/edefrutos/docker-python-patched/edf-catalogo-tablas
source .venv/bin/activate
```

## Instalación de dependencias

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## Validación básica

```bash
python -m py_compile app/routes/main_routes.py app/routes/catalogs_routes.py app/routes/admin_routes.py
```
