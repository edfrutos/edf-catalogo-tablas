# Reglas de Desarrollo para Azure

## Reglas Generales

- Al manejar peticiones relacionadas con Azure, usar siempre las herramientas de Azure apropiadas.
- Al generar código para Azure o realizar operaciones de Azure, seguir las Mejores Prácticas de Generación de Código.
- Al desplegar en Azure, seguir las Mejores Prácticas de Despliegue.

## Autenticación y Seguridad

- Usar autenticación apropiada según el contexto:

   - Identidad Administrada para servicios alojados en Azure
   - Principal de Servicio para CI/CD
   - Autenticación de Navegador Interactiva para aplicaciones de usuario
   - Secreto de Cliente para aplicaciones daemon

- Nunca codificar credenciales directamente; usar Key Vault
- Implementar rotación de credenciales y privilegios mínimos
- Habilitar cifrado y conexiones seguras

## Manejo de Errores y Fiabilidad

- Implementar lógica de reintentos con retroceso exponencial
- Agregar registro y monitoreo adecuados
- Incluir circuit breakers donde sea necesario
- Manejar errores específicos del servicio
- Asegurar la limpieza adecuada de recursos

## Rendimiento y Escalabilidad

- Usar agrupación de conexiones para bases de datos
- Configurar operaciones concurrentes y tiempos de espera
- Implementar caché de manera estratégica
- Monitorear el uso de recursos
- Optimizar operaciones por lotes

## Servicios Específicos

- Al trabajar con Azure Functions:

   - Seguir las Mejores Prácticas de Código para Functions
   - Optimizar el tiempo de ejecución
   - Manejar correctamente el estado

- Al trabajar con Aplicaciones Web Estáticas:

   - Seguir las Mejores Prácticas de SWA
   - Optimizar el rendimiento del frontend
   - Implementar estrategias de caché efectivas

## Operaciones con Datos

- Bases de Datos:
   - Usar consultas parametrizadas
   - Implementar indexación apropiada
   - Manejar conexiones eficientemente
   - Habilitar cifrado
   - Monitorear rendimiento de consultas

- Almacenamiento:
   - Manejar tamaños de archivo apropiadamente
   - Usar operaciones por lotes para múltiples archivos
   - Configurar niveles de acceso apropiados
   - Gestionar concurrencia