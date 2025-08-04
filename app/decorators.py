# app/decorators.py

from functools import wraps
import logging
from flask import session, redirect, url_for, request, flash
from typing import Callable, Any, TypeVar, cast
from flask.typing import ResponseReturnValue

logger = logging.getLogger(__name__)

# Type variable para funciones
F = TypeVar('F', bound=Callable[..., Any])

# Funciones auxiliares para verificar tipos de manera segura
def is_datetime(value: Any) -> bool:
    """Verifica si un valor es de tipo datetime sin usar isinstance"""
    return hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day')

def is_list(value: Any) -> bool:
    """Verifica si un valor es una lista sin usar isinstance"""
    return hasattr(value, '__iter__') and hasattr(value, 'append')

def is_string(value: Any) -> bool:
    """Verifica si un valor es un string sin usar isinstance"""
    return hasattr(value, 'lower') and hasattr(value, 'upper')

# --- Decorador para rutas protegidas ---
def login_required(f: F) -> F:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> ResponseReturnValue:
        logger.info(f"[LOGIN_REQUIRED] Ruta: {request.path}, Método: {request.method}, Sesión actual: {dict(session)}")
        # Verificar tanto user_id como logged_in para mayor seguridad
        if 'user_id' not in session or not session.get('logged_in', False):
            logger.warning(f"[LOGIN_REQUIRED] Autenticación fallida. user_id: {session.get('user_id')}, logged_in: {session.get('logged_in')}")
            # Guardar la URL actual para redireccionar después del login
            flash('Debes iniciar sesión primero.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        # Registrar acceso exitoso a ruta protegida
        logger.debug(f"[LOGIN_REQUIRED] Acceso permitido a {request.path} para usuario {session.get('username')} (ID: {session.get('user_id')})")
        return f(*args, **kwargs)
    return cast(F, decorated_function)

# --- Decorador para rutas que requieren rol de administrador ---
def admin_required(f: F) -> F:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> ResponseReturnValue:
        logger.info(f"[ADMIN_REQUIRED] Ruta: {request.path}, Método: {request.method}, Sesión actual: {dict(session)}")
        # Verificar si el usuario está logueado (verificar tanto user_id como logged_in)
        if not session.get('logged_in', False) or 'user_id' not in session:
            logger.warning(f"[ADMIN_REQUIRED] Usuario no autenticado intentando acceder a ruta admin: {request.path}")
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        # Verificar si el usuario tiene rol de admin
        if session.get('role') != 'admin':
            logger.warning(f"[ADMIN_REQUIRED] Usuario sin permisos de admin intentando acceder: {session.get('username')} (role: {session.get('role')})")
            flash('No tienes permisos para acceder a esta sección.', 'danger')
            return redirect(url_for('main.dashboard'))
        # Registrar acceso exitoso a ruta admin
        logger.debug(f"[ADMIN_REQUIRED] Acceso admin permitido a {request.path} para usuario {session.get('username')}")
        return f(*args, **kwargs)
    return cast(F, decorated_function)
