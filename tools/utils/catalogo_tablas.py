# Script: catalogo_tablas.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 catalogo_tablas.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

import sys

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


class CatalogoTablasWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuración del título correcto
        self.setWindowTitle("EDF CatálogoDeTablas")

        # Inicializar configuraciones
        self.settings = QSettings("EDF", "CatálogoDeTablas")

        # Widget central y layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Configurar geometría inicial
        self.setup_window_geometry()

    def setup_window_geometry(self):
        # Configurar tamaños
        self.setMinimumSize(800, 600)
        self.setMaximumSize(2560, 1600)

        # Restaurar último tamaño usado o usar predeterminado
        size = self.settings.value("window_size", (1024, 768))
        if isinstance(size, tuple):
            width, height = size
        else:
            width, height = (1024, 768)

        self.resize(int(width), int(height))
        self.center_window()

    def center_window(self):
        # Centrar en pantalla
        screen = self.screen().availableGeometry()  # type: ignore
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        # Guardar tamaño al cerrar
        self.settings.setValue(
            "window_size", (self.size().width(), self.size().height())
        )
        super().closeEvent(event)


def main():
    try:
        app = QApplication(sys.argv)
        window = CatalogoTablasWindow()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nAplicación cerrada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
