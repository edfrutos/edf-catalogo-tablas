function confirmarContinuar(mensaje = "¿Desea continuar con la iteración?") {
    return confirm(mensaje);
}

// Función disponible globalmente para confirmaciones con eventos
window.confirmarAccion = function(evento, mensaje = "¿Desea continuar con la iteración?") {
    if (!confirmarContinuar(mensaje)) {
        evento.preventDefault();
        return false;
    }
    return true;
};