#!/usr/bin/env python3
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi

def check_database():
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Conectar a MongoDB Atlas
        client = MongoClient(
            os.getenv('MONGO_URI'),
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1')
        )
        
        # Seleccionar la base de datos correcta
        db = client['app_catalogojoyero_nueva']
        users = db['users']
        
        print('Conexión a MongoDB Atlas establecida')
        print('\nUsuarios encontrados en app_catalogojoyero_nueva:')
        
        users_list = list(users.find())
        if not users_list:
            print('No hay usuarios en la base de datos')
            return
            
        for user in users_list:
            print(f'\n- ID: {user.get("_id")}')
            print(f'  Email: {user.get("email")}')
            print(f'  Nombre: {user.get("nombre")}')
            print(f'  Role: {user.get("role")}')
            print(f'  Password type: {type(user.get("password"))}')
            if user.get("password"):
                print(f'  Password length: {len(user.get("password"))}')
            print('---')
            
    except Exception as e:
        print(f'Error al conectar a la base de datos: {str(e)}')

if __name__ == '__main__':
    check_database()
