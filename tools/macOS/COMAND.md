# Limpiar caché de Python

```bat
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

# Limpiar archivos .pyc

```bat
find . -name "*.pyc" -delete 2>/dev/null || true
```

# Limpiar sesión de Flask

```bat
rm -rf flask_session/* 2>/dev/null || true
```

# Matar proceso de Python

pkill -f "python.*main_app.py" || true
```

# Verificar si el JavaScript se está cargando correctamente

```bat
curl -s "http://localhost:5001/admin/maintenance/dashboard" | grep -A 5 -B 5 "dashboard.js"
```

# verificar si el archivo dashboard.js existe y es accesible

```bat
ls -la app/static/js/dashboard.js
```

# verificar si el archivo es accesible desde el navegador

```bat
curl -I "http://localhost:5001/static/js/dashboard.js"
```