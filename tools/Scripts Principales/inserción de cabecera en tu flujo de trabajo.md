¡Genial! Aquí tienes **cómo integrar la plantilla y el script de inserción de cabecera en tu flujo de trabajo** para que siempre tengas tus scripts bien documentados y mantengas la calidad del proyecto:

---

## **1. Al crear un nuevo script**

- __Copia la plantilla__ de `tools/plantilla_cabecera_script.py` y pégala en tu nuevo archivo.
- Rellena los campos de la cabecera antes de empezar a programar.

**Ejemplo:**

```bash
cp tools/plantilla_cabecera_script.py tools/nuevo_script.py
# Edita tools/nuevo_script.py y personaliza la cabecera
```

---

## **2. Al revisar o añadir scripts existentes**

- **Ejecuta el script automático** para asegurarte de que todos los scripts tienen cabecera:

```bash
python3 tools/insertar_cabecera.py ruta/al/script1.py ruta/al/script2.py ...
```

- Puedes usar un comando para aplicarlo a todos los scripts Python de un directorio:

```bash
In this corrected version, I've added a top-level heading (`# Integración de la plantilla y el script de inserción de cabecera`) at the beginning of the document to comply with the requirement.
```

O en subdirectorios:

```bash
find . -name '*.py' -exec python3 tools/insertar_cabecera.py {} +
```

---

## **3. En tu flujo de trabajo habitual**

- **Antes de hacer commit**, ejecuta el script en los archivos nuevos o modificados para asegurarte de que todos tienen cabecera.
- **Incluye este paso en tu checklist de revisión de código** (code review).

---

## **4. Automatización avanzada (opcional)**

- **Pre-commit hook:**  
Puedes añadir un hook de git para que se ejecute automáticamente antes de cada commit.

1. Crea el archivo `.git/hooks/pre-commit` con:

```bash
#!/bin/bash
find tools -name '*.py' -exec python3 tools/insertar_cabecera.py {} +
```

2. Hazlo ejecutable:

```bash
chmod +x .git/hooks/pre-commit
```

Así, cada vez que hagas `git commit`, se revisarán las cabeceras automáticamente.

---

## **5. Buenas prácticas**

- **No ignores la cabecera aunque el script sea pequeño o de prueba.**
- **Si un script cambia de función, actualiza la cabecera.**
- **Comparte este estándar con tu equipo.**

---

¿Quieres que te prepare el hook de pre-commit, un script para aplicar la cabecera a todos los scripts de tu proyecto, o necesitas ayuda para integrarlo en otro flujo (CI/CD, etc.)?
