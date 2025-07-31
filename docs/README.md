# edf_catalogo_tablas

Una aplicación web desarrollada en Flask para gestionar catálogos de tablas mediante hojas de cálculo (Excel) y gestión de imágenes. Cada usuario puede crear, importar, editar y descargar su catálogo, el cual se almacena en archivos Excel y se complementa con imágenes. Además, incluye autenticación de usuarios, recuperación de contraseña mediante token enviado por correo y despliegue en Heroku.

## Características

- **Autenticación de Usuarios:**  
  Registro, inicio de sesión y cierre de sesión.  
  Inicio de sesión admite usuario (nombre) o email de forma indistinta.

- **Recuperación de Contraseña:**  
  Permite solicitar un enlace de recuperación mediante nombre o email; el enlace es enviado al correo registrado.

- **Gestión de Catálogos:**  
  Cada usuario puede tener varias hojas de cálculo (tablas) en las que se almacenan los datos de cada objeto (número, descripción, peso, valor e imágenes).

- **Importación y Creación de Hojas de Cálculo:**  
  Los usuarios pueden crear una nueva tabla vacía o importar un archivo Excel existente.

- **Gestión de Registros:**  
  Se pueden agregar, editar y eliminar registros dentro de la tabla seleccionada.

- **Descarga del Catálogo:**  
  El catálogo se exporta a un archivo Excel y, junto con las imágenes referenciadas, se comprime en un archivo ZIP para su descarga.

- **Despliegue en Heroku:**  
  La aplicación está preparada para desplegarse en Heroku utilizando Gunicorn y un Procfile.

## Estructura del Proyecto

```plaintext
edf_catalogo_tablas/
├── app.py                # Aplicación principal en Flask
├── Procfile              # Archivo para desplegar en Heroku (ej.: "web: gunicorn app:app")
├── requirements.txt      # Dependencias del proyecto
├── README.md             # Este archivo
├── .gitignore            # Archivos y carpetas a ignorar en Git (por ejemplo, .venv/)
├── spreadsheets/         # Carpeta para almacenar las hojas de cálculo (archivos .xlsx)
│   └── (archivos Excel)
├── imagenes_subidas/      # Carpeta para almacenar las imágenes subidas
│   └── (imágenes)
├── static/               # Archivos estáticos
│   └── styles.css        # Hojas de estilos CSS
└── templates/            # Plantillas HTML de la aplicación
    ├── register.html
    ├── login.html
    ├── forgot_password.html
    ├── reset_password_form.html
    ├── tables.html
    ├── index.html      # Catálogo (accesible en /catalog)
    └── editar.html
```

## Instalación y Configuración

### 1. Clonar el repositorio:

```bash
git clone https://github.com/tu_usuario/edf_catalogo_tablas.git
cd edf_catalogo_tablas
```

### 2. Crear y activar un entorno virtual (opcional, pero recomendado):

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno:
- Define SECRET_KEY en tu entorno de producción.
- Configura el URI de MongoDB Atlas en la variable MONGO_URI (ya está incluido en el código, pero puedes ajustarlo mediante variables de entorno si lo prefieres).

### 5. Asegúrate de que el archivo Procfile esté presente:

```
web: gunicorn app:app
```

## Uso

### Desarrollo local:
Ejecuta la aplicación con:

```bash
python app.py
```

Accede en tu navegador a http://127.0.0.1:5000.

### Funcionalidades principales:
- Regístrate o inicia sesión.
- Accede a la sección de "Tablas" para crear o importar una hoja de cálculo.
- Selecciona una tabla para trabajar en el catálogo.
- Agrega, edita o elimina registros en el catálogo.
- Descarga el catálogo completo (Excel + imágenes comprimidas en ZIP).

## Despliegue en Heroku

### 1. Inicia sesión en Heroku CLI:

```bash
heroku login
```

### 2. Crea una nueva aplicación en Heroku:

```bash
heroku create tu-aplicacion-nombre
```

### 3. Configura las variables de entorno:

```bash
heroku config:set SECRET_KEY=tu_clave_secreta_aqui
heroku config:set MONGO_URI=tu_uri_de_mongodb_atlas
```

### 4. Despliega la aplicación:

```bash
git add .
git commit -m "Despliegue inicial"
git push heroku master
```

### 5. Abre la aplicación:

```bash
heroku open
```

## Tecnologías Utilizadas

- **Backend:** Flask (Python)
- **Base de Datos:** MongoDB Atlas
- **Frontend:** HTML, CSS, JavaScript
- **Despliegue:** Heroku
- **Servidor WSGI:** Gunicorn
- **Gestión de Archivos:** Excel (openpyxl), ZIP

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto

Eduardo de Frutos - [@edfrutos](https://github.com/edfrutos)

Link del proyecto: [https://github.com/edfrutos/edf_catalogo_tablas](https://github.com/edfrutos/edf_catalogo_tablas)
