# Configuración del Correcto Ortográfico

## VS Code

1. Instalar extensiones:
   - Code Spell Checker (cspell)
   - Spell Right

2. La configuración ya está creada en `.vscode/settings.json`

## PyCharm

1. Ir a Settings > Editor > Natural Languages > Spelling
2. Configurar según `pycharm_spell_check_config.json`

## cspell (Code Spell Checker)

1. Instalar globalmente:
   ```bash
   npm install -g cspell
   ```

2. La configuración ya está creada en `cspell.json`

3. Ejecutar verificación:
   ```bash
   cspell "**/*.{py,md,html,js,css,txt}"
   ```

## Archivos de configuración creados:

- `.vscode/settings.json` - Configuración de VS Code
- `cspell.json` - Configuración de cspell
- `pycharm_spell_check_config.json` - Configuración de PyCharm
- `config/dictionaries/` - Diccionarios temáticos

## Comandos útiles:

```bash
# Verificar ortografía con cspell
cspell "**/*.{py,md,html,js,css,txt}"

# Ejecutar flujo completo de gestión
python tools/complete_spell_check_workflow.py

# Verificar archivo específico
python tools/quick_spell_check.py archivo.txt
```

## Notas importantes:

- Los archivos de código (.py, .js) tienen verificación de ortografía deshabilitada
- Los archivos de documentación (.md, .txt) tienen verificación habilitada
- Los términos técnicos y palabras del proyecto están en la lista blanca
- Se ignoran automáticamente directorios como venv, __pycache__, etc.
