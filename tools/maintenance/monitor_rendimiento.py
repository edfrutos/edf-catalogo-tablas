#!/usr/bin/env python3
# Script: monitor_rendimiento.py
# Descripción: Monitorea el rendimiento de la base de datos MongoDB
# Uso: python3 monitor_rendimiento.py [--intervalo 60] [--duracion 3600]
# Requiere: pymongo, python-dotenv, tabulate
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05

import argparse
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient
from tabulate import tabulate

# Configuración de argumentos
parser = argparse.ArgumentParser(description="Monitor de rendimiento de MongoDB")
parser.add_argument(
    "--intervalo", type=int, default=60, help="Intervalo entre mediciones en segundos"
)
parser.add_argument(
    "--duracion",
    type=int,
    default=3600,
    help="Duración total del monitoreo en segundos",
)
args = parser.parse_args()


def conectar_mongodb():
    """Establece conexión con MongoDB."""
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        print("ERROR: La variable de entorno MONGO_URI no está definida")
        return None

    try:
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True,
            w="majority",
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
        )
        client.admin.command("ping")
        return client
    except Exception as e:
        print(f"Error al conectar a MongoDB: {str(e)}")
        return None


def obtener_estadisticas(client):
    """Obtiene estadísticas de rendimiento de MongoDB."""
    db = client.get_database()

    # Estadísticas generales de la base de datos
    stats = db.command("dbstats")

    # Estadísticas de operaciones
    server_status = db.command("serverStatus")

    # Obtener operaciones lentas
    current_op = db.current_op()
    operaciones_lentas = [
        op for op in current_op.get("inprog", []) if op.get("secs_running", 0) > 10
    ]  # > 10 segundos

    # Estadísticas de colecciones
    collections_stats = {}
    for collection_name in db.list_collection_names():
        try:
            coll_stats = db.command("collstats", collection_name)
            collections_stats[collection_name] = {
                "documentos": coll_stats.get("count", 0),
                "tamano": f"{coll_stats.get('size', 0) / (1024*1024):.2f} MB",
                "almacenamiento": f"{coll_stats.get('storageSize', 0) / (1024*1024):.2f} MB",
                "indices": len(coll_stats.get("indexSizes", {})),
                "tamano_indices": f"{coll_stats.get('totalIndexSize', 0) / (1024*1024):.2f} MB",
            }
        except BaseException:
            continue

    return {
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estadisticas": {
            "documentos": stats.get("objects", 0),
            "tamano": f"{stats.get('dataSize', 0) / (1024*1024):.2f} MB",
            "almacenamiento": f"{stats.get('storageSize', 0) / (1024*1024):.2f} MB",
            "indices": stats.get("indexes", 0),
            "tamano_indices": f"{stats.get('indexSize', 0) / (1024*1024):.2f} MB",
            "conexiones_activas": server_status.get("connections", {}).get("active", 0),
            "operaciones": server_status.get("opcounters", {}),
            "cola_operaciones": server_status.get("globalLock", {})
            .get("currentQueue", {})
            .get("total", 0),
            "operaciones_lentas": len(operaciones_lentas),
        },
        "colecciones": collections_stats,
    }


def mostrar_resumen(estadisticas):
    """Muestra un resumen de las estadísticas."""
    print(f"\n=== Resumen de Rendimiento - {estadisticas['fecha_hora']} ===")

    # Estadísticas generales
    print("\n📊 Estadísticas Generales:")
    print(f"📄 Documentos totales: {estadisticas['estadisticas']['documentos']:,}")
    print(f"💾 Tamaño de datos: {estadisticas['estadisticas']['tamano']}")
    print(f"💿 Almacenamiento usado: {estadisticas['estadisticas']['almacenamiento']}")
    print(f"🔍 Total de índices: {estadisticas['estadisticas']['indices']:,}")
    print(f"📏 Tamaño de índices: {estadisticas['estadisticas']['tamano_indices']}")

    # Conexiones y operaciones
    print("\n🔄 Estado de Operaciones:")
    print(
        f"🔌 Conexiones activas: {estadisticas['estadisticas']['conexiones_activas']}"
    )
    print(f"⏳ Operaciones en cola: {estadisticas['estadisticas']['cola_operaciones']}")
    print(
        f"🐌 Operaciones lentas (>10s): {estadisticas['estadisticas']['operaciones_lentas']}"
    )

    # Estadísticas de operaciones
    ops = estadisticas["estadisticas"]["operaciones"]
    print("\n📈 Contadores de Operaciones (totales):")
    print(f"  • Inserciones: {ops.get('insert', 0):,}")
    print(f"  • Consultas: {ops.get('query', 0):,}")
    print(f"  • Actualizaciones: {ops.get('update', 0):,}")
    print(f"  • Eliminaciones: {ops.get('delete', 0):,}")

    # Tabla de colecciones
    if estadisticas["colecciones"]:
        print("\n🗂️ Estadísticas por Colección:")
        table_data = []
        for nombre, stats in estadisticas["colecciones"].items():
            table_data.append(
                [
                    nombre,
                    f"{stats['documentos']:,}",
                    stats["tamano"],
                    stats["almacenamiento"],
                    stats["indices"],
                    stats["tamano_indices"],
                ]
            )

        headers = [
            "Colección",
            "Documentos",
            "Tamaño",
            "Almacenamiento",
            "Índices",
            "Tamaño Índices",
        ]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    print("\n" + "=" * 80 + "\n")


def main():
    """Función principal."""
    print(
        f"🔍 Iniciando monitoreo de MongoDB (Intervalo: {args.intervalo}s, Duración: {args.duracion}s)"
    )

    client = conectar_mongodb()
    if not client:
        return

    try:
        inicio = time.time()
        while (time.time() - inicio) < args.duracion:
            try:
                estadisticas = obtener_estadisticas(client)
                mostrar_resumen(estadisticas)

                # Registrar en archivo de log
                with open("mongodb_monitor.log", "a") as f:
                    f.write(
                        f"{estadisticas['fecha_hora']} - "
                        f"Documentos: {estadisticas['estadisticas']['documentos']}, "
                        f"Tamaño: {estadisticas['estadisticas']['tamano']}, "
                        f"Conexiones: {estadisticas['estadisticas']['conexiones_activas']}\n"
                    )

                # Esperar hasta la próxima iteración
                time.sleep(args.intervalo)

            except KeyboardInterrupt:
                print("\nMonitoreo detenido manualmente.")
                break
            except Exception as e:
                print(f"Error durante el monitoreo: {str(e)}")
                time.sleep(5)  # Esperar antes de reintentar

    finally:
        client.close()
        print("Conexión cerrada.")


if __name__ == "__main__":
    main()
