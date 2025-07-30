#!/usr/bin/env python3
# Script para listar todas las rutas registradas en la aplicación Flask

import logging
from app import create_app

# Desactivar logging para este script
logging.disable(logging.CRITICAL)

app = create_app()

# Mostrar información sobre los blueprints registrados
print("\n\nBLUEPRINTS REGISTRADOS:")
print("-" * 50)
for name, blueprint in app.blueprints.items():
    print(f"Blueprint: {name}")
    print(f"  URL Prefix: {blueprint.url_prefix}")
    print(f"  Subdomain: {blueprint.subdomain}")
    print(f"  Template Folder: {blueprint.template_folder}")
    print(f"  Static Folder: {blueprint.static_folder}")
    print(f"  Import Name: {blueprint.import_name}")
    print()

# Mostrar todas las rutas registradas
print("\n\nRUTAS REGISTRADAS EN LA APLICACIÓN:")
print("-" * 50)
for rule in app.url_map.iter_rules():
    print(f"{rule} -> {rule.endpoint}")
print("-" * 50)
print(f"Total de rutas: {len(list(app.url_map.iter_rules()))}")

# Verificar si las rutas de diagnóstico están registradas
diagnostico_routes = [r for r in app.url_map.iter_rules() if 'diagnostico' in r.endpoint]
print(f"\nRutas de diagnóstico: {len(diagnostico_routes)}")
for route in diagnostico_routes:
    print(f"  {route} -> {route.endpoint}")

test_session_routes = [r for r in app.url_map.iter_rules() if 'test_session' in r.endpoint]
print(f"\nRutas de test_session: {len(test_session_routes)}")
for route in test_session_routes:
    print(f"  {route} -> {route.endpoint}")

# Verificar la configuración de sesión
print("\n\nCONFIGURACIÓN DE SESIÓN:")
print("-" * 50)
for key in sorted(app.config.keys()):
    if 'SESSION' in key:
        print(f"{key}: {app.config[key]}")

