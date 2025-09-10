# 🔧 Herramientas de Mantenimiento

Este directorio contiene scripts y herramientas para mantenimiento y reparación del sistema.

## 📋 Scripts Disponibles

### Reparación y Fixes
- `fix_*.py` - Scripts para corregir problemas específicos
- `create_*.py` - Scripts para crear/configurar elementos del sistema

### Categorías
- **Base de Datos**: Scripts de conexión y configuración
- **Usuarios**: Creación y gestión de usuarios
- **Sistema**: Reparación de problemas generales
- **Configuración**: Ajustes y optimizaciones

### Uso
```bash
# Ejecutar un script de mantenimiento
python3 tools/maintenance/fix_script_name.py

# Ejecutar desde el directorio raíz
python3 tools/maintenance/fix_script_name.py
```

## ⚠️ Importante
- **Siempre hacer backup** antes de ejecutar scripts de mantenimiento
- Revisar el código del script antes de ejecutarlo
- Algunos scripts pueden modificar la base de datos o configuración
