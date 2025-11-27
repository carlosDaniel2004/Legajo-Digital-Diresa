/**
 * Handlers específicos para perfil.html
 */

document.addEventListener('DOMContentLoaded', function() {
  // Cancelar formulario de email
  document.querySelectorAll('[data-cancel-email-form]').forEach(btn => {
    btn.addEventListener('click', function() {
      document.getElementById('email-form').style.display = 'none';
    });
  });

  // Cancelar cambio de contraseña
  document.querySelectorAll('[data-cancel-password-form]').forEach(btn => {
    btn.addEventListener('click', function() {
      window.history.back();
    });
  });

  // Botón para subir foto
  document.querySelectorAll('[data-trigger-file-input]').forEach(btn => {
    btn.addEventListener('click', function() {
      document.getElementById(this.getAttribute('data-trigger-file-input')).click();
    });
  });

  // Volver atrás
  document.querySelectorAll('[data-go-back]').forEach(btn => {
    btn.addEventListener('click', function() {
      window.history.back();
    });
  });

  // Toggle password visibility
  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const fieldId = this.getAttribute('data-toggle-password');
      const field = document.getElementById(fieldId);
      const icon = this.querySelector('i');
      
      if (field.type === 'password') {
        field.type = 'text';
        if (icon) icon.className = 'bi bi-eye-slash';
      } else {
        field.type = 'password';
        if (icon) icon.className = 'bi bi-eye';
      }
    });
  });
});
