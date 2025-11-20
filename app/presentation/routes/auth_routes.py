# RUTA: app/presentation/routes/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user
from app.application.forms import LoginForm, TwoFactorForm
from app import limiter
from app.application.services.usuario_service import UsuarioService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
# Seguridad: Aplicar un límite de intentos para prevenir ataques de fuerza bruta.
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Asumimos que 'index' maneja la redirección post-login si ya está autenticado
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            usuario_service = current_app.config['USUARIO_SERVICE']
            user_id = usuario_service.attempt_login(form.username.data, form.password.data)

            if user_id:
                session['2fa_user_id'] = user_id
                session['2fa_username'] = form.username.data
                # Guardar el estado de "Recordarme" en la sesión
                session['2fa_remember_me'] = form.remember_me.data
                return redirect(url_for('auth.verify_2fa'))
            else:
                flash('Usuario o contraseña incorrectos.', 'danger')
                return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Error inesperado en login: {e}")
            flash("Ocurrió un error inesperado. Por favor, intente de nuevo.", 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/login/verify', methods=['GET', 'POST'])
# Seguridad: Aplicar un límite de intentos para prevenir el bombardeo de códigos.
@limiter.limit("5 per minute")
def verify_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('auth.login'))

    form = TwoFactorForm()
    if form.validate_on_submit():
        user_id = session['2fa_user_id']
        usuario_service = current_app.config['USUARIO_SERVICE']
        user = usuario_service.verify_2fa_code(user_id, form.code.data)

        if user:
            usuario_service.update_last_login(user_id)
            # Recuperar el estado de "Recordarme" de la sesión
            remember = session.get('2fa_remember_me', False)
            login_user(user, remember=remember)
            
            # Limpiar toda la información de 2FA de la sesión
            session.pop('2fa_user_id', None)
            session.pop('2fa_username', None)
            session.pop('2fa_remember_me', None)
            
            flash(f'Bienvenido de nuevo, {user.nombre_completo or user.username}!', 'success')
            
            # ------------------------------------------------------------------
            # 🔑 CORRECCIÓN: Lógica de redirección basada en el rol
            # ------------------------------------------------------------------
            if user.rol == 'Sistemas':
                # Redirige al Dashboard de Sistemas (el de las 6 tarjetas)
                return redirect(url_for('sistemas.dashboard'))
            elif user.rol == 'RRHH':
                return redirect(url_for('rrhh.inicio_rrhh')) 
            elif user.rol == 'AdministradorLegajos':
                return redirect(url_for('legajo.dashboard'))
            else:
                # Redirige a una página de índice general si el rol no coincide
                return redirect(url_for('index'))
            # ------------------------------------------------------------------
            
        else:
            flash('Código de verificación incorrecto o expirado.', 'danger')

    return render_template('auth/verify_2fa.html', form=form, username=session.get('2fa_username'))

@auth_bp.route('/logout')
def logout():
    # Limpia todos los mensajes flash pendientes de la sesión anterior
    session.clear() 
    logout_user()
    flash('Has cerrado la sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.application.services.usuario_service import UsuarioService # Asegúrate de importar el servicio
from werkzeug.security import generate_password_hash

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """
    Muestra el perfil del usuario y permite cambiar la contraseña.
    """
    if request.method == 'POST':
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmacion = request.form.get('password_confirmacion')

        # Validaciones básicas
        if not password_actual or not password_nueva or not password_confirmacion:
            flash('Todos los campos son obligatorios.', 'warning')
            return redirect(url_for('auth.perfil'))

        if password_nueva != password_confirmacion:
            flash('Las nuevas contraseñas no coinciden.', 'danger')
            return redirect(url_for('auth.perfil'))

        # Verificar contraseña actual
        # Nota: check_password debe ser un método de tu modelo User (UserMixin)
        if not current_user.check_password(password_actual):
            flash('La contraseña actual es incorrecta.', 'danger')
            return redirect(url_for('auth.perfil'))

        try:
            # Actualizar contraseña usando el servicio
            # Asumimos que 'USUARIO_SERVICE' está registrado en la config, igual que 'LEGAJO_SERVICE'
            usuario_service = current_app.config.get('USUARIO_SERVICE')
            
            if usuario_service:
                # Encriptamos antes de enviar o el servicio lo hace (depende de tu lógica).
                # Aquí asumiremos que el servicio espera el hash o lo hashea él mismo.
                # Si tu servicio espera texto plano y él lo hashea:
                usuario_service.update_password(current_user.id, password_nueva) 
            else:
                # Fallback si el servicio no está en config (Actualización directa manual)
                current_user.password_hash = generate_password_hash(password_nueva)
                from app import db # Importación tardía para evitar ciclos
                db.session.commit()

            flash('¡Contraseña actualizada correctamente!', 'success')
        except Exception as e:
            current_app.logger.error(f"Error al cambiar password: {str(e)}")
            flash('Ocurrió un error al actualizar la contraseña.', 'danger')

    return render_template('auth/perfil.html', user=current_user)