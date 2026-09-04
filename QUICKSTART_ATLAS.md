# Quick Start: MongoDB Atlas + Docker Compose

## ⚡ Pasos Rápidos (5 minutos)

### 1. Obtener credenciales de MongoDB Atlas

```bash
# Ve a: https://www.mongodb.com/cloud/atlas
# 1. Crea cluster (free tier)
# 2. Database Access → crea usuario
# 3. Network Access → añade tu IP (o 0.0.0.0)
# 4. Connect → copia connection string
```

**Conexión string será como:**
```
mongodb+srv://username:password@cluster0.abc123.mongodb.net/database?retryWrites=true&w=majority
```

### 2. Configurar .env

```bash
cp .env.atlas.example .env

# Editar .env y reemplazar:
SECRET_KEY=<genera con: openssl rand -base64 32>
MONGO_URI=mongodb+srv://tu_usuario:tu_password@tu_cluster.mongodb.net/edf_catalogotablas?retryWrites=true&w=majority
REDIS_PASSWORD=tu_password_redis_aqui
```

### 3. Iniciar con Docker Compose

```bash
# Opción A: Solo la app (sin Redis)
docker-compose -f docker-compose.atlas.yml up -d

# Opción B: Con Redis local
docker-compose -f docker-compose.atlas.yml --profile with_redis up -d
```

### 4. Verificar que funciona

```bash
# Ver logs
docker-compose -f docker-compose.atlas.yml logs -f app

# Probar health check
curl http://localhost:5002/health

# Acceder a la app
open http://localhost:5002
```

---

## 📋 Explicación

### docker-compose.atlas.yml
- **MongoDB**: Nube (MongoDB Atlas) - sin necesidad de descargar imagen
- **Redis**: Opcional (comentado por defecto)
- **App**: Flask dockerizada en tu máquina

### Ventajas
✅ No requiere descargar mongo:latest (sin Docker Hub auth)
✅ Datos persistentes en MongoDB Atlas
✅ Accesible desde cualquier lugar
✅ Free tier disponible en Atlas
✅ Escalable fácilmente

### .env.atlas.example
- Preconfigurado para MongoDB Atlas
- Incluye instrucciones paso a paso
- Documentación de seguridad

---

## 🔐 Seguridad (IMPORTANTE)

### Para Desarrollo
```env
MONGO_URI=mongodb+srv://dev_user:dev_pass@cluster.mongodb.net/edf_catalogotablas?retryWrites=true&w=majority
# IP whitelist: 0.0.0.0/0 (permite cualquier IP)
```

### Para Producción
```env
MONGO_URI=mongodb+srv://prod_user:strong_pass@cluster.mongodb.net/edf_catalogotablas?retryWrites=true&w=majority
# IP whitelist: solo tu servidor IP
# Usuario con permisos limitados
# Password rotada regularmente
```

---

## Troubleshooting

### Error: "authentication failed"
```
Verificar que:
1. Username y password son correctos en MONGO_URI
2. IP está whitelisted en Atlas ("Network Access")
3. Database existe en Atlas
```

### Error: "unable to connect"
```
Verificar que:
1. Cluster está corriendo en Atlas
2. Connection string es mongodb+srv:// (no mongodb://)
3. Red connectivity OK
```

### Error: "401 Unauthorized"
```
Este error es del Docker pull, no de MongoDB Atlas.
Usar docker-compose.atlas.yml evita este problema
porque NO descarga imagen de mongo desde Docker Hub.
```

---

## Próximos Pasos

1. ✅ Crear cluster en MongoDB Atlas
2. ✅ Crear usuario de BD
3. ✅ Whitelist IP
4. ✅ Copiar connection string
5. ✅ `cp .env.atlas.example .env`
6. ✅ Editar MONGO_URI en .env
7. ✅ `docker-compose -f docker-compose.atlas.yml up -d`

¡Listo! Tu app está corriendo con MongoDB en la nube.

---

## Archivos Nuevos

- **docker-compose.atlas.yml** - Compose con MongoDB Atlas
- **.env.atlas.example** - Template de configuración para Atlas
- **QUICKSTART_ATLAS.md** - Este archivo

Ver también: DOCKER_AUTH_FIX.md, DOCKER.md, DOCKER_BUILD.md
