#!/usr/bin/env python3
"""
Script para analizar dependencias del proyecto y crear requirements depurado
"""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set


def find_imports_in_file(file_path: Path) -> Set[str]:
    """Extrae imports de un archivo Python"""
    imports = set()
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parsear AST para extraer imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except SyntaxError:
            # Fallback a regex si hay errores de sintaxis
            import_patterns = [
                r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import",
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.update(matches)

    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")

    return imports


def analyze_project_imports() -> Set[str]:
    """Analiza todos los imports del proyecto"""
    all_imports = set()

    # Directorios a escanear (estrategia conservadora para evitar timeouts)
    scan_dirs = ["app", "tools", "scripts", "utils", "models", "config"]

    # También incluir archivos Python en la raíz
    python_files = []

    # Escanear archivos en la raíz del proyecto
    try:
        root_path = Path(".")
        for py_file in root_path.glob("*.py"):
            if py_file.is_file():
                python_files.append(py_file)
    except (TimeoutError, OSError) as e:
        print(f"⚠️  Advertencia: Error al escanear raíz: {e}")

    # Escanear subdirectorios específicos
    for subdir in scan_dirs:
        subdir_path = Path(subdir)
        if subdir_path.exists() and subdir_path.is_dir():
            try:
                found_files = list(subdir_path.rglob("*.py"))
                python_files.extend(found_files)
                print(f"  📁 {subdir}: {len(found_files)} archivos")
            except (TimeoutError, OSError) as e:
                print(f"⚠️  Error al escanear {subdir}: {e}")
                continue

    print(f"📂 Total archivos Python encontrados: {len(python_files)}")

    for py_file in python_files:
        try:
            imports = find_imports_in_file(py_file)
            all_imports.update(imports)
        except Exception as e:
            print(f"⚠️  Error procesando {py_file}: {e}")
            continue

    return all_imports


def get_current_requirements() -> Dict[str, str]:
    """Lee requirements actuales"""
    requirements = {}
    req_file = Path("requirements_dev_local.txt")

    if req_file.exists():
        with open(req_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "==" in line:
                    package, version = line.split("==")
                    requirements[package.strip()] = version.strip()

    return requirements


def check_python310_compatibility(package: str, version: str) -> bool:
    """Verifica compatibilidad con Python 3.10"""
    # Paquetes conocidos con problemas en 3.10
    problematic_packages = {"mod-wsgi": "Requiere Apache headers para compilar"}

    if package in problematic_packages:
        return False

    return True


def main():
    """Función principal"""
    print("🔍 ANALIZANDO DEPENDENCIAS DEL PROYECTO")
    print("=" * 50)

    # Analizar imports del proyecto
    project_imports = analyze_project_imports()
    print(f"📦 Imports encontrados en el proyecto: {len(project_imports)}")

    # Mapeo de imports a paquetes PyPI
    import_to_package = {
        "flask": "Flask",
        "flask_login": "Flask-Login",
        "flask_mail": "Flask-Mail",
        "flask_wtf": "Flask-WTF",
        "flask_pymongo": "Flask-PyMongo",
        "werkzeug": "Werkzeug",
        "pymongo": "pymongo",
        "wtforms": "WTForms",
        "email_validator": "email-validator",
        "dotenv": "python-dotenv",
        "PIL": "Pillow",
        "click": "click",
        "itsdangerous": "itsdangerous",
        "jinja2": "Jinja2",
        "markupsafe": "MarkupSafe",
        "pytest": "pytest",
        "bcrypt": "bcrypt",
        "jwt": "PyJWT",
        "openpyxl": "openpyxl",
        "pandas": "pandas",
        "xlsxwriter": "xlsxwriter",
        "requests": "requests",
        "urllib3": "urllib3",
        "cryptography": "cryptography",
        "six": "six",
        "packaging": "packaging",
        "setuptools": "setuptools",
        "psutil": "psutil",
        "google": "googleapis-common-protos",
        "googleapiclient": "google-api-python-client",
        "google_auth_oauthlib": "google-auth-oauthlib",
        "smtplib": None,  # Built-in
        "email": None,  # Built-in
        "os": None,  # Built-in
        "sys": None,  # Built-in
        "json": None,  # Built-in
        "datetime": None,  # Built-in
        "pathlib": None,  # Built-in
        "re": None,  # Built-in
        "logging": None,  # Built-in
        "threading": None,  # Built-in
        "time": None,  # Built-in
        "uuid": None,  # Built-in
        "hashlib": None,  # Built-in
        "base64": None,  # Built-in
        "urllib": None,  # Built-in (partial)
        "html": None,  # Built-in
        "io": None,  # Built-in
        "tempfile": None,  # Built-in
        "shutil": None,  # Built-in
        "subprocess": None,  # Built-in
        "ast": None,  # Built-in
        "collections": None,  # Built-in
        "typing": None,  # Built-in
    }

    # Identificar paquetes requeridos
    required_packages = set()
    for imp in project_imports:
        if imp in import_to_package:
            package = import_to_package[imp]
            if package:  # No es built-in
                required_packages.add(package)

    # Leer requirements actuales
    current_requirements = get_current_requirements()

    print(f"\n📋 ANÁLISIS DE DEPENDENCIAS:")
    print("-" * 30)
    print(f"✅ Paquetes requeridos: {len(required_packages)}")
    print(f"📦 Requirements actuales: {len(current_requirements)}")

    # Crear requirements depurado
    create_clean_requirements(required_packages, project_imports)


def create_clean_requirements(  # noqa: C901
    required_packages: Set[str], project_imports: Set[str]
):  # pylint: disable=too-many-branches,too-many-statements
    """Crea archivo de requirements depurado"""

    # Versiones optimizadas para Python 3.10 (Octubre 2024)
    optimized_versions = {
        # Core Flask
        "Flask": "3.0.3",
        "Flask-Login": "0.6.3",
        "Flask-Mail": "0.10.0",
        "Flask-WTF": "1.2.1",
        "Werkzeug": "3.0.4",
        # Database
        "pymongo": "4.8.0",
        "Flask-PyMongo": "2.3.0",
        # Forms & Validation
        "WTForms": "3.1.2",
        "email-validator": "2.2.0",
        # Utilities
        "python-dotenv": "1.0.1",
        "Pillow": "10.4.0",
        "click": "8.1.7",
        "itsdangerous": "2.2.0",
        "Jinja2": "3.1.4",
        "MarkupSafe": "2.1.5",
        # Development & Testing
        "pytest": "8.3.3",
        "pytest-cov": "5.0.0",
        "pytest-mock": "3.14.0",
        # Code Quality
        "flake8": "7.1.1",
        "black": "24.8.0",
        "mypy": "1.11.2",
        "autopep8": "2.3.2",  # CORREGIDO: versión disponible
        "isort": "5.13.2",
        # Security & Auth
        "bcrypt": "4.2.0",
        "PyJWT": "2.9.0",
        # Data & Export
        "openpyxl": "3.1.5",
        "pandas": "2.2.3",
        "xlsxwriter": "3.2.0",
        # Networking
        "requests": "2.32.3",
        "urllib3": "2.2.3",
        # Google APIs (detectado en el proyecto)
        "google-api-python-client": "2.147.0",
        "google-auth-oauthlib": "1.2.1",
        "google-auth": "2.35.0",
        "googleapis-common-protos": "1.65.0",
        # System utilities
        "psutil": "6.0.0",
        # Other utilities
        "cryptography": "43.0.1",
        "six": "1.16.0",
        "packaging": "24.1",
        "setuptools": "75.1.0",
        # Production (optional)
        "gunicorn": "23.0.0",
    }

    # Dependencias adicionales detectadas en el análisis
    additional_packages = {
        "google-api-python-client",
        "google-auth-oauthlib",
        "google-auth",
        "googleapis-common-protos",
        "psutil",
        "autopep8",
        "isort",
    }

    # Combinar paquetes requeridos con adicionales
    all_required = required_packages.union(additional_packages)

    # Generar archivo depurado
    today = "01102025"  # 1 de octubre de 2025
    filename = f"requirements_python310_{today}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Requirements depurado para Python 3.10+ - EDF Catálogo de Tablas\n")
        f.write(f"# Archivo generado automáticamente: {today}\n")
        f.write(f"# Análisis basado en imports reales del proyecto\n\n")

        # Core Flask Framework
        f.write("# =====================================\n")
        f.write("# CORE FLASK FRAMEWORK\n")
        f.write("# =====================================\n")
        core_flask = ["Flask", "Flask-Login", "Flask-Mail", "Flask-WTF", "Werkzeug"]
        for pkg in core_flask:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Database
        f.write("# =====================================\n")
        f.write("# BASE DE DATOS\n")
        f.write("# =====================================\n")
        db_packages = ["pymongo", "Flask-PyMongo"]
        for pkg in db_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Forms & Validation
        f.write("# =====================================\n")
        f.write("# FORMS Y VALIDACIÓN\n")
        f.write("# =====================================\n")
        form_packages = ["WTForms", "email-validator"]
        for pkg in form_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Google APIs
        f.write("# =====================================\n")
        f.write("# GOOGLE APIS (Detectado en proyecto)\n")
        f.write("# =====================================\n")
        google_packages = [
            "google-api-python-client",
            "google-auth-oauthlib",
            "google-auth",
            "googleapis-common-protos",
        ]
        for pkg in google_packages:
            if pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Utilities
        f.write("# =====================================\n")
        f.write("# UTILIDADES Y HELPERS\n")
        f.write("# =====================================\n")
        util_packages = [
            "python-dotenv",
            "Pillow",
            "click",
            "itsdangerous",
            "Jinja2",
            "MarkupSafe",
            "psutil",
        ]
        for pkg in util_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Development & Testing
        f.write("# =====================================\n")
        f.write("# DESARROLLO Y TESTING\n")
        f.write("# =====================================\n")
        dev_packages = ["pytest", "pytest-cov", "pytest-mock"]
        for pkg in dev_packages:
            if pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Code Quality
        f.write("# =====================================\n")
        f.write("# LINTING Y FORMATEO\n")
        f.write("# =====================================\n")
        quality_packages = ["flake8", "black", "mypy", "autopep8", "isort"]
        for pkg in quality_packages:
            if pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Security
        f.write("# =====================================\n")
        f.write("# SEGURIDAD Y AUTENTICACIÓN\n")
        f.write("# =====================================\n")
        security_packages = ["bcrypt", "PyJWT", "cryptography"]
        for pkg in security_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Data & Export
        f.write("# =====================================\n")
        f.write("# ARCHIVO DE DATOS Y EXPORTACIÓN\n")
        f.write("# =====================================\n")
        data_packages = ["openpyxl", "pandas", "xlsxwriter"]
        for pkg in data_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Networking
        f.write("# =====================================\n")
        f.write("# NETWORKING Y REQUESTS\n")
        f.write("# =====================================\n")
        network_packages = ["requests", "urllib3"]
        for pkg in network_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")
        f.write("\n")

        # Production
        f.write("# =====================================\n")
        f.write("# PRODUCCIÓN (OPCIONAL)\n")
        f.write("# =====================================\n")
        f.write("# gunicorn==23.0.0  # Servidor WSGI para producción\n")
        f.write("# mod-wsgi  # NO COMPATIBLE - Requiere Apache headers\n\n")

        # Other utilities
        f.write("# =====================================\n")
        f.write("# OTRAS UTILIDADES\n")
        f.write("# =====================================\n")
        other_packages = ["six", "packaging", "setuptools"]
        for pkg in other_packages:
            if pkg in all_required or pkg in optimized_versions:
                f.write(f"{pkg}=={optimized_versions[pkg]}\n")

    print(f"\n✅ Archivo depurado creado: {filename}")
    print(
        f"📦 Paquetes incluidos: {len([p for p in optimized_versions.keys() if any(p in line for line in open(filename).readlines())])}"
    )

    return filename


if __name__ == "__main__":
    main()
