#!/usr/bin/env python3
# Script: pruebas_rendimiento.py
# Descripción: Realiza pruebas de rendimiento en la base de datos MongoDB
# Uso: python3 pruebas_rendimiento.py [--operaciones 1000] [--hilos 5]
# Requiere: pymongo, python-dotenv, faker, tqdm, tabulate
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import argparse
import os
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient, UpdateOne
from tabulate import tabulate
from tqdm import tqdm

# Configuración de argumentos
parser = argparse.ArgumentParser(description='Pruebas de rendimiento MongoDB')
parser.add_argument('--operaciones', type=int, default=1000,
                    help='Número total de operaciones a realizar')
parser.add_argument('--hilos', type=int, default=5,
                    help='Número de hilos para operaciones concurrentes')
args = parser.parse_args()

# Configuración
OPERACIONES_POR_HILO = args.operaciones // args.hilos
FAKER = Faker('es_ES')

class PruebaRendimiento:
    def __init__(self):
        self.client = None
        self.db = None
        self.resultados = {
            'inserciones': {'tiempos': [], 'exitosos': 0, 'fallidos': 0},
            'consultas': {'tiempos': [], 'exitosos': 0, 'fallidos': 0},
            'actualizaciones': {'tiempos': [], 'exitosos': 0, 'fallidos': 0},
            'eliminaciones': {'tiempos': [], 'exitosos': 0, 'fallidos': 0},
        }

    def conectar(self):
        """Establece conexión con MongoDB."""
        load_dotenv()
        mongo_uri = os.getenv('MONGO_URI')

        if not mongo_uri:
            print("ERROR: La variable de entorno MONGO_URI no está definida")
            return False

        try:
            self.client = MongoClient(
                mongo_uri,
                tls=True,
                tlsAllowInvalidCertificates=True,
                retryWrites=True,
                w='majority',
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                maxPoolSize=args.hilos + 5  # Pool de conexiones para los hilos
            )
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            return True
        except Exception as e:
            print(f"Error al conectar a MongoDB: {str(e)}")
            return False

    def generar_usuario_aleatorio(self):
        """Genera un usuario aleatorio para pruebas."""
        username = FAKER.user_name()
        email = f"{username}@example.com"
        return {
            'username': username,
            'email': email,
            'nombre': FAKER.first_name(),
            'apellido': FAKER.last_name(),
            'fecha_registro': datetime.utcnow(),
            'activo': random.choice([True, False]),
            'intentos_fallidos': random.randint(0, 5),
            'ultimo_acceso': FAKER.date_time_this_year(),
            'roles': random.choices(
                ['usuario', 'editor', 'admin'],
                weights=[0.8, 0.15, 0.05],
                k=random.randint(1, 2)
            )
        }

    def ejecutar_prueba_insercion(self, num_operaciones):
        """Ejecuta pruebas de inserción."""
        exitosos = 0
        fallidos = 0
        tiempos = []

        for _ in range(num_operaciones):
            usuario = self.generar_usuario_aleatorio()
            start_time = time.time()

            try:
                self.db.users.insert_one(usuario)
                exitosos += 1
            except Exception as e:
                fallidos += 1
            finally:
                tiempos.append(time.time() - start_time)

        return exitosos, fallidos, tiempos

    def ejecutar_prueba_consulta(self, num_operaciones):
        """Ejecuta pruebas de consulta."""
        exitosos = 0
        fallidos = 0
        tiempos = []

        for _ in range(num_operaciones):
            # Consulta aleatoria: 50% por username, 30% por email, 20% por estado
            query_type = random.choices(
                ['username', 'email', 'activo'],
                weights=[0.5, 0.3, 0.2],
                k=1
            )[0]

            if query_type == 'username':
                # Consulta por prefijo de username
                letra = random.choice(string.ascii_lowercase)
                query = {'username': {'$regex': f'^{letra}', '$options': 'i'}}
            elif query_type == 'email':
                # Consulta por dominio de email
                dominio = random.choice(['gmail.com', 'hotmail.com', 'example.com'])
                query = {'email': {'$regex': f'@{dominio}$'}}
            else:
                # Consulta por estado
                query = {'activo': random.choice([True, False])}

            start_time = time.time()

            try:
                resultados = list(self.db.users.find(query).limit(10))
                exitosos += 1
            except Exception as e:
                fallidos += 1
            finally:
                tiempos.append(time.time() - start_time)

        return exitosos, fallidos, tiempos

    def ejecutar_prueba_actualizacion(self, num_operaciones):
        """Ejecuta pruebas de actualización."""
        exitosos = 0
        fallidos = 0
        tiempos = []

        # Obtener algunos IDs de usuarios para actualizar
        usuarios = list(self.db.users.find({}, {'_id': 1}).limit(1000))
        if not usuarios:
            return 0, 0, []

        for _ in range(num_operaciones):
            usuario = random.choice(usuarios)

            # Actualización aleatoria
            update = {}
            if random.random() < 0.7:  # 70% de probabilidad de actualizar último acceso
                update['$set'] = {'ultimo_acceso': datetime.utcnow()}
            if random.random() < 0.3:  # 30% de probabilidad de incrementar intentos
                update['$inc'] = {'intentos_fallidos': 1}

            start_time = time.time()

            try:
                resultado = self.db.users.update_one(
                    {'_id': usuario['_id']},
                    update
                )
                if resultado.modified_count > 0:
                    exitosos += 1
                else:
                    fallidos += 1
            except Exception as e:
                fallidos += 1
            finally:
                tiempos.append(time.time() - start_time)

        return exitosos, fallidos, tiempos

    def ejecutar_prueba_eliminacion(self, num_operaciones):
        """Ejecuta pruebas de eliminación."""
        exitosos = 0
        fallidos = 0
        tiempos = []

        # Crear usuarios temporales para eliminar
        usuarios_a_eliminar = []
        for _ in range(num_operaciones):
            usuarios_a_eliminar.append(self.generar_usuario_aleatorio())

        # Insertar usuarios temporales
        if usuarios_a_eliminar:
            try:
                resultado = self.db.users.insert_many(usuarios_a_eliminar)
                ids_a_eliminar = resultado.inserted_ids
            except Exception as e:
                print(f"Error al insertar usuarios para prueba de eliminación: {str(e)}")
                return 0, 0, []

        # Realizar eliminaciones
        for user_id in ids_a_eliminar:
            start_time = time.time()

            try:
                resultado = self.db.users.delete_one({'_id': user_id})
                if resultado.deleted_count > 0:
                    exitosos += 1
                else:
                    fallidos += 1
            except Exception as e:
                fallidos += 1
            finally:
                tiempos.append(time.time() - start_time)

        return exitosos, fallidos, tiempos

    def ejecutar_pruebas_concurrentes(self, tipo_prueba, num_operaciones, num_hilos):
        """Ejecuta pruebas en paralelo usando múltiples hilos."""
        operaciones_por_hilo = num_operaciones // num_hilos
        resultados = []

        with ThreadPoolExecutor(max_workers=num_hilos) as executor:
            # Crear tareas
            futuros = []
            for _ in range(num_hilos):
                if tipo_prueba == 'insercion':
                    futuro = executor.submit(self.ejecutar_prueba_insercion, operaciones_por_hilo)
                elif tipo_prueba == 'consulta':
                    futuro = executor.submit(self.ejecutar_prueba_consulta, operaciones_por_hilo)
                elif tipo_prueba == 'actualizacion':
                    futuro = executor.submit(self.ejecutar_prueba_actualizacion, operaciones_por_hilo)
                elif tipo_prueba == 'eliminacion':
                    futuro = executor.submit(self.ejecutar_prueba_eliminacion, operaciones_por_hilo)
                else:
                    continue
                futuros.append(futuro)

            # Progreso
            with tqdm(total=num_operaciones, desc=f"Prueba de {tipo_prueca}", unit='op') as pbar:
                for futuro in as_completed(futuros):
                    try:
                        exitosos, fallidos, tiempos = futuro.result()
                        resultados.append((exitosos, fallidos, tiempos))
                        pbar.update(exitosos + fallidos)
                    except Exception as e:
                        print(f"Error en hilo: {str(e)}")

        # Consolidar resultados
        total_exitosos = sum(r[0] for r in resultados)
        total_fallidos = sum(r[1] for r in resultados)
        todos_tiempos = [t for r in resultados for t in r[2]]

        # Calcular estadísticas
        if todos_tiempos:
            tiempo_promedio = sum(todos_tiempos) / len(todos_tiempos)
            tiempo_min = min(todos_tiempos)
            tiempo_max = max(todos_tiempos)
            ops_por_segundo = len(todos_tiempos) / sum(todos_tiempos)
        else:
            tiempo_promedio = tiempo_min = tiempo_max = ops_por_segundo = 0

        # Almacenar resultados
        self.resultados[tipo_prueba] = {
            'total': total_exitosos + total_fallidos,
            'exitosos': total_exitosos,
            'fallidos': total_fallidos,
            'tiempo_promedio': tiempo_promedio,
            'tiempo_min': tiempo_min,
            'tiempo_max': tiempo_max,
            'ops_por_segundo': ops_por_segundo
        }

        return self.resultados[tipo_prueba]

    def mostrar_resultados(self):
        """Muestra los resultados de las pruebas."""
        print("\n" + "="*80)
        print("RESULTADOS DE LAS PRUEBAS DE RENDIMIENTO".center(80))
        print("="*80)

        # Tabla de resumen
        tabla = []
        for prueba, datos in self.resultados.items():
            if not isinstance(datos, dict) or 'total' not in datos:
                continue

            tabla.append([
                prueba.capitalize(),
                f"{datos['exitosos']:,}",
                f"{datos['fallidos']:,}",
                f"{datos['tiempo_promedio']*1000:.2f} ms",
                f"{datos['tiempo_min']*1000:.2f} ms",
                f"{datos['tiempo_max']*1000:.2f} ms",
                f"{datos['ops_por_segundo']:.2f} ops/s"
            ])

        headers = [
            'Prueba', 'Éxitos', 'Fallos', 'Tiempo Promedio',
            'Tiempo Mín', 'Tiempo Máx', 'Operaciones/seg'
        ]

        print(tabulate(tabla, headers=headers, tablefmt='grid'))

        # Recomendaciones
        print("\n" + "-"*80)
        print("RECOMENDACIONES".center(80))
        print("-"*80)

        # Analizar rendimiento de consultas
        if 'consulta' in self.resultados and self.resultados['consulta'].get('tiempo_promedio', 0) > 0.1:  # > 100ms
            print("⚠️  Las consultas están siendo lentas (más de 100ms en promedio).")
            print("   Considera agregar índices en los campos de búsqueda frecuentes.")

        # Analizar rendimiento de inserciones
        if 'insercion' in self.resultados:
            ops_insercion = self.resultados['insercion'].get('ops_por_segundo', 0)
            if ops_insercion < 100:  # Menos de 100 inserciones/segundo
                print(f"⚠️  Las inserciones son lentas ({ops_insercion:.2f} ops/seg).")
                print("   Considera usar insertMany para operaciones por lotes.")

        # Verificar tasa de fallos
        for prueba, datos in self.resultados.items():
            if not isinstance(datos, dict) or 'total' not in datos:
                continue

            total = datos['total']
            if total > 0 and datos['fallidos'] / total > 0.1:  # Más del 10% de fallos
                print(f"⚠️  Alta tasa de fallos en {prueba}: {datos['fallidos']} de {total} operaciones fallidas.")

        print("\n" + "="*80 + "\n")

def main():
    """Función principal."""
    print("="*80)
    print("PRUEBAS DE RENDIMIENTO MONGODB".center(80))
    print("="*80)
    print(f"Operaciones totales: {args.operaciones:,}")
    print(f"Hilos: {args.hilos}")
    print(f"Operaciones por hilo: {OPERACIONES_POR_HILO:,}")

    prueba = PruebaRendimiento()

    if not prueba.conectar():
        return 1

    try:
        # Ejecutar pruebas
        pruebas = [
            ('insercion', 'Inserción'),
            ('consulta', 'Consulta'),
            ('actualizacion', 'Actualización'),
            ('eliminacion', 'Eliminación')
        ]

        for tipo, nombre in pruebas:
            print(f"\n🔧 Ejecutando prueba de {nombre}...")
            prueba.ejecutar_pruebas_concurrentes(
                tipo,
                OPERACIONES_POR_HILO * args.hilos,
                args.hilos
            )

        # Mostrar resultados
        prueba.mostrar_resultados()

        return 0

    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario.")
        return 1
    except Exception as e:
        print(f"\nError durante las pruebas: {str(e)}")
        return 1
    finally:
        if prueba.client:
            prueba.client.close()
            print("\nConexión cerrada.")

if __name__ == "__main__":
    sys.exit(main())
