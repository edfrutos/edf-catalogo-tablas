from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        """
        Inicializa un usuario con datos de MongoDB.
        
        Args:
            user_data (dict): Datos del usuario desde MongoDB
        """
        self.id = str(user_data.get('_id'))
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password')
        self.role = user_data.get('role', 'user')
        self.name = user_data.get('name', '')
        self.active = user_data.get('active', True)
        self.created_at = user_data.get('created_at')
        self.last_login = user_data.get('last_login')
    
    def get_id(self):
        return self.email
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_active(self):
        return self.active
    
    def set_password(self, password):
        """Genera un hash de la contraseña y lo guarda."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_by_email(email):
        """
        Busca un usuario por su email.
        
        Args:
            email (str): Email del usuario a buscar
            
        Returns:
            User: Instancia de User o None si no se encuentra
        """
        from flask import current_app
        user_data = current_app.users_collection.find_one({'email': email})
        if user_data:
            return User(user_data)
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """
        Busca un usuario por su ID.
        
        Args:
            user_id (str): ID del usuario a buscar
            
        Returns:
            User: Instancia de User o None si no se encuentra
        """
        from flask import current_app
        try:
            user_data = current_app.users_collection.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except:
            pass
        return None
    
    def to_dict(self):
        """Convierte el usuario a un diccionario."""
        return {
            '_id': ObjectId(self.id) if self.id else None,
            'email': self.email,
            'password': self.password_hash,
            'role': self.role,
            'name': self.name,
            'active': self.active,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
