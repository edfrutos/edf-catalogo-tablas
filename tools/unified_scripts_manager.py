#!/usr/bin/env python3
"""
Gestor Unificado de Scripts - EDF CatalogoDeTablas
Combina funcionalidades de spell check y build scripts en una interfaz unificada
"""

import json
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Optional

import toml


class UnifiedScriptsManager:
    def __init__(self):
        # Obtener el directorio base del proyecto
        script_path = Path(__file__).resolve()
        self.base_dir = script_path.parent.parent
        self.tools_dir = self.base_dir / "tools"
        self.build_dir = self.tools_dir / "build"

        # Definir categorías unificadas
        self.categories = {
            "spell-check": {
                "description": "Verificación ortográfica y corrección",
                "icon": "🔍",
                "scripts": {
                    "quick_spell_check.py": {
                        "name": "Verificación Rápida",
                        "description": "Escanea archivos del proyecto y encuentra palabras desconocidas",
                        "type": "python",
                    },
                    "quick_setup_spell_check.py": {
                        "name": "Configuración Rápida",
                        "description": "Configura VS Code, cSpell y PyCharm sin escaneo completo",
                        "type": "python",
                    },
                    "complete_spell_check_workflow.py": {
                        "name": "Workflow Completo",
                        "description": "Escaneo completo, categorización y configuración automática",
                        "type": "python",
                    },
                    "add_common_words.py": {
                        "name": "Agregar Palabras Comunes",
                        "description": "Agrega palabras técnicas y términos del proyecto",
                        "type": "python",
                    },
                    "add_categorized_words.py": {
                        "name": "Agregar Palabras Categorizadas",
                        "description": "Usa resultados de escaneos previos para agregar por categorías",
                        "type": "python",
                    },
                    "fix_spell_check.py": {
                        "name": "Corregir Problemas",
                        "description": "Instala dependencias y corrige configuraciones",
                        "type": "python",
                    },
                },
            },
            "ci-cd": {
                "description": "Scripts críticos para CI/CD (GitHub Actions)",
                "icon": "🚀",
                "scripts": {
                    "build_macos_app.sh": {
                        "name": "Build macOS App",
                        "description": "Construye la aplicación para macOS",
                        "type": "shell",
                    },
                    "verify_build_environment.sh": {
                        "name": "Verificar Entorno",
                        "description": "Verifica el entorno de build",
                        "type": "shell",
                    },
                    "verify_requirements.sh": {
                        "name": "Verificar Requirements",
                        "description": "Verifica las dependencias del proyecto",
                        "type": "shell",
                    },
                    "fix_pyinstaller_tools_conflict_v2.sh": {
                        "name": "Fix PyInstaller v2",
                        "description": "Corrige conflictos de PyInstaller versión 2",
                        "type": "shell",
                    },
                    "fix_pyinstaller_tools_conflict_v3.sh": {
                        "name": "Fix PyInstaller v3",
                        "description": "Corrige conflictos de PyInstaller versión 3",
                        "type": "shell",
                    },
                    "pre_build_cleanup.sh": {
                        "name": "Pre-Build Cleanup",
                        "description": "Limpieza antes del build",
                        "type": "shell",
                    },
                    "ci_fix_pyinstaller.sh": {
                        "name": "CI Fix PyInstaller",
                        "description": "Corrección de PyInstaller para CI",
                        "type": "shell",
                    },
                    "fix_existing_spec.sh": {
                        "name": "Fix Existing Spec",
                        "description": "Corrige archivos .spec existentes",
                        "type": "shell",
                    },
                    "create_safe_spec.sh": {
                        "name": "Create Safe Spec",
                        "description": "Crea archivos .spec seguros",
                        "type": "shell",
                    },
                    "pre_build_final_check.sh": {
                        "name": "Pre-Build Final Check",
                        "description": "Verificación final antes del build",
                        "type": "shell",
                    },
                },
            },
            "documentation": {
                "description": "Scripts referenciados en documentación",
                "icon": "📚",
                "scripts": {
                    "build_web_app.sh": {
                        "name": "Build Web App",
                        "description": "Construye la aplicación web",
                        "type": "shell",
                    },
                    "build_native_app.sh": {
                        "name": "Build Native App",
                        "description": "Construye la aplicación nativa",
                        "type": "shell",
                    },
                    "build_all_versions.sh": {
                        "name": "Build All Versions",
                        "description": "Construye todas las versiones",
                        "type": "shell",
                    },
                    "fix_pyinstaller_tools_conflict.sh": {
                        "name": "Fix PyInstaller Tools",
                        "description": "Corrige conflictos de herramientas PyInstaller",
                        "type": "shell",
                    },
                    "clean_build.sh": {
                        "name": "Clean Build",
                        "description": "Limpia archivos de build",
                        "type": "shell",
                    },
                    "verify_build_files.sh": {
                        "name": "Verify Build Files",
                        "description": "Verifica archivos de build",
                        "type": "shell",
                    },
                    "verify_connectivity.sh": {
                        "name": "Verify Connectivity",
                        "description": "Verifica conectividad",
                        "type": "shell",
                    },
                    "verify_spec.sh": {
                        "name": "Verify Spec",
                        "description": "Verifica archivos .spec",
                        "type": "shell",
                    },
                    "safe_push.sh": {
                        "name": "Safe Push",
                        "description": "Push seguro al repositorio",
                        "type": "shell",
                    },
                },
            },
            "utilities": {
                "description": "Scripts de utilidades generales",
                "icon": "🔧",
                "scripts": {
                    "fix_tools_directory_conflict.sh": {
                        "name": "Fix Tools Directory",
                        "description": "Corrige conflictos del directorio tools",
                        "type": "shell",
                    },
                    "fix_pyinstaller_conflict.sh": {
                        "name": "Fix PyInstaller Conflict",
                        "description": "Corrige conflictos generales de PyInstaller",
                        "type": "shell",
                    },
                    "diagnose_pyinstaller_conflict.sh": {
                        "name": "Diagnose PyInstaller",
                        "description": "Diagnostica conflictos de PyInstaller",
                        "type": "shell",
                    },
                    "verify_markdown.sh": {
                        "name": "Verify Markdown",
                        "description": "Verifica archivos Markdown",
                        "type": "shell",
                    },
                },
            },
            "configuration": {
                "description": "Scripts de configuración y verificación",
                "icon": "⚙️",
                "scripts": {
                    "verify_pyright.sh": {
                        "name": "Verify Pyright",
                        "description": "Verifica configuración de Pyright",
                        "type": "shell",
                    }
                },
            },
        }

    def get_script_path(self, category: str, script: str) -> Path:
        """Obtener la ruta del script"""
        if script.endswith(".py"):
            return self.tools_dir / script
        else:
            return self.base_dir / script

    def execute_script(self, category: str, script: str) -> Dict[str, any]:
        """Ejecutar un script y retornar resultado"""
        if category not in self.categories:
            return {"success": False, "error": f"Categoría '{category}' no encontrada"}

        if script not in self.categories[category]["scripts"]:
            return {"success": False, "error": f"Script '{script}' no encontrado"}

        script_info = self.categories[category]["scripts"][script]
        script_path = self.get_script_path(category, script)

        if not script_path.exists():
            return {"success": False, "error": f"Script no encontrado: {script_path}"}

        try:
            # Construir comando según el tipo
            if script_info["type"] == "python":
                cmd = [sys.executable, str(script_path)]
            else:
                cmd = [str(script_path)]

            # Ejecutar script
            result = subprocess.run(
                cmd, cwd=self.base_dir, capture_output=True, text=True, check=False
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "script": script,
                "category": category,
            }

        except Exception as e:
            return {"success": False, "error": f"Error ejecutando script: {e}"}

    def get_spell_check_config(self) -> Dict[str, any]:
        """Obtener configuración actual de spell check"""
        config = {
            "pyproject_toml": {"exists": False, "words": []},
            "vscode_settings": {"exists": False, "words": []},
            "cspell_json": {"exists": False, "words": []},
        }

        # pyproject.toml
        pyproject_path = self.base_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, encoding="utf-8") as f:
                    toml_config = toml.load(f)
                cspell_words = (
                    toml_config.get("tool", {}).get("cspell", {}).get("words", [])
                )
                config["pyproject_toml"] = {"exists": True, "words": cspell_words}
            except Exception:
                pass

        # VS Code settings
        vscode_path = self.base_dir / ".vscode" / "settings.json"
        if vscode_path.exists():
            try:
                with open(vscode_path, encoding="utf-8") as f:
                    vscode_config = json.load(f)
                ignore_words = vscode_config.get("spellright", {}).get(
                    "ignoreWords", []
                )
                config["vscode_settings"] = {"exists": True, "words": ignore_words}
            except Exception:
                pass

        # cspell.json
        cspell_path = self.base_dir / "cspell.json"
        if cspell_path.exists():
            try:
                with open(cspell_path, encoding="utf-8") as f:
                    cspell_config = json.load(f)
                words = cspell_config.get("words", [])
                config["cspell_json"] = {"exists": True, "words": words}
            except Exception:
                pass

        return config


class UnifiedScriptsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔧 Gestor Unificado de Scripts - EDF Catalogotablas")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Inicializar gestor
        self.manager = UnifiedScriptsManager()

        # Variables
        self.current_status = tk.StringVar(value="🟢 Listo")
        self.progress_var = tk.DoubleVar()
        self.selected_category = tk.StringVar()
        self.selected_script = tk.StringVar()

        # Configurar estilo
        self.setup_styles()

        # Crear interfaz
        self.create_widgets()

    def setup_styles(self):
        """Configurar estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar colores
        style.configure(
            "Title.TLabel", font=("Arial", 18, "bold"), foreground="#2c3e50"
        )
        style.configure(
            "Subtitle.TLabel", font=("Arial", 12, "bold"), foreground="#34495e"
        )
        style.configure("Status.TLabel", font=("Arial", 10), foreground="#34495e")
        style.configure("Action.TButton", font=("Arial", 10, "bold"))
        style.configure("Info.TLabel", font=("Arial", 9), foreground="#7f8c8d")

    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Título
        title_label = ttk.Label(
            main_frame, text="🔧 Gestor Unificado de Scripts", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Estado actual
        status_frame = ttk.LabelFrame(main_frame, text="Estado Actual", padding="10")
        status_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20)
        )
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Estado:", style="Status.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Label(
            status_frame, textvariable=self.current_status, style="Status.TLabel"
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            status_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        # Panel principal con notebook
        notebook = ttk.Notebook(main_frame)
        notebook.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20)
        )
        main_frame.rowconfigure(2, weight=1)

        # Pestaña de Categorías (Principal)
        categories_frame = ttk.Frame(notebook)
        notebook.add(categories_frame, text="📁 Categorías")
        self.create_categories_tab(categories_frame)

        # Pestaña de Logs
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📋 Logs")
        self.create_logs_tab(logs_frame)

    def create_categories_tab(self, parent):
        """Crear pestaña principal de categorías"""
        # Frame principal con scroll
        canvas = tk.Canvas(parent, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Configurar grid
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Título principal
        title_label = ttk.Label(
            scrollable_frame, text="📁 Categorías de Scripts", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Crear tarjetas de categorías
        row = 1
        col = 0
        for category, info in self.manager.categories.items():
            category_frame = self.create_category_card(scrollable_frame, category, info)
            category_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

            col += 1
            if col > 1:  # 2 columnas
                col = 0
                row += 1

        # Configurar columnas del frame scrollable
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)

    def create_category_card(self, parent, category, info):
        """Crear tarjeta de categoría"""
        # Frame principal de la tarjeta
        card_frame = ttk.LabelFrame(
            parent, text=f"{info['icon']} {info['description']}", padding="15"
        )

        # Título de la categoría
        category_title = ttk.Label(
            card_frame, text=category.replace("-", " ").title(), style="Subtitle.TLabel"
        )
        category_title.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Estadísticas
        script_count = len(info["scripts"])
        stats_label = ttk.Label(
            card_frame,
            text=f"📊 {script_count} scripts disponibles",
            style="Info.TLabel",
        )
        stats_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))

        # Lista de scripts principales (máximo 5)
        scripts_list = list(info["scripts"].items())[:5]

        for i, (script_name, script_info) in enumerate(scripts_list):
            script_label = ttk.Label(
                card_frame, text=f"• {script_info['name']}", style="Info.TLabel"
            )
            script_label.grid(row=2 + i, column=0, columnspan=2, sticky="w", pady=2)

        # Botones de acción
        buttons_frame = ttk.Frame(card_frame)
        buttons_frame.grid(
            row=2 + len(scripts_list), column=0, columnspan=2, pady=(15, 0)
        )

        # Botón ver todos
        ttk.Button(
            buttons_frame,
            text="👁️ Ver Todos",
            command=lambda c=category: self.show_category_detail(c),
            style="Action.TButton",
        ).grid(row=0, column=0, padx=(0, 5))

        # Botón ejecutar rápido (solo para spell-check)
        if category == "spell-check":
            ttk.Button(
                buttons_frame,
                text="🚀 Ejecutar Rápido",
                command=lambda: self.execute_spell_check_script("quick_spell_check.py"),
                style="Action.TButton",
            ).grid(row=0, column=1, padx=(5, 0))

        return card_frame

    def show_category_detail(self, category):
        """Mostrar detalle de una categoría"""
        if category not in self.manager.categories:
            messagebox.showerror("Error", f"Categoría '{category}' no encontrada")
            return

        # Crear ventana de detalle
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"📁 {category.replace('-', ' ').title()}")
        detail_window.geometry("800x600")
        detail_window.configure(bg="#f0f0f0")

        info = self.manager.categories[category]

        # Frame principal
        main_frame = ttk.Frame(detail_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_frame,
            text=f"{info['icon']} {category.replace('-', ' ').title()}",
            style="Title.TLabel",
        )
        title_label.pack(pady=(0, 10))

        # Descripción
        desc_label = ttk.Label(
            main_frame, text=info["description"], style="Info.TLabel", wraplength=700
        )
        desc_label.pack(pady=(0, 20))

        # Frame para scripts
        scripts_frame = ttk.LabelFrame(
            main_frame, text="🔧 Scripts Disponibles", padding="15"
        )
        scripts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Crear lista de scripts con scroll
        canvas = tk.Canvas(scripts_frame, bg="white")
        scrollbar = ttk.Scrollbar(
            scripts_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Agregar scripts
        for i, (script_name, script_info) in enumerate(info["scripts"].items()):
            script_frame = ttk.Frame(scrollable_frame)
            script_frame.pack(fill="x", pady=5, padx=5)

            # Información del script
            info_frame = ttk.Frame(script_frame)
            info_frame.pack(side="left", fill="x", expand=True)

            script_title = ttk.Label(
                info_frame, text=script_info["name"], style="Subtitle.TLabel"
            )
            script_title.pack(anchor="w")

            script_desc = ttk.Label(
                info_frame,
                text=script_info["description"],
                style="Info.TLabel",
                wraplength=500,
            )
            script_desc.pack(anchor="w", pady=(5, 0))

            script_type = ttk.Label(
                info_frame,
                text=f"Tipo: {script_info['type']} | Archivo: {script_name}",
                style="Info.TLabel",
            )
            script_type.pack(anchor="w", pady=(5, 0))

            # Botones de acción
            buttons_frame = ttk.Frame(script_frame)
            buttons_frame.pack(side="right", padx=(10, 0))

            ttk.Button(
                buttons_frame,
                text="🚀 Ejecutar",
                command=lambda c=category, s=script_name: self.execute_script_threaded(
                    c, s
                ),
                style="Action.TButton",
            ).pack(side="top", pady=2)

            ttk.Button(
                buttons_frame,
                text="📋 Info",
                command=lambda c=category, s=script_name: self.show_script_info_detail(
                    c, s
                ),
                style="Action.TButton",
            ).pack(side="top", pady=2)

        # Botón cerrar
        ttk.Button(
            main_frame,
            text="❌ Cerrar",
            command=detail_window.destroy,
            style="Action.TButton",
        ).pack(pady=(20, 0))

    def show_script_info_detail(self, category, script_name):
        """Mostrar información detallada de un script"""
        if (
            category not in self.manager.categories
            or script_name not in self.manager.categories[category]["scripts"]
        ):
            messagebox.showerror("Error", "Script no encontrado")
            return

        script_info = self.manager.categories[category]["scripts"][script_name]
        script_path = self.manager.get_script_path(category, script_name)

        info_text = f"""
📋 INFORMACIÓN DETALLADA DEL SCRIPT

🔧 Nombre: {script_info['name']}
📁 Archivo: {script_name}
📂 Categoría: {category}
📝 Descripción: {script_info['description']}
🔧 Tipo: {script_info['type']}

📄 Ruta: {script_path}
✅ Existe: {'Sí' if script_path.exists() else 'No'}

💡 USO:
- Este script se ejecuta desde el directorio raíz del proyecto
- Los scripts Python se ejecutan con el intérprete actual
- Los scripts Shell se ejecutan directamente

⚠️ NOTAS:
- Verifica que el script existe antes de ejecutarlo
- Revisa los logs para ver el resultado de la ejecución
- Algunos scripts pueden requerir permisos especiales
        """

        self.show_info_window(f"Información de {script_info['name']}", info_text)

    def create_logs_tab(self, parent):
        """Crear pestaña de logs"""
        # Área de logs
        self.log_area = scrolledtext.ScrolledText(
            parent,
            height=30,
            width=120,
            font=("Consolas", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
        )
        self.log_area.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10
        )
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # Frame de botones
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=1, column=0, pady=(0, 10))

        ttk.Button(
            buttons_frame,
            text="🧹 Limpiar Logs",
            command=self.clear_logs,
            style="Action.TButton",
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            buttons_frame,
            text="💾 Guardar Logs",
            command=self.save_logs,
            style="Action.TButton",
        ).grid(row=0, column=1)

    def execute_spell_check_script(self, script_name):
        """Ejecutar script de spell check"""
        self.execute_script_threaded("spell-check", script_name)

    def execute_script_threaded(self, category, script_name):
        """Ejecutar script en hilo separado"""

        def run():
            try:
                self.current_status.set(f"🔄 Ejecutando {script_name}...")
                self.progress_var.set(10)
                self.log_message(f"🚀 Iniciando: {script_name}")

                result = self.manager.execute_script(category, script_name)

                self.progress_var.set(50)

                if result["success"]:
                    self.current_status.set("✅ Completado")
                    self.progress_var.set(100)
                    self.log_message(f"✅ {script_name} completado exitosamente")

                    if result.get("stdout"):
                        self.log_message(f"📤 Salida:\n{result['stdout']}")

                    messagebox.showinfo(
                        "Éxito", f"{script_name} completado exitosamente"
                    )
                else:
                    self.current_status.set("❌ Error")
                    self.progress_var.set(0)
                    self.log_message(
                        f"❌ {script_name} falló: {result.get('error', 'Error desconocido')}"
                    )

                    if result.get("stderr"):
                        self.log_message(f"⚠️ Errores:\n{result['stderr']}")

                    messagebox.showerror(
                        "Error", f"{script_name} falló. Revisa los logs."
                    )

            except Exception as e:
                self.current_status.set("❌ Error")
                self.progress_var.set(0)
                self.log_message(f"❌ Error ejecutando {script_name}: {e}")
                messagebox.showerror("Error", f"Error ejecutando {script_name}: {e}")

            # Recargar configuración si es spell check
            if category == "spell-check":
                self.load_spell_check_config()

        # Ejecutar en hilo separado
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def show_spell_check_config(self):
        """Mostrar configuración detallada de spell check"""
        try:
            config = self.manager.get_spell_check_config()

            config_text = "📋 CONFIGURACIÓN DETALLADA DE SPELL CHECK:\n\n"

            # pyproject.toml
            if config["pyproject_toml"]["exists"]:
                config_text += f"📄 pyproject.toml:\n"
                config_text += (
                    f"   - Palabras: {len(config['pyproject_toml']['words'])}\n"
                )
                config_text += f"   - Primeras 10: {', '.join(config['pyproject_toml']['words'][:10])}\n\n"

            # VS Code settings
            if config["vscode_settings"]["exists"]:
                config_text += f"⚙️ VS Code settings.json:\n"
                config_text += f"   - Palabras ignoradas: {len(config['vscode_settings']['words'])}\n"
                config_text += f"   - Primeras 10: {', '.join(config['vscode_settings']['words'][:10])}\n\n"

            # cspell.json
            if config["cspell_json"]["exists"]:
                config_text += f"🔤 cspell.json:\n"
                config_text += f"   - Palabras: {len(config['cspell_json']['words'])}\n"
                config_text += f"   - Primeras 10: {', '.join(config['cspell_json']['words'][:10])}\n\n"

            self.show_info_window("Configuración Spell Check", config_text)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar configuración: {e}")

    def show_spell_check_help(self):
        """Mostrar ayuda de spell check"""
        help_text = """
🔍 SPELL CHECK - AYUDA

📋 FUNCIONES DISPONIBLES:

🔍 Verificación Rápida:
   - Escanea archivos del proyecto
   - Encuentra palabras desconocidas
   - Categoriza automáticamente

⚙️ Configuración Rápida:
   - Configura VS Code, cSpell y PyCharm
   - Agrega palabras comunes
   - Sin escaneo completo

🔄 Workflow Completo:
   - Escaneo completo del proyecto
   - Categorización inteligente
   - Configuración automática
   - Creación de diccionarios

📝 Agregar Palabras Comunes:
   - Agrega palabras técnicas
   - Palabras del proyecto
   - Términos en español/inglés

📊 Agregar Palabras Categorizadas:
   - Usa resultados de escaneos previos
   - Agrega por categorías
   - Gestión inteligente

🔧 Corregir Problemas:
   - Instala dependencias faltantes
   - Corrige configuraciones
   - Resuelve errores comunes

💡 CONSEJOS:
- Usa "Verificación Rápida" para revisar cambios
- Usa "Workflow Completo" para configuración inicial
- Revisa los logs para ver detalles de las operaciones
        """
        self.show_info_window("Ayuda Spell Check", help_text)

    def log_message(self, message: str):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def clear_logs(self):
        """Limpiar logs"""
        self.log_area.delete(1.0, tk.END)
        self.log_message("🧹 Logs limpiados")

    def save_logs(self):
        """Guardar logs en archivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/unified_scripts_{timestamp}.log"

            # Crear directorio si no existe
            Path("logs").mkdir(exist_ok=True)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_area.get(1.0, tk.END))

            self.log_message(f"💾 Logs guardados en: {filename}")
            messagebox.showinfo("Éxito", f"Logs guardados en: {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Error guardando logs: {e}")

    def show_info_window(self, title: str, content: str):
        """Mostrar ventana de información"""
        info_window = tk.Toplevel(self.root)
        info_window.title(title)
        info_window.geometry("700x500")
        info_window.configure(bg="#f0f0f0")

        # Área de texto
        text_area = scrolledtext.ScrolledText(
            info_window, wrap=tk.WORD, font=("Arial", 10), bg="white"
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Insertar contenido
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED)

        # Botón cerrar
        ttk.Button(info_window, text="Cerrar", command=info_window.destroy).pack(
            pady=(0, 10)
        )


def main():
    """Función principal"""
    root = tk.Tk()
    app = UnifiedScriptsGUI(root)

    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
