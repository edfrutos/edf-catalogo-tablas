# Guía Técnica: Testing UI Interactiva y Modales en Flask

## 1. Agregar y Detectar Nuevos Tests

- **Ubicación recomendada:**
  - Para integración: `tests/integration/test_*.py`
  - Para funcionalidad: `tests/app/routes/test_*.py`
  - Para scripts/utilidades: `tests/scripts/test_*.py`
- **Detección automática:**
  - Cualquier archivo que siga el patrón `test_*.py` en los directorios de tests será detectado y aparecerá en la UI interactiva de testing.
  - No es necesario registrar manualmente los tests en la interfaz: la plantilla los lista automáticamente.

## 2. Extender el Modal de Resultados

- **Más ancho:** El modal usa `modal-xl` para mostrar mejor líneas largas.
- **Funcionalidades UX:**
  - **Botón Copiar:** Permite copiar el resultado del test o log al portapapeles.
  - **Autocross:** El modal hace scroll automático al final del resultado al actualizarse.
  - **Colores:**
    - Mensajes de error, traceback o fallos aparecen en rojo y fondo suave.
    - Resultados exitosos aparecen en color normal y fondo claro.
- **Mostrar logs u otros resultados:**
  - Puedes reutilizar el modal para mostrar cualquier texto:

    ```js
    window.showScriptResultModal(logContent, 'Logs del sistema');
    ```

## 3. Crear Nuevas Vistas Interactivas (Patrón AJAX + Modal)

### Ejemplo de patrón

**HTML:**

```html
<button class="btn btn-info run-action-btn" data-action="backup">Ejecutar Backup</button>
```

**JS (en `{% block scripts %}`):**

```js
$('.run-action-btn').click(function() {
  var action = $(this).data('action');
  $.post('/api/backup', { action: action }, function(data) {
    window.showScriptResultModal(data.result, 'Resultado Backup');
  });
});
```

**Backend Flask:**

```python
@app.route('/api/backup', methods=['POST'])
def run_backup():
    action = request.form.get('action')
    # ... lógica de backup ...
    return jsonify({'result': 'Backup completado correctamente.'})
```

## 4. Buenas Prácticas

- Usa `{% block scripts %}` para JS específico de cada vista, después de cargar jQuery y dashboard.js.
- Devuelve siempre JSON estructurado en endpoints AJAX.
- Usa clases y selectores claros para los botones de acción.
- Centraliza la lógica de modales en una función global (como `window.showScriptResultModal`).

## 5. Ejemplo de Extensión: Mostrar Logs del Sistema

**Botón en HTML:**

```html
<button class="btn btn-warning" id="showLogsBtn">Ver logs</button>
```

**JS:**

```js
$('#showLogsBtn').click(function() {
  $.get('/api/logs/last', function(data) {
    window.showScriptResultModal(data.logs, 'Últimos logs del sistema');
  });
});
```

**Backend:**

```python
@app.route('/api/logs/last')
def get_last_logs():
    # Lógica para leer logs
    return jsonify({'logs': '...contenido del log...'})
```

---

## 6. Experiencia de Usuario (UX)

- Modal ancho (`modal-xl`) para mejor lectura.
- Botón copiar resultado.
- Autoscroll automático.
- Colores diferenciados para errores.
- Mensajes claros de éxito y error.

---

**Este patrón es reutilizable para cualquier acción AJAX que quieras mostrar en la UI admin o de desarrollo.**

Para dudas, sugerencias o nuevas integraciones, consulta este archivo o contacta al equipo de desarrollo.
