"""
Routes para que los empleados accedan y gestionen sus propios datos personales.
Cumple con la Ley 29733 de Protección de Datos Personales del Perú.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.application.forms import ActualizarPersonalForm
from app.application.services.file_validation_service import FileValidationService # Importación clave
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
        
        if rol_nombre in ['Personal', 'Empleado']: # Aceptamos ambos por flexibilidad
            return None
            
        # Si no es Personal, redirigir según su rol
        if rol_nombre == 'RRHH':
            return redirect(url_for('rrhh.inicio'))
        elif 'Admin' in rol_nombre: # Admin o SuperAdmin
            return redirect(url_for('sistemas.dashboard'))
            
        # Si no tiene rol válido o no coincide
        flash('No tienes permiso para acceder a la sección de Personal.', 'danger')
        return redirect(url_for('auth.login'))

@personal_bp.route('/inicio', methods=['GET'])
@login_required
def inicio():
    """
    Dashboard principal del empleado.
    Muestra resumen y accesos directos.
    """
    try:
        logger.info(f"INIT: Accediendo a dashboard de Personal. Usuario: {current_user.username}")
        logger.info("-" * 40)
        logger.info(f"AUDITORIA: current_user.id: {current_user.id}")
        logger.info(f"AUDITORIA: current_user.username: {current_user.username}")
        logger.info(f"AUDITORIA: current_user.rol: {current_user.rol}")
        
        # Este es el dato clave que estaba fallando:
        logger.info(f"AUDITORIA: current_user.id_personal: {getattr(current_user, 'id_personal', 'NO EXISTE')}")
        logger.info("-" * 40)



        # 💡 CORRECCIÓN UNBOUNDLOCALERROR: Inicializar la variable
        persona = None 
        
        # Verificamos si el usuario tiene un personal_id asociado
        if not getattr(current_user, 'id_personal', None):
            logger.warning(f"FLOW: Usuario {current_user.username} (ID: {current_user.id}) no tiene id_personal asociado.")
            flash('Su usuario no está vinculado a ningún legajo de personal. Contacte a RRHH.', 'warning')
            
            # 💡 CORRECCIÓN 1: Usar el template de contenido (inicio_personal.html)
            return render_template('personal/inicio_personal.html', 
                                   usuario=current_user, 
                                   persona=persona) 

        # Si tiene id_personal, procedemos a obtener los datos
        legajo_service = current_app.config['LEGAJO_SERVICE']
        personal_repo = legajo_service._personal_repo
        
        # Obtenemos la información básica de la persona
        persona = personal_repo.find_by_id(current_user.id_personal)
        
        if persona:
            logger.info(f"SUCCESS: Datos de persona encontrados. DNI: {persona.dni if hasattr(persona, 'dni') else 'N/A'}")
        else:
            logger.error(f"FAIL: No se encontró el legajo para id_personal: {current_user.id_personal}")
            flash('Error: Legajo no encontrado a pesar de tener id_personal asociado. Contacte a RRHH.', 'danger')
            
        # 💡 CORRECCIÓN 2: Usar el template de contenido (inicio_personal.html)
        return render_template('personal/inicio_personal.html', 
                             usuario=current_user, 
                             persona=persona)
                             
    except Exception as e:
        logger.error(f"FATAL: Error en dashboard personal para usuario {current_user.username}: {e}", exc_info=True)
        flash('Error al cargar el panel principal.', 'danger')
        return redirect(url_for('auth.login'))




@personal_bp.route('/mi-legajo', methods=['GET'])
@login_required
def ver_mi_legajo():
    """Vista completa del legajo (Solo Lectura)."""
    try:
        id_personal = getattr(current_user, 'id_personal', None)
        if not id_personal:
            flash('No tiene un legajo asociado.', 'warning')
            return redirect(url_for('personal.inicio'))

        legajo_service = current_app.config['LEGAJO_SERVICE']
        legajo_completo = legajo_service._personal_repo.get_full_legajo_by_id(id_personal)
        
        return render_template('personal/ver_legajo_propio.html', legajo=legajo_completo)
    except Exception as e:
        logger.error(f"Error al cargar mi legajo: {e}")
        flash('Error al cargar el legajo.', 'danger')
        return redirect(url_for('personal.inicio'))

@personal_bp.route('/actualizar-datos', methods=['GET', 'POST'])
@login_required
def actualizar_datos():
    """Formulario de rectificación de datos."""
    try:
        id_personal = getattr(current_user, 'id_personal', None)
        if not id_personal:
            return redirect(url_for('personal.inicio'))

        legajo_service = current_app.config['LEGAJO_SERVICE']
        personal_repo = legajo_service._personal_repo
        audit_service = current_app.config['AUDIT_SERVICE']
        
        persona = personal_repo.find_by_id(id_personal)
        form = ActualizarPersonalForm()

        if form.validate_on_submit():
            # Actualizar solo campos permitidos
            persona.telefono = form.telefono.data
            persona.direccion = form.direccion.data
            persona.email_personal = form.email_personal.data
            persona.estado_civil = form.estado_civil.data
            
            # Usar método específico del repo para esto
            # Si no existe 'update_personal_by_employee', usar 'update' genérico con cuidado
            if hasattr(personal_repo, 'update_personal_by_employee'):
                personal_repo.update_personal_by_employee(persona)
            else:
                # Fallback: construir diccionario para update genérico
                data = {
                    'dni': persona.dni, 'nombres': persona.nombres, 'apellidos': persona.apellidos,
                    'sexo': persona.sexo, 'fecha_nacimiento': persona.fecha_nacimiento,
                    'direccion': persona.direccion, 'telefono': persona.telefono,
                    'email': persona.email_personal, 'estado_civil': persona.estado_civil,
                    'nacionalidad': persona.nacionalidad, 'id_unidad': persona.id_unidad,
                    'fecha_ingreso': persona.fecha_ingreso
                }
                personal_repo.update(persona.id_personal, data)

            audit_service.log(current_user.id, 'Personal', 'RECTIFICACION', 'Actualización de datos propios')
            flash('Datos actualizados correctamente.', 'success')
            return redirect(url_for('personal.actualizar_datos'))

        if request.method == 'GET' and persona:
            form.telefono.data = persona.telefono
            form.direccion.data = persona.direccion
            form.email_personal.data = getattr(persona, 'email_personal', '')
            form.estado_civil.data = persona.estado_civil

        return render_template('personal/actualizar_datos.html', form=form, persona=persona)
    except Exception as e:
        logger.error(f"Error update: {e}")
        flash('Error al actualizar datos.', 'danger')
        return redirect(url_for('personal.inicio'))

@personal_bp.route('/solicitar-cancelacion', methods=['GET', 'POST'])
@login_required
def solicitar_cancelacion():
    """Formulario para solicitar cancelación."""
    audit_service = current_app.config['AUDIT_SERVICE']
    solicitud_service = current_app.config.get('SOLICITUDES_SERVICE')

    if request.method == 'POST':
        try:
            razon = request.form.get('razon', '')
            datos = request.form.getlist('datos_cancelar')
            
            if not datos:
                flash('Debe seleccionar al menos un dato a cancelar.', 'warning')
            else:
                # Aquí iría la lógica real de crear solicitud si existiera el método
                # Por ahora solo logueamos
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
    """Formulario de oposición."""
    audit_service = current_app.config['AUDIT_SERVICE']
    
    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo', '')
            tipo = request.form.get('tipo_procesamiento', '')
            
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
    """Descarga de datos en JSON (Portabilidad)."""
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        audit_service = current_app.config['AUDIT_SERVICE']
        
        id_personal = getattr(current_user, 'id_personal', None)
        if not id_personal:
            return jsonify({'error': 'No tiene legajo asociado'}), 404

        personal_repo = legajo_service._personal_repo
        persona = personal_repo.find_by_id(id_personal)
        
        if not persona:
             return jsonify({'error': 'Datos no encontrados'}), 404
        
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


@personal_bp.route('/mis-datos', methods=['GET'])
@login_required
def ver_datos_personales():
    """
    Vista de datos personales resumida (Endpoint: personal.ver_datos_personales).
    """
    try:
        if not current_user.id_personal:
            flash('No tiene un legajo asociado.', 'warning')
            return redirect(url_for('personal.inicio'))

        legajo_service = current_app.config['LEGAJO_SERVICE']
        personal_repo = legajo_service._personal_repo
        
        # 💡 CORRECCIÓN: Llamar solo a get_full_legajo_by_id para reducir el riesgo de conflicto de conexión
        legajo_completo = personal_repo.get_full_legajo_by_id(current_user.id_personal)
        
        if not legajo_completo:
            flash('Error al obtener el legajo completo.', 'danger')
            return redirect(url_for('personal.inicio'))

        # Extraer los datos básicos de la persona del resultado completo
        persona = legajo_completo.get('personal')

        logger.info(f"FLOW: Empleado {current_user.username} visualizó sus datos personales (Resumen).")
        
        # Pasamos las variables requeridas por el template
        return render_template('personal/ver_datos_personales.html', 
                               persona=persona, 
                               legajo=legajo_completo) 

    except Exception as e:
        logger.error(f"FATAL: Error al cargar mis datos personales: {e}", exc_info=True)
        flash('Ocurrió un error al cargar su información detallada.', 'danger')
        return redirect(url_for('personal.inicio'))
    
@personal_bp.route('/solicitar-cambio-documento', methods=['GET', 'POST'])
@login_required
def solicitar_cambio_documento():
    """
    Formulario para solicitar la modificación o reemplazo de un documento existente.
    """
    audit_service = current_app.config['AUDIT_SERVICE']
    legajo_service = current_app.config['LEGAJO_SERVICE']
    
    # 1. Obtener ID del documento (de la URL si es GET, o del formulario si es POST)
    documento_id = request.args.get('documento_id') or request.form.get('documento_id')
    
    # Validación básica
    if not documento_id:
        flash('Error: No se especificó el documento a modificar.', 'warning')
        return redirect(url_for('personal.ver_mi_legajo'))

    # 2. Obtener los detalles del documento de la BD
    documento = legajo_service.get_document_by_id(documento_id)
    
    if not documento:
        flash('Error: El documento solicitado no existe o no tiene permisos.', 'danger')
        return redirect(url_for('personal.ver_mi_legajo'))

    if request.method == 'POST':
        try:
            razon = request.form.get('razon', '')
            archivo_nuevo = request.files.get('archivo_nuevo') # Si vas a procesar el archivo aquí
            
            # Aquí iría la lógica real para crear la solicitud...
            # solicitud_service.crear_solicitud(...)

            audit_service.log(
                current_user.id, 'Personal', 'SOLICITUD_CAMBIO_DOC', 
                f"Solicitó cambio para documento ID: {documento_id}. Motivo: {razon}"
            )
            flash('Solicitud de cambio de documento registrada. Será revisada por RRHH.', 'success')
            return redirect(url_for('personal.inicio'))
            
        except Exception as e:
            logger.error(f"Error solicitud cambio documento: {e}", exc_info=True)
            flash('Error al procesar la solicitud.', 'danger')

    # 3. Pasar la variable 'documento' a la plantilla
    return render_template('personal/solicitar_cambio_documento.html', documento=documento)    