# RUTA: app/decorators.py

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorador para restringir el acceso a rutas según una lista de nombres de roles permitidos.
    Los usuarios con rol 'Sistemas' tienen acceso a TODAS las funcionalidades.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Si el usuario no está autenticado, siempre se le envía a la página de login.
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # --- LÓGICA DE ACCESO ---
            # Los usuarios con rol 'Sistemas' tienen acceso a TODO (superusuario)
            if hasattr(current_user, 'rol') and current_user.rol == 'Sistemas':
                return f(*args, **kwargs)
            
            # Para otros roles, verificar si están en la lista de permitidos
            if not hasattr(current_user, 'rol') or current_user.rol not in roles:
                # Si el rol no es el correcto, muestra un mensaje de error.
                flash('No tiene los permisos necesarios para acceder a esta página.', 'danger')
                # Se redirige a la ruta raíz 'index', que sabe a qué dashboard enviar al usuario.
                return redirect(url_for('index'))
                
            # Si el rol es correcto, se permite el acceso a la ruta.
            return f(*args, **kwargs)
        return decorated_function
    return decorator