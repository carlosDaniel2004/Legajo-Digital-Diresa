# RUTA: app/presentation/routes/sistemas_routes.py

from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, send_file, jsonify
from flask_login import login_required, current_user
from app.decorators import role_required # Asumimos que este decorador verifica el rol
from app.application.forms import UserManagementForm # Asumimos un formulario para la gestión de usuarios
import io
from datetime import datetime

# --- IMPORTACIÓN ADICIONAL PARA LA NUEVA FUNCIONALIDAD ---
# Importamos el repositorio que puede hablar con la base de datos para los errores
from app.infrastructure.persistence.sqlserver_repository import SqlServerBackupRepository

# Blueprint para las funcionalidades exclusivas del rol de Sistemas.
sistemas_bp = Blueprint('sistemas', __name__) 

# ------------------------------------------------------------------------
# 1. VISTAS PRINCIPALES DEL DASHBOARD
# ------------------------------------------------------------------------

@sistemas_bp.route('/dashboard')
@login_required
@role_required('Sistemas')
def dashboard():
    """
    Controlador principal del Dashboard de Sistemas. 
    Muestra la vista VISUAL con tarjetas de acceso y monitoreo.
    """
    return render_template('sistemas/sistemas_inicio.html') 


@sistemas_bp.route('/auditoria')
@login_required
@role_required('Sistemas')
def auditoria():
    """
    Vista de Auditoría: Muestra la tabla de logs (el 'puro texto').
    """
    page = request.args.get('page', 1, type=int)
    audit_service = current_app.config['AUDIT_SERVICE']
    pagination = audit_service.get_logs(page, 20)
    audit_service.log(current_user.id, 'Auditoria', 'CONSULTA', f'El usuario consultó la página {page} de la bitácora.')
    return render_template('sistemas/auditoria.html', pagination=pagination)


# ------------------------------------------------------------------------
# 2. GESTIÓN DE USUARIOS (Desde la tarjeta 'Gestión de Roles y Usuarios')
# ------------------------------------------------------------------------

@sistemas_bp.route('/usuarios')
@login_required
@role_required('Sistemas')
def gestionar_usuarios():
    """
    Muestra el listado y el control de usuarios del sistema (CRUD).
    """
    usuario_service = current_app.config['USUARIO_SERVICE']
    usuarios = usuario_service.get_all_users_with_roles() 
    return render_template('sistemas/gestionar_usuarios.html', usuarios=usuarios)


@sistemas_bp.route('/usuarios/crear', methods=['GET', 'POST'])
@login_required
@role_required('Sistemas')
def crear_usuario():
    form = UserManagementForm() 
    
    # Poblar los roles en el formulario desde el repositorio
    try:
        repo = current_app.config['USUARIO_REPOSITORY']
        roles = repo.get_all_roles()
        form.id_rol.choices = [(r.id_rol, r.nombre_rol) for r in roles]
    except Exception as e:
        current_app.logger.warning(f"Error al cargar roles: {e}")
    
    if form.validate_on_submit():
        # Validaciones adicionales para creación
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
                
                # Actualizar nombre de usuario si se proporciona
                if form.nueva_username.data:
                    resultado, categoria = usuario_service.update_username(user_id, form.nueva_username.data)
                    if categoria == 'success':
                        cambios_realizados.append('usuario')
                    else:
                        cambios_fallidos.append(resultado)
                
                # Actualizar correo si se proporciona
                if form.nuevo_email.data:
                    resultado, categoria = usuario_service.update_email(user_id, form.nuevo_email.data)
                    if categoria == 'success':
                        cambios_realizados.append('correo')
                    else:
                        cambios_fallidos.append(resultado)
                
                # Actualizar contraseña si se proporciona
                if form.nueva_password.data:
                    resultado, categoria = usuario_service.update_user_password(user_id, form.nueva_password.data)
                    if categoria == 'success':
                        cambios_realizados.append('contraseña')
                    else:
                        cambios_fallidos.append(resultado)
                
                # Mostrar mensajes apropiados
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
                else:
                    # Si no hay cambios ni errores, vuelve al formulario
                    pass
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
# 3. MANTENIMIENTO TÉCNICO Y BACKUPS (Desde la tarjeta 'Monitoreo')
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

# --- MODIFICACIÓN: RUTA DE ERRORES CON LÓGICA REAL ---
@sistemas_bp.route('/errores')
@login_required
@role_required('Sistemas')
def errores():
    """
    Vista para ver el registro de errores. Ahora obtiene los datos reales de la BD.
    """
    try:
        # 1. Crea una instancia del repositorio para hablar con la BD
        repo = SqlServerBackupRepository()
        # 2. Llama a la función para obtener la lista de errores
        lista_de_errores = repo.obtener_historial_errores()
        # 3. Pasa la lista a la plantilla HTML
        return render_template('sistemas/registro_errores.html', errores=lista_de_errores)
    except Exception as e:
        # Si algo falla al obtener los errores, muestra un mensaje
        current_app.logger.error(f"No se pudo cargar el historial de errores: {e}")
        flash(f"No se pudo cargar el historial de errores: {e}", "danger")
        return render_template('sistemas/registro_errores.html', errores=[])

# --- NUEVA RUTA PARA GENERAR UN ERROR DE PRUEBA ---
@sistemas_bp.route('/test-error')
@login_required
@role_required('Sistemas')
def generar_error_prueba():
    """
    Visita esta URL para forzar un error y que se guarde en la bitácora.
    """
    repo = SqlServerBackupRepository()
    try:
        # Forzamos un error común (división por cero) para probar
        resultado = 1 / 0
    except Exception as e:
        # Obtenemos el ID del usuario actual para registrar quién causó el error
        usuario_id = current_user.id if current_user.is_authenticated else None
        
        # Usamos la función del repositorio para registrar el error en la base de datos
        repo.registrar_error(
            modulo='sistemas.test_error', 
            descripcion=f"Error de prueba forzado: {str(e)}", 
            usuario_id=usuario_id
        )
        flash('Se ha generado y registrado un error de prueba en la bitácora.', 'info')
        
    # Redirigimos de vuelta a la página de errores para ver el resultado
    return redirect(url_for('sistemas.errores'))


# ------------------------------------------------------------------------
# 4. REPORTES TÉCNICOS/AVANZADOS
# ------------------------------------------------------------------------

@sistemas_bp.route('/reportes')
@login_required
@role_required('Sistemas')
def reportes():
    return render_template('sistemas/reportes.html')


# ------------------------------------------------------------------------
# 5. SOLICITUDES PENDIENTES
# ------------------------------------------------------------------------

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
    action = request.form.get('action') # 'aprobar' o 'rechazar'
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
    Permite visualizar, recuperar o eliminar permanentemente.
    """
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        # Obtener documentos eliminados (activo = 0)
        documentos_eliminados = legajo_service.get_deleted_documents()
        
        # Si no hay documentos pero es porque falta el SP, mostrar alerta
        if not documentos_eliminados:
            flash(
                '⚠️ Nota: Para usar esta funcionalidad completamente, el DBA debe ejecutar el script ' +
                '"CREAR_SP_DOCUMENTOS_ELIMINADOS.sql" en la base de datos. ' +
                'De momento, la lista está vacía o los permisos no están asignados.',
                'warning'
            )
        
        # Registrar auditoría
        audit_service.log(
            current_user.id,
            'Documentos',
            'CONSULTA',
            'Consultó la lista de documentos eliminados'
        )
        
        return render_template('sistemas/documentos_eliminados.html', documentos=documentos_eliminados)
    except Exception as e:
        current_app.logger.error(f"Error al obtener documentos eliminados: {e}")
        flash(
            '❌ Error al cargar los documentos eliminados. ' +
            'Por favor, verifica que el DBA haya ejecutado el script de configuración.',
            'danger'
        )
        return redirect(url_for('sistemas.dashboard'))


@sistemas_bp.route('/documentos/recuperar/<int:documento_id>', methods=['POST'])
@login_required
@role_required('Sistemas')
def recuperar_documento(documento_id):
    """
    Recupera (reactiva) un documento que fue marcado como eliminado.
    """
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
    """
    Elimina permanentemente un documento (elimina el registro de la BD).
    Acción irreversible.
    """
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        # Obtener información del documento antes de eliminarlo
        documento = legajo_service.get_document_by_id(documento_id)
        
        legajo_service.permanently_delete_document(documento_id)
        
        audit_service.log(
            current_user.id,
            'Documentos',
            'ELIMINAR PERMANENTEMENTE',
            f'Eliminó permanentemente el documento {documento.nombre_archivo} (ID: {documento_id})'
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
    """
    Ruta de diagnóstico que prueba varias estrategias de acceso a documentos eliminados.
    Devuelve un JSON con el resultado de cada intento y mensajes de error si los hay.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    results = {
        'timestamp': str(__import__('datetime').datetime.now()),
        'strategies': {}
    }

    # 1) Intentar SP por get_db_read()
    try:
        from app.database.connector import get_db_read
        conn = get_db_read()
        cur = conn.cursor()
        cur.execute("{CALL sp_listar_documentos_eliminados}")
        rows = cur.fetchall()
        results['strategies']['sp_via_read'] = {'ok': True, 'count': len(rows), 'error': None}
        logger.info(f"✓ SP vía get_db_read() funcionó: {len(rows)} documentos")
    except Exception as e:
        results['strategies']['sp_via_read'] = {'ok': False, 'count': 0, 'error': str(e)}
        logger.warning(f"✗ SP vía get_db_read() falló: {e}")

    # 2) Intentar SP por get_db_write()
    try:
        from app.database.connector import get_db_write
        conn = get_db_write()
        cur = conn.cursor()
        cur.execute("{CALL sp_listar_documentos_eliminados}")
        rows = cur.fetchall()
        results['strategies']['sp_via_write'] = {'ok': True, 'count': len(rows), 'error': None}
        logger.info(f"✓ SP vía get_db_write() funcionó: {len(rows)} documentos")
    except Exception as e:
        results['strategies']['sp_via_write'] = {'ok': False, 'count': 0, 'error': str(e)}
        logger.warning(f"✗ SP vía get_db_write() falló: {e}")

    # 3) Intentar SELECT directo por get_db_write()
    try:
        conn = get_db_write()
        cur = conn.cursor()
        cur.execute("SELECT TOP 10 id_documento FROM documentos WHERE activo = 0")
        rows = cur.fetchall()
        results['strategies']['select_direct_write'] = {'ok': True, 'count': len(rows), 'error': None}
        logger.info(f"✓ SELECT directo vía get_db_write() funcionó: {len(rows)} documentos")
    except Exception as e:
        results['strategies']['select_direct_write'] = {'ok': False, 'count': 0, 'error': str(e)}
        logger.warning(f"✗ SELECT directo vía get_db_write() falló: {e}")

    # 4) Intentar el workaround (llamar al método que itera por personal)
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        deleted = legajo_service.get_deleted_documents()
        results['strategies']['workaround_method'] = {'ok': True, 'count': len(deleted), 'error': None}
        logger.info(f"✓ Workaround (iteración) funcionó: {len(deleted)} documentos")
    except Exception as e:
        results['strategies']['workaround_method'] = {'ok': False, 'count': 0, 'error': str(e)}
        logger.warning(f"✗ Workaround (iteración) falló: {e}")

    # Registrar auditoría del diagnóstico
    try:
        audit_service = current_app.config.get('AUDIT_SERVICE')
        if audit_service:
            audit_service.log(current_user.id, 'Documentos', 'DIAGNOSTICO', 'Ejecutó diagnóstico de documentos eliminados')
    except Exception:
        pass

    return jsonify(results)


