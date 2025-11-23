# app/presentation/routes/personal_routes.py
"""
Routes para que los empleados accedan y gestionen sus propios datos personales.
Cumple con la Ley 29733 de Protección de Datos Personales del Perú.

Derechos reconocidos en la Ley 29733:
- Acceso a datos personales
- Rectificación de datos inexactos
- Cancelación de datos
- Oposición al procesamiento
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.application.forms import PersonalForm, ActualizarPersonalForm
from app.domain.models.personal import Personal
import logging

personal_bp = Blueprint('personal', __name__, url_prefix='/mi-legajo')
logger = logging.getLogger(__name__)


@personal_bp.before_request
def check_personal_role():
    """Verifica que el usuario tenga rol 'Personal' para acceder a estas rutas."""
    if current_user.is_authenticated and current_user.rol != 'Personal':
        flash('No tienes permiso para acceder a esta sección.', 'danger')
        return redirect(url_for('main.dashboard'))


@personal_bp.route('/inicio', methods=['GET'])
@login_required
def inicio_personal():
    """
    Página de inicio para usuarios con rol Personal.
    Muestra acceso directo a su legajo personal.
    """
    usuario_service = current_app.config['USUARIO_SERVICE']
    legajo_service = current_app.config['LEGAJO_SERVICE']
    
    try:
        # Obtener datos del usuario actual
        usuario = usuario_service._usuario_repo.find_by_id(current_user.id)
        
        # Obtener legajo personal asociado al usuario
        personal_repo = legajo_service._personal_repo
        persona = None
        
        # Buscar por id_personal si existe
        if hasattr(usuario, 'id_personal') and usuario.id_personal:
            try:
                persona = personal_repo.find_by_id(usuario.id_personal)
            except Exception as e:
                logger.warning(f"Error buscando personal por id: {e}")
        
        return render_template('personal/inicio_personal.html', 
                             usuario=usuario, 
                             persona=persona)
    except Exception as e:
        logger.error(f"Error en inicio_personal: {e}")
        flash('Error al cargar la página de inicio.', 'danger')
        return redirect(url_for('auth.logout'))


@personal_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    Dashboard del empleado con acceso a su legajo personal.
    Cumple con Art. 8 de Ley 29733: Derecho de acceso a datos personales.
    """
    usuario_service = current_app.config['USUARIO_SERVICE']
    legajo_service = current_app.config['LEGAJO_SERVICE']
    
    try:
        # Obtener datos del usuario
        usuario = usuario_service._usuario_repo.find_by_id(current_user.id)
        
        # Obtener legajo personal del usuario
        personal_repo = legajo_service._personal_repo
        persona = None
        
        # Buscar por id_personal si existe
        if hasattr(usuario, 'id_personal') and usuario.id_personal:
            try:
                persona = personal_repo.find_by_id(usuario.id_personal)
            except Exception as e:
                logger.warning(f"Error buscando personal por id: {e}")
        
        if not persona:
            flash('No se encontró tu legajo personal. Por favor contacta a RRHH.', 'warning')
            return redirect(url_for('personal.inicio_personal'))
        
        # Obtener datos completos del legajo
        legajo_completo = personal_repo.get_full_legajo_by_id(persona.id)
        
        logger.info(f"Empleado {current_user.username} accedió a su legajo personal (ID: {persona.id})")
        
        return render_template(
            'personal/dashboard.html',
            usuario=usuario,
            persona=persona,
            legajo=legajo_completo,
            titulo='Mi Legajo Personal'
        )
    
    except Exception as e:
        logger.error(f"Error al cargar dashboard del empleado: {str(e)}", exc_info=True)
        flash('Error al cargar tu legajo personal.', 'danger')
        return redirect(url_for('personal.inicio_personal'))


@personal_bp.route('/datos-personales', methods=['GET'])
@login_required
def ver_datos_personales():
    """
    Visualización de datos personales del empleado.
    Cumple con Art. 8 Ley 29733: Derecho de acceso.
    """
    usuario_service = current_app.config['USUARIO_SERVICE']
    legajo_service = current_app.config['LEGAJO_SERVICE']
    
    try:
        usuario = usuario_service._usuario_repo.find_by_id(current_user.id)
        personal_repo = legajo_service._personal_repo
        persona = None
        
        # Buscar por id_personal si existe
        if usuario and hasattr(usuario, 'id_personal') and usuario.id_personal:
            try:
                persona = personal_repo.find_by_id(usuario.id_personal)
            except Exception as e:
                logger.warning(f"Error buscando personal por id {usuario.id_personal}: {e}")
        
        if not persona:
            flash('Legajo no encontrado. Por favor contacta a RRHH.', 'warning')
            return redirect(url_for('personal.inicio_personal'))
        
        # Obtener todos los datos del legajo
        try:
            legajo = personal_repo.get_full_legajo_by_id(persona.id)
        except Exception as e:
            logger.warning(f"Error obteniendo legajo completo: {e}")
            legajo = None
        
        logger.info(f"Empleado {current_user.username} consultó sus datos personales")
        
        return render_template(
            'personal/ver_datos_personales.html',
            persona=persona,
            legajo=legajo,
            titulo='Mis Datos Personales'
        )
    
    except Exception as e:
        logger.error(f"Error al obtener datos personales: {str(e)}", exc_info=True)
        flash('Error al obtener tus datos personales.', 'danger')
        return redirect(url_for('personal.inicio_personal'))


@personal_bp.route('/actualizar-datos', methods=['GET', 'POST'])
@login_required
def actualizar_datos():
    """
    Formulario para que el empleado rectifique sus datos personales.
    Cumple con Art. 9 Ley 29733: Derecho de rectificación.
    
    Permite modificar:
    - Datos de contacto (teléfono, email personal)
    - Información familiar (estado civil, dependientes)
    - Datos educativos (no críticos)
    - Información de salud autorizada
    """
    usuario_service = current_app.config['USUARIO_SERVICE']
    legajo_service = current_app.config['LEGAJO_SERVICE']
    audit_service = current_app.config['AUDIT_SERVICE']
    
    try:
        usuario = usuario_service._usuario_repo.find_by_id(current_user.id)
        personal_repo = legajo_service._personal_repo
        persona = None
        
        # Buscar por id_personal si existe
        if hasattr(usuario, 'id_personal') and usuario.id_personal:
            try:
                persona = personal_repo.find_by_id(usuario.id_personal)
            except Exception as e:
                logger.warning(f"Error buscando personal por id: {e}")
        
        if not persona:
            flash('Legajo no encontrado.', 'danger')
            return redirect(url_for('personal.dashboard'))
        
        form = ActualizarPersonalForm()
        
        if form.validate_on_submit():
            try:
                # Registrar cambios para auditoría (según Ley 29733)
                cambios_realizados = []
                
                # Actualizar datos permitidos al empleado
                if form.telefono.data and form.telefono.data != persona.telefono:
                    cambios_realizados.append(f"Teléfono: {persona.telefono} → {form.telefono.data}")
                    persona.telefono = form.telefono.data
                
                if form.estado_civil.data and form.estado_civil.data != persona.estado_civil:
                    cambios_realizados.append(f"Estado civil: {persona.estado_civil} → {form.estado_civil.data}")
                    persona.estado_civil = form.estado_civil.data
                
                if form.email_personal.data and form.email_personal.data != (persona.email_personal if hasattr(persona, 'email_personal') else ''):
                    cambios_realizados.append(f"Email personal actualizado")
                    persona.email_personal = form.email_personal.data
                
                if form.direccion.data and form.direccion.data != persona.direccion:
                    cambios_realizados.append(f"Dirección actualizada")
                    persona.direccion = form.direccion.data
                
                # Guardar cambios
                personal_repo.update_personal_by_employee(persona)
                
                # Auditar el cambio (Art. 14 Ley 29733 - Responsabilidades del titular)
                audit_service.log(
                    current_user.id,
                    'PersonalData',
                    'RECTIFICACION_DATOS',
                    f"Empleado rectificó sus datos personales: {'; '.join(cambios_realizados)}"
                )
                
                logger.info(f"Empleado {current_user.username} actualizó sus datos: {'; '.join(cambios_realizados)}")
                flash('Tus datos han sido actualizados exitosamente.', 'success')
                
                return redirect(url_for('personal.ver_datos_personales'))
            
            except Exception as e:
                logger.error(f"Error al actualizar datos del empleado: {str(e)}", exc_info=True)
                flash(f'Error al actualizar tus datos: {str(e)}', 'danger')
        
        else:
            # Pre-llenar formulario con datos existentes
            form.telefono.data = persona.telefono if hasattr(persona, 'telefono') else ''
            form.estado_civil.data = persona.estado_civil if hasattr(persona, 'estado_civil') else ''
            form.email_personal.data = persona.email_personal if hasattr(persona, 'email_personal') else ''
            form.direccion.data = persona.direccion if hasattr(persona, 'direccion') else ''
        
        return render_template(
            'personal/actualizar_datos.html',
            form=form,
            persona=persona,
            titulo='Actualizar Mis Datos'
        )
    
    except Exception as e:
        logger.error(f"Error en formulario de actualización: {str(e)}", exc_info=True)
        flash('Error al procesar el formulario.', 'danger')
        return redirect(url_for('personal.dashboard'))


@personal_bp.route('/solicitar-cancelacion', methods=['GET', 'POST'])
@login_required
def solicitar_cancelacion():
    """
    Formulario para solicitar la cancelación de datos personales.
    Cumple con Art. 10 Ley 29733: Derecho de cancelación.
    
    Nota: Esta es una solicitud formal que requiere aprobación de RRHH.
    No se elimina información crítica para nómina/contabilidad.
    """
    audit_service = current_app.config['AUDIT_SERVICE']
    solicitud_service = current_app.config.get('SOLICITUDES_SERVICE')
    
    if request.method == 'POST':
        try:
            razon = request.form.get('razon', '')
            datos_a_cancelar = request.form.getlist('datos_cancelar')
            
            if not datos_a_cancelar:
                flash('Debes seleccionar al menos un tipo de dato.', 'warning')
            else:
                # Crear solicitud formal
                solicitud_data = {
                    'tipo': 'CANCELACION_DATOS',
                    'solicitante_id': current_user.id,
                    'descripcion': f"Solicitud de cancelación de datos: {', '.join(datos_a_cancelar)}. Razón: {razon}",
                    'estado': 'PENDIENTE'
                }
                
                if solicitud_service:
                    solicitud_service.crear_solicitud(solicitud_data)
                
                # Auditar solicitud
                audit_service.log(
                    current_user.id,
                    'PersonalData',
                    'SOLICITUD_CANCELACION',
                    f"Empleado solicitó cancelación de datos: {', '.join(datos_a_cancelar)}"
                )
                
                logger.info(f"Empleado {current_user.username} solicitó cancelación de datos personales")
                flash('Tu solicitud de cancelación ha sido registrada. RRHH la procesará en 5 días hábiles.', 'success')
                
                return redirect(url_for('personal.dashboard'))
        
        except Exception as e:
            logger.error(f"Error al procesar solicitud de cancelación: {str(e)}", exc_info=True)
            flash('Error al procesar tu solicitud.', 'danger')
    
    return render_template(
        'personal/solicitar_cancelacion.html',
        titulo='Solicitar Cancelación de Datos'
    )


@personal_bp.route('/derecho-oposicion', methods=['GET', 'POST'])
@login_required
def derecho_oposicion():
    """
    Formulario para ejercer el derecho de oposición al procesamiento de datos.
    Cumple con Art. 11 Ley 29733: Derecho de oposición.
    """
    audit_service = current_app.config['AUDIT_SERVICE']
    solicitud_service = current_app.config.get('SOLICITUDES_SERVICE')
    
    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo', '')
            tipo_procesamiento = request.form.get('tipo_procesamiento', '')
            
            # Crear solicitud de oposición
            solicitud_data = {
                'tipo': 'OPOSICION_PROCESAMIENTO',
                'solicitante_id': current_user.id,
                'descripcion': f"Oposición al procesamiento de {tipo_procesamiento}. Motivo: {motivo}",
                'estado': 'PENDIENTE'
            }
            
            if solicitud_service:
                solicitud_service.crear_solicitud(solicitud_data)
            
            audit_service.log(
                current_user.id,
                'PersonalData',
                'DERECHO_OPOSICION',
                f"Empleado ejerció derecho de oposición: {tipo_procesamiento}"
            )
            
            logger.info(f"Empleado {current_user.username} ejerció derecho de oposición")
            flash('Tu solicitud de oposición ha sido registrada.', 'success')
            
            return redirect(url_for('personal.dashboard'))
        
        except Exception as e:
            logger.error(f"Error al procesar derecho de oposición: {str(e)}", exc_info=True)
            flash('Error al procesar tu solicitud.', 'danger')
    
    return render_template(
        'personal/derecho_oposicion.html',
        titulo='Derecho de Oposición'
    )


@personal_bp.route('/descargar-datos', methods=['GET'])
@login_required
def descargar_datos():
    """
    Permite al empleado descargar sus datos en formato estructurado (portabilidad).
    Cumple con Art. 22 Ley 29733 (relacionado) - Acceso a datos propios.
    """
    usuario_service = current_app.config['USUARIO_SERVICE']
    legajo_service = current_app.config['LEGAJO_SERVICE']
    
    try:
        usuario = usuario_service._usuario_repo.find_by_id(current_user.id)
        personal_repo = legajo_service._personal_repo
        persona = None
        
        # Buscar por id_personal si existe
        if hasattr(usuario, 'id_personal') and usuario.id_personal:
            try:
                persona = personal_repo.find_by_id(usuario.id_personal)
            except Exception as e:
                logger.warning(f"Error buscando personal por id: {e}")
        
        if not persona:
            return jsonify({'error': 'Legajo no encontrado'}), 404
        
        legajo = personal_repo.get_full_legajo_by_id(persona.id)
        
        # Compilar todos los datos del legajo
        datos_personales = {
            'usuario': {
                'username': usuario.username,
                'email': usuario.email,
                'rol': usuario.rol,
                'fecha_creacion': str(usuario.fecha_creacion) if hasattr(usuario, 'fecha_creacion') else ''
            },
            'personal': {
                'id': persona.id,
                'nombres': persona.nombres if hasattr(persona, 'nombres') else '',
                'apellidos': persona.apellidos if hasattr(persona, 'apellidos') else '',
                'dni': persona.dni,
                'fecha_nacimiento': str(persona.fecha_nacimiento) if hasattr(persona, 'fecha_nacimiento') else '',
                'estado_civil': persona.estado_civil if hasattr(persona, 'estado_civil') else '',
                'telefono': persona.telefono if hasattr(persona, 'telefono') else '',
                'direccion': persona.direccion if hasattr(persona, 'direccion') else '',
                'email_personal': persona.email_personal if hasattr(persona, 'email_personal') else ''
            }
        }
        
        audit_service = current_app.config['AUDIT_SERVICE']
        audit_service.log(
            current_user.id,
            'PersonalData',
            'DESCARGAR_DATOS',
            f"Empleado descargó copia de sus datos personales"
        )
        
        logger.info(f"Empleado {current_user.username} descargó sus datos personales")
        
        return jsonify(datos_personales)
    
    except Exception as e:
        logger.error(f"Error al descargar datos: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error al descargar datos'}), 500
