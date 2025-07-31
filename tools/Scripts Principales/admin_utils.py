#!/usr/bin/env python3
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId
import re
from app.models import get_users_collection

class AdminUtils:
    def __init__(self, db):
        self.db = db
        self.users_collection = get_users_collection()
        self.spreadsheets_collection = db['67b8c24a7fdc72dd4d8703cf']  # Colección de tablas
        self.SPREADSHEET_FOLDER = "/spreadsheets"
        
        # Asegurar que el directorio existe
        if not os.path.exists(self.SPREADSHEET_FOLDER):
            os.makedirs(self.SPREADSHEET_FOLDER, exist_ok=True)

    def list_all_users(self):
        """Lista todos los usuarios con sus roles y tablas"""
        users = list(self.users_collection.find())
        result = []
        for user in users:
            # Buscar tablas por propietario
            user_identifiers = {
                'owner_email': user.get('email', ''),
                'owner_name': user.get('nombre', ''),
                'owner_username': user.get('username', ''),
                'created_by': user.get('email', '')
            }
            
            # Construir la consulta OR para buscar por cualquier identificador
            query = {
                '$or': [
                    {field: value} for field, value in user_identifiers.items() if value
                ]
            }
            
            # Obtener tablas únicas del usuario
            tables = []
            unique_tables = self.spreadsheets_collection.distinct('table', query)
            
            for table_name in unique_tables:
                if table_name:  # Ignorar nombres vacíos
                    tables.append({'table': table_name})
            user_info = {
                'id': str(user['_id']),
                'email': user.get('email', 'Sin email'),
                'nombre': user.get('nombre', 'Sin nombre'),
                'role': user.get('role', 'normal'),
                'num_tables': len(tables),
                'username': user.get('username', '')
            }
            result.append(user_info)
        return result

    def find_suspicious_users(self):
        """Encuentra usuarios con nombres aleatorios o sospechosos"""
        def is_random_name(name):
            patterns = [
                r'^[A-Z]{2,}$',
                r'[0-9]{4,}',
                r'[A-Z]{3,}[a-z]{3,}[A-Z]{3,}',
                r'^[a-zA-Z0-9]{10,}$'
            ]
            return any(re.search(pattern, name) for pattern in patterns)

        suspicious = []
        for user in self.users_collection.find():
            if user.get('nombre') and is_random_name(user['nombre']):
                suspicious.append({
                    'id': str(user['_id']),
                    'email': user.get('email'),
                    'nombre': user.get('nombre')
                })
        return suspicious

    def cleanup_orphan_files(self):
        """Limpia archivos sin registro en BD y registros sin archivo físico"""
        try:
            # Verificar que el directorio existe
            if not os.path.exists(self.SPREADSHEET_FOLDER):
                os.makedirs(self.SPREADSHEET_FOLDER, exist_ok=True)
                return 0, 0
            
            # Archivos sin registro
            physical_files = set()
            try:
                physical_files = set(f for f in os.listdir(self.SPREADSHEET_FOLDER) 
                                   if f.endswith(('.xlsx', '.xls', '.csv')))
            except OSError as e:
                print(f"Error al listar archivos: {str(e)}")
                return 0, 0
            
            db_files = set()
            try:
                db_files = set(table['filename'] for table in self.spreadsheets_collection.find() 
                              if table.get('filename'))
            except Exception as e:
                print(f"Error al consultar la base de datos: {str(e)}")
                return 0, 0
            
            orphan_files = physical_files - db_files
            
            # Eliminar archivos huérfanos
            for file in orphan_files:
                try:
                    filepath = os.path.join(self.SPREADSHEET_FOLDER, file)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except OSError as e:
                    print(f"Error al eliminar archivo {file}: {str(e)}")
                    continue

            # Registros sin archivo
            missing_files = []
            try:
                for table in self.spreadsheets_collection.find():
                    if table.get('filename'):
                        filepath = os.path.join(self.SPREADSHEET_FOLDER, table['filename'])
                        if not os.path.exists(filepath):
                            missing_files.append(table['_id'])
                
                if missing_files:
                    self.spreadsheets_collection.delete_many({'_id': {'$in': missing_files}})
            except Exception as e:
                print(f"Error al procesar registros sin archivo: {str(e)}")
                return len(orphan_files), 0
            
            return len(orphan_files), len(missing_files)
        except Exception as e:
            print(f"Error general en cleanup_orphan_files: {str(e)}")
            return 0, 0

    def get_database_stats(self):
        """Obtiene estadísticas de la base de datos"""
        try:
            return {
                'total_users': self.users_collection.count_documents({}),
                'roles': {
                    'admin': self.users_collection.count_documents({'role': 'admin'}),
                    'normal': self.users_collection.count_documents({'role': 'normal'}),
                    'no_role': self.users_collection.count_documents({
                        '$or': [
                            {'role': {'$exists': False}},
                            {'role': None}
                        ]
                    })
                },
                'locked_accounts_24h': self.users_collection.count_documents({
                    'locked_until': {
                        '$gt': datetime.now()
                    }
                })
            }
        except Exception as e:
            print(f"Error al obtener estadísticas: {str(e)}")
            return {
                'total_users': 0,
                'roles': {
                    'admin': 0,
                    'normal': 0,
                    'no_role': 0
                },
                'locked_accounts_24h': 0
            }

    def update_user_role(self, email, new_role):
        """Actualiza el rol de un usuario usando su email"""
        if new_role not in ['admin', 'normal']:
            return False
        
        try:
            # Verificar si el usuario existe
            user = self.users_collection.find_one({'email': email})
            if not user:
                return False
            
            result = self.users_collection.update_one(
                {'email': email},
                {
                    '$set': {
                        'role': new_role,
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error al actualizar rol: {str(e)}")
            return False
    
    def update_user_email(self, user_id, new_email):
        """Actualiza el email de un usuario"""
        try:
            # Verificar si el usuario existe
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return False
            
            # Verificar si el email ya existe
            existing_user = self.users_collection.find_one({'email': new_email})
            if existing_user and str(existing_user['_id']) != user_id:
                return False
            
            # Validar formato de email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                return False
            
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'email': new_email,
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_user_password(self, user_id, new_password):
        """Actualiza la contraseña de un usuario"""
        try:
            # Verificar si el usuario existe
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return False
            
            # Validar requisitos de contraseña
            if len(new_password) < 8:
                return False
            if not re.search(r"[A-Z]", new_password):
                return False
            if not re.search(r"[a-z]", new_password):
                return False
            if not re.search(r"\d", new_password):
                return False
            
            from werkzeug.security import generate_password_hash
            
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'password': generate_password_hash(new_password),
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
            
    def update_user_nombre(self, user_id, new_nombre):
        """Actualiza el nombre de un usuario"""
        try:
            # Verificar si el usuario existe
            user = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return False
            
            # Validar longitud del nombre
            if len(new_nombre.strip()) < 2:
                return False
            
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'nombre': new_nombre.strip(),
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False

    def delete_user(self, email):
        """Elimina un usuario y sus tablas"""
        user = self.users_collection.find_one({'email': email})
        if not user:
            return False, "Usuario no encontrado"
        
        # Eliminar tablas del usuario
        tables = self.spreadsheets_collection.find({'owner': user.get('username', '')})
        for table in tables:
            if table.get('filename'):
                filepath = os.path.join(self.SPREADSHEET_FOLDER, table['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        self.spreadsheets_collection.delete_many({'owner': user.get('username', '')})
        self.users_collection.delete_one({'_id': user['_id']})
        return True, "Usuario y sus tablas eliminados correctamente"

    def check_duplicate_users(self):
        """Verifica usuarios duplicados basándose en email, nombre o username similar"""
        duplicates = []
        all_users = list(self.users_collection.find())
        
        # Función para normalizar texto
        def normalize_text(text):
            if not text:
                return ""
            return text.lower().strip()
        
        # Agrupar usuarios por email normalizado
        email_groups = {}
        for user in all_users:
            email = normalize_text(user.get('email'))
            if email:
                if email not in email_groups:
                    email_groups[email] = []
                email_groups[email].append(user)
        
        # Agrupar usuarios por nombre normalizado
        name_groups = {}
        for user in all_users:
            name = normalize_text(user.get('nombre', user.get('username', '')))
            if name:
                if name not in name_groups:
                    name_groups[name] = []
                name_groups[name].append(user)
        
        # Encontrar duplicados por email
        for email, users in email_groups.items():
            if len(users) > 1:
                duplicates.append({
                    'type': 'email',
                    'value': email,
                    'users': [{
                        'id': str(u['_id']),
                        'email': u.get('email'),
                        'nombre': u.get('nombre', u.get('username')),
                        'role': u.get('role', 'No especificado'),
                        'created_at': u.get('created_at')
                    } for u in users]
                })
        
        # Encontrar duplicados por nombre
        for name, users in name_groups.items():
            if len(users) > 1:
                # Verificar que no sean los mismos usuarios que ya encontramos por email
                user_ids = set(str(u['_id']) for u in users)
                already_found = False
                for dup in duplicates:
                    if any(u['id'] in user_ids for u in dup['users']):
                        already_found = True
                        break
                
                if not already_found:
                    duplicates.append({
                        'type': 'nombre',
                        'value': name,
                        'users': [{
                            'id': str(u['_id']),
                            'email': u.get('email'),
                            'nombre': u.get('nombre', u.get('username')),
                            'role': u.get('role', 'No especificado'),
                            'created_at': u.get('created_at')
                        } for u in users]
                    })
        
        return duplicates
