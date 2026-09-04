# Despliegue — EDF CatálogoTablas

## URLs

| Entorno | URL |
|---|---|
| **Producción** | https://catalogotablas.edefrutos2020.com |
| **Local** | http://localhost:5002 |

---

## Infraestructura

| Componente | Detalle |
|---|---|
| App | Flask / Gunicorn en Docker |
| Base de datos | MongoDB Atlas — `cluster0.alh9mwn.mongodb.net` / `edf_catalogotablas` |
| Almacenamiento | AWS S3 — bucket `edf-catalogo-tablas-sp` / región `eu-south-2` |
| Túnel | autossh Mac → Vultr (`208.76.221.20:2222`) |
| Proxy | nginx en Plesk → `127.0.0.1:5002` |
| SSL | Let's Encrypt (renovación automática por Plesk) |

---

## Arranque local

```bash
# Variables de entorno en:
# /Volumes/ESSAGER/__01.-Proyectos/edf_catalogotablas/.env

docker-compose -f docker-compose.atlas.yml up -d
```

> Si el contenedor no recoge cambios del `.env`: añadir `--force-recreate`  
> Si el shell tiene `MONGO_URI` exportada, desactivarla antes: `unset MONGO_URI`

## Parada local

```bash
docker-compose -f docker-compose.atlas.yml down
```

---

## Túnel SSH (Mac → Vultr)

El túnel arranca automáticamente al iniciar sesión en el Mac via LaunchAgent.

```bash
# Ver estado
launchctl list | grep catalogotablas

# Parar túnel
launchctl unload ~/Library/LaunchAgents/com.edf.catalogotablas.tunnel.plist

# Arrancar túnel
launchctl load ~/Library/LaunchAgents/com.edf.catalogotablas.tunnel.plist

# Verificar que el puerto llega al servidor
ssh -p 2222 root@208.76.221.20 "ss -tlnp | grep 5002"

# Log del túnel
tail -f /tmp/catalogotablas-tunnel.log
```

---

## Variables de entorno clave

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Obligatoria, ≥ 32 chars |
| `MONGO_URI` | URI Atlas con usuario, contraseña y nombre de BD |
| `MONGO_DB` | `edf_catalogotablas` |
| `AWS_ACCESS_KEY_ID` | Credenciales S3 |
| `AWS_SECRET_ACCESS_KEY` | Credenciales S3 |
| `AWS_REGION` | `eu-south-2` |
| `S3_BUCKET_NAME` | `edf-catalogo-tablas-sp` |

> El `.env` lo lee Docker Compose desde el directorio del proyecto.  
> **No** sourcear `~/.config/edf_catalogotablas/.env` en el shell — sobreescribe las variables.

---

## Rebuild de imagen

Solo necesario si se cambian dependencias (`requirements.txt`) o el `Dockerfile`:

```bash
docker-compose -f docker-compose.atlas.yml up -d --build
```

Tras un rebuild, las sesiones Flask se invalidan — hay que volver a hacer login.

---

## Logs

```bash
# App
docker logs edf_catalogotablas_app --tail 50 -f

# Túnel SSH
tail -f /tmp/catalogotablas-tunnel.log

# nginx en Vultr
ssh -p 2222 root@208.76.221.20 "tail -f /var/www/vhosts/system/catalogotablas.edefrutos2020.com/logs/proxy_error_log"
```
