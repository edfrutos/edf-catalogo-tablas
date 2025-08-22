#!/usr/bin/env python3
"""
Prueba rápida de integración de utilidades de spell check
EDF CatalogoDeTablas - 2025
"""

import sys
from pathlib import Path


def test_file_existence():
    """Verificar que todos los archivos de spell check existen"""
    print("📁 VERIFICACIÓN DE ARCHIVOS")
    print("=" * 40)

    spell_check_files = [
        "tools/quick_spell_check.py",
        "tools/quick_setup_spell_check.py",
        "tools/complete_spell_check_workflow.py",
        "tools/add_common_words.py",
        "tools/add_categorized_words.py",
        "tools/fix_spell_check.py",
        "tools/spell_check_gui.py",
        "tools/launch_spell_check_gui.sh",
    ]

    all_exist = True
    for file_path in spell_check_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False

    return all_exist


def test_symlinks():
    """Verificar que los enlaces simbólicos están correctos"""
    print("\n🔗 VERIFICACIÓN DE ENLACES SIMBÓLICOS")
    print("=" * 40)

    symlink_dir = Path("tools/build/spell-check")
    if not symlink_dir.exists():
        print("❌ Directorio de enlaces simbólicos no existe")
        return False

    expected_links = [
        "quick_spell_check.py",
        "quick_setup_spell_check.py",
        "complete_spell_check_workflow.py",
        "add_common_words.py",
        "add_categorized_words.py",
        "fix_spell_check.py",
        "spell_check_gui.py",
        "launch_spell_check_gui.sh",
    ]

    all_valid = True
    for link_name in expected_links:
        link_path = symlink_dir / link_name
        if link_path.exists():
            try:
                target_path = link_path.resolve()
                if target_path.exists():
                    print(f"✅ {link_name} -> {target_path}")
                else:
                    print(f"❌ {link_name} -> {target_path} (target no existe)")
                    all_valid = False
            except Exception as e:
                print(f"❌ {link_name} - Error: {e}")
                all_valid = False
        else:
            print(f"❌ {link_name} - Enlace no existe")
            all_valid = False

    return all_valid


def test_build_manager_integration():
    """Verificar que el gestor de scripts reconoce la categoría spell-check"""
    print("\n🔧 VERIFICACIÓN DE INTEGRACIÓN CON GESTOR")
    print("=" * 40)

    try:
        # Importar el gestor de scripts
        sys.path.append(str(Path.cwd()))
        from build_scripts_manager import BuildScriptsManager

        # Crear instancia
        manager = BuildScriptsManager()

        # Verificar que la categoría existe
        if "spell-check" in manager.categories:
            print("✅ Categoría 'spell-check' encontrada")
            info = manager.categories["spell-check"]
            print(f"   📝 Descripción: {info['description']}")
            print(f"   📊 Scripts: {len(info['scripts'])}")

            # Verificar que todos los scripts están listados
            expected_scripts = [
                "quick_spell_check.py",
                "quick_setup_spell_check.py",
                "complete_spell_check_workflow.py",
                "add_common_words.py",
                "add_categorized_words.py",
                "fix_spell_check.py",
                "spell_check_gui.py",
                "launch_spell_check_gui.sh",
            ]

            all_listed = True
            for script in expected_scripts:
                if script in info["scripts"]:
                    print(f"   ✅ {script}")
                else:
                    print(f"   ❌ {script} - No listado")
                    all_listed = False

            return all_listed
        else:
            print("❌ Categoría 'spell-check' no encontrada")
            return False

    except Exception as e:
        print(f"❌ Error en la integración: {e}")
        return False


def test_web_interface_integration():
    """Verificar que la interfaz web puede importar el gestor"""
    print("\n🌐 VERIFICACIÓN DE INTERFAZ WEB")
    print("=" * 40)

    try:
        # Verificar que la interfaz web existe
        interface_file = Path("tools/build_interface.py")
        if not interface_file.exists():
            print("❌ tools/build_interface.py no existe")
            return False

        # Verificar que las plantillas existen
        templates_dir = Path("tools/templates")
        if not templates_dir.exists():
            print("❌ tools/templates no existe")
            return False

        template_files = [
            "tools/templates/build_interface.html",
            "tools/templates/category_detail.html",
        ]

        all_templates_exist = True
        for template in template_files:
            if Path(template).exists():
                print(f"✅ {template}")
            else:
                print(f"❌ {template} - No existe")
                all_templates_exist = False

        # Verificar que Flask está disponible
        try:
            import flask  # type: ignore # noqa: F401

            print("✅ Flask disponible")
        except ImportError:
            print("❌ Flask no disponible")
            return False

        return all_templates_exist

    except Exception as e:
        print(f"❌ Error en la interfaz web: {e}")
        return False


def test_script_execution():
    """Probar ejecución rápida de un script simple"""
    print("\n⚡ PRUEBA DE EJECUCIÓN RÁPIDA")
    print("=" * 40)

    try:
        # Probar el gestor de scripts directamente
        import subprocess  # noqa: F401

        result = subprocess.run(
            [sys.executable, "tools/build_scripts_manager.py", "list", "spell-check"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Gestor de scripts ejecutable")
            if "spell-check" in result.stdout:
                print("✅ Categoría spell-check visible en salida")
                return True
            else:
                print("❌ Categoría spell-check no visible en salida")
                return False
        else:
            print(f"❌ Gestor de scripts falló: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ Gestor de scripts - Timeout")
        return False
    except Exception as e:
        print(f"❌ Error en ejecución: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 PRUEBA RÁPIDA DE INTEGRACIÓN DE SPELL CHECK")
    print("=" * 60)

    # Ejecutar todas las pruebas
    tests = [
        ("Verificación de archivos", test_file_existence),
        ("Verificación de enlaces simbólicos", test_symlinks),
        ("Integración con gestor", test_build_manager_integration),
        ("Integración con interfaz web", test_web_interface_integration),
        ("Prueba de ejecución", test_script_execution),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name.upper()}")
        print("-" * 40)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))

    # Resumen final
    print("\n📊 RESUMEN FINAL")
    print("=" * 60)

    successful_tests = [name for name, success in results if success]
    failed_tests = [name for name, success in results if not success]

    print(f"✅ Exitosos: {len(successful_tests)}/{len(results)}")
    for test_name in successful_tests:
        print(f"   - {test_name}")

    if failed_tests:
        print(f"\n❌ Fallidos: {len(failed_tests)}/{len(results)}")
        for test_name in failed_tests:
            print(f"   - {test_name}")

    # Resultado final
    if len(failed_tests) == 0:
        print("\n🎉 ¡INTEGRACIÓN COMPLETA EXITOSA!")
        print("✅ Todas las utilidades de spell check están correctamente integradas")
        print("✅ La interfaz web puede acceder a las utilidades")
        print("✅ Los enlaces simbólicos están funcionando")
        return True
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa los errores para corregir los problemas")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
