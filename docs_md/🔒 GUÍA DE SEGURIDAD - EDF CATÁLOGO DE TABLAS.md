# 🔒 GUÍA DE SEGURIDAD - EDF CATÁLOGO DE TABLAS

## 🛡️ **INFORMACIÓN SENSIBLE Y BUENAS PRÁCTICAS**

### **Variables de Entorno Sensibles**

#### **Archivos que contienen información sensible:**
- `.env` - Variables de entorno locales
- `app_data/edefrutos2025_notifications_config.json` - Configuración de notificaciones
- `tools/db_utils/credentials.json` - Credenciales de Google Drive
- `tools/db_utils/token.json` - Tokens de Google Drive
- `tools/db_utils/token.pickle` - Tokens serializados de Google Drive

#### **Variables sensibles identificadas:**
- `MONGO_URI` - Conexión a MongoDB Atlas
- `SECRET_KEY` - Clave secreta de Flask
- `BREVO_API_KEY` - API key de Brevo (notificaciones)
- `BREVO_SMTP_USERNAME` - Usuario SMTP
- `BREVO_SMTP_PASSWORD` - Contraseña SMTP

### **Archivos Excluidos del Control de Versiones**

#### **Archivos en .gitignore:**
```
.env
*.pyc
__pycache__/
*.log
logs/
backups/
instance/
flask_session/
tools/db_utils/credentials.json
tools/db_utils/token.json
tools/db_utils/token.pickle
```

## **ARCHIVOS CREADOS**

### **✅ Archivos Físicos Creados:**

1. **`fix_spec_ci_cd.py`** - Script de corrección de .spec
2. **`fix_sensitive_info.py`** - Script de corrección de información sensible  
3. **`setup_cicd.sh`** - Script de configuración CI/CD
4. **`SECURITY.md`** - Documentación de seguridad

### **🎯 Próximos Pasos:**

Ahora puedes ejecutar estos scripts:

```bash
# 1. Corregir archivo .spec
python3 fix_spec_ci_cd.py

# 2. Corregir información sensible
python3 fix_sensitive_info.py

# 3. Configurar CI/CD
chmod +x setup_cicd.sh
./setup_cicd.sh
```

¿Te gustaría que ejecute alguno de estos scripts ahora o necesitas que modifique algún archivo antes?

### **Corrección Automática de Información Sensible**

#### **Script implementado:**
```bash
python3 fix_sensitive_info.py
```

#### **Patrones detectados y corregidos:**
- MongoDB URIs: `mongodb+srv://...` → `[MONGO_URI_OCULTO]`
- Contraseñas en logs: `password: xxx` → `password: [OCULTO]`
- Tokens de API: `token: xxx` → `token: [OCULTO]`
- Credenciales: `credentials: xxx` → `credentials: [OCULTO]`

### **Configuración de CI/CD Segura**

#### **Secrets configurados en GitHub:**
- `MONGO_URI` - URI de conexión a MongoDB
- `SECRET_KEY` - Clave secreta de la aplicación
- `BREVO_API_KEY` - API key para notificaciones
- `BREVO_SMTP_USERNAME` - Usuario SMTP
- `BREVO_SMTP_PASSWORD` - Contraseña SMTP
- `NOTIFICATION_EMAIL_1` - Email de notificación 1
- `NOTIFICATION_EMAIL_2` - Email de notificación 2

#### **Workflow seguro:**
```yaml
- name: Configure secrets and environment
  run: |
    # Crear .env con secrets
    cat > .env << EOF
    MONGO_URI=${{ secrets.MONGO_URI }}
    SECRET_KEY=${{ secrets.SECRET_KEY }}
    BREVO_API_KEY=${{ secrets.BREVO_API_KEY }}
    EOF
```

### **Verificación de Seguridad**

#### **Comandos de verificación:**
```bash
# Verificar archivos sensibles
find . -name "*.env" -o -name "credentials.json" -o -name "token.json"

# Verificar información sensible en logs
grep -r "mongodb+srv://" logs/ || echo "No se encontró información sensible"

# Verificar archivos excluidos
git status --ignored
```

### **Recomendaciones de Seguridad**

#### **Para desarrollo local:**
1. Nunca committear archivos `.env`
2. Usar variables de entorno locales
3. Rotar credenciales regularmente
4. Revisar logs antes de compartir

#### **Para CI/CD:**
1. Usar secrets de GitHub
2. No exponer credenciales en logs
3. Limpiar archivos temporales
4. Verificar permisos de archivos

#### **Para producción:**
1. Usar credenciales específicas de producción
2. Implementar rotación automática de credenciales
3. Monitorear accesos a recursos sensibles
4. Mantener backups seguros

### **Contacto de Seguridad**

Si encuentras una vulnerabilidad de seguridad:
1. **NO** crear un issue público
2. Contactar directamente al administrador
3. Proporcionar detalles específicos del problema
4. Esperar confirmación antes de divulgar

---

** Esta guía debe ser revisada regularmente y actualizada según sea necesario.**