from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, send_file, jsonify
from flask_login import login_required, current_user
from app.decorators import role_required
from app.application.forms import UserManagementForm
import io
from datetime import datetime

# Importamos el repositorio para los errores y backups
from app.infrastructure.persistence.sqlserver_repository import SqlServerBackupRepository

sistemas_bp = Blueprint('sistemas', __name__) 

# ------------------------------------------------------------------------
# 1. VISTAS PRINCIPALES DEL DASHBOARD
# ------------------------------------------------------------------------

@sistemas_bp.route('/dashboard')
@login_required
@role_required('Sistemas')
def dashboard():
    return render_template('sistemas/sistemas_inicio.html') 

@sistemas_bp.route('/auditoria')
@login_required
@role_required('Sistemas')
def auditoria():
    page = request.args.get('page', 1, type=int)
    audit_service = current_app.config['AUDIT_SERVICE']
    pagination = audit_service.get_logs(page, 20)
    audit_service.log(current_user.id, 'Auditoria', 'CONSULTA', f'El usuario consultó la página {page} de la bitácora.')
    return render_template('sistemas/auditoria.html', pagination=pagination)


# ------------------------------------------------------------------------
# 2. GESTIÓN DE USUARIOS
# ------------------------------------------------------------------------

@sistemas_bp.route('/usuarios')
@login_required
@role_required('Sistemas')
def gestionar_usuarios():
    usuario_service = current_app.config['USUARIO_SERVICE']
    usuarios = usuario_service.get_all_users_with_roles() 
    return render_template('sistemas/gestionar_usuarios.html', usuarios=usuarios)


@sistemas_bp.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
@role_required('Sistemas')
def crear_usuario():
    form = UserManagementForm() 
    try:
        repo = current_app.config['USUARIO_REPOSITORY']
        roles = repo.get_all_roles()
        form.id_rol.choices = [(r.id_rol, r.nombre_rol) for r in roles]
    except Exception as e:
        current_app.logger.warning(f"Error al cargar roles: {e}")
    
    if form.validate_on_submit():
        if not form.username.data or not form.username.data.strip():
            form.username.errors = ('El nombre de usuario es requerido.',)
            return render_template('sistemas/crear_usuario.html', form=form)
        if not form.email.data or not form.email.data.strip():
            form.email.errors = ('El correo electrónico es requerido.',)
            return render_template('sistemas/crear_usuario.html', form=form)
        if not form.password.data or not form.password.data.strip():
            form.password.errors = ('La contraseña es requerida.',)
            return render_template('sistemas/crear_usuario.html', form=form)
        if not form.id_rol.data or form.id_rol.data == 0:
            form.id_rol.errors = ('Debe seleccionar un rol.',)
            return render_template('sistemas/crear_usuario.html', form=form)
        
        try:
            usuario_service = current_app.config['USUARIO_SERVICE']
            usuario_service.create_user(form.data)
            flash('Usuario creado con éxito.', 'success')
            return redirect(url_for('sistemas.gestionar_usuarios'))
        except Exception as e:
            flash(f'Error al crear usuario: {e}', 'danger')
    return render_template('sistemas/crear_usuario.html', form=form)


@sistemas_bp.route('/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('Sistemas')
def editar_usuario(user_id):
    try:
        usuario_service = current_app.config['USUARIO_SERVICE']
        user = usuario_service.get_user_by_id_for_editing(user_id)
        if not user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('sistemas.gestionar_usuarios'))
        
        form = UserManagementForm(obj=user)
        
        if form.validate_on_submit():
            try:
                cambios_realizados = []
                cambios_fallidos = []
                
                if form.nueva_username.data:
                    resultado, categoria = usuario_service.update_username(user_id, form.nueva_username.data)
                    if categoria == 'success':
                        cambios_realizados.append('usuario')
                    else:
                        cambios_fallidos.append(resultado)
                
                if form.nuevo_email.data:
                    resultado, categoria = usuario_service.update_email(user_id, form.nuevo_email.data)
                    if categoria == 'success':
                        cambios_realizados.append('correo')
                    else:
                        cambios_fallidos.append(resultado)
                
                if form.nueva_password.data:
                    resultado, categoria = usuario_service.update_user_password(user_id, form.nueva_password.data)
                    if categoria == 'success':
                        cambios_realizados.append('contraseña')
                    else:
                        cambios_fallidos.append(resultado)
                
                if cambios_fallidos:
                    for error in cambios_fallidos:
                        flash(error, 'warning')
                
                if cambios_realizados:
                    items = ' y '.join(cambios_realizados)
                    flash(f'Se actualizaron correctamente: {items}.', 'success')
                elif not cambios_fallidos:
                    flash('No se realizaron cambios.', 'info')
                
                if cambios_realizados or cambios_fallidos:
                    return redirect(url_for('sistemas.gestionar_usuarios'))
            except Exception as e:
                current_app.logger.error(f"Error al actualizar usuario {user_id}: {e}")
                flash(f'Error al actualizar el usuario: {e}', 'danger')
        
        return render_template('sistemas/editar_usuario.html', form=form, user=user)

    except Exception as e:
        current_app.logger.error(f"ERROR EN EDITAR_USUARIO: {e}")
        flash(f"Ocurrió un error al editar el usuario. Por favor intenta de nuevo.", 'danger')
        return redirect(url_for('sistemas.gestionar_usuarios'))


@sistemas_bp.route('/usuarios/reset_password/<int:user_id>', methods=['POST'])
@login_required
@role_required('Sistemas')
def reset_password(user_id):
    try:
        usuario_service = current_app.config['USUARIO_SERVICE']
        usuario_service.reset_user_password(user_id) 
        flash('Contraseña reseteada con éxito. El usuario deberá cambiarla al iniciar sesión.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error al resetear contraseña del usuario {user_id}: {e}")
        flash('Ocurrió un error técnico al resetear la contraseña.', 'danger')
    return redirect(url_for('sistemas.gestionar_usuarios'))


# ------------------------------------------------------------------------
# 3. MANTENIMIENTO TÉCNICO Y BACKUPS
# ------------------------------------------------------------------------

@sistemas_bp.route('/mantenimiento/backups')
@login_required
@role_required('Sistemas')
def gestion_backups():
    try:
        backup_service = current_app.config['BACKUP_SERVICE']
        historial_data = backup_service.get_backup_history() 
    except Exception as e:
        current_app.logger.error(f"Error al cargar historial de backups: {e}")
        historial_data = []
    return render_template('sistemas/gestion_backups.html', historial=historial_data) 

@sistemas_bp.route('/mantenimiento/run_backup', methods=['POST'])
@login_required
@role_required('Sistemas')
def run_backup():
    try:
        if 'BACKUP_SERVICE' not in current_app.config:
            raise Exception("El servicio de backup no está inicializado.")
        current_app.config['BACKUP_SERVICE'].execute_full_backup()
        flash('Copia de seguridad iniciada y completada con éxito.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error al ejecutar backup manual: {e}")
        flash(f'Error al ejecutar la copia de seguridad. Detalle: {e}', 'danger')
    return redirect(url_for('sistemas.gestion_backups'))


@sistemas_bp.route('/mantenimiento/estado_servidor')
@login_required
@role_required('Sistemas')
def estado_servidor():
    return render_template('sistemas/estado_servidor.html')

@sistemas_bp.route('/errores')
@login_required
@role_required('Sistemas')
def errores():
    try:
        repo = SqlServerBackupRepository()
        lista_de_errores = repo.obtener_historial_errores()
        return render_template('sistemas/registro_errores.html', errores=lista_de_errores)
    except Exception as e:
        current_app.logger.error(f"No se pudo cargar el historial de errores: {e}")
        flash(f"No se pudo cargar el historial de errores: {e}", "danger")
        return render_template('sistemas/registro_errores.html', errores=[])

@sistemas_bp.route('/test-error')
@login_required
@role_required('Sistemas')
def generar_error_prueba():
    repo = SqlServerBackupRepository()
    try:
        resultado = 1 / 0
    except Exception as e:
        usuario_id = current_user.id if current_user.is_authenticated else None
        repo.registrar_error(
            modulo='sistemas.test_error', 
            descripcion=f"Error de prueba forzado: {str(e)}", 
            usuario_id=usuario_id
        )
        flash('Se ha generado y registrado un error de prueba en la bitácora.', 'info')
    return redirect(url_for('sistemas.errores'))


# ------------------------------------------------------------------------
# 4. REPORTES Y SOLICITUDES
# ------------------------------------------------------------------------

@sistemas_bp.route('/reportes')
@login_required
@role_required('Sistemas')
def reportes():
    return render_template('sistemas/reportes.html')


@sistemas_bp.route('/solicitudes')
@login_required
@role_required('Sistemas')
def solicitudes_pendientes():
    solicitudes_service = current_app.config.get('SOLICITUDES_SERVICE')
    solicitudes = solicitudes_service.get_all_pending() if solicitudes_service else []
    return render_template('sistemas/solicitudes_pendientes.html', requests=solicitudes)


@sistemas_bp.route('/solicitudes/procesar/<int:request_id>', methods=['POST'])
@login_required
@role_required('Sistemas')
def procesar_solicitud(request_id):
    action = request.form.get('action')
    if action in ['aprobar', 'rechazar']:
        solicitud_service = current_app.config['SOLICITUDES_SERVICE']
        solicitud_service.process_request(request_id, action)
        flash(f'Solicitud {action}da con éxito.', 'success')
    else:
        flash('Acción no válida.', 'danger')
    return redirect(url_for('sistemas.solicitudes_pendientes'))


# ------------------------------------------------------------------------
# 5. GESTIÓN DE DOCUMENTOS ELIMINADOS
# ------------------------------------------------------------------------

@sistemas_bp.route('/documentos/eliminados')
@login_required
@role_required('Sistemas')
def documentos_eliminados():
    """
    Vista para gestionar documentos marcados como eliminados.
    """
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        # 1. OBTENER DATOS CRUDOS
        raw_docs = legajo_service.get_deleted_documents()
        
        # 2. CONVERSIÓN EXPLÍCITA A DICCIONARIOS
        # Convertimos cada fila (Row) a un diccionario de Python puro.
        documentos_lista = [dict(row) for row in raw_docs] if raw_docs else []
        
        audit_service.log(
            current_user.id,
            'Documentos',
            'CONSULTA',
            'Consultó la lista de documentos eliminados'
        )
        
        # 3. Enviar la lista al template
        return render_template('sistemas/documentos_eliminados.html', documentos=documentos_lista)

    except Exception as e:
        current_app.logger.error(f"Error al obtener documentos eliminados: {e}")
        flash(
            '❌ Error al cargar los documentos eliminados.',
            'danger'
        )
        return redirect(url_for('sistemas.dashboard'))


@sistemas_bp.route('/documentos/recuperar/<int:documento_id>', methods=['POST'])
@login_required
@role_required('Sistemas')
def recuperar_documento(documento_id):
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        legajo_service.recover_document(documento_id)
        
        audit_service.log(
            current_user.id,
            'Documentos',
            'RECUPERAR',
            f'Recuperó el documento con ID {documento_id}'
        )
        flash('Documento recuperado exitosamente.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error al recuperar documento {documento_id}: {e}")
        flash(f'Error al recuperar el documento: {e}', 'danger')
    
    return redirect(url_for('sistemas.documentos_eliminados'))


@sistemas_bp.route('/documentos/eliminar-permanente/<int:documento_id>', methods=['POST'])
@login_required
@role_required('Sistemas')
def eliminar_documento_permanente(documento_id):
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        legajo_service.permanently_delete_document(documento_id)
        
        audit_service.log(
            current_user.id,
            'Documentos',
            'ELIMINAR PERMANENTEMENTE',
            f'Eliminó permanentemente el documento ID: {documento_id}'
        )
        flash('Documento eliminado permanentemente de la base de datos.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error al eliminar permanentemente documento {documento_id}: {e}")
        flash(f'Error al eliminar el documento: {e}', 'danger')
    
    return redirect(url_for('sistemas.documentos_eliminados'))

@sistemas_bp.route('/documentos/diagnostico')
@login_required
@role_required('Sistemas')
def documentos_eliminados_diagnostico():
    results = {'timestamp': str(datetime.now()), 'status': 'running'}
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        docs = list(legajo_service.get_deleted_documents())
        results['count'] = len(docs)
        results['first_item'] = str(docs[0]) if docs else "None"
        results['status'] = 'success'
    except Exception as e:
        results['status'] = 'error'
        results['error'] = str(e)
    return jsonify(results)