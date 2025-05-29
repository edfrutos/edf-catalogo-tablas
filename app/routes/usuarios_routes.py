# Script: usuarios_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 usuarios_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.decorators import admin_required
from bson.objectid import ObjectId
import logging

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

# @usuarios_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     ...

@usuarios_bp.route('/register', methods=['GET', 'POST'])
def register():
    print("[DEBUG][REGISTER] users_collection:", getattr(current_app, 'users_collection', None))
    users_collection = getattr(current_app, 'users_collection', None)
    print("[DEBUG][REGISTER] session:", dict(session))
    if request.method == 'POST':
        if users_collection is None:
            flash('Error de conexión a la base de datos.', 'danger')
            return redirect(url_for('usuarios.register'))
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        if users_collection.find_one({'email': email}):
            flash('Este correo ya está registrado.', 'warning')
        else:
            users_collection.insert_one({'email': email, 'password': hashed_pw})
            flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('usuarios.login'))

    return render_template('auth/register.html')

@usuarios_bp.route('/logout')
def logout():
    print("[DEBUG][LOGOUT] session before clear:", dict(session))
    session.clear()
    print("[DEBUG][LOGOUT] session after clear:", dict(session))
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('usuarios.login'))

@usuarios_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    print("[DEBUG][FORGOT] users_collection:", getattr(current_app, 'users_collection', None))
    users_collection = getattr(current_app, 'users_collection', None)
    print("[DEBUG][FORGOT] session:", dict(session))
    if request.method == 'POST':
        if users_collection is None:
            flash('Error de conexión a la base de datos.', 'danger')
            return redirect(url_for('usuarios.forgot'))
        email = request.form['email']
        user = users_collection.find_one({'email': email})
        if user:
            flash('Si el correo existe, se enviarán instrucciones.', 'info')
        else:
            flash('Correo no encontrado.', 'warning')
    return render_template('auth/forgot.html')

@usuarios_bp.route('/edit', methods=['GET', 'POST'])
def edit():
    print("[DEBUG][EDIT] users_collection:", getattr(current_app, 'users_collection', None))
    users_collection = getattr(current_app, 'users_collection', None)
    print("[DEBUG][EDIT] session:", dict(session))
    if 'user_id' not in session:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('usuarios.login'))
    if users_collection is None:
        flash('Error de conexión a la base de datos.', 'danger')
        return redirect(url_for('main.dashboard'))
    user = users_collection.find_one({'_id': session['user_id']})

    if request.method == 'POST':
        new_email = request.form['email']
        users_collection.update_one({'_id': user['_id']}, {'$set': {'email': new_email}})
        flash('Correo actualizado.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/edit.html', user=user)

@usuarios_bp.route('/admin/usuarios')
@admin_required
def gestionar_usuarios():
    import logging
    logger = logging.getLogger(__name__)
    logger.info('[DEPURACIÓN] Entrando en gestionar_usuarios')
    try:
        users_collection = getattr(current_app, 'users_collection', None)
        logger.info(f'[DEPURACIÓN] users_collection: {users_collection}')
        if users_collection is None:
            logger.error('[DEPURACIÓN] No se pudo acceder a la colección de usuarios')
            flash('No se pudo acceder a la colección de usuarios.', 'error')
            return render_template('error.html', mensaje='No se pudo conectar a la colección de usuarios.')
        usuarios = list(users_collection.find())
        logger.info(f'[DEPURACIÓN] Usuarios recuperados: {len(usuarios)}')
        # Calcular estadísticas
        stats = {
            'total': len(usuarios),
            'roles': {
                'admin': 0,
                'normal': 0,
                'no_role': 0
            }
        }
        for user in usuarios:
            role = user.get('role')
            if role == 'admin':
                stats['roles']['admin'] += 1
            elif role in ('user', 'normal'):
                stats['roles']['normal'] += 1
            else:
                stats['roles']['no_role'] += 1
        return render_template('admin/users.html', usuarios=usuarios, stats=stats)
    except Exception as e:
        logger.error(f'[DEPURACIÓN] Error en gestionar_usuarios: {e}', exc_info=True)
        flash('Error al cargar los usuarios.', 'error')
        return render_template('error.html', mensaje=f'Error al cargar los usuarios: {e}')

# NUEVO ENDPOINT: Forzar cambio de contraseña
@usuarios_bp.route('/force_password_change', methods=['GET', 'POST'])
def force_password_change():
    print("[DEBUG][FORCE_PASSWORD_CHANGE] session:", dict(session))
    user_id = session.get('force_password_user_id')
    if not user_id:
        flash('No hay usuario para cambio de contraseña.', 'danger')
        return redirect(url_for('auth.login'))
    try:
        users_collection = getattr(current_app, 'users_collection', None)
        print("[DEBUG][FORCE_PASSWORD_CHANGE] users_collection:", users_collection)
        if users_collection is None:
            flash('Error de conexión a la base de datos.', 'danger')
            return redirect(url_for('auth.login'))
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        print("[DEBUG][FORCE_PASSWORD_CHANGE] user:", user)
    except Exception as e:
        print("[DEBUG][FORCE_PASSWORD_CHANGE] Exception:", e)
        flash('ID de usuario inválido.', 'danger')
        session.pop('force_password_user_id', None)
        return redirect(url_for('auth.login'))
    if not user:
        flash('Usuario no encontrado.', 'danger')
        session.pop('force_password_user_id', None)
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        # Validaciones básicas
        if not new_password or not confirm_password:
            flash('Debes completar ambos campos.', 'danger')
            return render_template('force_password_change.html', user=user)
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('force_password_change.html', user=user)
        if len(new_password) < 8 or not any(c.isupper() for c in new_password) or not any(c.islower() for c in new_password) or not any(c.isdigit() for c in new_password):
            flash('La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.', 'danger')
            return render_template('force_password_change.html', user=user)
        # Guardar nueva contraseña y limpiar flags
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {
                'password': generate_password_hash(new_password),
                'must_change_password': False
            }}
        )
        session.pop('force_password_user_id', None)
        flash('Contraseña actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('force_password_change.html', user=user)