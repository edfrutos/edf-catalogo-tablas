# Script: test_clean_old_logs_range.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_clean_old_logs_range.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

"""
Test de limpieza de logs por días y por rango de fecha/hora.

Este test verifica que la clase LogCleaner elimina correctamente los archivos de log
según dos criterios:
- Por retención en días (parámetro retention_days)
- Por rango de fecha y hora (parámetros start_datetime y end_datetime)

Ejecución:
    pytest -v tests/scripts/test_clean_old_logs_range.py

El test crea archivos temporales con diferentes fechas de modificación y verifica
que solo los archivos correctos sean eliminados según el criterio aplicado.

Requiere: pytest
"""
import os
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from scripts.maintenance.clean_old_logs import LogCleaner

def create_test_log(dir_path, name, mtime):
    file_path = dir_path / name
    with open(file_path, 'w') as f:
        f.write('log')
    os.utime(file_path, (mtime, mtime))
    return file_path

@pytest.fixture
def temp_log_dir(tmp_path):
    # Crea un directorio temporal para logs
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)

def test_clean_logs_by_datetime_range(temp_log_dir):
    # Crea 3 archivos con diferentes mtimes
    now = datetime.now()
    old = now - timedelta(days=10)
    mid = now - timedelta(days=5)
    recent = now - timedelta(days=1)

    files = [
        create_test_log(temp_log_dir, 'old.log', old.timestamp()),
        create_test_log(temp_log_dir, 'mid.log', mid.timestamp()),
        create_test_log(temp_log_dir, 'recent.log', recent.timestamp()),
    ]

    # Elimina solo los archivos entre 7 y 3 días atrás
    start_dt = now - timedelta(days=7)
    end_dt = now - timedelta(days=3)
    cleaner = LogCleaner(
        log_dir=temp_log_dir,
        retention_days=None,
        dry_run=False,
        start_datetime=start_dt,
        end_datetime=end_dt
    )
    cleaner.clean_old_logs()

    # Solo mid.log debe ser eliminado
    assert not (temp_log_dir / 'mid.log').exists()
    assert (temp_log_dir / 'old.log').exists()
    assert (temp_log_dir / 'recent.log').exists()


def test_clean_logs_by_days(temp_log_dir):
    now = datetime.now()
    old = now - timedelta(days=10)
    recent = now - timedelta(days=1)
    create_test_log(temp_log_dir, 'old.log', old.timestamp())
    create_test_log(temp_log_dir, 'recent.log', recent.timestamp())

    cleaner = LogCleaner(
        log_dir=temp_log_dir,
        retention_days=7,
        dry_run=False
    )
    cleaner.clean_old_logs()
    # old.log debe eliminarse, recent.log no
    assert not (temp_log_dir / 'old.log').exists()
    assert (temp_log_dir / 'recent.log').exists()
