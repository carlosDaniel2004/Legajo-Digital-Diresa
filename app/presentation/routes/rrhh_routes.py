# app/presentation/routes/rrhh_routes.py

from flask import Blueprint, render_template
from flask_login import current_user
# --- INICIO DE LA CORRECCIÓN ---
from flask_login import login_required
from app.decorators import role_required
# --- FIN DE LA CORRECCIÓN ---

# Creamos el Blueprint para el rol de RRHH
# Todas las rutas definidas aquí comenzarán con /rrhh
rrhh_bp = Blueprint('rrhh', __name__, url_prefix='/rrhh')

@rrhh_bp.route('/inicio_rrhh')
@login_required
@role_required('RRHH')
def inicio_rrhh():
    """
    Dashboard principal para el rol de Recursos Humanos.
    """
    return render_template('rrhh/inicio_rrhh.html', user=current_user)



# Acontinución se tiene la funcionalidad de listar y ver legajos, solo lectura para RRHH

from flask import render_template, request, current_app, flash, redirect, url_for
from datetime import datetime
from app.application.forms import FiltroPersonalForm, DocumentoForm

@rrhh_bp.route('/personal')
@login_required
@role_required('RRHH')
def listar_personal():
    """
    Listado de legajos para RRHH (solo lectura).
    """
    form = FiltroPersonalForm(request.args)
    page = request.args.get('page', 1, type=int)
    filters = {'dni': form.dni.data, 'nombres': form.nombres.data}

    legajo_service = current_app.config['LEGAJO_SERVICE']
    pagination = legajo_service.get_all_personal_paginated(page, 15, filters)
    document_status = legajo_service.check_document_status_for_all_personal()

    return render_template(
        'rrhh/listar_personal.html',
        form=form,
        pagination=pagination,
        document_status=document_status
    )

@rrhh_bp.route('/personal/<int:personal_id>')
@login_required
@role_required('RRHH')
def ver_legajo(personal_id):
    """
    Vista de detalle de legajo para RRHH.
    """
    legajo_service = current_app.config['LEGAJO_SERVICE']
    try:
        # Se pasa current_user para cualquier validación de permisos en el servicio
        legajo_completo = legajo_service.get_personal_details(personal_id, current_user)
    except PermissionError as e:
        flash(str(e), 'danger')
        return redirect(url_for('rrhh.listar_personal'))
    except Exception as e:
        current_app.logger.error(f"Error al ver legajo {personal_id} para RRHH: {e}")
        flash("Ocurrió un error al cargar el legajo.", "danger")
        return redirect(url_for('rrhh.listar_personal'))

    if not legajo_completo or not legajo_completo.get('personal'):
        flash('El legajo solicitado no existe.', 'danger')
        return redirect(url_for('rrhh.listar_personal'))

    form_documento = DocumentoForm()
    secciones = legajo_service.get_secciones_for_select()
    form_documento.id_seccion.choices = [('0', '-- Seleccione Sección --')] + secciones if secciones else [('0', 'No hay secciones disponibles')]
    form_documento.id_tipo.choices = [('0', '-- Seleccione Tipo --')]

    return render_template(
        'rrhh/ver_legajo_completo.html',
        legajo=legajo_completo,
        form_documento=form_documento,
        legajo_service=legajo_service,
        today=datetime.now().date()
    )

# Acontinuación se tiene  la funcionalidad de descargar la lista de personal en formato Excel, simula el REPORTE

# app/presentation/routes/rrhh_routes.py
from flask import send_file
from flask import current_app, send_file

@rrhh_bp.route('/reporte/empleados/excel')
@login_required
@role_required('RRHH')
def exportar_empleados_excel():
    """Exporta la lista de empleados a un archivo Excel (solo lectura para RRHH)."""
    legajo_service = current_app.config['LEGAJO_SERVICE']  # recuperar instancia
    excel_stream = legajo_service.generate_general_report_excel()

    return send_file(
        excel_stream,
        download_name="reporte_empleados.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Acontinuacón este será el grafico de panel: Cantidad de empleados por unidad administrativa

@rrhh_bp.route('/panel')
@login_required
def panel_rrhh():
    legajo_service = current_app.config['LEGAJO_SERVICE']
    empleados_unidad = legajo_service.get_empleados_por_unidad()

    # DEBUG temporal para consola
    print("DEBUG empleados_unidad:", empleados_unidad)

    # Acontinuación se tiene: Distribución de empleados activos vs inactivos
    empleados_estado = legajo_service.get_empleados_activos_inactivos()
    print("DEBUG empleados_estado:", empleados_estado)

    # Acontinuación se tiene: Distribución de empleados segun genero
    empleados_sexo = legajo_service.get_empleados_por_sexo()

    # 👇 Aquí devolvemos la plantilla
    return render_template(
        'rrhh/panel.html',
        empleados_unidad=empleados_unidad,
        empleados_estado=empleados_estado,
        empleados_sexo=empleados_sexo
    )
