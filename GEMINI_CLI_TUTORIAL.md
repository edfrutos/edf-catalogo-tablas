# Tutorial Completo de Gemini CLI

## Índice
1. [Introducción](#introducción)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Uso Básico](#uso-básico)
4. [Casos de Uso Avanzados](#casos-de-uso-avanzados)
5. [Ejemplos Prácticos](#ejemplos-prácticos)
6. [Configuración Avanzada](#configuración-avanzada)
7. [Solución de Problemas](#solución-de-problemas)
8. [Mejores Prácticas](#mejores-prácticas)
9. [Integración con Otros Sistemas](#integración-con-otros-sistemas)
10. [Automatización y Scripts](#automatización-y-scripts)

---

## Introducción

Gemini CLI es una herramienta de línea de comandos que te permite interactuar con el modelo de inteligencia artificial Gemini de Google directamente desde tu terminal. Esta herramienta está diseñada para desarrolladores, escritores, investigadores y cualquier persona que necesite acceso rápido y eficiente a las capacidades de Gemini.

### ¿Qué puedes hacer con Gemini CLI?

- **Consultas rápidas**: Obtener respuestas inmediatas a preguntas técnicas o generales
- **Generación de código**: Crear snippets de código en cualquier lenguaje de programación
- **Análisis de texto**: Revisar, corregir y mejorar textos
- **Traducción**: Traducir contenido entre diferentes idiomas
- **Explicaciones técnicas**: Obtener explicaciones detalladas de conceptos complejos
- **Brainstorming**: Generar ideas y soluciones creativas
- **Documentación**: Crear documentación técnica y guías de usuario

---

## Instalación y Configuración

### Requisitos Previos

- **Node.js**: Versión 14 o superior
- **npm**: Incluido con Node.js
- **Cuenta de Google Cloud**: Para obtener la API Key de Gemini
- **Terminal**: Bash, Zsh, o cualquier terminal compatible

### Paso 1: Obtener la API Key de Gemini

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea un nuevo proyecto o selecciona uno existente
4. Genera una nueva API Key
5. Copia la API Key (la necesitarás para la configuración)

### Paso 2: Configurar la API Key

Tienes dos opciones para configurar tu API Key:

#### Opción A: Variable de Entorno (Recomendado)

```bash
# Agregar a tu archivo ~/.zshrc o ~/.bashrc
export GEMINI_API_KEY="tu_api_key_aquí"

# Recargar la configuración
source ~/.zshrc  # o source ~/.bashrc
```

#### Opción B: Archivo .env

Crea un archivo `.env` en el directorio del proyecto:

```bash
# Crear archivo .env
echo "GEMINI_API_KEY=tu_api_key_aquí" > .env
```

### Paso 3: Verificar la Instalación

```bash
# Verificar que el comando está disponible
which gemini

# Probar el comando
gemini "Hola, ¿funcionas correctamente?"
```

---

## Uso Básico

### Sintaxis General

```bash
gemini "tu pregunta o solicitud aquí"
```

### Ejemplos Básicos

```bash
# Pregunta simple
gemini "¿Qué es JavaScript?"

# Solicitud de código
gemini "Crea una función en Python que calcule el factorial de un número"

# Traducción
gemini "Traduce 'Hello World' al español, francés e italiano"

# Explicación técnica
gemini "Explica qué es Docker y para qué se usa"
```

### Tipos de Consultas Soportadas

#### 1. Preguntas Informativas
```bash
gemini "¿Cuáles son las diferencias entre React y Vue.js?"
gemini "Explica el concepto de machine learning"
gemini "¿Qué es la programación funcional?"
```

#### 2. Generación de Código
```bash
gemini "Crea una API REST en Express.js con endpoints CRUD"
gemini "Escribe un algoritmo de ordenamiento burbuja en Java"
gemini "Genera un componente React para un formulario de login"
```

#### 3. Análisis y Revisión
```bash
gemini "Revisa este código y sugiere mejoras: [tu código aquí]"
gemini "Analiza este texto y corrige errores gramaticales: [tu texto]"
gemini "Optimiza esta consulta SQL: SELECT * FROM users WHERE..."
```

#### 4. Creatividad y Brainstorming
```bash
gemini "Dame 10 ideas para nombres de una startup de tecnología"
gemini "Crea un plan de marketing para una app móvil"
gemini "Escribe un poema sobre la programación"
```

---

## Casos de Uso Avanzados

### Desarrollo de Software

#### Debugging y Solución de Problemas
```bash
# Analizar errores
gemini "Tengo este error en Python: 'IndexError: list index out of range'. ¿Cómo lo soluciono?"

# Optimización de código
gemini "¿Cómo puedo optimizar este algoritmo para que sea más eficiente? [código]"

# Patrones de diseño
gemini "Explica el patrón Singleton y muestra un ejemplo en TypeScript"
```

#### Documentación Automática
```bash
# Generar documentación
gemini "Crea documentación JSDoc para esta función: [tu función]"

# README para proyectos
gemini "Crea un README.md para un proyecto de API REST en Node.js"

# Comentarios de código
gemini "Agrega comentarios explicativos a este código: [tu código]"
```

### Análisis de Datos

```bash
# Consultas SQL complejas
gemini "Crea una consulta SQL que muestre las ventas por mes del último año"

# Análisis estadístico
gemini "Explica cómo interpretar estos resultados estadísticos: [datos]"

# Visualización de datos
gemini "Sugiere el mejor tipo de gráfico para mostrar la evolución temporal de ventas"
```

### DevOps y Administración de Sistemas

```bash
# Scripts de automatización
gemini "Crea un script bash para hacer backup automático de una base de datos MySQL"

# Configuración de servidores
gemini "¿Cómo configuro nginx como proxy reverso para una aplicación Node.js?"

# Docker y contenedores
gemini "Crea un Dockerfile para una aplicación Python Flask"
```

### Seguridad

```bash
# Análisis de vulnerabilidades
gemini "¿Qué vulnerabilidades de seguridad puede tener este código? [código]"

# Mejores prácticas
gemini "Dame una lista de mejores prácticas de seguridad para APIs REST"

# Configuración segura
gemini "¿Cómo configuro HTTPS en un servidor Apache?"
```

---

## Ejemplos Prácticos

### Ejemplo 1: Desarrollo de una API

```bash
# Paso 1: Planificación
gemini "Diseña la estructura de una API REST para un sistema de gestión de tareas"

# Paso 2: Implementación
gemini "Crea el código base para una API de tareas usando Express.js y MongoDB"

# Paso 3: Autenticación
gemini "Agrega autenticación JWT a la API de tareas"

# Paso 4: Testing
gemini "Crea tests unitarios para los endpoints de la API de tareas"

# Paso 5: Documentación
gemini "Genera documentación Swagger para la API de tareas"
```

### Ejemplo 2: Análisis de Rendimiento

```bash
# Análisis de código
gemini "Analiza el rendimiento de este algoritmo y sugiere optimizaciones: [código]"

# Métricas
gemini "¿Qué métricas debo monitorear en una aplicación web Node.js?"

# Herramientas
gemini "Recomienda herramientas para monitorear el rendimiento de una aplicación React"
```

### Ejemplo 3: Migración de Tecnologías

```bash
# Planificación
gemini "Crea un plan para migrar una aplicación de jQuery a React"

# Estrategia
gemini "¿Cuál es la mejor estrategia para migrar de MySQL a PostgreSQL?"

# Implementación
gemini "Convierte este código jQuery a React: [código jQuery]"
```

---

## Configuración Avanzada

### Personalización del Script

Puedes modificar el archivo `gemini-cli.js` para agregar funcionalidades adicionales:

#### Agregar Logging
```javascript
// Agregar al inicio del archivo
const fs = require('fs');
const path = require('path');

// Función para logging
function logQuery(query, response) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        query: query,
        response: response.substring(0, 100) + '...'
    };
    
    const logFile = path.join(__dirname, 'gemini-log.json');
    let logs = [];
    
    if (fs.existsSync(logFile)) {
        logs = JSON.parse(fs.readFileSync(logFile, 'utf8'));
    }
    
    logs.push(logEntry);
    fs.writeFileSync(logFile, JSON.stringify(logs, null, 2));
}
```

#### Configurar Diferentes Modelos
```javascript
// Modificar la configuración del modelo
const modelName = process.env.GEMINI_MODEL || "gemini-1.5-flash";
const model = genAI.getGenerativeModel({ model: modelName });
```

### Variables de Entorno Adicionales

```bash
# Configuraciones adicionales en ~/.zshrc o ~/.bashrc
export GEMINI_API_KEY="tu_api_key"
export GEMINI_MODEL="gemini-1.5-pro"  # Modelo a usar
export GEMINI_MAX_TOKENS="1000"       # Límite de tokens
export GEMINI_TEMPERATURE="0.7"       # Creatividad (0-1)
export GEMINI_LOG_ENABLED="true"      # Habilitar logging
```

### Alias Útiles

```bash
# Agregar a ~/.zshrc o ~/.bashrc
alias gcode='gemini "Genera código para:"'
alias gexplain='gemini "Explica detalladamente:"'
alias gfix='gemini "Corrige este código:"'
alias gtranslate='gemini "Traduce al español:"'
alias gdebug='gemini "Ayúdame a debuggear este error:"'
```

---

## Solución de Problemas

### Problemas Comunes

#### Error: "No se encontró GEMINI_API_KEY"

**Solución:**
```bash
# Verificar que la variable esté configurada
echo $GEMINI_API_KEY

# Si no está configurada, agregarla
export GEMINI_API_KEY="tu_api_key_aquí"

# O crear archivo .env
echo "GEMINI_API_KEY=tu_api_key_aquí" > .env
```

#### Error: "Command not found: gemini"

**Solución:**
```bash
# Verificar la instalación
which gemini

# Reinstalar si es necesario
sudo npm install -g .

# Verificar permisos
chmod +x /Users/edefrutos/gemini
```

#### Error de Permisos

**Solución:**
```bash
# Dar permisos de ejecución
chmod +x /usr/local/bin/gemini

# Verificar ownership
ls -la /usr/local/bin/gemini
```

#### Respuestas Lentas o Timeouts

**Solución:**
```bash
# Verificar conectividad
ping google.com

# Usar modelo más rápido
export GEMINI_MODEL="gemini-1.5-flash"

# Reducir longitud de consultas
gemini "Respuesta breve: ¿qué es React?"
```

### Debugging

#### Habilitar Modo Verbose
```javascript
// Agregar al script para debugging
console.log('API Key configurada:', !!apiKey);
console.log('Modelo usado:', model.model);
console.log('Prompt enviado:', prompt);
```

#### Verificar Logs
```bash
# Ver logs del sistema
tail -f ~/.npm/_logs/*debug*.log

# Ver logs de Node.js
node --trace-warnings gemini-cli.js "test"
```

---

## Mejores Prácticas

### Formulación de Consultas Efectivas

#### 1. Sé Específico
```bash
# ❌ Malo
gemini "Ayuda con código"

# ✅ Bueno
gemini "Crea una función en Python que valide direcciones de email usando regex"
```

#### 2. Proporciona Contexto
```bash
# ❌ Malo
gemini "¿Cómo optimizar esto?"

# ✅ Bueno
gemini "¿Cómo optimizar esta consulta SQL para una tabla con 1 millón de registros? SELECT * FROM users WHERE created_at > '2023-01-01'"
```

#### 3. Especifica el Formato de Respuesta
```bash
# Para código
gemini "Crea una función JavaScript que... (incluye comentarios y ejemplos de uso)"

# Para listas
gemini "Dame 5 mejores prácticas para... (formato: título y explicación breve)"

# Para explicaciones
gemini "Explica paso a paso cómo..."
```

### Gestión de API Key

#### Seguridad
```bash
# ❌ Nunca hagas esto
git add .env

# ✅ Agregar .env al .gitignore
echo ".env" >> .gitignore

# ✅ Usar variables de entorno del sistema
export GEMINI_API_KEY="tu_key"
```

#### Rotación de Keys
```bash
# Crear script para rotar keys
#!/bin/bash
OLD_KEY=$GEMINI_API_KEY
NEW_KEY="nueva_key_aquí"

# Actualizar variable de entorno
export GEMINI_API_KEY=$NEW_KEY

# Verificar que funciona
gemini "Test de nueva API key"
```

### Optimización de Uso

#### Consultas Eficientes
```bash
# Usar consultas específicas en lugar de generales
gemini "Muestra solo la sintaxis de un bucle for en Python"

# Agrupar consultas relacionadas
gemini "Explica React hooks: useState, useEffect y useContext con ejemplos"
```

#### Gestión de Respuestas Largas
```bash
# Solicitar resúmenes
gemini "Resume en 3 puntos principales: [tema complejo]"

# Dividir consultas complejas
gemini "Parte 1: Explica los conceptos básicos de Docker"
gemini "Parte 2: Muestra ejemplos prácticos de Docker"
```

---

## Integración con Otros Sistemas

### Integración con Editores de Código

#### Visual Studio Code
```json
// settings.json
{
    "terminal.integrated.shellArgs.osx": [
        "-c",
        "alias ghelp='gemini \"Explica este código:\"' && exec zsh"
    ]
}
```

#### Vim/Neovim
```vim
" Agregar a .vimrc
command! -nargs=1 Gemini !gemini "<args>"
nnoremap <leader>g :Gemini 
```

### Scripts de Automatización

#### Script de Revisión de Código
```bash
#!/bin/bash
# code-review.sh

if [ $# -eq 0 ]; then
    echo "Uso: $0 <archivo_de_codigo>"
    exit 1
fi

FILE=$1
CODE=$(cat $FILE)

echo "Revisando código en $FILE..."
gemini "Revisa este código y sugiere mejoras, identifica posibles bugs y optimizaciones: $CODE"
```

#### Script de Documentación Automática
```bash
#!/bin/bash
# auto-doc.sh

for file in *.js; do
    echo "Generando documentación para $file..."
    code=$(cat $file)
    gemini "Genera documentación JSDoc para este código: $code" > "${file%.js}.doc.md"
done
```

### Integración con Git

#### Git Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Revisar código antes de commit
changed_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|py|java)$')

for file in $changed_files; do
    echo "Revisando $file..."
    code=$(cat $file)
    gemini "Revisa brevemente este código y reporta solo problemas críticos: $code"
done
```

### APIs y Webhooks

#### Servidor Express con Gemini
```javascript
const express = require('express');
const { exec } = require('child_process');

const app = express();
app.use(express.json());

app.post('/gemini', (req, res) => {
    const { query } = req.body;
    
    exec(`gemini "${query}"`, (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ error: error.message });
        }
        
        res.json({ response: stdout });
    });
});

app.listen(3000, () => {
    console.log('Gemini API server running on port 3000');
});
```

---

## Automatización y Scripts

### Scripts de Productividad

#### Generador de Commits
```bash
#!/bin/bash
# smart-commit.sh

# Obtener cambios
changes=$(git diff --cached --name-only)
diff=$(git diff --cached)

# Generar mensaje de commit
message=$(gemini "Genera un mensaje de commit conciso para estos cambios: $diff")

echo "Mensaje sugerido: $message"
read -p "¿Usar este mensaje? (y/n): " confirm

if [ "$confirm" = "y" ]; then
    git commit -m "$message"
else
    echo "Commit cancelado"
fi
```

#### Generador de README
```bash
#!/bin/bash
# generate-readme.sh

project_name=$(basename $(pwd))
files=$(ls -la)
package_json=""

if [ -f "package.json" ]; then
    package_json=$(cat package.json)
fi

gemini "Crea un README.md profesional para el proyecto '$project_name'. Archivos en el proyecto: $files. Package.json: $package_json" > README.md

echo "README.md generado exitosamente"
```

### Workflows de Desarrollo

#### Pipeline de Revisión Automática
```bash
#!/bin/bash
# review-pipeline.sh

echo "🔍 Iniciando revisión automática..."

# 1. Análisis de código
echo "📝 Analizando código..."
gemini "Analiza la calidad del código en este proyecto y sugiere mejoras generales" > review-report.md

# 2. Verificación de seguridad
echo "🔒 Verificando seguridad..."
gemini "Identifica posibles vulnerabilidades de seguridad en este proyecto" >> review-report.md

# 3. Optimización de rendimiento
echo "⚡ Analizando rendimiento..."
gemini "Sugiere optimizaciones de rendimiento para este proyecto" >> review-report.md

echo "✅ Revisión completada. Ver review-report.md"
```

### Monitoreo y Alertas

#### Script de Monitoreo de Logs
```bash
#!/bin/bash
# log-monitor.sh

LOG_FILE="/var/log/app.log"
LAST_CHECK_FILE="/tmp/last_check"

if [ ! -f "$LAST_CHECK_FILE" ]; then
    touch "$LAST_CHECK_FILE"
fi

# Obtener nuevas líneas desde la última verificación
new_logs=$(tail -n +$(wc -l < "$LAST_CHECK_FILE") "$LOG_FILE")

if [ ! -z "$new_logs" ]; then
    # Analizar logs con Gemini
    analysis=$(gemini "Analiza estos logs y identifica problemas críticos: $new_logs")
    
    if [[ $analysis == *"CRÍTICO"* ]] || [[ $analysis == *"ERROR"* ]]; then
        echo "🚨 Problema detectado en logs: $analysis"
        # Enviar alerta (email, Slack, etc.)
    fi
fi

# Actualizar contador de líneas
wc -l < "$LOG_FILE" > "$LAST_CHECK_FILE"
```

### Herramientas de Desarrollo

#### Generador de Tests
```bash
#!/bin/bash
# generate-tests.sh

if [ $# -eq 0 ]; then
    echo "Uso: $0 <archivo_de_codigo>"
    exit 1
fi

FILE=$1
CODE=$(cat $FILE)
FILENAME=$(basename $FILE .js)

echo "Generando tests para $FILE..."

gemini "Genera tests unitarios completos usando Jest para este código JavaScript: $CODE" > "${FILENAME}.test.js"

echo "Tests generados en ${FILENAME}.test.js"
```

#### Optimizador de Consultas SQL
```bash
#!/bin/bash
# optimize-sql.sh

SQL_FILE=$1
QUERIES=$(cat $SQL_FILE)

echo "Optimizando consultas SQL..."

gemini "Optimiza estas consultas SQL para mejor rendimiento y explica los cambios: $QUERIES" > "${SQL_FILE%.sql}_optimized.sql"

echo "Consultas optimizadas guardadas en ${SQL_FILE%.sql}_optimized.sql"
```

---

## Casos de Uso Específicos por Industria

### Desarrollo Web

```bash
# Análisis de rendimiento web
gemini "Analiza este código CSS y sugiere optimizaciones para mejorar el rendimiento de carga"

# Accesibilidad
gemini "Revisa este HTML y sugiere mejoras de accesibilidad siguiendo las pautas WCAG"

# SEO
gemini "Optimiza este contenido HTML para SEO y sugiere meta tags apropiados"
```

### Data Science

```bash
# Análisis de datos
gemini "Explica cómo interpretar estos resultados de regresión lineal: [datos]"

# Visualización
gemini "Sugiere el mejor tipo de gráfico para mostrar la correlación entre estas variables"

# Machine Learning
gemini "Explica cuándo usar Random Forest vs SVM para este problema de clasificación"
```

### DevOps

```bash
# Infraestructura como código
gemini "Crea un template de Terraform para desplegar una aplicación web en AWS"

# Monitoreo
gemini "Diseña una estrategia de monitoreo para una aplicación microservicios"

# CI/CD
gemini "Crea un pipeline de GitHub Actions para una aplicación Node.js con tests y deployment"
```

### Seguridad

```bash
# Auditoría de seguridad
gemini "Realiza una auditoría de seguridad de este código y identifica vulnerabilidades"

# Configuración segura
gemini "¿Cómo configurar de forma segura un servidor web nginx?"

# Incident response
gemini "Crea un plan de respuesta a incidentes para un ataque de ransomware"
```

---

## Conclusión

Gemini CLI es una herramienta poderosa que puede transformar tu flujo de trabajo de desarrollo. Desde consultas rápidas hasta automatización compleja, las posibilidades son prácticamente ilimitadas.

### Próximos Pasos

1. **Experimenta** con diferentes tipos de consultas
2. **Crea scripts** personalizados para tus necesidades específicas
3. **Integra** Gemini CLI en tu flujo de trabajo diario
4. **Comparte** tus scripts y mejores prácticas con tu equipo
5. **Mantente actualizado** con las nuevas funcionalidades de Gemini

### Recursos Adicionales

- [Documentación oficial de Gemini API](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com/)
- [Comunidad de desarrolladores](https://discuss.ai.google.dev/)

### Soporte y Contribuciones

Si encuentras problemas o tienes sugerencias de mejora:

1. Revisa la sección de [Solución de Problemas](#solución-de-problemas)
2. Consulta los logs de error
3. Verifica tu configuración de API Key
4. Prueba con consultas más simples

¡Disfruta explorando las capacidades de Gemini CLI y mejorando tu productividad!

---

*Última actualización: Junio 2024*
*Versión del tutorial: 1.0*
