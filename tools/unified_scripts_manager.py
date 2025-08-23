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
                        "type": "python"
                    },
                    "quick_setup_spell_check.py": {
                        "name": "Configuración Rápida",
                        "description": "Configura VS Code, cSpell y PyCharm sin escaneo completo",
                        "type": "python"
                    },
                    "complete_spell_check_workflow.py": {
                        "name": "Workflow Completo",
                        "description": "Escaneo completo, categorización y configuración automática",
                        "type": "python"
                    },
                    "add_common_words.py": {
                        "name": "Agregar Palabras Comunes",
                        "description": "Agrega palabras técnicas y términos del proyecto",
                        "type": "python"
                    },
                    "add_categorized_words.py": {
                        "name": "Agregar Palabras Categorizadas",
                        "description": "Usa resultados de escaneos previos para agregar por categorías",
                        "type": "python"
                    },
                    "fix_spell_check.py": {
                        "name": "Corregir Problemas",
                        "description": "Instala dependencias y corrige configuraciones",
                        "type": "python"
                    }
                }
            },
            "ci-cd": {
                "description": "Scripts críticos para CI/CD (GitHub Actions)",
                "icon": "🚀",
                "scripts": {
                    "build_macos_app.sh": {
                        "name": "Build macOS App",
                        "description": "Construye la aplicación para macOS",
                        "type": "shell"
                    },
                    "verify_build_environment.sh": {
                        "name": "Verificar Entorno",
                        "description": "Verifica el entorno de build",
                        "type": "shell"
                    },
                    "verify_requirements.sh": {
                        "name": "Verificar Requirements",
                        "description": "Verifica las dependencias del proyecto",
                        "type": "shell"
                    },
                    "fix_pyinstaller_tools_conflict_v2.sh": {
                        "name": "Fix PyInstaller v2",
                        "description": "Corrige conflictos de PyInstaller versión 2",
                        "type": "shell"
                    },
                    "fix_pyinstaller_tools_conflict_v3.sh": {
                        "name": "Fix PyInstaller v3",
                        "description": "Corrige conflictos de PyInstaller versión 3",
                        "type": "shell"
                    },
                    "pre_build_cleanup.sh": {
                        "name": "Pre-Build Cleanup",
                        "description": "Limpieza antes del build",
                        "type": "shell"
                    },
                    "ci_fix_pyinstaller.sh": {
                        "name": "CI Fix PyInstaller",
                        "description": "Corrección de PyInstaller para CI",
                        "type": "shell"
                    },
                    "fix_existing_spec.sh": {
                        "name": "Fix Existing Spec",
                        "description": "Corrige archivos .spec existentes",
                        "type": "shell"
                    },
                    "create_safe_spec.sh": {
                        "name": "Create Safe Spec",
                        "description": "Crea archivos .spec seguros",
                        "type": "shell"
                    },
                    "pre_build_final_check.sh": {
                        "name": "Pre-Build Final Check",
                        "description": "Verificación final antes del build",
                        "type": "shell"
                    }
                }
            },
            "documentation": {
                "description": "Scripts referenciados en documentación",
                "icon": "📚",
                "scripts": {
                    "build_web_app.sh": {
                        "name": "Build Web App",
                        "description": "Construye la aplicación web",
                        "type": "shell"
                    },
                    "build_native_app.sh": {
                        "name": "Build Native App",
                        "description": "Construye la aplicación nativa",
                        "type": "shell"
                    },
                    "build_all_versions.sh": {
                        "name": "Build All Versions",
                        "description": "Construye todas las versiones",
                        "type": "shell"
                    },
                    "fix_pyinstaller_tools_conflict.sh": {
                        "name": "Fix PyInstaller Tools",
                        "description": "Corrige conflictos de herramientas PyInstaller",
                        "type": "shell"
                    },
                    "clean_build.sh": {
                        "name": "Clean Build",
                        "description": "Limpia archivos de build",
                        "type": "shell"
                    },
                    "verify_build_files.sh": {
                        "name": "Verify Build Files",
                        "description": "Verifica archivos de build",
                        "type": "shell"
                    },
                    "verify_connectivity.sh": {
                        "name": "Verify Connectivity",
                        "description": "Verifica conectividad",
                        "type": "shell"
                    },
                    "verify_spec.sh": {
                        "name": "Verify Spec",
                        "description": "Verifica archivos .spec",
                        "type": "shell"
                    },
                    "safe_push.sh": {
                        "name": "Safe Push",
                        "description": "Push seguro al repositorio",
                        "type": "shell"
                    }
                }
            },
            "utilities": {
                "description": "Scripts de utilidades generales",
                "icon": "🔧",
                "scripts": {
                    "fix_tools_directory_conflict.sh": {
                        "name": "Fix Tools Directory",
                        "description": "Corrige conflictos del directorio tools",
                        "type": "shell"
                    },
                    "fix_pyinstaller_conflict.sh": {
                        "name": "Fix PyInstaller Conflict",
                        "description": "Corrige conflictos generales de PyInstaller",
                        "type": "shell"
                    },
                    "diagnose_pyinstaller_conflict.sh": {
                        "name": "Diagnose PyInstaller",
                        "description": "Diagnostica conflictos de PyInstaller",
                        "type": "shell"
                    },
                    "verify_markdown.sh": {
                        "name": "Verify Markdown",
                        "description": "Verifica archivos Markdown",
                        "type": "shell"
                    }
                }
            },
            "configuration": {
                "description": "Scripts de configuración y verificación",
                "icon": "⚙️",
                "scripts": {
                    "verify_pyright.sh": {
                        "name": "Verify Pyright",
                        "description": "Verifica configuración de Pyright",
                        "type": "shell"
                    }
                }
            }
        }

    def get_script_path(self, category: str, script: str) -> Path:
        """Obtener la ruta del script"""
        if script.endswith('.py'):
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
                cmd, 
                cwd=self.base_dir, 
                capture_output=True, 
                text=True, 
                check=False
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "script": script,
                "category": category
            }

        except Exception as e:
            return {"success": False, "error": f"Error ejecutando script: {e}"}

    def get_spell_check_config(self) -> Dict[str, any]:
        """Obtener configuración actual de spell check"""
        config = {
            "pyproject_toml": {"exists": False, "words": []},
            "vscode_settings": {"exists": False, "words": []},
            "cspell_json": {"exists": False, "words": []}
        }

        # pyproject.toml
        pyproject_path = self.base_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, encoding="utf-8") as f:
                    toml_config = toml.load(f)
                cspell_words = toml_config.get("tool", {}).get("cspell", {}).get("words", [])
                config["pyproject_toml"] = {"exists": True, "words": cspell_words}
            except Exception:
                pass

        # VS Code settings
        vscode_path = self.base_dir / ".vscode" / "settings.json"
        if vscode_path.exists():
            try:
                with open(vscode_path, encoding="utf-8") as f:
                    vscode_config = json.load(f)
                ignore_words = vscode_config.get("spellright", {}).get("ignoreWords", [])
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

        # Cargar configuración inicial
        self.load_spell_check_config()

    def setup_styles(self):
        """Configurar estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar colores
        style.configure("Title.TLabel", font=("Arial", 18, "bold"), foreground="#2c3e50")
        style.configure("Subtitle.TLabel", font=("Arial", 12, "bold"), foreground="#34495e")
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
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
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
        notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        main_frame.rowconfigure(2, weight=1)

        # Pestaña de Scripts
        scripts_frame = ttk.Frame(notebook)
        notebook.add(scripts_frame, text="📁 Scripts")
        self.create_scripts_tab(scripts_frame)

        # Pestaña de Spell Check
        spell_check_frame = ttk.Frame(notebook)
        notebook.add(spell_check_frame, text="🔍 Spell Check")
        self.create_spell_check_tab(spell_check_frame)

        # Pestaña de Logs
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📋 Logs")
        self.create_logs_tab(logs_frame)

    def create_scripts_tab(self, parent):
        """Crear pestaña de scripts"""
        # Frame izquierdo - Categorías
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        parent.columnconfigure(1, weight=1)

        # Título categorías
        ttk.Label(left_frame, text="📁 Categorías", style="Subtitle.TLabel").grid(
            row=0, column=0, pady=(0, 10)
        )

        # Lista de categorías
        self.categories_listbox = tk.Listbox(
            left_frame, width=30, height=15, font=("Arial", 10)
        )
        self.categories_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_frame.rowconfigure(1, weight=1)

        # Scrollbar para categorías
        categories_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.categories_listbox.yview)
        categories_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.categories_listbox.configure(yscrollcommand=categories_scrollbar.set)

        # Cargar categorías
        for category in self.manager.categories.keys():
            self.categories_listbox.insert(tk.END, category)

        # Binding para selección de categoría
        self.categories_listbox.bind('<<ListboxSelect>>', self.on_category_select)

        # Frame derecho - Scripts
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Título scripts
        ttk.Label(right_frame, text="🔧 Scripts", style="Subtitle.TLabel").grid(
            row=0, column=0, pady=(0, 10)
        )

        # Lista de scripts
        self.scripts_listbox = tk.Listbox(
            right_frame, width=50, height=15, font=("Arial", 10)
        )
        self.scripts_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(1, weight=1)

        # Scrollbar para scripts
        scripts_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.scripts_listbox.yview)
        scripts_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.scripts_listbox.configure(yscrollcommand=scripts_scrollbar.set)

        # Frame de botones
        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(
            buttons_frame,
            text="🚀 Ejecutar Script",
            command=self.execute_selected_script,
            style="Action.TButton"
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            buttons_frame,
            text="📋 Ver Información",
            command=self.show_script_info,
            style="Action.TButton"
        ).grid(row=0, column=1)

    def create_spell_check_tab(self, parent):
        """Crear pestaña de spell check"""
        # Frame de configuración
        config_frame = ttk.LabelFrame(parent, text="Configuración Actual", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        parent.columnconfigure(0, weight=1)

        # Información de configuración
        self.spell_check_info = tk.StringVar(value="Cargando configuración...")
        ttk.Label(
            config_frame,
            textvariable=self.spell_check_info,
            style="Info.TLabel",
            wraplength=1000
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Frame de acciones rápidas
        actions_frame = ttk.LabelFrame(parent, text="Acciones Rápidas", padding="10")
        actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        # Botones de spell check
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Primera fila
        row1_frame = ttk.Frame(buttons_frame)
        row1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
            row1_frame,
            text="🔍 Verificación Rápida",
            command=lambda: self.execute_spell_check_script("quick_spell_check.py"),
            style="Action.TButton"
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            row1_frame,
            text="⚙️ Configuración Rápida",
            command=lambda: self.execute_spell_check_script("quick_setup_spell_check.py"),
            style="Action.TButton"
        ).grid(row=0, column=1, padx=(0, 10))

        ttk.Button(
            row1_frame,
            text="🔄 Workflow Completo",
            command=lambda: self.execute_spell_check_script("complete_spell_check_workflow.py"),
            style="Action.TButton"
        ).grid(row=0, column=2, padx=(0, 10))

        # Segunda fila
        row2_frame = ttk.Frame(buttons_frame)
        row2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
            row2_frame,
            text="📝 Agregar Palabras Comunes",
            command=lambda: self.execute_spell_check_script("add_common_words.py"),
            style="Action.TButton"
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            row2_frame,
            text="📊 Agregar Palabras Categorizadas",
            command=lambda: self.execute_spell_check_script("add_categorized_words.py"),
            style="Action.TButton"
        ).grid(row=0, column=1, padx=(0, 10))

        ttk.Button(
            row2_frame,
            text="🔧 Corregir Problemas",
            command=lambda: self.execute_spell_check_script("fix_spell_check.py"),
            style="Action.TButton"
        ).grid(row=0, column=2, padx=(0, 10))

        # Tercera fila
        row3_frame = ttk.Frame(buttons_frame)
        row3_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

        ttk.Button(
            row3_frame,
            text="📋 Ver Configuración Detallada",
            command=self.show_spell_check_config,
            style="Action.TButton"
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            row3_frame,
            text="❓ Ayuda Spell Check",
            command=self.show_spell_check_help,
            style="Action.TButton"
        ).grid(row=0, column=1, padx=(0, 10))

    def create_logs_tab(self, parent):
        """Crear pestaña de logs"""
        # Área de logs
        self.log_area = scrolledtext.ScrolledText(
            parent,
            height=30,
            width=120,
            font=("Consolas", 9),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        self.log_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # Frame de botones
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=1, column=0, pady=(0, 10))

        ttk.Button(
            buttons_frame,
            text="🧹 Limpiar Logs",
            command=self.clear_logs,
            style="Action.TButton"
        ).grid(row=0, column=0, padx=(0, 10))

        ttk.Button(
            buttons_frame,
            text="💾 Guardar Logs",
            command=self.save_logs,
            style="Action.TButton"
        ).grid(row=0, column=1)

    def on_category_select(self, event):
        """Manejar selección de categoría"""
        selection = self.categories_listbox.curselection()
        if selection:
            category = self.categories_listbox.get(selection[0])
            self.load_scripts_for_category(category)

    def load_scripts_for_category(self, category):
        """Cargar scripts de una categoría"""
        self.scripts_listbox.delete(0, tk.END)
        
        if category in self.manager.categories:
            scripts = self.manager.categories[category]["scripts"]
            for script_name, script_info in scripts.items():
                display_name = script_info["name"]
                self.scripts_listbox.insert(tk.END, f"{display_name} ({script_name})")

    def execute_selected_script(self):
        """Ejecutar script seleccionado"""
        category_selection = self.categories_listbox.curselection()
        script_selection = self.scripts_listbox.curselection()
        
        if not category_selection or not script_selection:
            messagebox.showwarning("Advertencia", "Selecciona una categoría y un script")
            return

        category = self.categories_listbox.get(category_selection[0])
        script_display = self.scripts_listbox.get(script_selection[0])
        
        # Extraer nombre del script del display
        script_name = script_display.split(" (")[-1].rstrip(")")
        
        self.execute_script_threaded(category, script_name)

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
                    
                    messagebox.showinfo("Éxito", f"{script_name} completado exitosamente")
                else:
                    self.current_status.set("❌ Error")
                    self.progress_var.set(0)
                    self.log_message(f"❌ {script_name} falló: {result.get('error', 'Error desconocido')}")
                    
                    if result.get("stderr"):
                        self.log_message(f"⚠️ Errores:\n{result['stderr']}")
                    
                    messagebox.showerror("Error", f"{script_name} falló. Revisa los logs.")

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

    def show_script_info(self):
        """Mostrar información del script seleccionado"""
        category_selection = self.categories_listbox.curselection()
        script_selection = self.scripts_listbox.curselection()
        
        if not category_selection or not script_selection:
            messagebox.showwarning("Advertencia", "Selecciona una categoría y un script")
            return

        category = self.categories_listbox.get(category_selection[0])
        script_display = self.scripts_listbox.get(script_selection[0])
        script_name = script_display.split(" (")[-1].rstrip(")")
        
        if category in self.manager.categories and script_name in self.manager.categories[category]["scripts"]:
            script_info = self.manager.categories[category]["scripts"][script_name]
            
            info_text = f"""
📋 INFORMACIÓN DEL SCRIPT

🔧 Nombre: {script_info['name']}
📁 Archivo: {script_name}
📂 Categoría: {category}
📝 Descripción: {script_info['description']}
🔧 Tipo: {script_info['type']}

📄 Ruta: {self.manager.get_script_path(category, script_name)}
✅ Existe: {'Sí' if self.manager.get_script_path(category, script_name).exists() else 'No'}
            """
            
            self.show_info_window("Información del Script", info_text)
        else:
            messagebox.showerror("Error", "No se pudo obtener información del script")

    def load_spell_check_config(self):
        """Cargar configuración de spell check"""
        try:
            config = self.manager.get_spell_check_config()
            
            total_words = (
                len(config["pyproject_toml"]["words"]) +
                len(config["vscode_settings"]["words"]) +
                len(config["cspell_json"]["words"])
            )
            
            config_info = f"📋 Configuración Spell Check:\n"
            config_info += f"   📄 pyproject.toml: {'✅' if config['pyproject_toml']['exists'] else '❌'} ({len(config['pyproject_toml']['words'])} palabras)\n"
            config_info += f"   ⚙️ VS Code settings: {'✅' if config['vscode_settings']['exists'] else '❌'} ({len(config['vscode_settings']['words'])} palabras)\n"
            config_info += f"   🔤 cspell.json: {'✅' if config['cspell_json']['exists'] else '❌'} ({len(config['cspell_json']['words'])} palabras)\n"
            config_info += f"   📊 Total palabras: {total_words}"
            
            self.spell_check_info.set(config_info)
            
        except Exception as e:
            self.spell_check_info.set(f"❌ Error al cargar configuración: {e}")

    def show_spell_check_config(self):
        """Mostrar configuración detallada de spell check"""
        try:
            config = self.manager.get_spell_check_config()
            
            config_text = "📋 CONFIGURACIÓN DETALLADA DE SPELL CHECK:\n\n"
            
            # pyproject.toml
            if config["pyproject_toml"]["exists"]:
                config_text += f"📄 pyproject.toml:\n"
                config_text += f"   - Palabras: {len(config['pyproject_toml']['words'])}\n"
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
