#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script mejorado para limpieza de imágenes no utilizadas

Características principales:
- Verifica imágenes no referenciadas en MongoDB
- Detecta duplicados usando hash perceptual
- Valida integridad de imágenes
- Soporta múltiples formatos
- Logging detallado
- Modo simulación (dry-run)
- Estadísticas detalladas
"""

import os
import sys
import json
import hashlib
import logging
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional, Union, TypedDict
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, UnidentifiedImageError
import imagehash
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import certifi


class ConfigDict(TypedDict):
    image_dirs: List[str]
    unused_dir: str
    extensions: List[str]
    min_file_size: int
    max_file_size: int
    min_dimension: int
    min_age_days: int
    hash_size: int
    max_workers: int


# Cargar variables de entorno
load_dotenv()

# Configuración por defecto
DEFAULT_CONFIG: ConfigDict = {
    "image_dirs": [
        "/Users/edefrutos/_Repositorios/01.IDE_Cursor/edf_catalogotablas/app/static/uploads"
    ],
    "unused_dir": "/Users/edefrutos/_Repositorios/01.IDE_Cursor/edf_catalogotablas/app/static/unused_images",
    "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "min_file_size": 1024,  # 1KB
    "max_file_size": 20 * 1024 * 1024,  # 20MB
    "min_dimension": 50,  # 50x50 píxeles
    "min_age_days": 30,  # Edad mínima en días
    "hash_size": 8,  # Tamaño del hash para comparación de imágenes
    "max_workers": 4,  # Número de hilos para procesamiento paralelo
}


class ImageCleaner:
    """Clase principal para la limpieza de imágenes"""

    def __init__(self, config: Optional[ConfigDict] = None):
        """Inicializar con configuración personalizada"""
        if config is None:
            self.config = DEFAULT_CONFIG
        else:
            self.config = {**DEFAULT_CONFIG, **config}
        self.logger = self._setup_logging()
        self.stats = {
            "total_processed": 0,
            "duplicates_found": 0,
            "unused_found": 0,
            "moved": 0,
            "errors": 0,
            "freed_space": 0,  # bytes
        }

        # Conexión a MongoDB
        self.db = self._connect_mongodb()

        # Crear directorio de respaldo si no existe
        unused_dir: str = self.config["unused_dir"]
        os.makedirs(unused_dir, exist_ok=True)

    def _setup_logging(self) -> logging.Logger:
        """Configurar el sistema de logging"""
        logger = logging.getLogger("image_cleaner")
        logger.setLevel(logging.INFO)

        # Formato del log
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler para archivo
        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "logs",
            f"clean_images_{datetime.now().strftime('%Y%m%d')}.log",
        )
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _connect_mongodb(self):
        """Establecer conexión con MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("La variable de entorno MONGO_URI no está configurada")

            client = MongoClient(
                mongo_uri,
                tls=True,
                tlsCAFile=certifi.where(),
                server_api=ServerApi("1"),
            )

            # Verificar conexión
            client.admin.command("ping")
            self.logger.info("Conexión exitosa a MongoDB")

            # Retornar la base de datos configurada
            db_name = os.getenv("MONGO_DB", "app_catalogojoyero_nueva")
            return client[db_name]

        except Exception as e:
            self.logger.error(f"Error al conectar con MongoDB: {e}")
            sys.exit(1)

    def is_image_used(self, image_path: str) -> bool:
        """Verifica si una imagen está siendo usada en la base de datos"""
        try:
            # Calcular hash MD5 de la imagen
            with open(image_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # Buscar en colecciones que podrían contener referencias a imágenes
            collections_to_check = [
                (self.db["catalogos"], ["imagenes", "imagen", "logo"]),
                (self.db["productos"], ["imagenes", "imagen"]),
                (self.db["usuarios"], ["avatar", "foto_perfil"]),
            ]

            filename = os.path.basename(image_path)

            for collection, fields in collections_to_check:
                query = {
                    "$or": [
                        {field: {"$regex": filename, "$options": "i"}}
                        for field in fields
                    ]
                }

                # Agregar búsqueda por hash si está disponible
                query["$or"].append({"image_hash": {"$eq": file_hash}})

                if collection.count_documents(query) > 0:
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error al verificar uso de imagen {image_path}: {e}")
            return True  # Por seguridad, asumir que está en uso

    def is_valid_image(self, file_path: str) -> bool:
        """Verifica si un archivo es una imagen válida"""
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verificar integridad

                # Verificar dimensiones mínimas
                min_dimension: int = self.config["min_dimension"]
                if min(img.size) < min_dimension:
                    self.logger.warning(
                        f"Imagen muy pequeña: {file_path} ({img.size[0]}x{img.size[1]})"
                    )
                    return False

                return True

        except (UnidentifiedImageError, Exception) as e:
            self.logger.warning(f"Imagen inválida: {file_path} - {e}")
            return False

    def find_duplicates(self) -> Dict[str, List[str]]:
        """Encuentra imágenes duplicadas usando hash perceptual"""
        self.logger.info("Buscando imágenes duplicadas...")
        hashes: Dict[str, List[str]] = {}

        extensions: List[str] = self.config["extensions"]
        image_dirs: List[str] = self.config["image_dirs"]
        for ext in extensions:
            for img_dir in image_dirs:
                for img_path in Path(img_dir).rglob(f"*{ext}"):
                    img_path_str = str(img_path)

                    if not self.is_valid_image(img_path_str):
                        continue

                    try:
                        with Image.open(img_path) as img:
                            # Usar hash perceptual para encontrar duplicados
                            hash_size: int = self.config["hash_size"]
                            img_hash = str(imagehash.average_hash(img, hash_size))

                            if img_hash in hashes:
                                hashes[img_hash].append(img_path_str)
                            else:
                                hashes[img_hash] = [img_path_str]
                    except Exception as e:
                        self.logger.error(f"Error al procesar {img_path}: {e}")

        # Filtrar solo los duplicados
        return {k: v for k, v in hashes.items() if len(v) > 1}

    def process_file(
        self, filepath: str, duplicates: Dict[str, List[str]], dry_run: bool = True
    ) -> None:
        """Procesa un archivo individual"""
        try:
            file_stat = os.stat(filepath)
            file_age = (
                datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
            ).days

            # Verificar tamaño del archivo
            min_file_size: int = self.config["min_file_size"]
            max_file_size: int = self.config["max_file_size"]
            if not (min_file_size <= file_stat.st_size <= max_file_size):
                self.logger.warning(
                    f"Tamaño de archivo fuera de rango: {filepath} ({file_stat.st_size} bytes)"
                )
                return

            # Verificar si es un duplicado
            is_duplicate = any(
                filepath in dup_list
                for dup_list in duplicates.values()
                if len(dup_list) > 1
                and filepath != dup_list[0]  # Mantener la primera ocurrencia
            )

            if is_duplicate:
                self.stats["duplicates_found"] += 1
                action = "DUPLICADO"
            # Verificar si no se usa y es más viejo que min_age_days
            else:
                min_age_days: int = self.config["min_age_days"]
                if file_age > min_age_days and not self.is_image_used(filepath):
                    self.stats["unused_found"] += 1
                    action = "NO USADA"
                else:
                    return

            # Tomar acción
            if dry_run:
                self.logger.info(f"[SIMULACIÓN] {action}: {filepath} ({file_age} días)")
            else:
                try:
                    # Mover a directorio de respaldo
                    unused_dir: str = self.config["unused_dir"]
                    backup_path = os.path.join(unused_dir, os.path.basename(filepath))

                    # Evitar colisiones de nombres
                    counter = 1
                    while os.path.exists(backup_path):
                        name, ext = os.path.splitext(backup_path)
                        backup_path = f"{name}_{counter}{ext}"
                        counter += 1

                    shutil.move(filepath, backup_path)
                    self.stats["moved"] += 1
                    self.stats["freed_space"] += file_stat.st_size
                    self.logger.info(f"MOVIDA: {filepath} -> {backup_path}")
                except Exception as e:
                    self.stats["errors"] += 1
                    self.logger.error(f"Error al mover {filepath}: {e}")

        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Error al procesar {filepath}: {e}")

    def clean_directory(self, dry_run: bool = True) -> None:
        """Limpia el directorio de imágenes no utilizadas"""
        self.logger.info("Iniciando limpieza de imágenes...")
        self.logger.info(f"Modo simulación: {'ACTIVADO' if dry_run else 'DESACTIVADO'}")

        # Encontrar duplicados
        duplicates = self.find_duplicates()

        # Procesar archivos
        image_dirs: List[str] = self.config["image_dirs"]
        for img_dir in image_dirs:
            if not os.path.isdir(img_dir):
                self.logger.warning(f"El directorio no existe: {img_dir}")
                continue

            self.logger.info(f"Procesando directorio: {img_dir}")

            # Recorrer archivos en paralelo
            max_workers: int = self.config["max_workers"]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for root, _, files in os.walk(img_dir):
                    # Saltar directorio de respaldo
                    if "unused_images" in root:
                        continue

                    for filename in files:
                        extensions: List[str] = self.config["extensions"]
                        if not any(
                            filename.lower().endswith(ext) for ext in extensions
                        ):
                            continue

                        filepath = os.path.join(root, filename)
                        self.stats["total_processed"] += 1

                        # Procesar archivo
                        executor.submit(
                            self.process_file, filepath, duplicates, dry_run
                        )

        # Mostrar resumen
        self._print_summary(dry_run)

    def _print_summary(self, dry_run: bool) -> None:
        """Muestra un resumen de la operación"""
        summary = [
            "\n" + "=" * 50,
            "RESUMEN DE LIMPIEZA",
            "=" * 50,
            f"Total de imágenes analizadas: {self.stats['total_processed']}",
            f"Imágenes duplicadas encontradas: {self.stats['duplicates_found']}",
            f"Imágenes no utilizadas: {self.stats['unused_found']}",
            f"Imágenes movidas a respaldo: {self.stats['moved']}",
            f"Espacio liberado: {self.stats['freed_space'] / (1024 * 1024):.2f} MB",
            f"Errores encontrados: {self.stats['errors']}",
        ]

        if dry_run:
            summary.append("\nMODO SIMULACIÓN: No se realizaron cambios reales")
        else:
            unused_dir: str = self.config["unused_dir"]
            summary.append(f"\nLas imágenes se movieron a: {unused_dir}")

        for line in summary:
            self.logger.info(line)


def parse_arguments():
    """Configura los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description="Limpia imágenes no utilizadas")
    parser.add_argument(
        "--dry-run", action="store_true", help="Solo simular sin hacer cambios"
    )
    parser.add_argument(
        "--config", type=str, help="Ruta al archivo de configuración JSON"
    )
    parser.add_argument(
        "--min-age",
        type=int,
        help="Edad mínima en días para considerar una imagen como no utilizada",
    )
    return parser.parse_args()


def load_config(
    config_file: Optional[str] = None,
) -> ConfigDict:
    """Carga la configuración desde un archivo JSON"""
    config = DEFAULT_CONFIG.copy()

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file) as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"Error al cargar el archivo de configuración: {e}")
            sys.exit(1)

    return config


def main():
    """Función principal"""
    args = parse_arguments()

    # Cargar configuración
    config = load_config(args.config)

    # Sobrescribir configuración desde argumentos
    if args.min_age is not None:
        config["min_age_days"] = args.min_age

    # Iniciar limpieza
    cleaner = ImageCleaner(config)
    cleaner.clean_directory(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
