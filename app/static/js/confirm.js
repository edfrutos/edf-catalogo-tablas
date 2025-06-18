function confirmarContinuar(mensaje = '¿Desea continuar con la iteración?') {
    return confirm(mensaje);
}

function confirmarAccion(evento, mensaje = '¿Desea continuar con la iteración?') {
    if (!confirmarContinuar(mensaje)) {
        evento.preventDefault();
        return false;
    }
    return true;
}