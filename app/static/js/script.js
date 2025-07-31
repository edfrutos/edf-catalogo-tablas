// Ejemplo de contenido para script.js
document.addEventListener("DOMContentLoaded", () => {
    console.log("[script.js] DOM loaded");

    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(document.getElementById("imageModal"));
    const modalImage = document.getElementById("modalImage");

    // Event listener for images
    document.querySelectorAll(".catalog-img").forEach(img => {
        img.addEventListener("click", function() {
            console.log("[script.js] Image clicked");
            const src = this.getAttribute("src");
            if (modalImage) {
                modalImage.src = src;
                modal.show();
            }
        });
    });
});