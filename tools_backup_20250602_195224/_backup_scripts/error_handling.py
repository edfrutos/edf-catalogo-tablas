#!/usr/bin/env python3
# Función de decorador para manejar excepciones en rutas
def route_error_handler(func):
    from functools import wraps
    import traceback
    from flask import current_app

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Registrar el error en logs
            error_msg = f"Error en {func.__name__}: {str(e)}"
            stack_trace = traceback.format_exc()
            current_app.logger.error(f"{error_msg}\n{stack_trace}")
            
            # Si estamos en una ruta que maneja JSON, devolver JSON
            if request.path.startswith('/api/'):
                return jsonify({"error": str(e)}), 500
            
            # Mostrar una página de error amigable con detalles técnicos
            return render_template("error.html", error=str(e), 
                                 traceback=stack_trace), 500
    
    return wrapper

# Manejador de errores global para la aplicación
def setup_error_handlers(app):
    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(f"Error 500: {str(e)}")
        return render_template("error.html", error=str(e)), 500
        
    @app.errorhandler(404)
    def handle_404(e):
        return render_template("not_found.html"), 404
