#!/usr/bin/env python3
"""
Interfaz gráfica para gestión de spell check
Integra todos los scripts de spell check en una aplicación fácil de usar
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


class SpellCheckGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Gestor de Spell Check - EDF Catalogotablas")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")

        # Variables
        self.current_status = tk.StringVar(value="🟢 Listo")
        self.progress_var = tk.DoubleVar()
        self.log_text = ""

        # Configurar estilo
        self.setup_styles()

        # Crear interfaz
        self.create_widgets()

        # Cargar configuración actual
        self.load_current_config()

    def setup_styles(self):
        """Configurar estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar colores
        style.configure(
            "Title.TLabel", font=("Arial", 16, "bold"), foreground="#2c3e50"
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
            main_frame, text="🔍 Gestor de Spell Check", style="Title.TLabel"
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

        # Panel de acciones
        actions_frame = ttk.LabelFrame(
            main_frame, text="Acciones Disponibles", padding="10"
        )
        actions_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20)
        )

        # Botones principales
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Primera fila de botones
        row1_frame = ttk.Frame(buttons_frame)
        row1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
            row1_frame,
            text="🔍 Verificación Rápida",
            command=self.quick_check,
            style="Action.TButton",
        ).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(
            row1_frame,
            text="⚙️ Configuración Rápida",
            command=self.quick_setup,
            style="Action.TButton",
        ).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(
            row1_frame,
            text="🔄 Workflow Completo",
            command=self.complete_workflow,
            style="Action.TButton",
        ).grid(row=0, column=2, padx=(0, 10))

        # Segunda fila de botones
        row2_frame = ttk.Frame(buttons_frame)
        row2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
            row2_frame,
            text="📝 Agregar Palabras Comunes",
            command=self.add_common_words,
            style="Action.TButton",
        ).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(
            row2_frame,
            text="📊 Agregar Palabras Categorizadas",
            command=self.add_categorized_words,
            style="Action.TButton",
        ).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(
            row2_frame,
            text="🔧 Corregir Problemas",
            command=self.fix_issues,
            style="Action.TButton",
        ).grid(row=0, column=2, padx=(0, 10))

        # Tercera fila de botones
        row3_frame = ttk.Frame(buttons_frame)
        row3_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

        ttk.Button(
            row3_frame,
            text="📋 Ver Configuración Actual",
            command=self.show_current_config,
            style="Action.TButton",
        ).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(
            row3_frame,
            text="🧹 Limpiar Logs",
            command=self.clear_logs,
            style="Action.TButton",
        ).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(
            row3_frame, text="❓ Ayuda", command=self.show_help, style="Action.TButton"
        ).grid(row=0, column=2, padx=(0, 10))

        # Panel de configuración actual
        config_frame = ttk.LabelFrame(
            main_frame, text="Configuración Actual", padding="10"
        )
        config_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20)
        )
        config_frame.columnconfigure(0, weight=1)

        # Información de configuración
        self.config_info = tk.StringVar(value="Cargando configuración...")
        ttk.Label(
            config_frame,
            textvariable=self.config_info,
            style="Info.TLabel",
            wraplength=800,
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Panel de logs
        logs_frame = ttk.LabelFrame(main_frame, text="Logs de Actividad", padding="10")
        logs_frame.grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Área de logs
        self.log_area = scrolledtext.ScrolledText(
            logs_frame,
            height=15,
            width=100,
            font=("Consolas", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
        )
        self.log_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def load_current_config(self):
        """Cargar configuración actual del proyecto"""
        try:
            # Cargar pyproject.toml
            if Path("pyproject.toml").exists():
                with open("pyproject.toml", encoding="utf-8") as f:
                    config = toml.load(f)
                cspell_words = config.get("tool", {}).get("cspell", {}).get("words", [])
                config_info = f"📋 Palabras en cSpell: {len(cspell_words)} | "
            else:
                config_info = "❌ pyproject.toml no encontrado | "

            # Verificar archivos de configuración
            vscode_exists = Path(".vscode/settings.json").exists()
            cspell_exists = Path("cspell.json").exists()

            config_info += f"VS Code: {'✅' if vscode_exists else '❌'} | "
            config_info += f"cSpell: {'✅' if cspell_exists else '❌'}"

            self.config_info.set(config_info)

        except Exception as e:
            self.config_info.set(f"❌ Error al cargar configuración: {e}")

    def log_message(self, message: str):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def run_script(self, script_name: str, description: str):
        """Ejecutar script en un hilo separado"""

        def run():
            try:
                self.current_status.set(f"🔄 {description}...")
                self.progress_var.set(10)
                self.log_message(f"🚀 Iniciando: {description}")

                # Ejecutar script
                result = subprocess.run(
                    [sys.executable, f"tools/{script_name}"],
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd(),
                )

                self.progress_var.set(50)

                # Mostrar resultado
                if result.stdout:
                    self.log_message(f"📤 Salida:\n{result.stdout}")

                if result.stderr:
                    self.log_message(f"⚠️ Errores:\n{result.stderr}")

                if result.returncode == 0:
                    self.current_status.set("✅ Completado")
                    self.progress_var.set(100)
                    self.log_message(f"✅ {description} completado exitosamente")
                    messagebox.showinfo(
                        "Éxito", f"{description} completado exitosamente"
                    )
                else:
                    self.current_status.set("❌ Error")
                    self.progress_var.set(0)
                    self.log_message(
                        f"❌ {description} falló con código {result.returncode}"
                    )
                    messagebox.showerror(
                        "Error", f"{description} falló. Revisa los logs."
                    )

            except Exception as e:
                self.current_status.set("❌ Error")
                self.progress_var.set(0)
                self.log_message(f"❌ Error ejecutando {description}: {e}")
                messagebox.showerror("Error", f"Error ejecutando {description}: {e}")

            # Recargar configuración
            self.load_current_config()

        # Ejecutar en hilo separado
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def quick_check(self):
        """Ejecutar verificación rápida"""
        self.run_script("quick_spell_check.py", "Verificación Rápida")

    def quick_setup(self):
        """Ejecutar configuración rápida"""
        self.run_script("quick_setup_spell_check.py", "Configuración Rápida")

    def complete_workflow(self):
        """Ejecutar workflow completo"""
        self.run_script("complete_spell_check_workflow.py", "Workflow Completo")

    def add_common_words(self):
        """Agregar palabras comunes"""
        self.run_script("add_common_words.py", "Agregar Palabras Comunes")

    def add_categorized_words(self):
        """Agregar palabras categorizadas"""
        self.run_script("add_categorized_words.py", "Agregar Palabras Categorizadas")

    def fix_issues(self):
        """Corregir problemas"""
        self.run_script("fix_spell_check.py", "Corregir Problemas")

    def show_current_config(self):
        """Mostrar configuración actual"""
        try:
            config_text = "📋 CONFIGURACIÓN ACTUAL:\n\n"

            # pyproject.toml
            if Path("pyproject.toml").exists():
                with open("pyproject.toml", encoding="utf-8") as f:
                    config = toml.load(f)
                cspell_words = config.get("tool", {}).get("cspell", {}).get("words", [])
                config_text += f"📄 pyproject.toml:\n"
                config_text += f"   - Palabras en cSpell: {len(cspell_words)}\n"
                config_text += (
                    f"   - Primeras 10 palabras: {', '.join(cspell_words[:10])}\n\n"
                )

            # VS Code settings
            if Path(".vscode/settings.json").exists():
                with open(".vscode/settings.json", encoding="utf-8") as f:
                    vscode_config = json.load(f)
                ignore_words = vscode_config.get("spellright", {}).get(
                    "ignoreWords", []
                )
                config_text += f"⚙️ VS Code settings.json:\n"
                config_text += f"   - Palabras ignoradas: {len(ignore_words)}\n"
                config_text += f"   - Primeras 10: {', '.join(ignore_words[:10])}\n\n"

            # cspell.json
            if Path("cspell.json").exists():
                with open("cspell.json", encoding="utf-8") as f:
                    cspell_config = json.load(f)
                words = cspell_config.get("words", [])
                config_text += f"🔤 cspell.json:\n"
                config_text += f"   - Palabras: {len(words)}\n"
                config_text += f"   - Primeras 10: {', '.join(words[:10])}\n\n"

            # Mostrar en ventana separada
            self.show_info_window("Configuración Actual", config_text)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar configuración: {e}")

    def clear_logs(self):
        """Limpiar logs"""
        self.log_area.delete(1.0, tk.END)
        self.log_message("🧹 Logs limpiados")

    def show_help(self):
        """Mostrar ayuda"""
        help_text = """
🔍 GESTOR DE SPELL CHECK - AYUDA

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
        self.show_info_window("Ayuda", help_text)

    def show_info_window(self, title: str, content: str):
        """Mostrar ventana de información"""
        info_window = tk.Toplevel(self.root)
        info_window.title(title)
        info_window.geometry("600x400")
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
    app = SpellCheckGUI(root)

    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
