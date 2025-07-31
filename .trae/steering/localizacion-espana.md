---
inclusion: always
priority: medium
---

# Configuración de Localización - España

## 🇪🇸 Configuración Regional

### Formato de Fechas y Horas
- **Formato de fecha**: DD/MM/YYYY
- **Formato de hora**: HH:MM (24 horas)
- **Formato completo**: DD/MM/YYYY HH:MM:SS
- **Zona horaria**: Europe/Madrid (CET/CEST)

### Formato Numérico
- **Separador decimal**: Coma (,)
- **Separador de miles**: Punto (.)
- **Moneda**: Euro (€)
- **Formato moneda**: 1.234,56 €

### Ejemplos de Uso en Código

#### Python
```python
import locale
from datetime import datetime

# Configurar localización española
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

# Formatear fecha
fecha_actual = datetime.now()
fecha_formateada = fecha_actual.strftime("%d/%m/%Y %H:%M")
print(f"Fecha actual: {fecha_formateada}")

# Formatear números
precio = 1234.56
precio_formateado = locale.currency(precio, grouping=True)
print(f"Precio: {precio_formateado}")
```

#### JavaScript
```javascript
// Configurar localización española
const opciones_fecha = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Madrid'
};

// Formatear fecha
const fecha_actual = new Date();
const fecha_formateada = fecha_actual.toLocaleDateString('es-ES', opciones_fecha);
console.log(`Fecha actual: ${fecha_formateada}`);

// Formatear números
const precio = 1234.56;
const precio_formateado = precio.toLocaleString('es-ES', {
    style: 'currency',
    currency: 'EUR'
});
console.log(`Precio: ${precio_formateado}`);
```

## 📅 Días y Meses en Español

### Días de la semana
- Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo

### Meses del año
- Enero, Febrero, Marzo, Abril, Mayo, Junio
- Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre

## 🏢 Configuración de Negocio

### Horarios Comerciales
- **Horario estándar**: 09:00 - 18:00
- **Pausa comida**: 14:00 - 15:00
- **Días laborables**: Lunes a Viernes
- **Festivos**: Según calendario español

### Formatos de Documentos
- **DNI/NIE**: Formato español estándar
- **Teléfono**: +34 XXX XXX XXX
- **Código postal**: 5 dígitos (XXXXX)
- **Dirección**: Calle/Plaza/Avenida, Número, Piso, Puerta