# 🔄 Guía de Recuperación de Archivos Sensibles

Esta guía te explica cómo recuperar archivos sensibles en diferentes situaciones.

## 📋 Archivos Sensibles del Proyecto

### **Archivos locales (desarrollo):**
- `app_data/edefrutos2025_notifications_config.json` - Configuración de notificaciones
- `.env` - Variables de entorno
- `setup_github_secrets_manual.sh` - Script de configuración de secrets

### **Archivos en GitHub:**
- **GitHub Secrets** - Claves encriptadas en GitHub
- **Archivos de ejemplo** - Con placeholders

## 🔄 Opciones de Recuperación

### **1. 🐍 Script Automático (Recomendado)**

Si perdiste los archivos locales, ejecuta:

```bash
# Recrear todos los archivos sensibles
python3 tools/recreate_sensitive_files.py
```

Este script recreará:
- ✅ `app_data/edefrutos2025_notifications_config.json`
- ✅ `.env`
- ✅ `setup_github_secrets_manual.sh`

### **2. 🔐 Recuperar GitHub Secrets**

Si necesitas reconfigurar los secrets en GitHub:

#### **Opción A: Script automático**
```bash
# Ejecutar el script de configuración
./setup_github_secrets_manual.sh
```

#### **Opción B: Manual via GitHub Web**
1. Ve a: https://github.com/edfrutos/edf_catalogotablas/settings/secrets/actions
2. Haz clic en "New repository secret"
3. Configura cada secret:

| Secret | Valor |
|--------|-------|
| `BREVO_API_KEY` | `TU_API_KEY_DE_BREVO_AQUI` |
| `BREVO_SMTP_USERNAME` | `TU_USUARIO_SMTP_AQUI` |
| `BREVO_SMTP_PASSWORD` | `TU_PASSWORD_SMTP_AQUI` |
| `NOTIFICATION_EMAIL_1` | `tu-email-principal@ejemplo.com` |
| `NOTIFICATION_EMAIL_2` | `tu-email-secundario@ejemplo.com` |
| `MONGO_URI` | `mongodb://localhost:27017/edefrutos2025` |
| `SECRET_KEY` | `edefrutos2025-secret-key-[timestamp]` |

#### **Opción C: GitHub CLI**
```bash
# Configurar cada secret individualmente
gh secret set BREVO_API_KEY --body "TU_API_KEY_DE_BREVO_AQUI"
gh secret set BREVO_SMTP_USERNAME --body "TU_USUARIO_SMTP_AQUI"
gh secret set BREVO_SMTP_PASSWORD --body "TU_PASSWORD_SMTP_AQUI"
gh secret set NOTIFICATION_EMAIL_1 --body "tu-email-principal@ejemplo.com"
gh secret set NOTIFICATION_EMAIL_2 --body "tu-email-secundario@ejemplo.com"
gh secret set MONGO_URI --body "mongodb://localhost:27017/edefrutos2025"
gh secret set SECRET_KEY --body "edefrutos2025-secret-key-$(date +%s)"
```

### **3. 📁 Recuperar archivos específicos**

#### **Recuperar solo configuración de notificaciones:**
```bash
# Crear directorio si no existe
mkdir -p app_data

# Crear archivo de configuración
cat > app_data/edefrutos2025_notifications_config.json << 'EOF'
{
  "enabled": true,
  "smtp": {
    "server": "smtp-relay.brevo.com",
    "port": 587,
    "username": "TU_USUARIO_SMTP_AQUI",
    "password": "TU_PASSWORD_SMTP_AQUI",
    "use_tls": true
  },
  "brevo_api": {
    "api_key": "TU_API_KEY_DE_BREVO_AQUI",
    "sender_name": "Administrador",
    "sender_email": "no-reply@edefrutos2025.xyz"
  },
  "use_api": true,
  "recipients": [
    "tu-email-principal@ejemplo.com",
    "tu-email-secundario@ejemplo.com"
  ],
  "thresholds": {
    "cpu": 80,
    "memory": 90,
    "disk": 85,
    "error_rate": 5
  },
  "cooldown_minutes": 60,
  "last_alerts": {}
}
EOF
```

#### **Recuperar solo archivo .env:**
```bash
cat > .env << 'EOF'
# Variables de entorno para EDF Catálogo de Tablas

# MongoDB
MONGO_URI=mongodb://localhost:27017/edefrutos2025

# Flask
SECRET_KEY=edefrutos2025-secret-key-local

# Brevo API
BREVO_API_KEY=TU_API_KEY_DE_BREVO_AQUI
BREVO_SMTP_USERNAME=TU_USUARIO_SMTP_AQUI
BREVO_SMTP_PASSWORD=TU_PASSWORD_SMTP_AQUI

# Emails de notificación
NOTIFICATION_EMAIL_1=tu-email-principal@ejemplo.com
NOTIFICATION_EMAIL_2=tu-email-secundario@ejemplo.com
EOF
```

## 🚨 Situaciones Específicas

### **Si cambias de máquina:**
1. Clona el repositorio
2. Ejecuta: `python3 tools/recreate_sensitive_files.py`
3. Configura GitHub Secrets si es necesario

### **Si GitHub Secrets se corrompen:**
1. Ve a GitHub Settings → Secrets
2. Elimina los secrets corruptos
3. Ejecuta: `./setup_github_secrets_manual.sh`

### **Si pierdes acceso a GitHub:**
1. Contacta con el administrador del repositorio
2. Solicita acceso de nuevo
3. Reconfigura los secrets

### **Si necesitas cambiar las claves:**
1. Actualiza las claves en Brevo
2. Actualiza los archivos locales
3. Actualiza los GitHub Secrets

## ✅ Verificación

Después de recuperar los archivos, verifica que todo funciona:

```bash
# Verificar archivos locales
ls -la app_data/edefrutos2025_notifications_config.json
ls -la .env
ls -la setup_github_secrets_manual.sh

# Verificar GitHub Secrets
gh secret list

# Probar la aplicación
python3 run_server.py
```

## 🔒 Seguridad

- **Nunca** commits archivos con claves reales
- Los archivos recreados están en `.gitignore`
- Los GitHub Secrets están encriptados
- Cambia las claves regularmente

## 📞 Soporte

Si tienes problemas:
1. Revisa esta guía
2. Ejecuta el script de recreación
3. Verifica los logs de la aplicación
4. Contacta con el administrador

---

**Última actualización:** 2025-08-27  
**Versión:** 1.0
