# 🔍 Scripts de Verificación de Ortografía

Este directorio contiene scripts para detectar y gestionar palabras desconocidas en el proyecto.

## 📋 Scripts Disponibles

### 1. `detect_unknown_words.py` - Detector Completo

**Descripción**: Escanea todo el proyecto y añade automáticamente palabras desconocidas a `pyproject.toml`

**Uso**:

```bash
# Detectar y añadir automáticamente
python tools/detect_unknown_words.py

# Solo detectar sin añadir
python tools/detect_unknown_words.py --no-auto-add
```

**Características**:

- Escanea archivos `.py`, `.md`, `.html`, `.js`, `.css`, `.txt`
- Filtra palabras comunes en inglés y español
- Añade automáticamente palabras relevantes del proyecto
- Ignora directorios como `venv`, `__pycache__`, `.git`

### 2. `quick_spell_check.py` - Verificación Rápida

**Descripción**: Verifica palabras desconocidas en archivos específicos sin añadirlas

**Uso**:

```bash
# Verificar archivo específico
python tools/quick_spell_check.py main_app.py

# Verificar directorio específico
python tools/quick_spell_check.py app/routes/

# Verificar todo el proyecto
python tools/quick_spell_check.py
```

**Características**:

- Verificación rápida sin modificar configuración
- Muestra palabras desconocidas por archivo
- Útil para revisar antes de añadir palabras

### 3. `add_words_to_config.py` - Añadir Palabras Específicas

**Descripción**: Añade palabras específicas a la configuración de cSpell

**Uso**:

```bash
# Añadir palabras específicas
python tools/add_words_to_config.py Flask MongoDB Python

# Añadir palabras en español
python tools/add_words_to_config.py catálogo tabla usuario
```

**Características**:

- Añade palabras específicas sin escanear el proyecto
- Evita duplicados automáticamente
- Útil para añadir términos técnicos específicos

## 🔧 Configuración

### Archivo de Configuración

Las palabras se almacenan en `pyproject.toml` en la sección `[tool.cspell]`:

```toml
[tool.cspell]
words = [
    "catalogodetablas",
    "edefrutos",
    "Flask",
    "MongoDB",
    # ... más palabras
]
```

### Dependencias Requeridas

```bash
pip install toml
```

## 📝 Flujo de Trabajo Recomendado

### 1. Verificación Inicial

```bash
# Verificar palabras desconocidas sin añadirlas
python tools/quick_spell_check.py main_app.py
```

### 2. Añadir Palabras Relevantes

```bash
# Añadir palabras específicas que sabes que son correctas
python tools/add_words_to_config.py palabra1 palabra2 palabra3
```

### 3. Detección Automática (Opcional)

```bash
# Detectar y añadir automáticamente palabras del proyecto
python tools/detect_unknown_words.py
```

### 4. Verificación Final

```bash
# Verificar que no quedan palabras desconocidas importantes
python tools/quick_spell_check.py
```

## ⚠️ Consideraciones

### Palabras que se Ignoran Automáticamente

- Palabras muy cortas (< 3 caracteres) o muy largas (> 30 caracteres)
- Palabras comunes en inglés y español
- Nombres de archivos y rutas
- Caracteres especiales de idiomas no latinos

### Palabras que se Añaden Automáticamente

- Términos que empiezan con: `catalog`, `tabla`, `user`, `admin`, `app`, `data`
- Términos que terminan con: `tion`, `cion`, `ment`, `mento`, `able`, `ible`
- Términos técnicos específicos: `pip`, `flask`, `mongodb`, `python`, etc.

## 🎯 Beneficios

1. **Reducción de Falsos Positivos**: Solo se marcan como errores palabras realmente desconocidas
2. **Configuración Centralizada**: Todas las palabras en un solo archivo
3. **Automatización**: Detección automática de términos del proyecto
4. **Flexibilidad**: Múltiples formas de añadir palabras según las necesidades

## 🔄 Mantenimiento

### Actualización Periódica

Se recomienda ejecutar el detector completo periódicamente:

```bash
python tools/detect_unknown_words.py
```

### Limpieza de Configuración

Si la lista de palabras se vuelve muy larga, puedes:

1. Revisar y eliminar palabras obsoletas manualmente en `pyproject.toml`
2. Usar el script de detección para añadir solo palabras relevantes

## 📊 Estadísticas

- **Palabras conocidas actuales**: ~22,000+ palabras
- **Archivos escaneados**: Todos los archivos de código y documentación
- **Idiomas soportados**: Español, inglés y términos técnicos