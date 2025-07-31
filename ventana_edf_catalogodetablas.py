# Script: ventana_edf_catalogodetablas.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 ventana_edf_catalogodetablas.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QSettings, Qt, QTimer
import sys


class CatalogoTablasWindow(QMainWindow):
    def __init__(self, custom_width=None, custom_height=None):
        super().__init__()

        # Definir el tamaño predeterminado de la ventana
        # Puedes cambiar estos valores para ajustar el tamaño inicial
        self.DEFAULT_WIDTH = custom_width if custom_width else 1024
        self.DEFAULT_HEIGHT = custom_height if custom_height else 768

        # CONFIGURACIÓN RÁPIDA DE TAMAÑOS PREDEFINIDOS:
        # Para cambiar el tamaño, modifica estos valores:
        # - Pequeño: 800x600
        # - Mediano: 1024x768 (actual)
        # - Grande: 1280x800
        # - Extra Grande: 1440x900
        # - Pantalla completa HD: 1920x1080

        # Corregir el título de la ventana con el nombre correcto
        self.setWindowTitle("EDF CatálogoDeTablas")

        # Inicializar configuraciones con el nuevo nombre
        self.settings = QSettings("EDF", "CatálogoDeTablas")

        # Configurar el widget central y contenido
        self.setup_ui()

        # Configurar el tamaño y posición inicial
        self.setup_window_geometry()

        # Aplicar configuraciones adicionales
        self.setup_window_properties()

    def setup_ui(self):
        """Configurar la interfaz de usuario básica."""
        # Widget central y layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Añadir contenido básico para que no esté en blanco
        self.info_label = QLabel()
        self.info_label.setText(f"""
        <div style="text-align: center; padding: 50px;">
            <h1>EDF CatálogoDeTablas</h1>
            <p><strong>Tamaño de ventana:</strong> {self.DEFAULT_WIDTH} x {self.DEFAULT_HEIGHT} píxeles</p>
            <p><strong>Estado:</strong> Aplicación iniciada correctamente</p>
            <br>
            <p style="color: #666;">Esta es una ventana de prueba para verificar el tamaño configurado.</p>
            <p style="color: #666;">La aplicación principal se cargará aquí.</p>
        </div>
        """)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin: 20px;
            }
        """)

        self.main_layout.addWidget(self.info_label)

    def setup_window_geometry(self):
        # Configurar límites de tamaño primero
        self.setMinimumSize(800, 600)
        self.setMaximumSize(2560, 1600)

        # Establecer el tamaño deseado
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Usar QTimer para centrar después de que la ventana esté completamente inicializada
        QTimer.singleShot(100, self.center_window)

        # Guardar el tamaño en la configuración
        self.settings.setValue("window_size", (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT))

    def setup_window_properties(self):
        # Configurar flags de ventana para macOS
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    def center_window(self):
        """Centrar la ventana en la pantalla."""
        # Obtener la geometría de la pantalla disponible
        screen = self.screen().availableGeometry()  # type: ignore

        # Obtener el tamaño actual de la ventana
        window_geometry = self.frameGeometry()

        # Calcular la posición central
        center_point = screen.center()
        window_geometry.moveCenter(center_point)

        # Mover la ventana a la posición calculada
        self.move(window_geometry.topLeft())

    def showEvent(self, a0):  # type: ignore
        """Evento que se ejecuta cuando se muestra la ventana."""
        super().showEvent(a0)
        # Actualizar la información mostrada
        self.info_label.setText(f"""
        <div style="text-align: center; padding: 50px;">
            <h1>EDF CatálogoDeTablas</h1>
            <p><strong>Tamaño configurado:</strong> {self.DEFAULT_WIDTH} x {self.DEFAULT_HEIGHT} píxeles</p>
            <p><strong>Tamaño actual:</strong> {self.width()} x {self.height()} píxeles</p>
            <p><strong>Estado:</strong> Ventana mostrada correctamente</p>
            <br>
            <p style="color: #666;">Esta es una ventana de prueba para verificar el tamaño configurado.</p>
            <p style="color: #666;">La aplicación principal se cargará aquí.</p>
        </div>
        """)

    def closeEvent(self, a0):  # type: ignore
        # Guardar el tamaño actual antes de cerrar
        self.settings.setValue(
            "window_size", (self.size().width(), self.size().height())
        )
        super().closeEvent(a0)


def main():
    # Crear la aplicación
    app = QApplication(sys.argv)

    # Configurar el estilo para macOS
    app.setStyle("Fusion")

    # Crear y mostrar la ventana principal
    # Para cambiar el tamaño, modifica estos valores:
    # window = CatalogoTablasWindow(800, 600)     # Pequeño
    # window = CatalogoTablasWindow(1024, 768)    # Mediano (predeterminado)
    # window = CatalogoTablasWindow(1280, 800)    # Grande
    # window = CatalogoTablasWindow(1440, 900)    # Extra Grande
    window = CatalogoTablasWindow(1920, 1080)  # Pantalla completa HD

    # Descomentar la línea del tamaño deseado y comentar las demás
    # window = CatalogoTablasWindow()  # Tamaño predeterminado (1024x768)
    window.show()

    # Ejecutar la aplicación
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
