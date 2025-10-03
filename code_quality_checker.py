
#!/usr/bin/env python3
"""
Script completo para verificar y corregir la calidad del código Python
Incluye limpieza de espacios, verificación de sintaxis, imports, y más
"""

import os
import sys
import ast
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse


class CodeQualityChecker:
    """Clase principal para verificar y corregir la calidad del código"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.issues = []
        self.fixes_applied = []
        
    def check_file_exists(self) -> bool:
        """Verifica que el archivo existe"""
        if not self.file_path.exists():
            self.issues.append(f"❌ El archivo {self.file_path} no existe")
            return False
        return True
    
    def fix_whitespace_issues(self) -> bool:
        """Corrige problemas de espacios en blanco"""
        try:
            print("🔧 Corrigiendo espacios en blanco...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Eliminar espacios al final de líneas
            content = re.sub(r'[ \t]+, '', content, flags=re.MULTILINE)
            
            # Corregir líneas vacías con espacios
            content = re.sub(r'^[ \t]+, '', content, flags=re.MULTILINE)
            
            # Eliminar múltiples líneas vacías consecutivas (máximo 2)
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Asegurar que el archivo termine con una sola línea vacía
            content = content.rstrip() + '\n'
            
            if content != original_content:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixes_applied.append("✅ Espacios en blanco corregidos")
                return True
            else:
                print("ℹ️ No se encontraron problemas de espacios en blanco")
                return True
                
        except Exception as e:
            self.issues.append(f"❌ Error al corregir espacios: {str(e)}")
            return False
    
    def check_syntax(self) -> bool:
        """Verifica la sintaxis del archivo Python"""
        try:
            print("🔍 Verificando sintaxis...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                ast.parse(content)
                print("✅ Sintaxis correcta")
                return True
            except SyntaxError as e:
                self.issues.append(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
                return False
                
        except Exception as e:
            self.issues.append(f"❌ Error al verificar sintaxis: {str(e)}")
            return False
    
    def check_imports(self) -> bool:
        """Verifica y organiza los imports"""
        try:
            print("🔍 Verificando imports...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar imports
            import_lines = []
            other_lines = []
            in_docstring = False
            docstring_quotes = None
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Detectar docstrings
                if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                    docstring_quotes = stripped[:3]
                    if stripped.count(docstring_quotes) == 1:  # Docstring de múltiples líneas
                        in_docstring = True
                    other_lines.append(line)
                elif in_docstring and docstring_quotes in stripped:
                    in_docstring = False
                    other_lines.append(line)
                elif in_docstring:
                    other_lines.append(line)
                elif stripped.startswith('import ') or stripped.startswith('from '):
                    import_lines.append((i, line, stripped))
                else:
                    other_lines.append(line)
            
            # Verificar imports duplicados
            seen_imports = set()
            duplicate_imports = []
            
            for line_num, full_line, import_stmt in import_lines:
                if import_stmt in seen_imports:
                    duplicate_imports.append(f"Línea {line_num + 1}: {import_stmt}")
                seen_imports.add(import_stmt)
            
            if duplicate_imports:
                self.issues.append(f"❌ Imports duplicados encontrados:\n" + "\n".join(duplicate_imports))
            else:
                print("✅ No se encontraron imports duplicados")
            
            # Verificar imports no utilizados (básico)
            unused_imports = self.check_unused_imports(content, import_lines)
            if unused_imports:
                self.issues.append(f"⚠️ Posibles imports no utilizados:\n" + "\n".join(unused_imports))
            
            return len(duplicate_imports) == 0
            
        except Exception as e:
            self.issues.append(f"❌ Error al verificar imports: {str(e)}")
            return False
    
    def check_unused_imports(self, content: str, import_lines: List[Tuple]) -> List[str]:
        """Verifica imports que posiblemente no se usan"""
        unused = []
        
        for line_num, full_line, import_stmt in import_lines:
            if import_stmt.startswith('import '):
                # import module
                module = import_stmt.replace('import ', '').split(' as ')[0].strip()
                if module not in content.replace(import_stmt, ''):
                    unused.append(f"Línea {line_num + 1}: {import_stmt}")
            elif import_stmt.startswith('from '):
                # from module import something
                parts = import_stmt.split(' import ')
                if len(parts) == 2:
                    imported_items = [item.strip() for item in parts[1].split(',')]
                    for item in imported_items:
                        item_name = item.split(' as ')[-1].strip()
                        if item_name not in content.replace(import_stmt, ''):
                            unused.append(f"Línea {line_num + 1}: {item_name} de {import_stmt}")
        
        return unused
    
    def check_shebang(self) -> bool:
        """Verifica y añade shebang si es necesario"""
        try:
            print("🔍 Verificando shebang...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            first_line = lines[0] if lines else ""
            
            if not first_line.startswith('#!'):
                print("🔧 Añadiendo shebang...")
                new_content = "#!/usr/bin/env python3\n" + content
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.fixes_applied.append("✅ Shebang añadido")
                return True
            else:
                print("✅ Shebang presente")
                return True
                
        except Exception as e:
            self.issues.append(f"❌ Error al verificar shebang: {str(e)}")
            return False
    
    def check_encoding(self) -> bool:
        """Verifica la declaración de encoding"""
        try:
            print("🔍 Verificando encoding...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Buscar encoding en las primeras 2 líneas
            encoding_found = False
            for i in range(min(2, len(lines))):
                if 'coding:' in lines[i] or 'coding=' in lines[i]:
                    encoding_found = True
                    break
            
            if not encoding_found:
                print("ℹ️ No se encontró declaración de encoding (no es obligatorio en Python 3)")
            else:
                print("✅ Declaración de encoding encontrada")
            
            return True
            
        except Exception as e:
            self.issues.append(f"❌ Error al verificar encoding: {str(e)}")
            return False
    
    def check_line_length(self, max_length: int = 88) -> bool:
        """Verifica la longitud de las líneas"""
        try:
            print(f"🔍 Verificando longitud de líneas (máx: {max_length})...")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            long_lines = []
            for i, line in enumerate(lines, 1):
                if len(line.rstrip()) > max_length:
                    long_lines.append(f"Línea {i}: {len(line.rstrip())} caracteres")
            
            if long_lines:
                self.issues.append(f"⚠️ Líneas demasiado largas:\n" + "\n".join(long_lines[:10]))
                if len(long_lines) > 10:
                    self.issues.append(f"... y {len(long_lines) - 10} más")
                return False
            else:
                print("✅ Longitud de líneas correcta")
                return True
                
        except Exception as e:
            self.issues.append(f"❌ Error al verificar longitud de líneas: {str(e)}")
            return False
    
    def run_external_linters(self) -> Dict[str, bool]:
        """Ejecuta linters externos si están disponibles"""
        results = {}
        
        # Flake8
        try:
            print("🔍 Ejecutando flake8...")
            result = subprocess.run(
                ['flake8', str(self.file_path), '--max-line-length=88'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("✅ Flake8: Sin errores")
                results['flake8'] = True
            else:
                self.issues.append(f"⚠️ Flake8 encontró problemas:\n{result.stdout}")
                results['flake8'] = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("ℹ️ Flake8 no disponible")
            results['flake8'] = None
        except Exception as e:
            print(f"ℹ️ Error ejecutando flake8: {e}")
            results['flake8'] = None
        
        # Black (verificar formato)
        try:
            print("🔍 Verificando formato con black...")
            result = subprocess.run(
                ['black', '--check', '--line-length=88', str(self.file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("✅ Black: Formato correcto")
                results['black'] = True
            else:
                print("⚠️ Black sugiere cambios de formato")
                results['black'] = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("ℹ️ Black no disponible")
            results['black'] = None
        except Exception as e:
            print(f"ℹ️ Error ejecutando black: {e}")
            results['black'] = None
        
        return results
    
    def apply_black_formatting(self) -> bool:
        """Aplica formato automático con black"""
        try:
            print("🔧 Aplicando formato con black...")
            result = subprocess.run(
                ['black', '--line-length=88', str(self.file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self.fixes_applied.append("✅ Formato aplicado con black")
                return True
            else:
                self.issues.append(f"❌ Error al aplicar black: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("ℹ️ Black no disponible para aplicar formato")
            return False
    
    def check_permissions(self) -> bool:
        """Verifica y corrige permisos de ejecución"""
        try:
            print("🔍 Verificando permisos...")
            
            if not os.access(self.file_path, os.X_OK):
                print("🔧 Añadiendo permisos de ejecución...")
                os.chmod(self.file_path, 0o755)
                self.fixes_applied.append("✅ Permisos de ejecución añadidos")
            else:
                print("✅ Permisos correctos")
            
            return True
            
        except Exception as e:
            self.issues.append(f"❌ Error al verificar permisos: {str(e)}")
            return False
    
    def generate_report(self) -> str:
        """Genera un reporte completo"""
        report = []
        report.append("=" * 60)
        report.append(f"REPORTE DE CALIDAD DE CÓDIGO: {self.file_path.name}")
        report.append("=" * 60)
        
        if self.fixes_applied:
            report.append("\n🔧 CORRECCIONES APLICADAS:")
            for fix in self.fixes_applied:
                report.append(f"  {fix}")
        
        if self.issues:
            report.append("\n⚠️ PROBLEMAS ENCONTRADOS:")
            for issue in self.issues:
                report.append(f"  {issue}")
        
        if not self.issues and not self.fixes_applied:
            report.append("\n✅ EL ARCHIVO ESTÁ EN PERFECTO ESTADO")
        elif not self.issues:
            report.append("\n✅ EL ARCHIVO TIENE CORRECCIONES PENDIENTES")
        else:
            report.append("\n⚠️ EL ARCHIVO TIENE PROBLEMAS QUE DEBEN SER RESUELTOS")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Verificador y corrector de calidad de código Python")
    parser.add_argument("file", help="Ruta al archivo Python a verificar")
    parser.add_argument("--apply-fixes", action="store_true", help="Aplicar correcciones automáticas")
    parser.add_argument("--max-line-length", type=int, default=88, help="Longitud máxima de línea (por defecto: 88)")
    
    args = parser.parse_args()
    
    checker = CodeQualityChecker(args.file)
    
    if not checker.check_file_exists():
        sys.exit(1)
    
    print(f"🚀 Iniciando verificación del archivo: {args.file}")
    print("-" * 60)
    
    # Ejecutar todas las verificaciones
    checks = [
        checker.check_shebang,
        checker.check_encoding,
        checker.fix_whitespace_issues,
        checker.check_syntax,
        checker.check_imports,
        lambda: checker.check_line_length(args.max_line_length),
        checker.check_permissions
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ Error en {check.__name__}: {str(e)}")
            all_passed = False
    
    # Ejecutar linters externos
    print("\n🔍 Ejecutando linters externos...")
    linter_results = checker.run_external_linters()
    
    # Aplicar correcciones automáticas si se solicita
    if args.apply_fixes:
        print("\n🔧 Aplicando correcciones automáticas...")
        if not checker.apply_black_formatting():
            all_passed = False
    
    # Generar reporte
    print("\n" + checker.generate_report())
    
    if all_passed:
        print("\n🎉 ¡Todas las verificaciones pasaron exitosamente!")
        sys.exit(0)
    else:
        print("\n⚠️ Algunas verificaciones fallaron o requieren atención")
        sys.exit(1)


if __name__ == "__main__":
    main()
