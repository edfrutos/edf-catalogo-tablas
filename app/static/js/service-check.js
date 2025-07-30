// Archivo para verificar el estado del servicio
document.addEventListener("DOMContentLoaded", function() {
    // Solo ejecutar en la página de mantenimiento
    if (document.querySelector(".error-container")) {
        checkServiceStatus();
    }
});

function checkServiceStatus() {
    // Comprueba el estado del servicio cada 10 segundos
    setInterval(function() {
        fetch("/status")
            .then(response => response.json())
            .then(data => {
                if (data.status === "ready") {
                    console.log("La aplicación principal está lista");
                    // Recargar la página para usar la aplicación principal
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error("Error al comprobar el estado:", error);
            });
    }, 10000); // 10 segundos
}
