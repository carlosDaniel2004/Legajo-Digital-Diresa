# RUTA: app/presentation/routes/legajo_routes.py
# RUTA: app/presentation/routes/legajo_routes.py

import io
import mimetypes
import pyodbc
from flask import Blueprint, jsonify, render_template, redirect, send_file, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.decorators import role_required
from app.application.forms import PersonalForm, DocumentoForm, FiltroPersonalForm
from app.domain.models.personal import Personal
from datetime import datetime
legajo_bp = Blueprint('legajo', __name__, url_prefix='/legajo')

@legajo_bp.route('/api/tipos_documento/por_seccion/<int:id_seccion>')
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas')
def api_tipos_documento_por_seccion(id_seccion):
    """
    API endpoint para obtener los tipos de documento filtrados por sección.
    """
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        tipos = legajo_service.get_tipos_documento_by_seccion(id_seccion)
        return jsonify(tipos)
    except Exception as e:
        current_app.logger.error(f"Error en API de tipos de documento: {e}")
        return jsonify({"error": "No se pudieron cargar los datos"}), 500


# --- NUEVA RUTA API para obtener tipos de documento por sección ---
@legajo_bp.route('/api/tipos_documento/por_seccion/<int:seccion_id>', methods=['GET'])
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas') # Ajusta los roles si es necesario
def get_tipos_documento_by_seccion(seccion_id):
    legajo_service = current_app.config['LEGAJO_SERVICE']
    tipos_documento = legajo_service.get_tipos_documento_by_seccion(seccion_id)
    # Formatea la respuesta para que sea fácil de consumir por JavaScript
    return jsonify([{'id': id, 'nombre': nombre} for id, nombre in tipos_documento])

@legajo_bp.route('/dashboard')
@login_required
@role_required('AdministradorLegajos', 'RRHH')
def dashboard():
    return render_template('admin/dashboard.html', username=current_user.username)

@legajo_bp.route('/personal/<int:personal_id>')
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas')
def ver_legajo(personal_id):
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        # Seguridad: Pasar el usuario actual al servicio para la validación de permisos (IDOR).
        legajo_completo = legajo_service.get_personal_details(personal_id, current_user)
    except PermissionError as e:
        # Seguridad: Capturar el error de permiso y mostrar un mensaje claro.
        flash(str(e), 'danger')
        return redirect(url_for('legajo.listar_personal'))
    except Exception as e:
        current_app.logger.error(f"Error inesperado al ver legajo {personal_id}: {e}")
        flash("Ocurrió un error al cargar el legajo.", "danger")
        return redirect(url_for('legajo.listar_personal'))
    
    if not legajo_completo or not legajo_completo.get('personal'):
        flash('El legajo solicitado no existe.', 'danger')
        return redirect(url_for('legajo.listar_personal'))
        
    form_documento = DocumentoForm()
    # Se asegura de que la lista de opciones no esté vacía antes de añadir
    secciones = legajo_service.get_secciones_for_select()
    if secciones:
        form_documento.id_seccion.choices = [('0', '-- Seleccione Sección --')] + secciones
    else:
        form_documento.id_seccion.choices = [('0', 'No hay secciones disponibles')]

    form_documento.id_tipo.choices = [('0', '-- Seleccione Tipo --')]
    
    return render_template(
        'admin/ver_legajo_completo.html', 
        legajo=legajo_completo, 
        form_documento=form_documento,
        legajo_service=legajo_service,
        today=datetime.now().date()
    )

@legajo_bp.route('/personal')
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas')
def listar_personal():
    form = FiltroPersonalForm(request.args)
    page = request.args.get('page', 1, type=int)
    filters = {'dni': form.dni.data, 'nombres': form.nombres.data}
    
    legajo_service = current_app.config['LEGAJO_SERVICE']
    pagination = legajo_service.get_all_personal_paginated(page, 15, filters)
    
    # Nueva lógica para obtener el estado de los documentos
    document_status = legajo_service.check_document_status_for_all_personal()
    
    return render_template('admin/listar_personal.html', 
                           form=form, 
                           pagination=pagination,
                           document_status=document_status)

@legajo_bp.route('/personal/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('AdministradorLegajos')
def crear_personal():
    form = PersonalForm()
    legajo_service = current_app.config['LEGAJO_SERVICE']
    form.id_unidad.choices = [('0', '-- Seleccione Unidad --')] + legajo_service.get_unidades_for_select()
    
    if form.validate_on_submit():
        try:
            legajo_service.register_new_personal(form.data, current_user.id)
            flash('Legajo creado exitosamente.', 'success')
            return redirect(url_for('legajo.listar_personal'))
        except pyodbc.Error as db_err:
            err_msg = str(db_err)
            current_app.logger.error(f"Error de base de datos al crear legajo: {err_msg}")
            if 'DNI ya se encuentra registrado' in err_msg:
                flash('Error al crear el legajo: El DNI ingresado ya existe.', 'danger')
            elif 'correo electrónico ya está en uso' in err_msg:
                flash('Error al crear el legajo: El correo electrónico ingresado ya está en uso.', 'danger')
            else:
                flash('Ocurrió un error en la base de datos al intentar crear el legajo.', 'danger')
        except Exception as e:
            current_app.logger.error(f"Error inesperado al crear legajo: {e}")
            flash('Ocurrió un error inesperado al procesar su solicitud.', 'danger')
            
    return render_template('admin/crear_personal.html', form=form, titulo="Crear Nuevo Legajo")


@legajo_bp.route('/personal/<int:personal_id>/documento/subir', methods=['POST'])
@login_required
@role_required('AdministradorLegajos')
def subir_documento(personal_id):
    form = DocumentoForm()
    legajo_service = current_app.config['LEGAJO_SERVICE']
    form.id_seccion.choices = [('0', '-- Seleccione Sección --')] + legajo_service.get_secciones_for_select()
    form.id_tipo.choices = [('0', '-- Seleccione Tipo --')] + legajo_service.get_tipos_documento_for_select()
    
    if form.validate_on_submit():
        try:
            form_data = form.data
            form_data['id_personal'] = personal_id
            legajo_service.upload_document_to_personal(form_data, form.archivo.data, current_user.id)
            flash('Documento subido correctamente.', 'success')
        except ValueError as ve:
            # Captura errores de validación específicos del servicio (ej. tamaño de archivo)
            current_app.logger.warning(f"Error de validación al subir documento para personal {personal_id}: {ve}")
            flash(str(ve), 'danger')
        except Exception as e:
            current_app.logger.error(f"Error inesperado al subir documento para personal {personal_id}: {e}")
            flash(f'Ocurrió un error inesperado al subir el documento.', 'danger')
    else:
        # Si la validación del formulario falla, registra el error y flashea los mensajes.
        error_str = "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
        current_app.logger.warning(f"Fallo de validación al subir documento para personal {personal_id}: {error_str}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en el campo '{getattr(form, field).label.text}': {error}", 'danger')
                break # Muestra solo el primer error por campo para no saturar
    return redirect(url_for('legajo.ver_legajo', personal_id=personal_id))



@legajo_bp.route('/personal/<int:personal_id>/eliminar', methods=['POST'])
@login_required
@role_required('AdministradorLegajos')
def eliminar_personal(personal_id):
    legajo_service = current_app.config['LEGAJO_SERVICE']
    try:
        # Se intenta desactivar el legajo
        legajo_service.delete_personal_by_id(personal_id, current_user.id)
        flash('El legajo ha sido desactivado correctamente.', 'success')

    except ValueError as ve:
        # Se captura el error específico si la persona no existe
        current_app.logger.warning(f"Intento de eliminar un legajo no existente ({personal_id}): {ve}")
        # Se muestra el mensaje de error del servicio directamente al usuario
        flash(str(ve), 'warning')

    except Exception as e:
        # Se captura cualquier otro error inesperado
        current_app.logger.error(f"Error al eliminar legajo {personal_id}: {e}")
        flash(f'Ocurrió un error al desactivar el legajo: {e}', 'danger')
        
    return redirect(url_for('legajo.listar_personal'))

@legajo_bp.route('/personal/<int:personal_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('AdministradorLegajos')
def editar_personal(personal_id):
    legajo_service = current_app.config['LEGAJO_SERVICE']
    
    # Se pasa current_user para validaciones de seguridad en el servicio
    legajo_data = legajo_service.get_personal_details(personal_id, current_user)
    if not legajo_data or not legajo_data.get('personal'):
        flash('El legajo que intenta editar no existe.', 'danger')
        return redirect(url_for('legajo.listar_personal'))

    persona_data = legajo_data['personal']
    
    form = PersonalForm(data=persona_data)
    form.id_unidad.choices = [('0', '-- Seleccione Unidad --')] + legajo_service.get_unidades_for_select()
    
    if request.method == 'GET':
        form.id_unidad.data = persona_data.get('id_unidad')

    if form.validate_on_submit():
        try:
            legajo_service.update_personal_details(personal_id, form.data, current_user.id)
            flash('Legajo actualizado exitosamente.', 'success')
            return redirect(url_for('legajo.ver_legajo', personal_id=personal_id))
        except Exception as e:
            current_app.logger.error(f"Error al actualizar legajo {personal_id}: {e}")
            flash('Ocurrió un error al actualizar el legajo.', 'danger')
            
    return render_template('admin/editar_personal.html', form=form, persona=persona_data, titulo="Editar Legajo")



@legajo_bp.route('/documento/<int:documento_id>/ver')
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas')
def ver_documento(documento_id):
    """
    Gestiona la solicitud para ver un archivo en una nueva pestaña.
    Obtiene el archivo desde el servicio y lo envía al navegador para ser mostrado.
    """
    legajo_service = current_app.config['LEGAJO_SERVICE']
    try:
        document = legajo_service.get_document_for_download(documento_id)
        
        if not document or not document.get('data'):
            flash('El documento no fue encontrado o no tiene contenido adjunto.', 'danger')
            return redirect(request.referrer or url_for('legajo.listar_personal'))

        # La clave está en cambiar as_attachment a False
        return send_file(
            io.BytesIO(document['data']),
            as_attachment=False, # Importante: le dice al navegador que lo muestre
            download_name=document['filename']
        )
    except Exception as e:
        current_app.logger.error(f"Error al visualizar documento {documento_id}: {e}")
        flash('Ocurrió un error al intentar mostrar el archivo.', 'danger')
        return redirect(request.referrer or url_for('legajo.listar_personal'))
    

@legajo_bp.route('/documento/<int:documento_id>/eliminar', methods=['POST'])
@login_required
@role_required('AdministradorLegajos')
def eliminar_documento(documento_id):
    """
    Gestiona la solicitud de eliminación (lógica) de un documento.
    """
    # --- INICIO DEL CÓDIGO DE SEGUIMIENTO ---
    print(f"DEBUG: Iniciando eliminación para el documento ID: {documento_id}")
    # --- FIN DEL CÓDIGO DE SEGUIMIENTO ---
    
    legajo_service = current_app.config['LEGAJO_SERVICE']
    try:
        legajo_service.delete_document_by_id(documento_id, current_user.id)
        
        flash('Documento eliminado correctamente.', 'success')

    except Exception as e:
        current_app.logger.error(f"Error al eliminar documento {documento_id}: {e}")
    
    # Redirige al usuario a la página anterior
    print("DEBUG: Redirigiendo al usuario.")
    return redirect(request.referrer or url_for('main_dashboard'))


@legajo_bp.route('/documento/<int:documento_id>/visualizar')
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas')
def visualizar_documento(documento_id):
        """
        Gestiona la solicitud de visualización de un archivo en el navegador.
        Sirve el archivo con el mimetype adecuado para que el navegador lo muestre en línea.
        """
        legajo_service = current_app.config['LEGAJO_SERVICE']
        try:
            document = legajo_service.get_document_for_download(documento_id)
            
            if not document or not document.get('data'):
                flash('El documento no fue encontrado o no tiene contenido adjunto.', 'danger')
                return redirect(request.referrer or url_for('main_dashboard'))

            mimetype, _ = mimetypes.guess_type(document['filename'])
            if not mimetype:
                mimetype = 'application/octet-stream'

            # Lista de tipos de archivo que los navegadores pueden mostrar de forma nativa
            SAFE_INLINE_MIMETYPES = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/gif',
                'image/webp',
                'text/plain'
            ]

            # Si el tipo de archivo no es seguro para mostrar, forzamos la descarga
            should_be_attachment = mimetype not in SAFE_INLINE_MIMETYPES

            return send_file(
                io.BytesIO(document['data']),
                mimetype=mimetype,
                as_attachment=should_be_attachment, # ¡Ahora es dinámico!
                download_name=document['filename']
            )
        except Exception as e:
            current_app.logger.error(f"Error al visualizar documento {documento_id}: {e}")
            flash('Ocurrió un error al intentar visualizar el archivo.', 'danger')
            return redirect(request.referrer or url_for('main_dashboard'))    


@legajo_bp.route('/api/personal/check_dni/<string:dni>')
@login_required
def check_dni(dni):
    """
    API endpoint para verificar si un DNI ya existe.
    """
    legajo_service = current_app.config['LEGAJO_SERVICE']
    exists = legajo_service.check_if_dni_exists(dni)
    return jsonify({'exists': exists})


@legajo_bp.route('/personal/exportar/general')
@login_required
@role_required('AdministradorLegajos', 'RRHH', 'Sistemas')
def exportar_lista_general_excel():
    """
    Genera y descarga un archivo Excel con el reporte general de todo el personal.
    """
    try:
        legajo_service = current_app.config['LEGAJO_SERVICE']
        
        # Llama al método existente que genera el reporte en memoria
        excel_stream = legajo_service.generate_general_report_excel()
        
        # Registrar en auditoría
        audit_service = current_app.config['AUDIT_SERVICE']
        audit_service.log(current_user.id, 'Reportes', 'EXPORTAR_GENERAL_EXCEL', "Exportó el reporte general de personal a Excel.")

        # Enviar el archivo al usuario
        return send_file(
            excel_stream,
            as_attachment=True,
            download_name='Reporte_General_Personal.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(f"Error al exportar el reporte general a Excel: {e}")
        flash('Ocurrió un error al generar el reporte de Excel.', 'danger')
        return redirect(url_for('legajo.listar_personal'))