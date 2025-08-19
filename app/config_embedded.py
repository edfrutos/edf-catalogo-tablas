#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Script: config_embedded.py
# Descripción: [Configuración para la aplicación empaquetada. Aplica configuraciones para reducir la información verbosa que ya no es necesaria.]
# Uso: python3 config_embedded.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28
"""
Configuración para aplicación empaquetada
Autor: Eugenio de Frutos
Fecha: 2025-06-29
"""

import os
import sys


class EmbeddedConfig:
    # Configuración general de Flask
    SECRET_KEY = "embedded_app_secret_key_2025"

    # Configuración de MongoDB - usar variables de entorno si están disponibles
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/catalogotablas")
    MONGODB_SETTINGS = {"connect": False}

    # Configuración de correo electrónico
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = (
        "EDF Catálogo de Tablas",
        os.getenv("MAIL_DEFAULT_SENDER_EMAIL", ""),
    )
    MAIL_DEBUG = False

    # Configuración de sesión
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False

    # Configuración de AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
    USE_S3 = os.getenv("USE_S3", "false").lower() in ["true", "1"]

    # Rutas de carpetas para aplicación empaquetada
    if getattr(sys, "frozen", False):
        # Aplicación empaquetada
        BASE_DIR = os.path.dirname(sys.executable)
        UPLOAD_FOLDER = os.path.join(
            os.path.expanduser("~"),
            "Documents",
            "EDF_CatalogoTablas",
            "imagenes_subidas",
        )
        SPREADSHEET_FOLDER = os.path.join(
            os.path.expanduser("~"), "Documents", "EDF_CatalogoTablas", "spreadsheets"
        )
    else:
        # Desarrollo
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        UPLOAD_FOLDER = os.path.join(
            BASE_DIR, "static/uploads"
        )  # Corregido: app/static/uploads
        SPREADSHEET_FOLDER = os.path.join(BASE_DIR, "../spreadsheets")

    # Crear directorios si no existen
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(SPREADSHEET_FOLDER, exist_ok=True)

    # Otros
    ENV = "production"
    DEBUG = False
