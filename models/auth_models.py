# Script: auth_models.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 auth_models.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from datetime import datetime, timedelta
from bson import ObjectId

class LoginAttempt:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']
        self.attempts_collection = db['login_attempts']
        self.max_attempts = 5
        self.lockout_duration = 30  # minutos

    def record_attempt(self, email, success):
        try:
            now = datetime.now()
            attempt = {
                'email': email,
                'timestamp': now,
                'success': success
            }
            self.attempts_collection.insert_one(attempt)
            
            if not success:
                # Contar intentos fallidos en los últimos 30 minutos
                recent_attempts = self.attempts_collection.count_documents({
                    'email': email,
                    'success': False,
                    'timestamp': {'$gt': now - timedelta(minutes=30)}
                })
                
                if recent_attempts >= self.max_attempts:
                    # Bloquear usuario
                    self.users_collection.update_one(
                        {'email': email},
                        {'$set': {
                            'locked_until': now + timedelta(minutes=self.lockout_duration),
                            'updated_at': now
                        }}
                    )
                    return False, 'Cuenta bloqueada por múltiples intentos fallidos'
                    
            return True, None
            
        except Exception as e:
            print(f'Error al registrar intento de login: {str(e)}')
            return False, 'Error interno del servidor'

    def check_lockout(self, email):
        try:
            user = self.users_collection.find_one({'email': email})
            if not user:
                return False, 'Usuario no encontrado'
                
            if 'locked_until' in user:
                if user['locked_until'] > datetime.now():
                    remaining = (user['locked_until'] - datetime.now()).total_seconds() / 60
                    return True, f'Cuenta bloqueada. Intente de nuevo en {int(remaining)} minutos'
                else:
                    # Desbloquear usuario
                    self.users_collection.update_one(
                        {'email': email},
                        {'$unset': {'locked_until': 1},
                         '$set': {'updated_at': datetime.now()}}
                    )
                    
            return False, None
            
        except Exception as e:
            print(f'Error al verificar bloqueo: {str(e)}')
            return True, 'Error interno del servidor'

class SecurityLog:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']
        self.security_log = db['security_log']

    def log_security_event(self, event_type, user_id=None, email=None, details=None, ip_address=None):
        try:
            # Obtener información del usuario si se proporciona user_id
            user_info = None
            if user_id:
                user = self.users_collection.find_one({'_id': ObjectId(user_id)})
                if user:
                    user_info = {
                        'email': user.get('email'),
                        'role': user.get('role'),
                        'nombre': user.get('nombre')
                    }

            # Crear registro de evento
            event = {
                'event_type': event_type,
                'timestamp': datetime.now(),
                'user_id': ObjectId(user_id) if user_id else None,
                'email': email or (user_info['email'] if user_info else None),
                'user_info': user_info,
                'details': details,
                'ip_address': ip_address
            }

            # Insertar evento en el log
            self.security_log.insert_one(event)
            return True

        except Exception as e:
            print(f'Error al registrar evento de seguridad: {str(e)}')
            return False

    def get_user_events(self, user_id, limit=50):
        try:
            events = list(self.security_log.find(
                {'user_id': ObjectId(user_id)}
            ).sort('timestamp', -1).limit(limit))
            return events
        except Exception as e:
            print(f'Error al obtener eventos del usuario: {str(e)}')
            return []

    def get_recent_events(self, event_type=None, limit=50):
        try:
            query = {'event_type': event_type} if event_type else {}
            events = list(self.security_log.find(query).sort('timestamp', -1).limit(limit))
            return events
        except Exception as e:
            print(f'Error al obtener eventos recientes: {str(e)}')
            return []

class UserProfile:
    def __init__(self, db):
        self.db = db
        self.users_collection = db['users']
        self.profile_collection = db['user_profiles']

    def update_profile(self, user_id, profile_data):
        try:
            # Verificar que el usuario existe
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return False, 'Usuario no encontrado'

            # Actualizar datos básicos del usuario
            update_data = {}
            if 'nombre' in profile_data:
                update_data['nombre'] = profile_data['nombre']
            if 'email' in profile_data:
                update_data['email'] = profile_data['email']

            if update_data:
                result = self.users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
                if not result.modified_count:
                    return False, 'No se pudo actualizar el perfil'

            # Actualizar datos adicionales del perfil
            profile_result = self.profile_collection.update_one(
                {'user_id': ObjectId(user_id)},
                {'$set': {
                    'user_id': ObjectId(user_id),
                    'data': profile_data,
                    'updated_at': datetime.now()
                }},
                upsert=True
            )

            return True, 'Perfil actualizado correctamente'

        except Exception as e:
            print(f'Error al actualizar perfil: {str(e)}')
            return False, 'Error interno del servidor'

    def get_profile(self, user_id):
        try:
            # Obtener datos básicos del usuario
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return None

            # Obtener datos adicionales del perfil
            profile = self.profile_collection.find_one({'user_id': ObjectId(user_id)})

            # Combinar datos
            user_data = {
                'id': str(user['_id']),
                'email': user.get('email'),
                'nombre': user.get('nombre'),
                'role': user.get('role'),
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at')
            }

            if profile and 'data' in profile:
                user_data.update(profile['data'])

            return user_data

        except Exception as e:
            print(f'Error al obtener perfil: {str(e)}')
            return None

    @staticmethod
    def update_last_login(db, user_id):
        try:
            users_collection = db['users']
            result = users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'last_login': datetime.now(),
                    'updated_at': datetime.now()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f'Error al actualizar último login: {str(e)}')
            return False
    
    @staticmethod
    def get_login_history(db, user_id, limit=10):
        return list(db.login_attempts.find(
            {'user_id': ObjectId(user_id)}
        ).sort('timestamp', -1).limit(limit))
