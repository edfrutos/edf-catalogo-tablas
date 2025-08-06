#!/usr/bin/env python3
# Script: 04_depurar_huérfanos.py
# Descripción: Depura y corrige documentos huérfanos encontrados en la validación de integridad
# Uso: python3 04_depurar_huérfanos.py [opciones]
# Requiere: python-dotenv, pymongo
# Variables de entorno: MONGO_URI, DB_NAME (desde .env)
# Autor: EDF Developer - 2025-05-28

import os
import certifi
from pymongo import MongoClient
from bson import ObjectId
from collections import Counter
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "app_catalogojoyero_nueva")

if not MONGO_URI:
    print("❌ Error: Variable de entorno MONGO_URI no está configurada")
    exit(1)

try:
    client: MongoClient = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    client.admin.command("ping")
    db = client[DB_NAME]
    print("✅ Conexión a MongoDB establecida correctamente")
except Exception as e:
    print(f"❌ Error al conectar con MongoDB: {e}")
    exit(1)


def obtener_usuarios_validos():
    """Obtiene lista de usuarios válidos con email y username"""
    users = list(db["users"].find())
    usuarios_validos = {}

    for user in users:
        email = user.get("email", "").lower()
        username = user.get("username", "").lower()

        if email:
            usuarios_validos[email] = {
                "id": str(user["_id"]),
                "username": username,
                "email": email,
                "role": user.get("role", "user"),
            }

        if username:
            usuarios_validos[username] = {
                "id": str(user["_id"]),
                "username": username,
                "email": email,
                "role": user.get("role", "user"),
            }

    return usuarios_validos


def encontrar_huérfanos():
    """Encuentra todos los documentos huérfanos"""
    usuarios_validos = obtener_usuarios_validos()
    huérfanos = {"catalogs": [], "spreadsheets": []}

    # Buscar en catalogs
    for doc in db["catalogs"].find():
        owner = (
            doc.get("owner") or doc.get("created_by") or doc.get("owner_name") or ""
        ).lower()
        if owner and owner not in usuarios_validos:
            huérfanos["catalogs"].append(
                {
                    "_id": str(doc["_id"]),
                    "owner": owner,
                    "name": doc.get("name", ""),
                    "doc": doc,
                }
            )

    # Buscar en spreadsheets
    for doc in db["spreadsheets"].find():
        owner = (
            doc.get("owner") or doc.get("created_by") or doc.get("owner_name") or ""
        ).lower()
        if owner and owner not in usuarios_validos:
            huérfanos["spreadsheets"].append(
                {
                    "_id": str(doc["_id"]),
                    "owner": owner,
                    "name": doc.get("name", ""),
                    "doc": doc,
                }
            )

    return huérfanos, usuarios_validos


def mostrar_usuarios_disponibles(usuarios_validos):
    """Muestra lista de usuarios disponibles para reasignación"""
    print("\n📋 USUARIOS DISPONIBLES:")
    print("-" * 50)
    for i, (key, user) in enumerate(usuarios_validos.items(), 1):
        print(f"{i:2d}. {key} (ID: {user['id']}, Role: {user['role']})")


def reasignar_owner(collection, doc_id, nuevo_owner, usuarios_validos):
    """Reasigna el owner de un documento"""
    try:
        # Obtener información del nuevo owner
        nuevo_owner_info = usuarios_validos.get(nuevo_owner.lower())
        if not nuevo_owner_info:
            print(f"❌ Usuario '{nuevo_owner}' no encontrado")
            return False

        # Convertir doc_id a ObjectId
        try:
            object_id = ObjectId(doc_id)
        except Exception as e:
            print(f"❌ ID de documento inválido: {doc_id} - {e}")
            return False

        # Actualizar el documento
        result = db[collection].update_one(
            {"_id": object_id},
            {
                "$set": {
                    "owner": nuevo_owner_info["email"] or nuevo_owner_info["username"],
                    "created_by": nuevo_owner_info["email"]
                    or nuevo_owner_info["username"],
                    "owner_name": nuevo_owner_info["email"]
                    or nuevo_owner_info["username"],
                }
            },
        )

        if result.modified_count > 0:
            print(f"✅ Documento actualizado: {collection} - {doc_id}")
            return True
        else:
            print(f"❌ No se pudo actualizar el documento: {collection} - {doc_id}")
            return False

    except Exception as e:
        print(f"❌ Error al actualizar: {e}")
        return False


def main():
    print("🔍 DEPURACIÓN DE DOCUMENTOS HUÉRFANOS")
    print("=" * 50)

    huérfanos, usuarios_validos = encontrar_huérfanos()

    if not huérfanos["catalogs"] and not huérfanos["spreadsheets"]:
        print("✅ No se encontraron documentos huérfanos")
        return

    # Mostrar resumen
    print(f"\n📊 RESUMEN DE HUÉRFANOS:")
    print(f"   - Catálogos: {len(huérfanos['catalogs'])}")
    print(f"   - Spreadsheets: {len(huérfanos['spreadsheets'])}")

    # Mostrar usuarios disponibles
    mostrar_usuarios_disponibles(usuarios_validos)

    # Procesar cada tipo de documento
    for tipo, docs in huérfanos.items():
        if not docs:
            continue

        print(f"\n📁 PROCESANDO {tipo.upper()}:")
        print("-" * 40)

        for doc in docs:
            print(f"\n📄 Documento: {doc['name']} (ID: {doc['_id']})")
            print(f"   Owner actual: {doc['owner']}")

            # Opciones para el usuario
            print("\nOpciones:")
            print("1. Reasignar a un usuario válido")
            print("2. Eliminar documento")
            print("3. Saltar este documento")

            try:
                opcion = input("\nSelecciona una opción (1-3): ").strip()

                if opcion == "1":
                    print("\nUsuarios disponibles:")
                    usuarios_list = list(usuarios_validos.keys())
                    for i, usuario in enumerate(
                        usuarios_list[:10], 1
                    ):  # Mostrar solo los primeros 10
                        print(f"{i}. {usuario}")

                    try:
                        idx = int(input("Selecciona el número de usuario: ")) - 1
                        if 0 <= idx < len(usuarios_list):
                            nuevo_owner = usuarios_list[idx]
                            if reasignar_owner(
                                tipo, doc["_id"], nuevo_owner, usuarios_validos
                            ):
                                print("✅ Reasignación exitosa")
                            else:
                                print("❌ Error en la reasignación")
                        else:
                            print("❌ Número inválido")
                    except ValueError:
                        print("❌ Entrada inválida")

                elif opcion == "2":
                    confirmar = (
                        input(
                            "¿Estás seguro de que quieres eliminar este documento? (s/N): "
                        )
                        .strip()
                        .lower()
                    )
                    if confirmar == "s":
                        try:
                            # Convertir doc_id a ObjectId
                            object_id = ObjectId(doc["_id"])
                            result = db[tipo].delete_one({"_id": object_id})
                            if result.deleted_count > 0:
                                print("✅ Documento eliminado")
                            else:
                                print("❌ No se pudo eliminar el documento")
                        except Exception as e:
                            print(f"❌ Error al eliminar: {e}")
                    else:
                        print("Operación cancelada")

                elif opcion == "3":
                    print("Documento saltado")

                else:
                    print("❌ Opción inválida")

            except KeyboardInterrupt:
                print("\n\n⏹️  Operación cancelada por el usuario")
                return

    print("\n🎉 Proceso de depuración completado")


if __name__ == "__main__":
    main()
