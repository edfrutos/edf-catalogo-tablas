#!/usr/bin/env python3

def test_backup_validation():
    """Prueba la validación de archivos de backup para eliminación"""
    print("=== PRUEBA DE VALIDACIÓN DE ELIMINACIÓN DE BACKUPS ===\n")
    
    # Extensiones válidas (las mismas que en get_backup_files)
    valid_extensions = [
        ".bak", ".backup", ".zip", ".tar", ".gz", ".json.gz",
        ".sql", ".dump", ".old", ".back", ".tmp", ".swp",
        "~", ".csv", ".json"
    ]
    
    # Archivos de prueba
    test_files = [
        # Archivos válidos
        "catalogs_20250801_1426.csv",
        "catalogs_20250801_1426.json", 
        "backup_20250804_200054.json.gz",
        "mongodb_backup_20250626_131830.gz",
        "spreadsheets_20250801_2042.csv",
        "users_20250802_1852.json",
        
        # Archivos inválidos
        "document.txt",
        "image.png",
        "script.py",
        "config.ini",
        "readme.md",
        
        # Archivos con caracteres peligrosos
        "../backup.json",
        "backup/../file.json",
        "backup\\file.json",
        "backup..json"
    ]
    
    print("Archivos de prueba:")
    for filename in test_files:
        # Verificar extensión válida
        has_valid_extension = any(filename.endswith(ext) for ext in valid_extensions)
        
        # Verificar caracteres peligrosos
        has_dangerous_chars = ".." in filename or "/" in filename or "\\" in filename
        
        # Resultado final
        is_valid = has_valid_extension and not has_dangerous_chars
        
        status = "✅ VÁLIDO" if is_valid else "❌ INVÁLIDO"
        reason = ""
        
        if not has_valid_extension:
            reason = " - extensión no permitida"
        elif has_dangerous_chars:
            reason = " - nombre inseguro"
        
        print(f"  {status} {filename}{reason}")
    
    print(f"\nResumen:")
    print(f"  Extensiones válidas: {len(valid_extensions)}")
    print(f"  Archivos de prueba: {len(test_files)}")
    
    # Contar archivos válidos e inválidos
    valid_count = 0
    invalid_count = 0
    
    for filename in test_files:
        has_valid_extension = any(filename.endswith(ext) for ext in valid_extensions)
        has_dangerous_chars = ".." in filename or "/" in filename or "\\" in filename
        is_valid = has_valid_extension and not has_dangerous_chars
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
    
    print(f"  Archivos válidos: {valid_count}")
    print(f"  Archivos inválidos: {invalid_count}")

if __name__ == "__main__":
    test_backup_validation() 