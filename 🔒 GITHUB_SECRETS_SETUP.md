# 🔐 Configuración de GitHub Secrets

Este archivo contiene las instrucciones para configurar los secrets necesarios en GitHub para que el workflow de CI/CD funcione correctamente.

## 📋 Secrets Requeridos

### 1. **BREVO_API_KEY**
- **Descripción:** API Key de Brevo para envío de emails
- **Valor:** `TU_API_KEY_DE_BREVO_AQUI`
- **Uso:** Envío de emails via API de Brevo

### 2. **BREVO_SMTP_USERNAME**
- **Descripción:** Usuario SMTP de Brevo
- **Valor:** `TU_USUARIO_SMTP_AQUI`
- **Uso:** Configuración SMTP de respaldo

### 3. **BREVO_SMTP_PASSWORD**
- **Descripción:** Contraseña SMTP de Brevo
- **Valor:** `TU_PASSWORD_SMTP_AQUI`
- **Uso:** Configuración SMTP de respaldo

### 4. **NOTIFICATION_EMAIL_1**
- **Descripción:** Email principal para notificaciones
- **Valor:** `tu-email-principal@ejemplo.com`
- **Uso:** Destinatario de emails del sistema

### 5. **NOTIFICATION_EMAIL_2**
- **Descripción:** Email secundario para notificaciones
- **Valor:** `tu-email-secundario@ejemplo.com`
- **Uso:** Destinatario secundario de emails del sistema

### 6. **MONGO_URI**
- **Descripción:** URI de conexión a MongoDB
- **Valor:** `mongodb://localhost:27017/edefrutos2025`
- **Uso:** Conexión a la base de datos

### 7. **SECRET_KEY**
- **Descripción:** Clave secreta para Flask
- **Valor:** `tu-clave-secreta-aqui`
- **Uso:** Sesiones y seguridad de Flask

## 🔧 Cómo Configurar los Secrets

### Opción 1: Via GitHub Web Interface

1. Ve a tu repositorio en GitHub
2. Haz clic en **Settings** (Configuración)
3. En el menú lateral, haz clic en **Secrets and variables** → **Actions**
4. Haz clic en **New repository secret**
5. Para cada secret:
   - **Name:** El nombre del secret (ej: `BREVO_API_KEY`)
   - **Value:** El valor correspondiente
6. Haz clic en **Add secret**

### Opción 2: Via GitHub CLI

```bash
# Instalar GitHub CLI si no lo tienes
# brew install gh

# Autenticarse
gh auth login

# Configurar cada secret (reemplaza con tus valores reales)
gh secret set BREVO_API_KEY --body "TU_API_KEY_DE_BREVO_AQUI"
gh secret set BREVO_SMTP_USERNAME --body "TU_USUARIO_SMTP_AQUI"
gh secret set BREVO_SMTP_PASSWORD --body "TU_PASSWORD_SMTP_AQUI"
gh secret set NOTIFICATION_EMAIL_1 --body "tu-email-principal@ejemplo.com"
gh secret set NOTIFICATION_EMAIL_2 --body "tu-email-secundario@ejemplo.com"
gh secret set MONGO_URI --body "mongodb://localhost:27017/edefrutos2025"
gh secret set SECRET_KEY --body "tu-clave-secreta-aqui"
```

## ✅ Verificación

Después de configurar los secrets, puedes verificar que estén configurados correctamente:

1. Ve a **Settings** → **Secrets and variables** → **Actions**
2. Deberías ver todos los secrets listados
3. Los valores están ocultos por seguridad

## 🚀 Uso en Workflows

Los secrets se usan automáticamente en el workflow `.github/workflows/build_macos_app.yml`:

```yaml
- name: Configure secrets and environment
  run: |
    # Crear archivo de configuración con secrets
    cat > app_data/edefrutos2025_notifications_config.json << EOF
    {
      "brevo_api": {
        "api_key": "${{ secrets.BREVO_API_KEY }}"
      }
    }
    EOF
```

## 🔒 Seguridad

- Los secrets están encriptados y solo son visibles durante la ejecución del workflow
- Los valores nunca se muestran en los logs
- Los secrets son específicos del repositorio
- Solo los colaboradores con permisos pueden ver/editar los secrets

## 📝 Notas Importantes

- **Nunca** commits los valores reales de los secrets al repositorio
- Los secrets están protegidos por `.gitignore`
- El workflow crea los archivos de configuración dinámicamente durante el build
- Los archivos locales siguen funcionando para desarrollo local
