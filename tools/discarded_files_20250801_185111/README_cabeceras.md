# Estandarización de Cabeceras en Scripts Python

## ¿Por qué es importante?
Mantener una cabecera estándar en todos los scripts Python del proyecto facilita la comprensión, el mantenimiento y la colaboración en el equipo. Así, cualquier persona puede saber rápidamente qué hace un script, cómo se usa y quién lo creó.

---

## 1. Plantilla de cabecera
Utiliza siempre la plantilla de `tools/plantilla_cabecera_script.py` al crear un nuevo script. Rellena los campos antes de empezar a programar.

**Ejemplo de cabecera:**
```python
# Script: NOMBRE_DEL_SCRIPT.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 NOMBRE_DEL_SCRIPT.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - [Fecha]
```

---

## 2. Automatización con scripts y hook

### a) Script para aplicar cabeceras a todo el proyecto

Ejecuta desde la raíz del proyecto:
```bash
python3 tools/aplicar_cabecera_todos.py
```
Esto revisará todos los scripts `.py` (excepto los de venv, .git y site-packages) y añadirá la cabecera estándar si falta.

### b) Hook de pre-commit

El hook `.git/hooks/pre-commit` aplica automáticamente la cabecera a todos los scripts Python antes de cada commit. Así, nunca se te olvidará documentar un script.

---

## 3. Buenas prácticas
- **No ignores la cabecera aunque el script sea pequeño o de prueba.**
- **Si un script cambia de función, actualiza la cabecera.**
- **Comparte este estándar con tu equipo.**
- **Incluye este paso en tu checklist de revisión de código.**

---

## 4. Ejemplo de flujo recomendado
1. Crea un nuevo script copiando la plantilla:
   ```bash
   cp tools/plantilla_cabecera_script.py tools/mi_nuevo_script.py
   # Edita y personaliza la cabecera
   ```
2. Antes de hacer commit, asegúrate de que todos los scripts tienen cabecera:
   ```bash
   python3 tools/aplicar_cabecera_todos.py
   # o simplemente haz git commit y el hook lo hará por ti
   ```

---

## 5. ¿Dudas o mejoras?
Si tienes sugerencias para mejorar la plantilla o el flujo, compártelas con el equipo. 