"""
Routes para que los empleados accedan y gestionen sus propios datos personales.
Cumple con la Ley 29733 de Protección de Datos Personales del Perú.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.application.forms import ActualizarPersonalForm
import logging

# Definición del Blueprint
personal_bp = Blueprint('personal', __name__, url_prefix='/personal')
logger = logging.getLogger(__name__)

@personal_bp.before_request
def check_personal_role():
    """Verifica que el usuario tenga rol 'Personal' para acceder a estas rutas."""
    if current_user.is_authenticated:
        # Se verifica de forma flexible (por nombre de rol o ID si fuera necesario)
        rol_nombre = current_user.rol if hasattr(current_user, 'rol') else ''
        if rol_nombre != 'Personal':
            flash('No tienes permiso para acceder a la sección de Personal.', 'danger')
            # Si es admin o RRHH, lo manda a su dashboard correspondiente, si no al login
            if rol_nombre == 'RRHH':
                return redirect(url_for('rrhh.inicio'))
            elif 'Admin' in rol_nombre:
                return redirect(url_for('sistemas.dashboard'))
            return redirect(url_for('auth.login'))

@personal_bp.route('/inicio', methods=['GET'])
@login_required
def inicio():
    """
    Dashboard principal del empleado.
    Muestra resumen y accesos directos.
    """
    try:
        usuario_service = current_app.config['USUARIO_SERVICE']
        legajo_service = current_app.config['LEGAJO_SERVICE']

        # Verificamos si el usuario tiene un personal_id asociado
        if not current_user.id_personal:
            flash('Su usuario no está vinculado a ningún legajo de personal. Contacte a RRHH.', 'warning')
            return render_template('personal/dashboard.html', persona=None)

        # Obtenemos la información básica de la persona
        personal_repo = legajo_service._personal_repo
        persona = personal_repo.find_by_id(current_user.id_personal)
        
        return render_template('personal/dashboard.html', 
                             usuario=current_user, 
                             persona=persona)
    except Exception as e:
        logger.error(f"Error en dashboard personal: {e}")
        flash('Error al cargar el panel principal.', 'danger')
        return redirect(url_for('auth.login'))

@personal_bp.route('/mi-legajo', methods=['GET'])
@login_required
def ver_mi_legajo():
    """
    Vista completa del legajo (Solo Lectura).
    Cumple con Art. 8 de Ley 29733: Derecho de acceso.
    """
    try:
        if not current_user.id_personal:
            flash('No tiene un legajo asociado.', 'warning')
            return redirect(url_for('personal.inicio'))

        legajo_service = current_app.config['LEGAJO_SERVICE']
        
        # get_full_legajo_by_id devuelve un objeto/diccionario con todas las listas
        legajo_completo = legajo_service._personal_repo.get_full_legajo_by_id(current_user.id_personal)
        
        logger.info(f"Empleado {current_user.username} visualizó su legajo completo.")
        
        return render_template('personal/ver_legajo_propio.html', legajo=legajo_completo)

    except Exception as e:
        logger.error(f"Error al cargar mi legajo: {e}", exc_info=True)
        flash('Ocurrió un error al cargar su información detallada.', 'danger')
        return redirect(url_for('personal.inicio'))

@personal_bp.route('/actualizar-datos', methods=['GET', 'POST'])
@login_required
def actualizar_datos():
    """
    Formulario de rectificación de datos (Art. 9 Ley 29733).
    """
    try:
        if not current_user.id_personal:
            return redirect(url_for('personal.inicio'))

        legajo_service = current_app.config['LEGAJO_SERVICE']
        personal_repo = legajo_service._personal_repo
        audit_service = current_app.config['AUDIT_SERVICE']
        
        persona = personal_repo.find_by_id(current_user.id_personal)
        form = ActualizarPersonalForm()

        if form.validate_on_submit():
            # Registrar cambios para auditoría
            cambios = []
            if persona.telefono != form.telefono.data:
                cambios.append(f"Teléfono: {persona.telefono} -> {form.telefono.data}")
                persona.telefono = form.telefono.data
            
            if persona.direccion != form.direccion.data:
                cambios.append("Dirección actualizada")
                persona.direccion = form.direccion.data

            if getattr(persona, 'email_personal', '') != form.email_personal.data:
                cambios.append("Email personal actualizado")
                persona.email_personal = form.email_personal.data

            if persona.estado_civil != form.estado_civil.data:
                cambios.append(f"Estado Civil: {persona.estado_civil} -> {form.estado_civil.data}")
                persona.estado_civil = form.estado_civil.data
            
            if cambios:
                personal_repo.update_personal_by_employee(persona)
                
                # Auditoría
                audit_service.log(
                    current_user.id, 'Personal', 'RECTIFICACION', 
                    f"Usuario {current_user.username} actualizó: {', '.join(cambios)}"
                )
                flash('Sus datos han sido actualizados correctamente.', 'success')
            else:
                flash('No se detectaron cambios.', 'info')
                
            return redirect(url_for('personal.actualizar_datos'))

        # Pre-llenar formulario con datos actuales
        if request.method == 'GET':
            form.telefono.data = persona.telefono
            form.direccion.data = persona.direccion
            form.email_personal.data = getattr(persona, 'email_personal', '')
            form.estado_civil.data = persona.estado_civil

        return render_template('personal/actualizar_datos.html', form=form, persona=persona)

    except Exception as e:
        logger.error(f"Error en actualizar datos: {e}")
        flash('Error al procesar la solicitud.', 'danger')
        return redirect(url_for('personal.inicio'))

@personal_bp.route('/solicitar-cancelacion', methods=['GET', 'POST'])
@login_required
def solicitar_cancelacion():
    """
    Formulario para solicitar cancelación (Art. 10 Ley 29733).
    """
    audit_service = current_app.config['AUDIT_SERVICE']
    solicitud_service = current_app.config.get('SOLICITUDES_SERVICE')

    if request.method == 'POST':
        try:
            razon = request.form.get('razon', '')
            datos = request.form.getlist('datos_cancelar')
            
            if not datos:
                flash('Debe seleccionar al menos un dato a cancelar.', 'warning')
            else:
                if solicitud_service:
                    solicitud_service.crear_solicitud({
                        'tipo': 'CANCELACION_DATOS',
                        'solicitante_id': current_user.id,
                        'descripcion': f"Solicita cancelar: {', '.join(datos)}. Motivo: {razon}",
                        'estado': 'PENDIENTE'
                    })
                
                audit_service.log(current_user.id, 'PersonalData', 'SOLICITUD_CANCELACION', f"Solicitó cancelar: {', '.join(datos)}")
                flash('Solicitud registrada. RRHH responderá en 5 días hábiles.', 'success')
                return redirect(url_for('personal.inicio'))
        
        except Exception as e:
            logger.error(f"Error solicitud cancelacion: {e}")
            flash('Error al procesar la solicitud.', 'danger')

    return render_template('personal/solicitar_cancelacion.html')

@personal_bp.route('/derecho-oposicion', methods=['GET', 'POST'])
@login_required
def derecho_oposicion():
    """
    Formulario de oposición (Art. 11 Ley 29733).
    """
    audit_service = current_app.config['AUDIT_SERVICE']
    solicitud_service = current_app.config.get('SOLICITUDES_SERVICE')

    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo', '')
            tipo = request.form.get('tipo_procesamiento', '')
            
            if solicitud_service:
                solicitud_service.crear_solicitud({
                    'tipo': 'OPOSICION',
                    'solicitante_id': current_user.id,
                    'descripcion': f"Oposición a: {tipo}. Motivo: {motivo}",
                    'estado': 'PENDIENTE'
                })
            
            audit_service.log(current_user.id, 'PersonalData', 'OPOSICION', f"Oposición a {tipo}")
            flash('Solicitud de oposición registrada.', 'success')
            return redirect(url_for('personal.inicio'))
            
        except Exception as e:
            logger.error(f"Error oposicion: {e}")
            flash('Error al procesar.', 'danger')

    return render_template('personal/derecho_oposicion.html')

@personal_bp.route('/descargar-datos', methods=['GET'])
@login_required
def descargar_datos():
    """
    Descarga de datos en JSON (Portabilidad).
    """
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        if not current_user.id_personal:
            return jsonify({'error': 'No tiene legajo asociado'}), 404

        # Obtener datos
        personal_repo = legajo_service._personal_repo
        persona = personal_repo.find_by_id(current_user.id_personal)
        
        datos = {
            'usuario': {'username': current_user.username, 'email': current_user.email},
            'personal': {
                'nombres': persona.nombres,
                'apellidos': persona.apellidos,
                'dni': persona.dni,
                'telefono': persona.telefono,
                'direccion': persona.direccion
            },
            'nota': 'Este archivo contiene sus datos personales registrados.'
        }

        audit_service.log(current_user.id, 'PersonalData', 'DESCARGA', 'Descargó sus datos personales')
        return jsonify(datos)

    except Exception as e:
        logger.error(f"Error descarga: {e}")
        return jsonify({'error': 'Error interno'}), 500