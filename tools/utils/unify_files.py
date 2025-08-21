#!/usr/bin/env python3
"""
Script para unificar/sincronizar contenido de archivos txt
Autor: EDF Developer - 2025
"""

import argparse
import os
import sys
from datetime import datetime
from typing import List


def read_file_lines(filename: str) -> List[str]:
    """Lee un archivo y retorna sus líneas."""
    try:
        with open(filename, encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {filename}")
        return []
    except Exception as e:
        print(f"❌ Error leyendo {filename}: {e}")
        return []


def write_file_lines(filename: str, lines: List[str]) -> bool:
    """Escribe líneas en un archivo."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for line in lines:
                _ = f.write(line + "\n")
        return True
    except Exception as e:
        print(f"❌ Error escribiendo {filename}: {e}")
        return False


def unify_append(file1: str, file2: str, output: str = None) -> bool:
    """
    Une dos archivos añadiendo el contenido del segundo al final del primero.
    """
    print(f"📝 Unificando {file1} + {file2}")

    lines1 = read_file_lines(file1)
    lines2 = read_file_lines(file2)

    if not lines1 and not lines2:
        print("❌ Ambos archivos están vacíos")
        return False

    # Combinar líneas
    combined_lines = lines1 + lines2

    # Determinar archivo de salida
    if output is None:
        output = f"{file1}_unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    # Escribir resultado
    if write_file_lines(output, combined_lines):
        print(f"✅ Archivo unificado guardado como: {output}")
        print(f"📊 Líneas del archivo 1: {len(lines1)}")
        print(f"📊 Líneas del archivo 2: {len(lines2)}")
        print(f"📊 Total de líneas: {len(combined_lines)}")
        return True
    return False


def unify_merge(file1: str, file2: str, output: str = None) -> bool:
    """
    Une dos archivos eliminando duplicados y ordenando.
    """
    print(f"🔄 Fusionando {file1} + {file2} (sin duplicados)")

    lines1 = read_file_lines(file1)
    lines2 = read_file_lines(file2)

    if not lines1 and not lines2:
        print("❌ Ambos archivos están vacíos")
        return False

    # Combinar y eliminar duplicados
    combined_set = set(lines1 + lines2)
    combined_lines = sorted(list(combined_set))

    # Determinar archivo de salida
    if output is None:
        output = f"{file1}_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    # Escribir resultado
    if write_file_lines(output, combined_lines):
        print(f"✅ Archivo fusionado guardado como: {output}")
        print(f"📊 Líneas únicas del archivo 1: {len(set(lines1))}")
        print(f"📊 Líneas únicas del archivo 2: {len(set(lines2))}")
        print(f"📊 Total de líneas únicas: {len(combined_lines)}")
        print(
            f"📊 Duplicados eliminados: {len(lines1) + len(lines2) - len(combined_lines)}"
        )
        return True
    return False


def sync_files(file1: str, file2: str, backup: bool = True) -> bool:
    """
    Sincroniza dos archivos, haciendo que ambos tengan el mismo contenido.
    """
    print(f"🔄 Sincronizando {file1} ↔ {file2}")

    lines1 = read_file_lines(file1)
    lines2 = read_file_lines(file2)

    if not lines1 and not lines2:
        print("❌ Ambos archivos están vacíos")
        return False

    # Crear backup si se solicita
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup1 = f"{file1}.backup_{timestamp}"
        backup2 = f"{file2}.backup_{timestamp}"

        if write_file_lines(backup1, lines1):
            print(f"💾 Backup creado: {backup1}")
        if write_file_lines(backup2, lines2):
            print(f"💾 Backup creado: {backup2}")

    # Combinar contenido único
    combined_set = set(lines1 + lines2)
    combined_lines = sorted(list(combined_set))

    # Sincronizar ambos archivos
    success1 = write_file_lines(file1, combined_lines)
    success2 = write_file_lines(file2, combined_lines)

    if success1 and success2:
        print(f"✅ Archivos sincronizados exitosamente")
        print(f"📊 Contenido único en ambos archivos: {len(combined_lines)} líneas")
        return True
    else:
        print("❌ Error al sincronizar archivos")
        return False


def compare_files(file1: str, file2: str) -> bool:
    """
    Compara dos archivos y muestra las diferencias.
    """
    print(f"🔍 Comparando {file1} vs {file2}")

    lines1 = set(read_file_lines(file1))
    lines2 = set(read_file_lines(file2))

    only_in_1 = lines1 - lines2
    only_in_2 = lines2 - lines1
    common = lines1 & lines2

    print(f"📊 Líneas únicas en {file1}: {len(only_in_1)}")
    print(f"📊 Líneas únicas en {file2}: {len(only_in_2)}")
    print(f"📊 Líneas comunes: {len(common)}")

    if only_in_1:
        print(f"\n📄 Solo en {file1}:")
        for line in sorted(only_in_1):
            print(f"  + {line}")

    if only_in_2:
        print(f"\n📄 Solo en {file2}:")
        for line in sorted(only_in_2):
            print(f"  + {line}")

    return len(only_in_1) == 0 and len(only_in_2) == 0


def main():
    parser = argparse.ArgumentParser(description="Unificar/sincronizar archivos txt")
    parser.add_argument("file1", help="Primer archivo")
    parser.add_argument("file2", help="Segundo archivo")
    parser.add_argument(
        "--mode",
        choices=["append", "merge", "sync", "compare"],
        default="merge",
        help="Modo de operación",
    )
    parser.add_argument("--output", help="Archivo de salida (solo para append/merge)")
    parser.add_argument(
        "--no-backup", action="store_true", help="No crear backups (solo para sync)"
    )

    args = parser.parse_args()

    # Verificar que los archivos existen
    if not os.path.exists(args.file1):
        print(f"❌ Error: {args.file1} no existe")
        return 1

    if not os.path.exists(args.file2):
        print(f"❌ Error: {args.file2} no existe")
        return 1

    # Ejecutar operación según el modo
    if args.mode == "append":
        success = unify_append(args.file1, args.file2, args.output)
    elif args.mode == "merge":
        success = unify_merge(args.file1, args.file2, args.output)
    elif args.mode == "sync":
        success = sync_files(args.file1, args.file2, not args.no_backup)
    elif args.mode == "compare":
        success = compare_files(args.file1, args.file2)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
