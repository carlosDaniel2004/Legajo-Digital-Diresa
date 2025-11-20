/**
 * Script para verificación de DNI en tiempo real
 * Ubicación: app/presentation/static/js/crear_personal.js
 */

document.addEventListener('DOMContentLoaded', function () {
    const dniInput = document.getElementById('dni');
    const dniFeedback = document.getElementById('dni-feedback');
    const submitBtn = document.getElementById('submit-btn');

    if (dniInput) {
        dniInput.addEventListener('blur', function () {
            const dni = this.value.trim();
            
            dniFeedback.textContent = '';
            dniInput.classList.remove('is-invalid', 'is-valid');
            submitBtn.disabled = false;

            if (dni.length === 8) {
                dniFeedback.textContent = 'Verificando...';
                
                fetch(`/legajo/api/personal/check_dni/${dni}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            dniFeedback.textContent = 'Este DNI ya se encuentra registrado.';
                            dniInput.classList.add('is-invalid');
                            submitBtn.disabled = true;
                        } else {
                            dniFeedback.textContent = 'DNI disponible.';
                            dniInput.classList.add('is-valid');
                        }
                    })
                    .catch(error => {
                        console.error('Error al verificar DNI:', error);
                        dniFeedback.textContent = 'No se pudo verificar el DNI. Intente de nuevo.';
                    });
            } else if (dni.length > 0) {
                dniFeedback.textContent = 'El DNI debe tener 8 dígitos.';
                dniInput.classList.add('is-invalid');
            }
        });
    }
});
