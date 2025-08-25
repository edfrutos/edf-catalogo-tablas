#!/usr/bin/env python3
"""
EDF Catálogo de Tablas - Aplicación Nativa con WebSockets
Aplicación de escritorio nativa usando tkinter y WebSockets
para comunicación en tiempo real sin navegador
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import asyncio
import websockets
import json
import threading
import sqlite3
import os
from datetime import datetime
from pathlib import Path
import sys


class EDFCatalogoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EDF Catálogo de Tablas - Aplicación Nativa WebSockets")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Configurar WebSocket
        self.websocket = None
        self.websocket_connected = False
        self.server_url = "ws://localhost:8765"

        # Configurar estilo
        self.setup_styles()

        # Variables
        self.current_user = None
        self.catalogos = []
        self.current_catalogo = None

        # Crear interfaz
        self.create_widgets()

        # Iniciar WebSocket en hilo separado
        self.start_websocket()

        # Cargar datos iniciales
        self.load_initial_data()

    def setup_styles(self):
        """Configurar estilos de la aplicación"""
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar colores
        style.configure(
            "Title.TLabel",
            font=("Helvetica", 16, "bold"),
            foreground="#2c3e50",
            background="#f0f0f0",
        )

        style.configure(
            "Header.TLabel",
            font=("Helvetica", 12, "bold"),
            foreground="#34495e",
            background="#f0f0f0",
        )

        style.configure("Action.TButton", font=("Helvetica", 10, "bold"), padding=10)

        style.configure("Success.TButton", background="#27ae60", foreground="white")

        style.configure("Warning.TButton", background="#e74c3c", foreground="white")

    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Título principal
        title_label = ttk.Label(
            main_frame, text="EDF Catálogo de Tablas (WebSockets)", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Frame de navegación
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        # Botones de navegación
        ttk.Button(
            nav_frame, text="🏠 Inicio", command=self.show_home, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            nav_frame,
            text="📋 Catálogos",
            command=self.show_catalogos,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            nav_frame,
            text="👤 Usuarios",
            command=self.show_usuarios,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            nav_frame,
            text="🔧 Herramientas",
            command=self.show_herramientas,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            nav_frame, text="❓ Ayuda", command=self.show_ayuda, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=5)

        # Frame de contenido principal
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S)
        )
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # Barra de estado con WebSocket
        self.status_var = tk.StringVar()
        self.status_var.set("Conectando a WebSocket...")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0)
        )

    def start_websocket(self):
        """Iniciar conexión WebSocket en hilo separado"""

        def websocket_thread():
            asyncio.run(self.websocket_client())

        thread = threading.Thread(target=websocket_thread, daemon=True)
        thread.start()

    async def websocket_client(self):
        """Cliente WebSocket"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                self.websocket = websocket
                self.websocket_connected = True

                # Actualizar estado en el hilo principal
                self.root.after(
                    0, lambda: self.status_var.set("✅ Conectado a WebSocket")
                )

                # Enviar mensaje de autenticación
                await self.send_websocket_message(
                    {"type": "auth", "user": "admin", "action": "login"}
                )

                # Escuchar mensajes
                async for message in websocket:
                    await self.handle_websocket_message(message)

        except Exception as e:
            self.websocket_connected = False
            self.root.after(0, lambda: self.status_var.set(f"❌ Error WebSocket: {e}"))
            print(f"Error WebSocket: {e}")

    async def send_websocket_message(self, data):
        """Enviar mensaje por WebSocket"""
        if self.websocket and self.websocket_connected:
            try:
                await self.websocket.send(json.dumps(data))
            except Exception as e:
                print(f"Error enviando mensaje: {e}")

    async def handle_websocket_message(self, message):
        """Manejar mensaje recibido por WebSocket"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "catalogos":
                self.catalogos = data.get("data", [])
                self.root.after(0, self.update_catalogos_display)
            elif message_type == "users":
                users = data.get("data", [])
                self.root.after(0, lambda: self.update_users_display(users))
            elif message_type == "notification":
                self.root.after(
                    0, lambda: messagebox.showinfo("Notificación", data.get("message"))
                )

        except Exception as e:
            print(f"Error procesando mensaje: {e}")

    def update_catalogos_display(self):
        """Actualizar display de catálogos"""
        if hasattr(self, "catalogos_listbox"):
            self.load_catalogos()

    def update_users_display(self, users):
        """Actualizar display de usuarios"""
        # Implementar actualización de usuarios
        pass

    def show_home(self):
        """Mostrar página de inicio"""
        self.clear_content()

        # Frame de bienvenida
        welcome_frame = ttk.Frame(self.content_frame)
        welcome_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20
        )
        welcome_frame.columnconfigure(0, weight=1)

        # Mensaje de bienvenida
        welcome_text = """
        🎉 ¡Bienvenido a EDF Catálogo de Tablas!
        
        Esta es una aplicación nativa con WebSockets que te permite:
        
        📋 • Gestionar catálogos de productos en tiempo real
        👤 • Administrar usuarios y permisos
        🖼️  • Gestionar imágenes y documentos
        📊 • Generar reportes y estadísticas
        🔧 • Acceder a herramientas de mantenimiento
        
        🌐 Comunicación WebSocket: {}
        
        Selecciona una opción del menú superior para comenzar.
        """.format(
            "✅ Conectado" if self.websocket_connected else "❌ Desconectado"
        )

        welcome_label = ttk.Label(
            welcome_frame, text=welcome_text, font=("Helvetica", 12), justify=tk.LEFT
        )
        welcome_label.grid(row=0, column=0, pady=20)

        # Estadísticas rápidas
        stats_frame = ttk.LabelFrame(
            welcome_frame, text="📊 Estadísticas Rápidas", padding=20
        )
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=20)

        # Simular estadísticas
        stats_text = f"""
        📋 Catálogos: {len(self.catalogos)}
        👤 Usuarios: 5
        🖼️  Imágenes: 25
        📄 Documentos: 12
        🌐 WebSocket: {'Conectado' if self.websocket_connected else 'Desconectado'}
        """

        stats_label = ttk.Label(
            stats_frame, text=stats_text, font=("Helvetica", 10), justify=tk.LEFT
        )
        stats_label.grid(row=0, column=0)

    def show_catalogos(self):
        """Mostrar gestión de catálogos"""
        self.clear_content()

        # Frame principal de catálogos
        catalogos_frame = ttk.Frame(self.content_frame)
        catalogos_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20
        )
        catalogos_frame.columnconfigure(1, weight=1)
        catalogos_frame.rowconfigure(1, weight=1)

        # Panel izquierdo - Lista de catálogos
        left_panel = ttk.LabelFrame(
            catalogos_frame, text="📋 Catálogos Disponibles", padding=10
        )
        left_panel.grid(
            row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10)
        )

        # Botones de acción
        ttk.Button(
            left_panel,
            text="➕ Nuevo Catálogo",
            command=self.nuevo_catalogo,
            style="Action.TButton",
        ).pack(fill=tk.X, pady=5)
        ttk.Button(
            left_panel,
            text="📥 Importar",
            command=self.importar_catalogo,
            style="Action.TButton",
        ).pack(fill=tk.X, pady=5)
        ttk.Button(
            left_panel,
            text="📤 Exportar",
            command=self.exportar_catalogo,
            style="Action.TButton",
        ).pack(fill=tk.X, pady=5)

        # Lista de catálogos
        self.catalogos_listbox = tk.Listbox(
            left_panel, height=15, font=("Helvetica", 10)
        )
        self.catalogos_listbox.pack(fill=tk.BOTH, expand=True, pady=10)
        self.catalogos_listbox.bind("<<ListboxSelect>>", self.on_catalogo_select)

        # Panel derecho - Detalles del catálogo
        right_panel = ttk.LabelFrame(
            catalogos_frame, text="📄 Detalles del Catálogo", padding=10
        )
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)

        # Información del catálogo
        self.catalogo_info = tk.Text(
            right_panel, height=10, width=50, font=("Helvetica", 10), wrap=tk.WORD
        )
        self.catalogo_info.pack(fill=tk.BOTH, expand=True, pady=5)

        # Botones de acción del catálogo
        action_frame = ttk.Frame(right_panel)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            action_frame,
            text="✏️  Editar",
            command=self.editar_catalogo,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame,
            text="🗑️  Eliminar",
            command=self.eliminar_catalogo,
            style="Warning.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame,
            text="👁️  Ver",
            command=self.ver_catalogo,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)

        # Cargar catálogos
        self.load_catalogos()

    def show_usuarios(self):
        """Mostrar gestión de usuarios"""
        self.clear_content()

        usuarios_frame = ttk.Frame(self.content_frame)
        usuarios_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20
        )

        # Título
        ttk.Label(
            usuarios_frame, text="👤 Gestión de Usuarios", style="Header.TLabel"
        ).grid(row=0, column=0, pady=(0, 20))

        # Botones de acción
        action_frame = ttk.Frame(usuarios_frame)
        action_frame.grid(row=1, column=0, pady=20)

        ttk.Button(
            action_frame,
            text="➕ Nuevo Usuario",
            command=self.nuevo_usuario,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame,
            text="🔐 Cambiar Contraseña",
            command=self.cambiar_password,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame,
            text="👥 Gestionar Roles",
            command=self.gestionar_roles,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=5)

        # Lista de usuarios (simulada)
        usuarios_data = [
            ("admin", "Administrador", "admin@edf.com", "Activo"),
            ("usuario1", "Usuario 1", "user1@edf.com", "Activo"),
            ("usuario2", "Usuario 2", "user2@edf.com", "Inactivo"),
        ]

        # Crear tabla de usuarios
        columns = ("Usuario", "Nombre", "Email", "Estado")
        tree = ttk.Treeview(usuarios_frame, columns=columns, show="headings", height=10)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        for usuario in usuarios_data:
            tree.insert("", tk.END, values=usuario)

        tree.grid(row=2, column=0, pady=20)

    def show_herramientas(self):
        """Mostrar herramientas de mantenimiento"""
        self.clear_content()

        tools_frame = ttk.Frame(self.content_frame)
        tools_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20
        )

        # Título
        ttk.Label(
            tools_frame, text="🔧 Herramientas de Mantenimiento", style="Header.TLabel"
        ).grid(row=0, column=0, pady=(0, 20))

        # Grid de herramientas
        tools = [
            ("💾 Backup", "Crear copia de seguridad", self.backup_system),
            ("🔄 Restore", "Restaurar desde backup", self.restore_system),
            ("🧹 Limpieza", "Limpiar archivos temporales", self.cleanup_system),
            ("📊 Diagnóstico", "Diagnosticar sistema", self.diagnose_system),
            ("🔍 Logs", "Ver logs del sistema", self.view_logs),
            ("⚙️  Configuración", "Configurar aplicación", self.configure_app),
        ]

        for i, (name, desc, command) in enumerate(tools):
            row = i // 2
            col = i % 2

            tool_frame = ttk.LabelFrame(tools_frame, text=name, padding=10)
            tool_frame.grid(
                row=row + 1,
                column=col,
                sticky=(tk.W, tk.E, tk.N, tk.S),
                padx=10,
                pady=10,
            )

            ttk.Label(tool_frame, text=desc, font=("Helvetica", 10)).pack(pady=5)
            ttk.Button(
                tool_frame, text="Ejecutar", command=command, style="Action.TButton"
            ).pack(pady=5)

    def show_ayuda(self):
        """Mostrar ayuda y documentación"""
        self.clear_content()

        help_frame = ttk.Frame(self.content_frame)
        help_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20
        )

        # Título
        ttk.Label(
            help_frame, text="❓ Ayuda y Documentación", style="Header.TLabel"
        ).grid(row=0, column=0, pady=(0, 20))

        # Contenido de ayuda
        help_text = """
        🎯 EDF Catálogo de Tablas - Aplicación Nativa con WebSockets
        
        📋 GESTIÓN DE CATÁLOGOS:
        • Crear nuevos catálogos de productos
        • Editar catálogos existentes
        • Importar/exportar datos
        • Gestionar imágenes y documentos
        
        👤 GESTIÓN DE USUARIOS:
        • Crear nuevos usuarios
        • Asignar roles y permisos
        • Gestionar contraseñas
        • Control de acceso
        
        🔧 HERRAMIENTAS:
        • Backup y restauración
        • Limpieza del sistema
        • Diagnóstico y logs
        • Configuración avanzada
        
        🌐 WEBSOCKETS:
        • Comunicación en tiempo real
        • Sin necesidad de navegador
        • Actualizaciones automáticas
        • Conexión persistente
        
        💡 CONSEJOS:
        • Realiza backups regularmente
        • Mantén actualizada la aplicación
        • Revisa los logs periódicamente
        • Contacta al administrador si tienes problemas
        
        📞 SOPORTE:
        • Email: soporte@edf.com
        • Teléfono: +34 123 456 789
        • Horario: L-V 9:00-18:00
        """

        help_label = ttk.Label(
            help_frame, text=help_text, font=("Helvetica", 11), justify=tk.LEFT
        )
        help_label.grid(row=1, column=0, pady=20)

    def clear_content(self):
        """Limpiar el contenido del frame principal"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def load_initial_data(self):
        """Cargar datos iniciales de la aplicación"""
        # Simular carga de catálogos
        self.catalogos = [
            {
                "id": 1,
                "nombre": "Catálogo 2025",
                "fecha": "2025-01-15",
                "productos": 150,
            },
            {
                "id": 2,
                "nombre": "Catálogo Especial",
                "fecha": "2025-01-20",
                "productos": 75,
            },
            {
                "id": 3,
                "nombre": "Catálogo Básico",
                "fecha": "2025-01-25",
                "productos": 200,
            },
        ]

        self.status_var.set(f"Cargados {len(self.catalogos)} catálogos")

    def load_catalogos(self):
        """Cargar catálogos en la lista"""
        self.catalogos_listbox.delete(0, tk.END)
        for catalogo in self.catalogos:
            self.catalogos_listbox.insert(tk.END, catalogo["nombre"])

    def on_catalogo_select(self, event):
        """Manejar selección de catálogo"""
        selection = self.catalogos_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_catalogo = self.catalogos[index]
            self.show_catalogo_details()

    def show_catalogo_details(self):
        """Mostrar detalles del catálogo seleccionado"""
        if self.current_catalogo:
            details = f"""
            📋 CATÁLOGO: {self.current_catalogo['nombre']}
            
            🆔 ID: {self.current_catalogo['id']}
            📅 Fecha: {self.current_catalogo['fecha']}
            📦 Productos: {self.current_catalogo['productos']}
            
            📄 DESCRIPCIÓN:
            Este es un catálogo de productos con información detallada
            sobre precios, especificaciones y disponibilidad.
            
            🔧 ACCIONES DISPONIBLES:
            • Editar información del catálogo
            • Gestionar productos
            • Exportar a diferentes formatos
            • Compartir con otros usuarios
            
            🌐 WEBSOCKET: {'Conectado' if self.websocket_connected else 'Desconectado'}
            """

            self.catalogo_info.delete(1.0, tk.END)
            self.catalogo_info.insert(1.0, details)

    # Métodos de acción (simulados)
    def nuevo_catalogo(self):
        messagebox.showinfo("Nuevo Catálogo", "Función de nuevo catálogo")

    def importar_catalogo(self):
        filename = filedialog.askopenfilename(
            title="Importar Catálogo",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            messagebox.showinfo("Importar", f"Importando desde: {filename}")

    def exportar_catalogo(self):
        filename = filedialog.asksaveasfilename(
            title="Exportar Catálogo",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("PDF files", "*.pdf"),
            ],
        )
        if filename:
            messagebox.showinfo("Exportar", f"Exportando a: {filename}")

    def editar_catalogo(self):
        if self.current_catalogo:
            messagebox.showinfo(
                "Editar", f"Editando: {self.current_catalogo['nombre']}"
            )
        else:
            messagebox.showwarning("Advertencia", "Selecciona un catálogo primero")

    def eliminar_catalogo(self):
        if self.current_catalogo:
            if messagebox.askyesno(
                "Confirmar", f"¿Eliminar {self.current_catalogo['nombre']}?"
            ):
                messagebox.showinfo("Eliminado", "Catálogo eliminado")
        else:
            messagebox.showwarning("Advertencia", "Selecciona un catálogo primero")

    def ver_catalogo(self):
        if self.current_catalogo:
            messagebox.showinfo("Ver", f"Viendo: {self.current_catalogo['nombre']}")
        else:
            messagebox.showwarning("Advertencia", "Selecciona un catálogo primero")

    def nuevo_usuario(self):
        messagebox.showinfo("Nuevo Usuario", "Función de nuevo usuario")

    def cambiar_password(self):
        messagebox.showinfo("Cambiar Contraseña", "Función de cambiar contraseña")

    def gestionar_roles(self):
        messagebox.showinfo("Gestionar Roles", "Función de gestionar roles")

    def backup_system(self):
        messagebox.showinfo("Backup", "Iniciando backup del sistema...")

    def restore_system(self):
        messagebox.showinfo("Restore", "Función de restauración")

    def cleanup_system(self):
        messagebox.showinfo("Limpieza", "Iniciando limpieza del sistema...")

    def diagnose_system(self):
        messagebox.showinfo("Diagnóstico", "Ejecutando diagnóstico del sistema...")

    def view_logs(self):
        messagebox.showinfo("Logs", "Mostrando logs del sistema...")

    def configure_app(self):
        messagebox.showinfo(
            "Configuración", "Abriendo configuración de la aplicación..."
        )


def main():
    """Función principal de la aplicación"""
    root = tk.Tk()
    app = EDFCatalogoApp(root)

    # Configurar cierre de ventana
    def on_closing():
        if messagebox.askokcancel("Salir", "¿Quieres salir de la aplicación?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Iniciar aplicación
    root.mainloop()


if __name__ == "__main__":
    main()
