// RUTA: app/presentation/static/js/main.js

// Espera a que todo el contenido del DOM esté cargado.
window.addEventListener('DOMContentLoaded', event => {
    // Lógica para el botón de mostrar/ocultar la barra lateral
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.getElementById('wrapper').classList.toggle('toggled');
        });
    }

    // Puedes añadir más lógica de JavaScript global aquí en el futuro.

    // --- LÓGICA PARA EL MODAL DE CONFIRMACIÓN DE ELIMINACIÓN DE PERSONAL ---
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    if (confirmDeleteModal) {
        confirmDeleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const personalId = button.getAttribute('data-personal-id');
            const personalName = button.getAttribute('data-personal-name');
            const deleteForm = confirmDeleteModal.querySelector('#deleteForm');
            
            // Leer la plantilla de URL desde el atributo data-* del modal
            const urlTemplate = confirmDeleteModal.getAttribute('data-url-template');
            
            if (personalId && deleteForm && urlTemplate) {
                const finalUrl = urlTemplate.replace('0', personalId);
                deleteForm.action = finalUrl;
                
                const nameElement = confirmDeleteModal.querySelector('#personalNameToDelete');
                if (nameElement) {
                    nameElement.textContent = personalName;
                }
            }
        });
    }
});
