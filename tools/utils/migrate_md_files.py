#!/usr/bin/env python3
"""
Script para migrar archivos .md a la estructura de docs/ organizados por categorías
"""

import os
import re
import shutil
from pathlib import Path

# Definir categorías y sus archivos correspondientes
CATEGORIES = {
    "setup": [
        "README.md",
        "local_development_setup.md",
        "configuracion_despliegue.md",
        "CRON_SETUP.md",
        "Creacion_y_distribucion_profesional_app_macOS.md",
        "mongodb_whitelist_instructions.md",
        "mongodb_solution_summary.md",
        "aws_instructions.md",
        "preferencias_comunicacion.md",
    ],
    "maintenance": [
        "Checklist de Mantenimiento, Seguridad y Backups.md",
        "Checklist de Mantenimiento, Seguridad.md",
        "Comandos útiles para mantenimiento.md",
        "cleanup_plan.md",
        "CLEANUP_SUMMARY.md",
        "AUDITORIA_RESUMEN_20250618.md",
        "Análisis Sistema Catálogos Tablas.md",
        "Archivo de rutas Python.md",
    ],
    "development": [
        "testing_ui.md",
        "TESTING_GUIDE.md",
        "INSTRUCCIONES_IA.md",
        "README_cabeceras.md",
        "README_headers_EN.md",
        "inserción de cabecera en tu flujo de trabajo.md",
    ],
    "deployment": [
        "configuracion_despliegue.md",
        "SOLUCION_PAGINA_MANTENIMIENTO.md",
        "🌿 **Estado de las Ramas del Proyecto.md",
        "🔧 **Migración a Rama 'main'**.md",
        "🔧 Actualización de pip.md",
        "🔧 Correcciones Google Drive Backup.md",
    ],
    "tutorials": ["GEMINI_CLI_TUTORIAL.md", "GUIA_INTERFAZ_WEB_GEMINI.md"],
    "troubleshooting": [
        "⚠️ Error de Instalación Detectado.md",
        "⚠️ Error Persistente: Marcadores de Git Restantes.md",
        "resolucion_problemas_edefrutos2025.md",
        "RESUMEN_CONVERSACION.md",
    ],
    "security": ["auth_implementation.md"],
}

# Archivos que deben permanecer en docs/ raíz
ROOT_FILES = ["docs/README.md"]


def get_file_category(filename):
    """Determina la categoría de un archivo basándose en su nombre y contenido"""
    filename_lower = filename.lower()

    # Verificar categorías específicas
    for category, files in CATEGORIES.items():
        for file in files:
            if file.lower() in filename_lower or filename_lower in file.lower():
                return category

    # Categorización por palabras clave en el nombre
    if any(word in filename_lower for word in ["setup", "config", "install", "setup"]):
        return "setup"
    elif any(
        word in filename_lower for word in ["maintenance", "backup", "cleanup", "audit"]
    ):
        return "maintenance"
    elif any(
        word in filename_lower for word in ["test", "dev", "development", "guide"]
    ):
        return "development"
    elif any(word in filename_lower for word in ["deploy", "production", "server"]):
        return "deployment"
    elif any(word in filename_lower for word in ["tutorial", "guide", "howto"]):
        return "tutorials"
    elif any(word in filename_lower for word in ["error", "problem", "trouble", "fix"]):
        return "troubleshooting"
    elif any(word in filename_lower for word in ["auth", "security", "login"]):
        return "security"

    # Por defecto, ir a development
    return "development"


def migrate_md_files():
    """Migra los archivos .md a la estructura de docs/ organizados por categorías"""

    # Obtener todos los archivos .md relevantes
    md_files = []
    for root, dirs, files in os.walk("."):
        # Excluir directorios no relevantes
        dirs[:] = [
            d
            for d in dirs
            if d not in ["node_modules", "venv310", ".git", "discarded_files"]
        ]

        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                # Excluir archivos en node_modules y venv310
                if "node_modules" not in file_path and "venv310" not in file_path:
                    md_files.append(file_path)

    print(f"📁 Encontrados {len(md_files)} archivos .md")

    # Crear directorios de categorías si no existen
    for category in CATEGORIES.keys():
        os.makedirs(f"docs/{category}", exist_ok=True)

    # Migrar archivos
    migrated_count = 0
    for file_path in md_files:
        filename = os.path.basename(file_path)

        # Saltar archivos que ya están en docs/ raíz
        if file_path in ROOT_FILES:
            print(f"⏭️  Saltando {filename} (ya en docs/ raíz)")
            continue

        # Determinar categoría
        category = get_file_category(filename)

        # Crear nuevo path
        new_path = f"docs/{category}/{filename}"

        # Evitar sobrescribir archivos existentes
        if os.path.exists(new_path):
            base_name = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1]
            counter = 1
            while os.path.exists(new_path):
                new_path = f"docs/{category}/{base_name}_{counter}{ext}"
                counter += 1

        try:
            # Mover archivo
            shutil.move(file_path, new_path)
            print(f"✅ Migrado: {file_path} → {new_path}")
            migrated_count += 1
        except Exception as e:
            print(f"❌ Error migrando {file_path}: {e}")

    print(f"\n🎉 Migración completada: {migrated_count} archivos migrados")

    # Crear índice de documentación
    create_docs_index()


def create_docs_index():
    """Crea un índice de documentación en docs/README.md"""

    index_content = """# 📚 Documentación del Proyecto

## 📁 Estructura de Documentación

Esta documentación está organizada en las siguientes categorías:

### 🔧 [Setup](./setup/)
Documentación de configuración e instalación del proyecto.

### 🛠️ [Maintenance](./maintenance/)
Guías de mantenimiento, backups y operaciones del sistema.

### 💻 [Development](./development/)
Documentación para desarrolladores, testing y guías de desarrollo.

### 🚀 [Deployment](./deployment/)
Guías de despliegue y configuración en producción.

### 📖 [Tutorials](./tutorials/)
Tutoriales y guías paso a paso.

### 🔍 [Troubleshooting](./troubleshooting/)
Solución de problemas y errores comunes.

### 🔐 [Security](./security/)
Documentación de seguridad y autenticación.

### 🔌 [API](./api/)
Documentación de APIs y endpoints.

---

## 📋 Archivos Principales

- **[README.md](./README.md)** - Documentación principal del proyecto
- **[Configuración de Despliegue](./deployment/configuracion_despliegue.md)** - Guía completa de despliegue
- **[Checklist de Mantenimiento](./maintenance/Checklist%20de%20Mantenimiento,%20Seguridad%20y%20Backups.md)** - Checklist de mantenimiento

---

## 🔄 Actualización de Documentación

Para actualizar esta documentación:

1. Coloca los archivos .md en la categoría correspondiente
2. Actualiza este índice si es necesario
3. Mantén la estructura organizada por temas

---

*Última actualización: $(date)*
"""

    with open("docs/README.md", "w", encoding="utf-8") as f:
        f.write(index_content)

    print("📝 Índice de documentación creado en docs/README.md")


if __name__ == "__main__":
    print("🚀 Iniciando migración de archivos .md...")
    migrate_md_files()
    print("✅ Migración completada exitosamente!")
