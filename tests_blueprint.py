#!/usr/bin/env python3
# Script temporal para verificar que los blueprints se registran correctamente

try:
    from main_app import app

    print("✅ Aplicación cargada correctamente")
    print("\nBlueprints registrados:")

    # Filtrar solo las rutas que nos interesan
    relevant_endpoints = []
    for rule in app.url_map.iter_rules():
        keywords = ["scripts", "maintenance", "admin", "tools"]
        if any(keyword in rule.endpoint for keyword in keywords):
            relevant_endpoints.append(f"  {rule.endpoint}: {rule.rule}")

    for endpoint in sorted(relevant_endpoints):
        print(endpoint)

    # Verificar específicamente los endpoints problemáticos
    print("\n🔍 Verificando endpoints específicos:")

    try:
        with app.test_request_context():
            from flask import url_for

            # Probar scripts.tools_dashboard
            try:
                url_scripts = url_for("scripts.tools_dashboard")
                print(f"✅ scripts.tools_dashboard: {url_scripts}")
            except Exception as e:
                print(f"❌ scripts.tools_dashboard: {e}")

            # Probar maintenance.maintenance_dashboard
            try:
                url_maintenance = url_for("maintenance.maintenance_dashboard")
                print(f"✅ maintenance.maintenance_dashboard: {url_maintenance}")
            except Exception as e:
                print(f"❌ maintenance.maintenance_dashboard: {e}")

    except Exception as e:
        print(f"❌ Error al probar URLs: {e}")

except Exception as e:
    print(f"❌ Error al cargar la aplicación: {e}")
    import traceback

    traceback.print_exc()
