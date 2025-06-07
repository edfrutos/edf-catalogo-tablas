# Scripts de Utilidades para la Base de Datos

Este directorio contiene scripts útiles para el mantenimiento y administración de la base de datos de la aplicación.

## Scripts Disponibles

### 1. check_headers_catalog.py
**Descripción:** Verifica las cabeceras de un catálogo específico por su ID.
**Uso:**
```bash
python3 check_headers_catalog.py --catalog_id <ObjectId>
```
**Ejemplo:**
```bash
python3 check_headers_catalog.py --catalog_id 5f8d8f9b8e1c9f3b3c7d9e1a
```

### 2. fix_headers_catalogs.py
**Descripción:** Corrige las cabeceras de los catálogos que no las tengan definidas correctamente.
**Uso:**
```bash
python3 fix_headers_catalogs.py [--dry-run] [--catalog_id <ObjectId>]
```
**Opciones:**
- `--dry-run`: Muestra los cambios que se realizarán sin aplicarlos
- `--catalog_id`: Especifica un catálogo en particular a corregir

### 3. fix_owner_catalogs.py
**Descripción:** Asigna propietarios a catálogos que no tengan uno definido.
**Uso:**
```bash
python3 fix_owner_catalogs.py [--dry-run] [--user_id <ObjectId>] [--catalog_id <ObjectId>]
```
**Opciones:**
- `--dry-run`: Muestra los cambios que se realizarán sin aplicarlos
- `--user_id`: Especifica el ID del usuario que será asignado como propietario
- `--catalog_id`: Especifica un catálogo en particular a corregir

### 4. fix_rows_data_catalogs.py
**Descripción:** Corrige problemas en los datos de las filas de los catálogos.
**Uso:**
```bash
python3 fix_rows_data_catalogs.py [--dry-run] [--catalog_id <ObjectId>] [--fix]
```
**Opciones:**
- `--dry-run`: Muestra los problemas encontrados sin corregirlos
- `--catalog_id`: Especifica un catálogo en particular a analizar
- `--fix`: Aplica las correcciones automáticamente

### 5. report_rows_data_catalogs.py
**Descripción:** Genera un informe sobre los datos de los catálogos.
**Uso:**
```bash
python3 report_rows_data_catalogs.py [--output reporte.html] [--catalog_id <ObjectId>]
```
**Opciones:**
- `--output`: Especifica el archivo de salida para el informe
- `--catalog_id`: Genera el informe solo para un catálogo específico

## Uso en el Panel de Administración

Estos scripts están integrados en el panel de administración en la sección "Scripts". Para usarlos:

1. Navega a la sección de "Scripts" en el panel de administración
2. Selecciona el script que deseas ejecutar
3. Especifica los argumentos necesarios
4. Haz clic en "Ejecutar"

## Precauciones

- Siempre realiza una copia de seguridad antes de ejecutar scripts que modifiquen datos
- Usa la opción `--dry-run` para ver qué cambios se realizarán antes de aplicarlos
- Algunos scripts requieren permisos de administrador para ejecutarse

## Requisitos

- Python 3.6 o superior
- Dependencias de Python listadas en `requirements.txt`
- Acceso a la base de datos MongoDB
- Variables de entorno configuradas correctamente (MONGO_URI, etc.)
