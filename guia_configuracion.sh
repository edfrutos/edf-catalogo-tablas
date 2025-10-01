#!/bin/bash

# GUÍA PARA OBTENER LOS VALORES REALES DE CONFIGURACIÓN
# EDF Catálogo de Tablas

echo "🔍 GUÍA PARA OBTENER VALORES DE CONFIGURACIÓN"
echo "=============================================="
echo

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📋 VALORES QUE NECESITAS OBTENER:${NC}"
echo

echo -e "${BLUE}1. MONGO_URI:${NC}"
echo "   🌐 Fuente: MongoDB Atlas o servidor MongoDB externo"
echo "   📝 Formato: mongodb+srv://usuario:password@cluster.mongodb.net/database"
echo "   🔗 Donde obtenerlo: https://cloud.mongodb.com → Connect → Application"
echo

echo -e "${BLUE}2. BREVO_API_KEY:${NC}"
echo "   🌐 Fuente: Panel de Brevo (Sendinblue)"
echo "   📝 Formato: xkeysib-xxxxxxxxxxxxxxxxx"
echo "   🔗 Donde obtenerlo: https://app.brevo.com → SMTP & API → API Keys"
echo

echo -e "${BLUE}3. BREVO_SMTP_USERNAME:${NC}"
echo "   🌐 Fuente: Panel de Brevo"
echo "   📝 Formato: tu-email@dominio.com"
echo "   🔗 Donde obtenerlo: https://app.brevo.com → SMTP & API → SMTP"
echo

echo -e "${BLUE}4. BREVO_SMTP_PASSWORD:${NC}"
echo "   🌐 Fuente: Panel de Brevo"
echo "   📝 Formato: Contraseña SMTP generada"
echo "   🔗 Donde obtenerlo: https://app.brevo.com → SMTP & API → Generate SMTP Key"
echo

echo -e "${RED}⚠️  CONFIGURACIÓN TEMPORAL ACTUAL:${NC}"
echo "   • La aplicación puede funcionar en modo desarrollo local"
echo "   • MongoDB: usando base local (mongodb://localhost:27017/edefrutos2025_dev)"
echo "   • Emails: deshabilitados (valores temporales)"
echo

echo -e "${GREEN}✅ CUANDO OBTENGAS LOS VALORES REALES:${NC}"
echo "   1. Ejecuta: ./actualizar_secrets.sh"
echo "   2. O edita manualmente el archivo .env"
echo "   3. Reinicia la aplicación"
echo

echo -e "${YELLOW}💡 PARA DESARROLLO LOCAL INMEDIATO:${NC}"
echo "   • Instala MongoDB localmente:"
echo "     sudo apt install mongodb"
echo "   • O usa Docker:"
echo "     docker run -d -p 27017:27017 --name mongo mongo:latest"
echo

echo -e "${BLUE}🚀 COMANDOS ÚTILES:${NC}"
echo "   • Verificar configuración: ./verificar_env_simple.sh"
echo "   • Actualizar valores: ./actualizar_secrets.sh"
echo "   • Iniciar aplicación: python run_server.py"
echo