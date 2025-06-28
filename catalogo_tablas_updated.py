# Script: catalogo_tablas_updated.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 catalogo_tablas_updated.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QSettings, Qt
import sys

class CatalogoTablasWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Corregir el título de la ventana con el nombre correcto
        self.setWindowTitle('EDF CatálogoDeTablas')  # Nombre corregido con tilde
        
        # Inicializar configuraciones con el nuevo nombre
        self.settings = QSettings('EDF', 'CatálogoDeTablas')
        
        # Widget central y layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Configurar el tamaño y posición inicial
        self.setup_window_geometry()
        
        # Aplicar configuraciones adicionales
        self.setup_window_properties()

    def setup_window_geometry(self):
        # Obtener el tamaño guardado o usar el predeterminado
        default_size = (1024, 768)  # Tamaño por defecto optimizado
        size = self.settings.value('window_size', default_size)
        
        # Convertir valores a int si vienen como string
        if isinstance(size, tuple):
            width, height = size
        else:
            width, height = default_size
            
        self.resize(int(width), int(height))
        self.center_window()

    def setup_window_properties(self):
        # Configurar límites de tamaño
        self.setMinimumSize(800, 600)
        self.setMaximumSize(2560, 1600)
        
        # Configurar flags de ventana para macOS
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )

    def center_window(self):
        screen = self.screen().availableGeometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        # Guardar el tamaño actual antes de cerrar
        self.settings.setValue('window_size', (
            self.size().width(),
            self.size().height()
        ))
        super().closeEvent(event)

def main():
    # Crear la aplicación
    app = QApplication(sys.argv)
    
    # Configurar el estilo para macOS
    app.setStyle('Fusion')
    
    # Crear y mostrar la ventana principal con el nuevo nombre
    window = CatalogoTablasWindow()
    window.show()
    
    # Ejecutar la aplicación
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
