#!/usr/bin/env python3
"""
Script para comparar dos archivos requirements.txt y generar un reporte de diferencias
Muestra: paquetes faltantes, versiones diferentes, y paquetes únicos en cada archivo
"""

import re
import sys
from pathlib import Path
from typing import Dict, Optional, Set, Tuple


def parse_requirement_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parsea una línea de requirements.txt y retorna (nombre_paquete, versión)
    Soporta formatos: paquete==version, paquete>=version, paquete, etc.
    """
    line = line.strip()

    # Ignorar comentarios y líneas vacías
    if not line or line.startswith("#") or line.startswith("-"):
        return None, None

    # Remover comentarios inline
    if "#" in line:
        line = line.split("#")[0].strip()

    # Parsear diferentes formatos de versión
    patterns = [
        r"^([a-zA-Z0-9_-]+)\s*==\s*(.+)$",  # paquete==version
        r"^([a-zA-Z0-9_-]+)\s*>=\s*(.+)$",  # paquete>=version
        r"^([a-zA-Z0-9_-]+)\s*<=\s*(.+)$",  # paquete<=version
        r"^([a-zA-Z0-9_-]+)\s*~=\s*(.+)$",  # paquete~=version
        r"^([a-zA-Z0-9_-]+)\s*>\s*(.+)$",  # paquete>version
        r"^([a-zA-Z0-9_-]+)\s*<\s*(.+)$",  # paquete<version
        r"^([a-zA-Z0-9_-]+)\s*!=\s*(.+)$",  # paquete!=version
        r"^([a-zA-Z0-9_-]+)$",  # paquete (sin versión)
    ]

    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            groups = match.groups()
            package = groups[0].lower()
            version = groups[1] if len(groups) > 1 else "sin versión"
            return package, version

    return None, None


def parse_requirements_file(filepath: Path) -> Dict[str, str]:
    """Lee un archivo requirements.txt y retorna un dict {paquete: versión}"""
    requirements: Dict[str, str] = {}

    if not filepath.exists():
        print(f"⚠️  Archivo no encontrado: {filepath}")
        return requirements

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            package, version = parse_requirement_line(line)
            if package and version:
                requirements[package] = version

    return requirements


def compare_requirements(file1: Path, file2: Path, output_file: Path):
    """Compara dos archivos requirements y genera un reporte"""

    print(f"📋 Comparando archivos:")
    print(f"   Archivo 1: {file1.name}")
    print(f"   Archivo 2: {file2.name}")
    print()

    # Parsear ambos archivos
    req1 = parse_requirements_file(file1)
    req2 = parse_requirements_file(file2)

    # Obtener conjuntos de paquetes
    packages1 = set(req1.keys())
    packages2 = set(req2.keys())

    # Calcular diferencias
    only_in_1 = packages1 - packages2
    only_in_2 = packages2 - packages1
    common = packages1 & packages2

    # Paquetes con versiones diferentes
    different_versions = {
        pkg: (req1[pkg], req2[pkg]) for pkg in common if req1[pkg] != req2[pkg]
    }

    # Generar reporte
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("COMPARACIÓN DE ARCHIVOS REQUIREMENTS")
    report_lines.append("=" * 80)
    report_lines.append(f"Archivo 1: {file1.name}")
    report_lines.append(f"Archivo 2: {file2.name}")
    report_lines.append(f"Fecha: {Path(__file__).stat().st_mtime}")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Resumen
    report_lines.append("📊 RESUMEN:")
    report_lines.append(f"   • Total paquetes en {file1.name}: {len(packages1)}")
    report_lines.append(f"   • Total paquetes en {file2.name}: {len(packages2)}")
    report_lines.append(f"   • Paquetes comunes: {len(common)}")
    report_lines.append(f"   • Solo en {file1.name}: {len(only_in_1)}")
    report_lines.append(f"   • Solo en {file2.name}: {len(only_in_2)}")
    report_lines.append(f"   • Versiones diferentes: {len(different_versions)}")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("")

    # Paquetes solo en archivo 1
    if only_in_1:
        report_lines.append(
            f"🔴 PAQUETES SOLO EN {file1.name.upper()} ({len(only_in_1)}):"
        )
        report_lines.append("")
        for pkg in sorted(only_in_1):
            report_lines.append(f"   {pkg}=={req1[pkg]}")
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("")

    # Paquetes solo en archivo 2
    if only_in_2:
        report_lines.append(
            f"🟢 PAQUETES SOLO EN {file2.name.upper()} ({len(only_in_2)}):"
        )
        report_lines.append("")
        for pkg in sorted(only_in_2):
            report_lines.append(f"   {pkg}=={req2[pkg]}")
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("")

    # Versiones diferentes
    if different_versions:
        report_lines.append(
            f"⚠️  PAQUETES CON VERSIONES DIFERENTES ({len(different_versions)}):"
        )
        report_lines.append("")
        for pkg in sorted(different_versions.keys()):
            v1, v2 = different_versions[pkg]
            report_lines.append(f"   {pkg}:")
            report_lines.append(f"      {file1.name}: {v1}")
            report_lines.append(f"      {file2.name}: {v2}")
            report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("")

    # Paquetes comunes con misma versión
    same_version = {pkg for pkg in common if req1[pkg] == req2[pkg]}
    if same_version:
        report_lines.append(
            f"✅ PAQUETES COMUNES CON MISMA VERSIÓN ({len(same_version)}):"
        )
        report_lines.append("")
        for pkg in sorted(same_version):
            report_lines.append(f"   {pkg}=={req1[pkg]}")
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("")

    # Generar archivo con paquetes faltantes o diferentes
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("SUGERENCIAS PARA SINCRONIZAR")
    report_lines.append("=" * 80)
    report_lines.append("")

    if only_in_2 or different_versions:
        report_lines.append(
            f"Para actualizar {file1.name} con paquetes de {file2.name}:"
        )
        report_lines.append("")
        for pkg in sorted(only_in_2):
            report_lines.append(f"{pkg}=={req2[pkg]}")
        for pkg in sorted(different_versions.keys()):
            report_lines.append(f"{pkg}=={req2[pkg]}")

    # Escribir reporte
    report_text = "\n".join(report_lines)

    with open(output_file, mode="w", encoding="utf-8") as f:
        f.write(report_text)

    # Mostrar en consola
    print(report_text)
    print()
    print(f"✅ Reporte guardado en: {output_file}")

    return len(only_in_1), len(only_in_2), len(different_versions)


def main():
    """Función principal"""

    # Directorio del proyecto
    project_dir = Path(__file__).parent

    # Archivos por defecto
    default_file1 = project_dir / "requirements.txt"
    default_file2 = project_dir / "requirements_python310.txt"
    default_output = project_dir / "requirements_compare.txt"

    # Procesar argumentos de línea de comandos
    if len(sys.argv) >= 3:
        file1 = Path(sys.argv[1])
        file2 = Path(sys.argv[2])
        output = Path(sys.argv[3]) if len(sys.argv) >= 4 else default_output
    else:
        print("💡 Uso:")
        print(f"   python {Path(__file__).name} <archivo1> <archivo2> [archivo_salida]")
        print()
        print("📝 Usando archivos por defecto:")
        file1 = default_file1
        file2 = default_file2
        output = default_output

    # Verificar que los archivos existan
    if not file1.exists():
        print(f"❌ Error: {file1} no existe")
        return 1

    if not file2.exists():
        print(f"❌ Error: {file2} no existe")
        return 1

    # Comparar
    only1, only2, diff = compare_requirements(file1, file2, output)

    print()
    print("=" * 80)
    print("📈 ESTADÍSTICAS FINALES:")
    print(f"   • Paquetes únicos en archivo 1: {only1}")
    print(f"   • Paquetes únicos en archivo 2: {only2}")
    print(f"   • Versiones diferentes: {diff}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
