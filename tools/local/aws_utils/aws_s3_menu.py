#!/usr/bin/env python3
"""
Script: aws_s3_menu.py
Descripción: Menú interactivo para acceder a todos los scripts de AWS S3.
             Proporciona acceso al README y ejecución de scripts.

Funcionalidades:
  ✅ Menú interactivo con opciones numeradas
  ✅ Acceso al README.md
  ✅ Ejecución de scripts de configuración
  ✅ Ejecución de scripts de diagnóstico
  ✅ Ejecución de scripts de migración
  ✅ Ejecución de scripts de monitoreo
  ✅ Información de ayuda

Uso:
  python3 tools/local/aws_utils/aws_s3_menu.py

Autor: EDF Developer - 2025-08-08
Versión: 1.0
"""

import os
import subprocess
import sys
from pathlib import Path


class AWS_S3_Menu:
    """Menú interactivo para scripts de AWS S3."""

    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.readme_file = self.scripts_dir / "README.md"
        self.scripts = {
            "1": {
                "name": "📖 Ver README.md",
                "description": "Mostrar documentación completa",
                "script": None,
                "action": self.show_readme,
            },
            "2": {
                "name": "🔧 Configurar S3",
                "description": "configure_s3_access.py - Configura y valida acceso a S3",
                "script": "configure_s3_access.py",
                "action": self.run_script,
            },
            "3": {
                "name": "🔍 Diagnosticar permisos",
                "description": "diagnose_s3_permissions.py - Diagnostica permisos y problemas",
                "script": "diagnose_s3_permissions.py",
                "action": self.run_script,
            },
            "4": {
                "name": "📦 Listar buckets",
                "description": "list_buckets.py - Lista buckets S3 disponibles",
                "script": "list_buckets.py",
                "action": self.run_script,
            },
            "5": {
                "name": "🔄 Migrar imágenes a S3",
                "description": "migrate_images_to_s3.py - Migra imágenes locales a S3",
                "script": "migrate_images_to_s3.py",
                "action": self.run_script,
            },
            "6": {
                "name": "📊 Monitorear S3",
                "description": "monitor_s3.py - Monitoreo y métricas de S3",
                "script": "monitor_s3.py",
                "action": self.run_script,
            },
            "7": {
                "name": "🔧 Probar S3 Utils",
                "description": "s3_utils.py - Probar módulo de utilidades S3",
                "script": "s3_utils.py",
                "action": self.run_script,
            },
            "8": {
                "name": "📄 Ver reportes generados",
                "description": "Mostrar reportes JSON generados por los scripts",
                "script": None,
                "action": self.show_reports,
            },
            "9": {
                "name": "❓ Ayuda",
                "description": "Mostrar información de ayuda",
                "script": None,
                "action": self.show_help,
            },
            "0": {
                "name": "🚪 Salir",
                "description": "Salir del menú",
                "script": None,
                "action": self.exit_menu,
            },
        }

    def show_banner(self):
        """Muestra el banner del menú."""
        print("\n" + "=" * 60)
        print("🚀 AWS S3 - MENÚ DE UTILIDADES")
        print("=" * 60)
        print("📁 Directorio: tools/local/aws_utils/")
        print("📖 Documentación: README.md")
        print("🔧 Scripts disponibles: 6 scripts + utilidades")
        print("=" * 60)

    def show_menu(self):
        """Muestra el menú principal."""
        print("\n📋 OPCIONES DISPONIBLES:")
        print("-" * 40)

        for key, option in self.scripts.items():
            print(f"{key}. {option['name']}")
            print(f"   {option['description']}")
            print()

    def get_user_choice(self):
        """Obtiene la elección del usuario."""
        while True:
            try:
                choice = input("🎯 Selecciona una opción (0-9): ").strip()
                if choice in self.scripts:
                    return choice
                else:
                    print("❌ Opción inválida. Por favor selecciona 0-9.")
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                sys.exit(0)

    def show_readme(self):
        """Muestra el contenido del README.md."""
        print("\n" + "=" * 60)
        print("📖 LEYENDO README.md")
        print("=" * 60)

        if self.readme_file.exists():
            try:
                with open(self.readme_file, encoding="utf-8") as f:
                    content = f.read()

                # Mostrar contenido con paginación
                lines = content.split("\n")
                page_size = 20
                current_page = 0
                total_pages = (len(lines) + page_size - 1) // page_size

                while current_page < total_pages:
                    start_idx = current_page * page_size
                    end_idx = min(start_idx + page_size, len(lines))

                    print(f"\n--- Página {current_page + 1} de {total_pages} ---")
                    for line in lines[start_idx:end_idx]:
                        print(line)

                    if current_page < total_pages - 1:
                        input("\n⏸️  Presiona Enter para continuar...")

                    current_page += 1

                print("\n✅ README.md mostrado completamente")

            except Exception as e:
                print(f"❌ Error leyendo README.md: {e}")
        else:
            print("❌ README.md no encontrado")

    def run_script(self, script_name):
        """Ejecuta un script específico."""
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            print(f"❌ Script no encontrado: {script_name}")
            return

        print(f"\n🚀 Ejecutando: {script_name}")
        print("=" * 50)

        try:
            # Ejecutar el script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.scripts_dir,
                capture_output=False,
                text=True,
            )

            print(f"\n✅ Script completado con código de salida: {result.returncode}")

        except Exception as e:
            print(f"❌ Error ejecutando script: {e}")

    def show_reports(self):
        """Muestra los reportes generados."""
        print("\n" + "=" * 60)
        print("📄 REPORTES GENERADOS")
        print("=" * 60)

        report_files = [
            "s3_config.json",
            "s3_diagnostic_report.json",
            "s3_monitoring_report.json",
        ]

        found_reports = False

        for report_file in report_files:
            report_path = self.scripts_dir / report_file
            if report_path.exists():
                found_reports = True
                file_size = report_path.stat().st_size
                print(f"📄 {report_file} ({file_size} bytes)")

                # Mostrar contenido del reporte
                try:
                    with open(report_path) as f:
                        content = f.read()

                    # Mostrar solo las primeras líneas
                    lines = content.split("\n")[:10]
                    print("   Contenido (primeras 10 líneas):")
                    for line in lines:
                        print(f"   {line}")

                    if len(content.split("\n")) > 10:
                        print("   ... (archivo truncado)")

                except Exception as e:
                    print(f"   ❌ Error leyendo archivo: {e}")

                print()

        if not found_reports:
            print("📭 No se encontraron reportes generados")
            print(
                "💡 Ejecuta los scripts de configuración, diagnóstico o monitoreo para generar reportes"
            )

    def show_help(self):
        """Muestra información de ayuda."""
        print("\n" + "=" * 60)
        print("❓ AYUDA - AWS S3 UTILIDADES")
        print("=" * 60)

        help_text = """
🔧 CONFIGURACIÓN REQUERIDA:

1. Variables de entorno en .env:
   AWS_ACCESS_KEY_ID=tu_access_key
   AWS_SECRET_ACCESS_KEY=tu_secret_key
   AWS_REGION=tu_region
   S3_BUCKET_NAME=tu_bucket_name

2. Permisos IAM necesarios:
   - s3:ListAllMyBuckets
   - s3:GetObject, s3:PutObject, s3:DeleteObject
   - s3:ListBucket, s3:GetBucketPolicy, s3:PutBucketPolicy

🚀 FLUJO DE TRABAJO RECOMENDADO:

1. Configuración inicial:
   - Opción 2: Configurar S3
   - Opción 3: Diagnosticar permisos
   - Opción 4: Listar buckets

2. Migración de datos:
   - Opción 5: Migrar imágenes a S3

3. Monitoreo continuo:
   - Opción 6: Monitorear S3

📊 REPORTES GENERADOS:

- s3_config.json: Configuración de S3
- s3_diagnostic_report.json: Reporte de diagnóstico
- s3_monitoring_report.json: Reporte de monitoreo

💡 CONSEJOS:

- Ejecuta siempre la configuración antes de usar otros scripts
- Usa el diagnóstico para identificar problemas
- Monitorea regularmente para controlar costos
- Revisa el README.md para información detallada

🔗 ENLACES ÚTILES:

- Documentación AWS S3: https://docs.aws.amazon.com/s3/
- Precios S3: https://aws.amazon.com/s3/pricing/
- IAM Permissions: https://docs.aws.amazon.com/IAM/latest/UserGuide/
        """

        print(help_text)

    def exit_menu(self):
        """Sale del menú."""
        print("\n👋 ¡Gracias por usar AWS S3 Utils!")
        print("💡 Recuerda revisar el README.md para más información")
        sys.exit(0)

    def run(self):
        """Ejecuta el menú principal."""
        while True:
            try:
                self.show_banner()
                self.show_menu()
                choice = self.get_user_choice()

                option = self.scripts[choice]
                print(f"\n🎯 Seleccionaste: {option['name']}")

                if option["script"]:
                    option["action"](option["script"])
                else:
                    option["action"]()

                if choice != "0":
                    input("\n⏸️  Presiona Enter para continuar...")

            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")
                input("⏸️  Presiona Enter para continuar...")


def main():
    """Función principal."""
    menu = AWS_S3_Menu()
    menu.run()


if __name__ == "__main__":
    main()
