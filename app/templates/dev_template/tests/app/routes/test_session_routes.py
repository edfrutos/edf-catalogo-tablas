# app/routes/test_session.py

import logging
from flask import Blueprint, render_template, session, request, current_app, jsonify, flash, redirect, url_for
from datetime import datetime

logger = logging.getLogger(__name__)
test_session_bp = Blueprint('test_session', __name__, url_prefix='/test_session')

@test_session_bp.route('/')
def test_session_home():
    """Página principal para probar la sesión"""
    # Registrar información de la sesión actual
    logger.info(f"[TEST_SESSION] Sesión actual: {dict(session)}")
    
    # Añadir un valor a la sesión para probar persistencia
    session['test_timestamp'] = datetime.utcnow().isoformat()
    session.modified = True
    
    return render_template('test_session/home.html', 
                          session_data=dict(session),
                          cookie_name=current_app.config.get('SESSION_COOKIE_NAME'),
                          cookie_secure=current_app.config.get('SESSION_COOKIE_SECURE'))

@test_session_bp.route('/check')
def test_session_check():
    """Verificar si el valor de prueba persiste en la sesión"""
    test_timestamp = session.get('test_timestamp')
    logger.info(f"[TEST_SESSION_CHECK] Timestamp de prueba: {test_timestamp}")
    
    if test_timestamp:
        flash(f'¡Éxito! El valor de prueba persiste en la sesión: {test_timestamp}', 'success')
    else:
        flash('Error: El valor de prueba no se encontró en la sesión', 'error')
    
    return redirect(url_for('test_session.test_session_home'))

@test_session_bp.route('/api/status')
def test_session_api():
    """API para verificar el estado de la sesión"""
    return jsonify({
        'session_active': bool(session),
        'user_logged_in': session.get('logged_in', False),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role'),
        'test_timestamp': session.get('test_timestamp'),
        'session_cookie_name': current_app.config.get('SESSION_COOKIE_NAME'),
        'session_cookie_secure': current_app.config.get('SESSION_COOKIE_SECURE'),
        'request_cookies': {k: v for k, v in request.cookies.items()},
        'server_time': datetime.utcnow().isoformat()
    })

@test_session_bp.route('/reset')
def test_session_reset():
    """Reiniciar la sesión de prueba"""
    if 'test_timestamp' in session:
        del session['test_timestamp']
        session.modified = True
        flash('Valor de prueba eliminado de la sesión', 'info')
    else:
        flash('No hay valor de prueba para eliminar', 'warning')
    
    return redirect(url_for('test_session.test_session_home'))
