# 🔧 Solución: Evitar la Página de Mantenimiento

## 🚨 Problema Identificado

Al intentar acceder a `http://localhost:3000` o `http://localhost:3456`, aparecía una página de mantenimiento del sistema "Catálogo Tablas" en lugar de la interfaz de Gemini CLI.

## ✅ Solución Implementada

### 1. **Cambio de Puerto**
- **Puerto original problemático**: 3000, 3456
- **Puerto nuevo funcional**: **8765**
- **Comando actualizado**: `PORT=8765 node gemini-server-fixed.js`

### 2. **Configuración Anti-Caché**
Se añadieron headers específicos para evitar conflictos de caché:

```javascript
// Middleware para evitar el caché
app.use((req, res, next) => {
    res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.header('Pragma', 'no-cache');
    res.header('Expires', '0');
    res.header('X-Powered-By', 'Gemini-CLI-Server');
    next();
});
```

### 3. **Rutas Específicas**
Se crearon rutas más específicas para evitar conflictos:

```javascript
// Ruta específica para Gemini
app.get("/gemini", (req, res) => {
    res.sendFile(path.join(__dirname, "gemini-web-interface.html"));
});

// Ruta de salud del servidor
app.get("/health", (req, res) => {
    res.json({ 
        status: "OK", 
        service: "Gemini CLI Web Interface",
        timestamp: new Date().toISOString()
    });
});

// Redirección desde la raíz
app.get("/", (req, res) => {
    res.redirect("/gemini");
});
```

## 🎯 URLs Funcionales

### ✅ **URLs que Funcionan Correctamente**

1. **Interfaz Principal**:
   ```
   http://localhost:8765
   http://localhost:8765/gemini
   ```

2. **Verificación de Estado**:
   ```
   http://localhost:8765/health
   ```

3. **API Endpoint**:
   ```
   POST http://localhost:8765/api/gemini
   ```

## 🛠️ Comandos de Gestión Actualizados

### Iniciar Servidor
```bash
# Opción 1: Puerto específico
PORT=8765 node gemini-server-fixed.js

# Opción 2: En segundo plano
PORT=8765 node gemini-server-fixed.js &

# Opción 3: Con npm (actualizar package.json)
npm start
```

### Verificar Estado
```bash
# Verificar que el servidor esté ejecutándose
curl http://localhost:8765/health

# Verificar puertos ocupados
lsof -i :8765

# Ver procesos de Node.js
ps aux | grep "node gemini-server"
```

### Detener Servidor
```bash
# Si está en primer plano
Ctrl+C

# Si está en segundo plano
pkill -f "node gemini-server-fixed.js"

# Por PID específico
kill [PID_NUMBER]
```

## 🔍 Diagnóstico de Problemas

### Problema: Puerto Ocupado
```bash
# Verificar qué está usando el puerto
lsof -i :8765

# Cambiar a puerto alternativo
PORT=9876 node gemini-server-fixed.js
```

### Problema: Caché del Navegador
```bash
# Limpiar caché de Chrome (macOS)
rm -rf ~/Library/Caches/Google/Chrome/Default/Cache/*

# Abrir en modo incógnito
open -a "Google Chrome" --args --incognito http://localhost:8765
```

### Problema: Conflicto con Otros Servicios
```bash
# Verificar servicios en puertos comunes
lsof -i :3000  # Flask/React dev servers
lsof -i :8080  # Tomcat/Jenkins
lsof -i :5000  # Flask default

# Usar puerto único para Gemini
PORT=8765 node gemini-server-fixed.js
```

## 📋 Checklist de Verificación

### ✅ **Antes de Iniciar el Servidor**

- [ ] Verificar que el puerto 8765 esté libre
- [ ] Confirmar que `gemini-cli.js` funciona en terminal
- [ ] Verificar que la API Key de Gemini esté configurada
- [ ] Comprobar que Node.js y npm estén instalados

### ✅ **Después de Iniciar el Servidor**

- [ ] Verificar respuesta en `http://localhost:8765/health`
- [ ] Confirmar que la interfaz carga en `http://localhost:8765`
- [ ] Probar una consulta simple
- [ ] Verificar que las acciones rápidas funcionan

## 🚀 Configuración Recomendada para Producción

### Script de Inicio Automático

Crear `start-gemini-server.sh`:

```bash
#!/bin/bash

# Configurar variables de entorno
export GEMINI_API_KEY="tu_api_key_aquí"
export PORT=8765

# Verificar dependencias
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado"
    exit 1
fi

if ! command -v gemini &> /dev/null; then
    echo "❌ Comando 'gemini' no está disponible"
    exit 1
fi

# Detener servidor anterior si existe
pkill -f "node gemini-server-fixed.js" 2>/dev/null

# Iniciar servidor
echo "🚀 Iniciando Gemini CLI Web Interface..."
node gemini-server-fixed.js

echo "✅ Servidor iniciado en http://localhost:$PORT"
```

### Hacer el Script Ejecutable
```bash
chmod +x start-gemini-server.sh
./start-gemini-server.sh
```

## 📊 Comparación: Antes vs Después

| Aspecto | ❌ Antes (Problemático) | ✅ Después (Solucionado) |
|---------|-------------------------|---------------------------|
| **Puerto** | 3000/3456 (conflicto) | 8765 (libre) |
| **Caché** | Problemas de caché | Headers anti-caché |
| **Rutas** | Conflicto con otros servicios | Rutas específicas |
| **Diagnóstico** | Sin herramientas | Endpoint `/health` |
| **Acceso** | Página de mantenimiento | Interfaz Gemini correcta |

## 🎯 Resultado Final

### ✅ **Estado Actual**
- **Servidor funcionando**: Puerto 8765
- **Interfaz accesible**: `http://localhost:8765`
- **Sin conflictos**: Página de mantenimiento evitada
- **Funcionalidad completa**: Todas las características operativas

### 🔗 **Enlaces Rápidos**
- **Interfaz Web**: http://localhost:8765
- **Estado del Servidor**: http://localhost:8765/health
- **Documentación**: `GUIA_INTERFAZ_WEB_GEMINI.md`
- **Tutorial CLI**: `GEMINI_CLI_TUTORIAL.md`

---

## 💡 Consejos Adicionales

1. **Usar siempre el puerto 8765** para evitar conflictos
2. **Verificar el estado** con `/health` antes de usar
3. **Limpiar caché** si hay problemas de visualización
4. **Usar modo incógnito** para pruebas sin caché
5. **Mantener actualizada** la API Key de Gemini

---

*Problema resuelto exitosamente - Junio 2024*
