#!/usr/bin/env python3
"""
Script para corregir las rutas de imágenes para usar S3
"""

import glob
import os
import re


def fix_s3_image_paths():
    """Corrige las rutas de imágenes para usar S3"""

    print("🔧 CORRIGIENDO RUTAS DE IMÁGENES PARA S3")
    print("=" * 60)

    # Patrones a buscar y reemplazar
    patterns = [
        # Reemplazar rutas directas a /imagenes_subidas/ con ?s3=true
        (r'src="/imagenes_subidas/([^"]+)"', r'src="/imagenes_subidas/\1?s3=true"'),
        (r'href="/imagenes_subidas/([^"]+)"', r'href="/imagenes_subidas/\1?s3=true"'),
        (
            r'onclick="mostrarImagenModal\(\'/imagenes_subidas/([^\']+)\'\)',
            r'onclick="mostrarImagenModal(\'/imagenes_subidas/\1?s3=true\'\)',
        ),
        (
            r'rutaImagen = "/imagenes_subidas/" \+ imagen;',
            r'rutaImagen = "/imagenes_subidas/" + imagen + "?s3=true";',
        ),
    ]

    # Buscar todos los archivos HTML
    html_files = glob.glob("app/templates/**/*.html", recursive=True)

    total_fixed = 0

    for file_path in html_files:
        print(f"\n📄 Procesando: {file_path}")

        try:
            # Leer el archivo
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content
            file_fixed = False

            # Aplicar cada patrón
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    file_fixed = True

            # Si se hicieron cambios, escribir el archivo
            if file_fixed:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print("   ✅ Corregido para S3")
                total_fixed += 1
            else:
                print("   ⏭️  Sin cambios necesarios")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n🎉 CORRECCIÓN S3 COMPLETADA")
    print(f"   📄 Archivos procesados: {len(html_files)}")
    print(f"   ✅ Archivos corregidos: {total_fixed}")

    return total_fixed


def fix_python_s3_paths():
    """Corrige las rutas de imágenes en archivos Python para usar S3"""

    print("\n🔧 CORRIGIENDO RUTAS PYTHON PARA S3")
    print("=" * 60)

    # Patrones específicos para Python
    patterns = [
        (
            r"url_for\(\'static\', filename=f\'uploads/\{([^}]+)\}\)",
            r"/imagenes_subidas/\1?s3=true",
        ),
        (
            r"url_for\(\'static\', filename=\'uploads/\' \+ ([^)]+)\)",
            r"/imagenes_subidas/\1?s3=true",
        ),
    ]

    # Archivos Python específicos que sabemos que tienen problemas
    python_files = [
        "app/models/user.py",
        "app/routes/main_routes.py",
        "app/routes/admin_routes.py",
        "app/utils/image_utils.py",
    ]

    total_fixed = 0

    for file_path in python_files:
        if not os.path.exists(file_path):
            continue

        print(f"\n🐍 Procesando: {file_path}")

        try:
            # Leer el archivo
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content
            file_fixed = False

            # Aplicar cada patrón
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    file_fixed = True

            # Si se hicieron cambios, escribir el archivo
            if file_fixed:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print("   ✅ Corregido para S3")
                total_fixed += 1
            else:
                print("   ⏭️  Sin cambios necesarios")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n🎉 CORRECCIÓN PYTHON S3 COMPLETADA")
    print(f"   🐍 Archivos procesados: {len(python_files)}")
    print(f"   ✅ Archivos corregidos: {total_fixed}")

    return total_fixed


def main():
    """Función principal"""

    print("🚀 CORRIGIENDO RUTAS DE IMÁGENES PARA S3")
    print("=" * 60)

    # Corregir templates HTML
    html_fixed = fix_s3_image_paths()

    # Corregir archivos Python
    python_fixed = fix_python_s3_paths()

    print("\n🎉 RESUMEN FINAL")
    print("=" * 60)
    print(f"   📄 Templates HTML corregidos: {html_fixed}")
    print(f"   🐍 Archivos Python corregidos: {python_fixed}")
    print(f"   📊 Total de archivos corregidos: {html_fixed + python_fixed}")

    if html_fixed + python_fixed > 0:
        print("\n💡 Ahora las imágenes se cargarán desde S3")
        print("   🔄 Reinicia el servicio para aplicar los cambios")
        print("   ☁️  Las imágenes se servirán desde el bucket de S3")
    else:
        print("\nℹ️  No se encontraron archivos que necesiten corrección")


if __name__ == "__main__":
    main()
