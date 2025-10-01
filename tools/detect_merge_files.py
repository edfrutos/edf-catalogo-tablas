#!/usr/bin/env python3
"""
Script para detectar archivos que han sido modificados por merges de Git.
Analiza el historial de Git para identificar archivos que fueron parcheados
durante operaciones de merge.
"""

import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime


def run_git_command(command):
    """Ejecuta un comando de Git y retorna la salida."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=os.getcwd()
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1


def get_merge_commits():
    """Obtiene la lista de commits de merge."""
    stdout, stderr, returncode = run_git_command("git log --merges --oneline")
    if returncode != 0:
        print(f"❌ Error al obtener commits de merge: {stderr}")
        return []

    merges = []
    for line in stdout.split("\n"):
        if line.strip():
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commit_hash, message = parts
                merges.append((commit_hash, message))

    return merges


def get_files_in_commit(commit_hash):
    """Obtiene los archivos modificados en un commit específico."""
    stdout, stderr, returncode = run_git_command(
        f"git show --name-only --pretty=format: {commit_hash}"
    )
    if returncode != 0:
        return []

    files = [f.strip() for f in stdout.split("\n") if f.strip()]
    return files


def get_commit_details(commit_hash):
    """Obtiene detalles de un commit específico."""
    stdout, stderr, returncode = run_git_command(f"git show --stat {commit_hash}")
    if returncode != 0:
        return None

    return stdout


def analyze_merge_files():
    """Analiza archivos modificados por merges."""
    print("🔍 Analizando archivos modificados por merges de Git...")
    print("=" * 60)

    # Obtener commits de merge
    merges = get_merge_commits()
    if not merges:
        print("❌ No se encontraron commits de merge")
        return

    print(f"📋 Encontrados {len(merges)} commits de merge:")
    print()

    # Diccionario para rastrear archivos por merge
    merge_files = defaultdict(list)
    all_modified_files = set()

    for i, (commit_hash, message) in enumerate(merges, 1):
        print(f"{i}. {commit_hash[:8]} - {message}")

        # Obtener archivos modificados en este merge
        files = get_files_in_commit(commit_hash)
        if files:
            merge_files[commit_hash] = files
            all_modified_files.update(files)
            print(f"   📁 Archivos modificados: {len(files)}")
        else:
            print("   📁 Sin archivos modificados")
        print()

    # Mostrar resumen de archivos
    print("📊 RESUMEN DE ARCHIVOS MODIFICADOS POR MERGES:")
    print("=" * 60)

    if all_modified_files:
        print(f"📈 Total de archivos únicos modificados: {len(all_modified_files)}")
        print()

        # Agrupar por tipo de archivo
        file_types = defaultdict(list)
        for file_path in sorted(all_modified_files):
            ext = os.path.splitext(file_path)[1].lower()
            if ext:
                file_types[ext].append(file_path)
            else:
                file_types["sin_extension"].append(file_path)

        print("📁 Archivos por tipo:")
        for ext, files in sorted(file_types.items()):
            print(f"   {ext or 'sin_extension'}: {len(files)} archivos")
        print()

        # Mostrar archivos más modificados
        file_count = defaultdict(int)
        for files in merge_files.values():
            for file_path in files:
                file_count[file_path] += 1

        print("🔄 Archivos más frecuentemente modificados:")
        sorted_files = sorted(file_count.items(), key=lambda x: x[1], reverse=True)
        for file_path, count in sorted_files[:10]:
            print(f"   {file_path} ({count} veces)")
        print()

        # Mostrar detalles por merge
        print("🔍 DETALLES POR MERGE:")
        print("=" * 60)

        for commit_hash, message in merges:
            if commit_hash in merge_files:
                print(f"\n📝 {commit_hash[:8]} - {message}")
                files = merge_files[commit_hash]
                for file_path in sorted(files):
                    print(f"   • {file_path}")

    else:
        print("✅ No se encontraron archivos modificados por merges")


def check_current_conflicts():
    """Verifica si hay conflictos de merge actuales."""
    print("🔍 Verificando conflictos de merge actuales...")
    print("=" * 60)

    stdout, stderr, returncode = run_git_command("git status --porcelain")
    if returncode != 0:
        print(f"❌ Error al verificar estado: {stderr}")
        return

    conflict_files = []
    for line in stdout.split("\n"):
        if line.strip():
            status = line[:2]
            file_path = line[3:]
            if "U" in status or "A" in status or "D" in status:
                conflict_files.append((status, file_path))

    if conflict_files:
        print("⚠️  Archivos con conflictos de merge detectados:")
        for status, file_path in conflict_files:
            print(f"   {status} {file_path}")
    else:
        print("✅ No hay conflictos de merge actuales")


def main():
    """Función principal."""
    print("🔍 DETECTOR DE ARCHIVOS PARCHEADOS POR MERGES DE GIT")
    print("=" * 60)
    print(f"📅 Análisis realizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Verificar que estamos en un repositorio Git
    stdout, stderr, returncode = run_git_command("git rev-parse --git-dir")
    if returncode != 0:
        print("❌ Error: No se detectó un repositorio Git en el directorio actual")
        sys.exit(1)

    # Verificar conflictos actuales
    check_current_conflicts()
    print()

    # Analizar archivos de merges
    analyze_merge_files()

    print("\n" + "=" * 60)
    print("✅ Análisis completado")


if __name__ == "__main__":
    main()
