/**
 * Event Handlers centralizados para seguridad CSP
 * Todos los onclick handlers aquí en lugar de inline en templates
 */

// Handler para confirmar antes de eliminar
function confirmarAccion(mensaje = '¿Está seguro?') {
  return confirm(mensaje);
}

// Handler para desactivar botón y mostrar loading
function desactivarYEnviar(event) {
  event.preventDefault();
  const btn = event.currentTarget;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
  btn.form.submit();
}

// Handler para ocultar/mostrar password
function togglePasswordVisibility(fieldId) {
  const field = document.getElementById(fieldId);
  if (field.type === 'password') {
    field.type = 'text';
  } else {
    field.type = 'password';
  }
}

// Handler para copiar al portapapeles
function copiarAlPortapapeles(fieldId) {
  const field = document.getElementById(fieldId);
  const text = field.textContent || field.value;
  navigator.clipboard.writeText(text).then(() => {
    const btn = event.currentTarget;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Copiado!';
    setTimeout(() => {
      btn.innerHTML = originalHTML;
    }, 2000);
  }).catch(err => {
    console.error('Error al copiar:', err);
    alert('Error al copiar al portapapeles');
  });
}

// Handler para mostrar/ocultar password (confirmación de usuario creado)
function mostrarOcultarPassword() {
  const passwordField = document.getElementById('password');
  const btn = event.currentTarget;
  if (passwordField.type === 'password') {
    passwordField.type = 'text';
    btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
  } else {
    passwordField.type = 'password';
    btn.innerHTML = '<i class="bi bi-eye"></i>';
  }
}

// Handler para imprimir
function imprimirDatos() {
  window.print();
}

// Handler para activar input de archivo
function activarInputArchivo(inputId) {
  document.getElementById(inputId).click();
}

// Handler para ocultar elemento
function ocultarElemento(elementId) {
  document.getElementById(elementId).style.display = 'none';
}

// Handler para volver atrás
function volverAtras() {
  window.history.back();
}

// Inicializar todos los event listeners cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
  // Confirmar acciones peligrosas
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function(e) {
      if (!confirm(this.getAttribute('data-confirm'))) {
        e.preventDefault();
      }
    });
  });

  // Desactivar botones de submit
  document.querySelectorAll('[data-disable-on-submit]').forEach(btn => {
    btn.addEventListener('click', desactivarYEnviar);
  });

  // Toggle password visibility
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', function() {
      togglePasswordVisibility(this.getAttribute('data-toggle-password'));
    });
  });

  // Copiar al portapapeles
  document.querySelectorAll('[data-copy-to-clipboard]').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      copiarAlPortapapeles(this.getAttribute('data-copy-to-clipboard'));
    });
  });
});
