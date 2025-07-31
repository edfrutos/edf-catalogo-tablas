---
inclusion: always
priority: high
---

# Configuración de Idioma - Español de España

## 🇪🇸 Instrucciones de Idioma

- **Idioma principal**: Español de España (castellano peninsular)
- **Comentarios en código**: Siempre en español
- **Documentación**: Siempre en español
- **Mensajes de commit**: En español
- **Variables y funciones**: En inglés (estándar de programación)
- **Nombres de archivos**: En inglés o español según contexto

## 📝 Estilo de Comunicación

- **Formalidad**: Profesional pero cercano
- **Tuteo**: Usar "tú" en lugar de "usted"
- **Estructura**: Respuestas organizadas con encabezados y listas
- **Emojis**: Usar para mejorar legibilidad
- **Claridad**: Explicaciones directas y precisas

## 🔧 Configuraciones Técnicas

- **Encoding**: UTF-8
- **Locale**: es_ES.UTF-8
- **Formato de fecha**: DD/MM/YYYY
- **Separador decimal**: Coma (,)
- **Separador de miles**: Punto (.)
- **Zona horaria**: Europe/Madrid

## 💻 Comentarios en Código

### Python
```python
# Función para procesar datos de usuario
def procesar_datos_usuario(datos):
    """
    Procesa los datos del usuario y devuelve un diccionario limpio.
    
    Args:
        datos (dict): Datos sin procesar del usuario
        
    Returns:
        dict: Datos procesados y validados
        
    Raises:
        ValueError: Si los datos no son válidos
    """
    # Validar entrada de datos
    if not isinstance(datos, dict):
        raise ValueError("Los datos deben ser un diccionario")
    
    # Procesar y limpiar datos
    datos_limpios = {}
    # ... resto de la implementación
    
    return datos_limpios
```

### JavaScript
```javascript
// Función para validar formulario
function validarFormulario(datos) {
    /**
     * Valida los datos del formulario antes del envío
     * 
     * @param {Object} datos - Datos del formulario
     * @returns {boolean} - True si es válido, false en caso contrario
     */
    
    // Verificar que los datos existen
    if (!datos) {
        console.error('No se proporcionaron datos para validar');
        return false;
    }
    
    // Validar campos requeridos
    const camposRequeridos = ['nombre', 'email'];
    // ... resto de la validación
    
    return true;
}
```

### HTML
```html
<!-- Formulario de contacto -->
<form id="formulario-contacto" method="post">
    <!-- Campo de nombre -->
    <label for="nombre">Nombre completo:</label>
    <input type="text" id="nombre" name="nombre" required>
    
    <!-- Campo de email -->
    <label for="email">Correo electrónico:</label>
    <input type="email" id="email" name="email" required>
    
    <!-- Botón de envío -->
    <button type="submit">Enviar formulario</button>
</form>
```

## 📋 Mensajes de Commit

### Tipos de commit en español:
- `feat: añadir funcionalidad de login`
- `fix: corregir error en validación de formularios`
- `docs: actualizar documentación de la API`
- `style: mejorar formato del código`
- `refactor: reestructurar módulo de autenticación`
- `test: añadir pruebas unitarias para usuarios`
- `chore: actualizar dependencias del proyecto`

### Estructura del mensaje:
```
tipo: descripción breve en español

Descripción más detallada del cambio realizado,
explicando el qué y el por qué del cambio.

- Cambio específico 1
- Cambio específico 2
- Cambio específico 3
```

## 🗂️ Estructura de Archivos

### Nombres de archivos y carpetas:
- **Código fuente**: En inglés (`models.py`, `views.py`, `utils.js`)
- **Documentación**: En español (`README.md`, `INSTALACION.md`)
- **Configuración**: En inglés (`config.json`, `settings.py`)
- **Tests**: En inglés (`test_models.py`, `test_utils.js`)

## 🎯 Buenas Prácticas

- Mantener consistencia en el idioma dentro de cada archivo
- Usar terminología técnica estándar en inglés cuando sea apropiado
- Documentar APIs y funciones públicas en español
- Comentarios inline en español para explicar lógica compleja
- Variables de configuración en inglés, comentarios en español