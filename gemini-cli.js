#!/usr/bin/env node

const { GoogleGenerativeAI } = require('@google/generative-ai');
const fs = require('fs');
const path = require('path');

// Lee la API key desde las variables de entorno o desde un archivo .env
function getApiKey() {
    // Primero intenta desde variables de entorno
    if (process.env.GEMINI_API_KEY) {
        return process.env.GEMINI_API_KEY;
    }
    
    // Luego intenta desde el archivo .env
    const envPath = path.join(__dirname, '.env');
    if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        const match = envContent.match(/GEMINI_API_KEY\s*=\s*(.+)/);
        if (match) {
            return match[1].trim().replace(/^["']|["']$/g, '');
        }
    }
    
    throw new Error('No se encontró GEMINI_API_KEY. Configúrala en las variables de entorno o en el archivo .env');
}

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('Uso: node gemini-cli.js "tu pregunta aquí"');
        console.log('Ejemplo: node gemini-cli.js "Explícame qué es JavaScript"');
        process.exit(1);
    }
    
    const prompt = args.join(' ');
    
    try {
        const apiKey = getApiKey();
        const genAI = new GoogleGenerativeAI(apiKey);
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        
        console.log('🤖 Consultando a Gemini...\n');
        
        const result = await model.generateContent(prompt);
        const response = result.response;
        const text = response.text();
        
        console.log('📝 Respuesta de Gemini:');
        console.log('─'.repeat(50));
        console.log(text);
        console.log('─'.repeat(50));
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    }
}

main();
