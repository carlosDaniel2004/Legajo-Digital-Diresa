# app/presentation/routes/error_routes.py
from flask import Blueprint, render_template, current_app

# Se utiliza un Blueprint para organizar las rutas de manejo de errores.
error_bp = Blueprint('errors', __name__)

@error_bp.app_errorhandler(404)
def not_found_error(error):
    """
    Manejador para errores 404 (Página no encontrada).
    
    Esta función se activa cuando Flask no puede encontrar una ruta.
    Renderiza una plantilla HTML personalizada para informar al usuario.
    """
    current_app.logger.warning(f"Se accedió a una ruta no encontrada: {error}")
    return render_template('errors/404.html'), 404

@error_bp.app_errorhandler(500)
def internal_error(error):
    """
    Manejador para errores 500 (Error interno del servidor).
    
    Esta función se activa cuando ocurre una excepción no controlada en la aplicación.
    Registra el error completo en el log para depuración y muestra una página genérica al usuario.
    """
    # Es crucial registrar el traceback completo para poder diagnosticar el problema.
    current_app.logger.error(f"Error interno del servidor: {error}", exc_info=True)
    return render_template('errors/500.html'), 500
