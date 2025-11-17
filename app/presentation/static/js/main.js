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

    // --- LÓGICA PARA EL MODAL DE CONFIRMACIÓN DE ELIMINACIÓN DE DOCUMENTOS ---
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    if (confirmDeleteModal) {
        confirmDeleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const docId = button.getAttribute('data-doc-id');
            const docName = button.getAttribute('data-doc-name');
            const deleteDocForm = confirmDeleteModal.querySelector('#deleteDocForm');
            
            if (docId && deleteDocForm) {
                // Construir la URL para la eliminación del documento
                const deleteUrl = '/legajo/documento/' + docId + '/eliminar';
                deleteDocForm.action = deleteUrl;
                
                const nameElement = confirmDeleteModal.querySelector('#docNameToDelete');
                if (nameElement) {
                    nameElement.textContent = docName;
                }
            }
        });
    }

    // --- LÓGICA PARA EL MODAL DE CONFIRMACIÓN DE DESACTIVACIÓN DE PERSONAL ---
    const confirmDeactivateModal = document.getElementById('confirmDeactivateModal');
    if (confirmDeactivateModal) {
        confirmDeactivateModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const personalId = button.getAttribute('data-personal-id');
            const personalName = button.getAttribute('data-personal-name');
            const deactivateForm = confirmDeactivateModal.querySelector('#deactivateForm');
            
            if (personalId && deactivateForm) {
                // Construir la URL para la desactivación
                const deactivateUrl = '/legajo/personal/' + personalId + '/eliminar';
                deactivateForm.action = deactivateUrl;
                
                const nameElement = confirmDeactivateModal.querySelector('#personalNameToDeactivate');
                if (nameElement) {
                    nameElement.textContent = personalName;
                }
            }
        });
    }

    // --- LÓGICA PARA EL MODAL DE CONFIRMACIÓN DE ACTIVACIÓN DE PERSONAL ---
    const confirmActivateModal = document.getElementById('confirmActivateModal');
    if (confirmActivateModal) {
        confirmActivateModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const personalId = button.getAttribute('data-personal-id');
            const personalName = button.getAttribute('data-personal-name');
            const activateForm = confirmActivateModal.querySelector('#activateForm');
            
            if (personalId && activateForm) {
                // Construir la URL para la reactivación
                const activateUrl = '/legajo/personal/' + personalId + '/reactivar';
                activateForm.action = activateUrl;
                
                const nameElement = confirmActivateModal.querySelector('#personalNameToActivate');
                if (nameElement) {
                    nameElement.textContent = personalName;
                }
            }
        });
    }

    // --- LÓGICA PARA LOS MENÚS DESPLEGABLES DEPENDIENTES (SECCIÓN -> TIPO DOCUMENTO) ---
    const seccionSelect = document.getElementById('seccion_select');
    const tipoDocSelect = document.getElementById('tipo_doc_select');
    
    if (seccionSelect && tipoDocSelect) {
        const loadTiposDocumento = (seccionId) => {
            tipoDocSelect.innerHTML = '<option value="0">Cargando...</option>';
            tipoDocSelect.disabled = true;

            if (seccionId && seccionId !== '0') {
                const urlTemplate = seccionSelect.getAttribute('data-tipos-url');
                if (!urlTemplate) {
                    console.error('El atributo data-tipos-url no se encontró en el select de sección.');
                    return;
                }
                const finalUrl = urlTemplate.replace('/0', `/${seccionId}`);

                fetch(finalUrl)
                    .then(response => {
                        if (!response.ok) { throw new Error('La respuesta de la red no fue correcta.'); }
                        return response.json();
                    })
                    .then(data => {
                        tipoDocSelect.innerHTML = '<option value="0">-- Seleccione un tipo --</option>';
                        if (data && data.length > 0) {
                            data.forEach(tipo => tipoDocSelect.add(new Option(tipo.nombre, tipo.id)));
                            tipoDocSelect.disabled = false;
                        } else {
                            tipoDocSelect.innerHTML = '<option value="0">-- No hay tipos para esta sección --</option>';
                        }
                    })
                    .catch(error => {
                        console.error('Error al cargar tipos de documento:', error);
                        tipoDocSelect.innerHTML = '<option value="0">-- Error al cargar --</option>';
                        tipoDocSelect.disabled = false;
                    });
            } else {
                tipoDocSelect.innerHTML = '<option value="0">-- Seleccione una sección primero --</option>';
                tipoDocSelect.disabled = true;
            }
        };

        seccionSelect.addEventListener('change', function () { loadTiposDocumento(this.value); });

        // Carga inicial si ya hay una sección seleccionada al cargar la página
        if (seccionSelect.value && seccionSelect.value !== '0') {
            loadTiposDocumento(seccionSelect.value);
        } else {
            tipoDocSelect.innerHTML = '<option value="0">-- Seleccione una sección primero --</option>';
            tipoDocSelect.disabled = true;
        }
    }
});
