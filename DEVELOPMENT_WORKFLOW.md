# 🔧 Workflow de Desarrollo - Verificaciones Previas al Push

## 📋 Resumen

Este proyecto incluye un sistema completo de verificaciones previas al push para evitar errores en GitHub Actions y mantener la calidad del código.

## 🚀 Comandos Disponibles

### 1. **Verificación Manual**
```bash
./verify_build_files.sh
```
Ejecuta todas las verificaciones de archivos críticos y sintaxis.

### 2. **Push Seguro (Recomendado)**
```bash
./safe_push.sh
```
Ejecuta verificaciones automáticas y hace push de forma segura.

### 3. **Push Normal (Con Hook Automático)**
```bash
git push origin main
```
El hook de pre-push se ejecuta automáticamente y verifica todo antes del push.

## 🔍 Verificaciones Incluidas

### **Archivos Críticos**
- ✅ `EDF_CatalogoDeTablas.spec`
- ✅ `requirements_python310.txt`
- ✅ `run_server.py`
- ✅ `app/__init__.py`
- ✅ `app/routes/admin_routes.py`
- ✅ `app/routes/catalogs_routes.py`

### **Directorios Críticos**
- ✅ `app/`
- ✅ `app/routes/`
- ✅ `app/templates/`
- ✅ `app/static/`
- ✅ `tools/`

### **Archivos de Configuración**
- ✅ `.github/workflows/mac_build.yml`
- ✅ `pyproject.toml`
- ✅ `pyrightconfig.json`
- ✅ `cspell.json`

### **Verificaciones de Sintaxis**
- ✅ Sintaxis de `requirements_python310.txt`
- ✅ Sintaxis de archivos Python (muestra de 10 archivos)
- ✅ Detección de archivos sensibles
- ✅ Verificación de mensajes de commit

## 🛡️ Protecciones de Seguridad

### **Hook de Pre-Push**
- Se ejecuta automáticamente antes de cada `git push`
- Verifica archivos críticos
- Detecta archivos sensibles
- Valida mensajes de commit

### **Detección de Archivos Sensibles**
El sistema detecta y bloquea archivos con extensiones sensibles:
- `.log`, `.key`, `.pem`, `.p12`, `.pfx`
- `.env`, `.secret`, `.password`, `.credential`

## 📊 Flujo de Trabajo Recomendado

### **Para Desarrollo Diario:**
1. Hacer cambios en el código
2. Ejecutar `./verify_build_files.sh` para verificar
3. Hacer commit con mensaje descriptivo
4. Ejecutar `./safe_push.sh` para push seguro

### **Para Cambios Críticos:**
1. Hacer cambios
2. Ejecutar verificaciones manuales
3. Probar localmente
4. Hacer commit
5. Usar `./safe_push.sh`

## ⚠️ Casos de Error

### **Si las Verificaciones Fallan:**
```
❌ Verificaciones fallaron
🚫 Push cancelado
```
**Solución:** Corregir los errores antes de hacer push.

### **Si se Detectan Archivos Sensibles:**
```
❌ ARCHIVOS SENSIBLES DETECTADOS
🚫 Push cancelado
```
**Solución:** Remover archivos sensibles del commit.

### **Si el Mensaje de Commit es Muy Corto:**
```
⚠️ Mensaje de commit muy corto
💡 Considera usar un mensaje más descriptivo
```
**Solución:** Usar mensajes descriptivos como:
- `🔧 FIX: Corregir error en login`
- `✨ FEAT: Añadir nueva funcionalidad`
- `📝 DOC: Actualizar documentación`

## 🔧 Configuración

### **Habilitar/Deshabilitar Hook de Pre-Push:**
```bash
# Habilitar
chmod +x .git/hooks/pre-push

# Deshabilitar
chmod -x .git/hooks/pre-push
```

### **Personalizar Verificaciones:**
Editar `verify_build_files.sh` para añadir o quitar verificaciones.

## 📈 Beneficios

1. **🚫 Previene Errores:** Detecta problemas antes del push
2. **⚡ Ahorra Tiempo:** Evita builds fallidos en GitHub Actions
3. **🛡️ Mejora Seguridad:** Detecta archivos sensibles
4. **📊 Mantiene Calidad:** Verifica sintaxis y estructura
5. **🔄 Automatización:** Proceso automático y confiable

## 🆘 Solución de Problemas

### **Error: "Script de verificación no encontrado"**
```bash
# Asegurar que el script existe y es ejecutable
ls -la verify_build_files.sh
chmod +x verify_build_files.sh
```

### **Error: "Hook no se ejecuta"**
```bash
# Verificar que el hook existe y es ejecutable
ls -la .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

### **Error: "Permisos denegados"**
```bash
# Dar permisos de ejecución a todos los scripts
chmod +x *.sh
chmod +x .git/hooks/pre-push
```

## 📝 Notas Importantes

- Los scripts funcionan en macOS y Linux
- Requieren bash para funcionar correctamente
- El hook de pre-push es específico para este repositorio
- Las verificaciones se pueden personalizar según necesidades
- El sistema es compatible con el workflow de GitHub Actions

---

**🎯 Objetivo:** Mantener un flujo de desarrollo seguro, eficiente y libre de errores.
