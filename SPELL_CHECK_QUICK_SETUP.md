# Configuración Rápida del Correcto Ortográfico

## ✅ Configuración Completada

Los siguientes archivos han sido creados:
- `.vscode/settings.json` - Configuración de VS Code
- `cspell.json` - Configuración de cspell
- `pycharm_spell_check_config.json` - Configuración de PyCharm
- `pyproject.toml` - Actualizado con palabras básicas

## 🚀 Próximos Pasos

### 1. Instalar Extensiones de VS Code
```bash
# En VS Code, instalar:
# - Code Spell Checker (cspell)
# - Spell Right
```

### 2. Instalar cspell Globalmente
```bash
npm install -g cspell
```

### 3. Verificar Configuración
```bash
# Verificar ortografía con cspell
cspell "**/*.{md,txt,html}"

# Verificar archivo específico
python tools/quick_spell_check.py README.md
```

## 📋 Palabras Configuradas

Se han agregado automáticamente:
- **Términos del proyecto**: edefrutos, catalogotablas, edf, xyz
- **Términos técnicos**: api, http, ssl, json, mongodb, aws, s3
- **Módulos Python**: flask, pymongo, werkzeug, jinja2, boto3
- **Herramientas**: pytest, black, flake8, gunicorn

## 🎯 Uso

El corrector ortográfico ahora:
- ✅ Ignora archivos de código (.py, .js)
- ✅ Verifica documentación (.md, .txt, .html)
- ✅ Reconoce términos técnicos y del proyecto
- ✅ Funciona en español e inglés

---
*Configuración rápida completada - EDF Catalogotablas 2025*
