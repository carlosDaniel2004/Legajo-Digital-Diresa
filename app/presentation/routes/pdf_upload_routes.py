# app/presentation/routes/pdf_upload_routes.py
"""
Rutas para carga masiva y separación de PDFs de legajos.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.application.services.pdf_split_service import PdfSplitService
from app.core.security import IDORProtection
from werkzeug.utils import secure_filename
import os
import logging

logger = logging.getLogger(__name__)

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')


@pdf_bp.route('/api/debug', methods=['GET'])
@login_required
def debug_info():
    """
    Endpoint de debugging para verificar estado de servicios
    """
    return jsonify({
        'user': current_user.username,
        'rol': current_user.rol,
        'legajo_service': 'OK' if current_app.config.get('LEGAJO_SERVICE') else 'MISSING',
        'personal_repository': 'OK' if current_app.config.get('PERSONAL_REPOSITORY') else 'MISSING',
    })


@pdf_bp.route('/api/personal-list', methods=['GET'])
@login_required
def get_personal_list():
    """
    API endpoint que retorna lista de personal disponible para asociar al PDF.
    Retorna JSON con estructura: [{'id': ..., 'nombre': '...', 'dni': '...'}]
    """
    try:
        from app.database.connector import get_db_read
        from app.infrastructure.persistence.sqlserver_repository import _row_to_dict
        
        # Obtener conexión directa para consulta simple
        conn = get_db_read()
        cursor = conn.cursor()
        
        # Consulta SQL simple para traer personal activo
        query = """
            SELECT 
                id_personal,
                nombres,
                apellidos,
                dni
            FROM personal
            WHERE activo = 1
            ORDER BY apellidos, nombres
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            logger.info(f"Lista de personal vacía para usuario: {current_user.username}")
            return jsonify([])
        
        # Formatear para el frontend
        result = []
        for row in rows:
            try:
                row_dict = _row_to_dict(cursor, row)
                
                p_id = row_dict.get('id_personal')
                p_nombres = row_dict.get('nombres', '')
                p_apellidos = row_dict.get('apellidos', '')
                p_dni = row_dict.get('dni', 'N/A')
                
                nombre_completo = f"{p_apellidos}, {p_nombres}".strip() if p_apellidos and p_nombres else p_nombres
                
                item = {
                    'id': p_id,
                    'nombre': nombre_completo if nombre_completo else 'N/A',
                    'dni': p_dni if p_dni else 'N/A'
                }
                
                if item['id']:  # Solo agregar si tiene ID válido
                    result.append(item)
                    
            except Exception as item_err:
                logger.warning(f"Error procesando personal: {item_err}")
                continue
        
        logger.info(f"Retornando {len(result)} personal para carga de PDF (usuario: {current_user.username})")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo lista de personal: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@pdf_bp.route('/api/estructura-personal/<int:id_personal>', methods=['GET'])
@login_required
def get_estructura_personal(id_personal):
    """
    API endpoint que retorna la estructura de legajo personalizada para un personal.
    Primero intenta obtener estructura personalizada, si no existe retorna la por defecto.
    Retorna JSON con estructura: {'estructura': {'nombre_doc': [pagina_inicio, pagina_fin], ...}}
    """
    try:
        personal_repo = current_app.config.get('PERSONAL_REPOSITORY')
        
        if not personal_repo:
            # Retornar estructura por defecto si no hay repositorio
            return jsonify({'estructura': ESTRUCTURA_LEGAJO_DEFAULT})
        
        # Intentar obtener estructura personalizada si existe el método
        estructura_personalizada = None
        if hasattr(personal_repo, 'get_estructura_legajo'):
            try:
                estructura_personalizada = personal_repo.get_estructura_legajo(id_personal)
            except Exception as e:
                logger.warning(f"No se pudo obtener estructura personalizada: {e}")
        
        if estructura_personalizada:
            logger.info(f"Usando estructura personalizada para personal {id_personal}")
            return jsonify({'estructura': estructura_personalizada})
        else:
            logger.info(f"Usando estructura por defecto para personal {id_personal}")
            return jsonify({'estructura': ESTRUCTURA_LEGAJO_DEFAULT})
        
    except Exception as e:
        logger.error(f"Error obteniendo estructura de personal: {e}", exc_info=True)
        # Retornar estructura por defecto en caso de error
        return jsonify({'estructura': ESTRUCTURA_LEGAJO_DEFAULT})


# Estructura por defecto para legajos
ESTRUCTURA_LEGAJO_DEFAULT = {
    "01_DNI": {
        "tipo_documento": "DNI",
        "descripcion": "Cédula de Identidad",
        "pagina_inicio": 1,
        "pagina_fin": 1,
    },
    "02_Curriculum": {
        "tipo_documento": "Curriculum",
        "descripcion": "Currículum Vitae",
        "pagina_inicio": 2,
        "pagina_fin": 5,
    },
    "03_Titulo_Universitario": {
        "tipo_documento": "Titulo",
        "descripcion": "Título Universitario",
        "pagina_inicio": 6,
        "pagina_fin": 6,
    },
    "04_Contrato_Laboral": {
        "tipo_documento": "Contrato",
        "descripcion": "Contrato Laboral",
        "pagina_inicio": 7,
        "pagina_fin": 12,
    },
    "05_Antecedentes_Penales": {
        "tipo_documento": "Antecedentes",
        "descripcion": "Antecedentes Penales",
        "pagina_inicio": 13,
        "pagina_fin": 14,
    },
    "06_Carnet_Sanitario": {
        "tipo_documento": "Carnet",
        "descripcion": "Carnet Sanitario",
        "pagina_inicio": 15,
        "pagina_fin": 15,
    },
    "07_Licencias": {
        "tipo_documento": "Licencias",
        "descripcion": "Licencias Profesionales",
        "pagina_inicio": 16,
        "pagina_fin": 20,
    },
}


@pdf_bp.route('/upload', methods=['GET', 'POST'])
@pdf_bp.route('/upload/<int:personal_id>', methods=['GET', 'POST'])
@login_required
def upload_legajo_pdf(personal_id=None):
    """
    Permite cargar un PDF completo de legajo y separarlo automáticamente
    en documentos individuales, asociándolos a un personal específico.
    
    Solo accesible desde la página del legajo con personal_id preseleccionado.
    Si se intenta acceder sin personal_id, redirije a "Consultar Legajo".
    
    Flujo:
    1. Usuario accede desde la página del legajo (con personal_id en URL)
    2. Carga el PDF del legajo completo
    3. Sistema separa el PDF según estructura predefinida
    4. Cada documento se guarda en la sección correspondiente del personal
    """
    # Solo AdministradorLegajos y Sistemas pueden hacer esto
    if current_user.rol not in ('AdministradorLegajos', 'Sistemas'):
        flash('No tienes permiso para acceder a esta función.', 'danger')
        return redirect(url_for('rrhh.inicio_rrhh'))

    # Si intenta acceder sin personal_id, redirije a "Consultar Legajo"
    if not personal_id:
        flash('Accede a esta función desde la página del legajo.', 'info')
        return redirect(url_for('legajo.listar_personal'))
    
    # SEGURIDAD: Validar IDOR - Verificar que el usuario tenga permiso para acceder a este personal
    if not IDORProtection.can_access_personal(current_user.id, personal_id, current_user.rol):
        logger.warning(f"SEGURIDAD: Intento IDOR detectado - Usuario {current_user.id} intenta acceder a personal {personal_id}")
        flash('No tienes permiso para acceder a este personal.', 'danger')
        return redirect(url_for('legajo.listar_personal'))

    legajo_service = current_app.config.get('LEGAJO_SERVICE')
    personal_repo = current_app.config.get('PERSONAL_REPOSITORY')

    if request.method == 'POST':
        try:
            # Verificar que se envió un archivo
            if 'archivo_pdf' not in request.files:
                flash('No se seleccionó ningún archivo.', 'warning')
                return redirect(request.url)

            file = request.files['archivo_pdf']
            if file.filename == '':
                flash('No se seleccionó ningún archivo.', 'warning')
                return redirect(request.url)

            # Obtener el ID del personal desde la URL (ya validado en los parámetros de la ruta)
            id_personal = personal_id
            if not id_personal:
                flash('Debes seleccionar un personal.', 'warning')
                return redirect(request.url)

            # Validar que sea un PDF
            if not file.filename.lower().endswith('.pdf'):
                flash('Solo se aceptan archivos PDF.', 'danger')
                return redirect(request.url)

            # Guardar el archivo temporalmente
            filename = secure_filename(file.filename)
            temp_path = os.path.join('temp_uploads', filename)
            os.makedirs('temp_uploads', exist_ok=True)
            file.save(temp_path)

            logger.info(f"PDF cargado: {temp_path} para personal ID {id_personal}")

            # Obtener la estructura personalizada
            estructura_a_usar = ESTRUCTURA_LEGAJO_DEFAULT
            
            # PRIMERO: intentar obtener la estructura enviada en el formulario
            estructura_enviada = request.form.get('estructura_json')
            logger.info(f"Estructura JSON recibida del cliente (raw): {estructura_enviada}")
            
            if estructura_enviada and estructura_enviada != '{}':
                try:
                    import json
                    estructura_a_usar = json.loads(estructura_enviada)
                    
                    # SEGURIDAD: Validar estructura recibida
                    if not isinstance(estructura_a_usar, dict):
                        raise ValueError("Estructura debe ser un objeto JSON")
                    
                    # Validar cada entrada de la estructura
                    for doc_key, doc_info in estructura_a_usar.items():
                        if not isinstance(doc_info, dict):
                            raise ValueError(f"Entrada {doc_key} debe ser un objeto")
                        
                        # Validar campos requeridos
                        if not all(k in doc_info for k in ['id_seccion', 'tipo_documento', 'pagina_inicio', 'pagina_fin']):
                            raise ValueError(f"Entrada {doc_key} falta campos requeridos")
                        
                        # Validar tipos de datos
                        if not isinstance(doc_info.get('id_seccion'), int) or doc_info.get('id_seccion') < 1:
                            raise ValueError(f"id_seccion debe ser un número positivo")
                        
                        if not isinstance(doc_info.get('pagina_inicio'), int) or doc_info.get('pagina_inicio') < 1:
                            raise ValueError(f"pagina_inicio debe ser un número positivo")
                        
                        if not isinstance(doc_info.get('pagina_fin'), int) or doc_info.get('pagina_fin') < 1:
                            raise ValueError(f"pagina_fin debe ser un número positivo")
                        
                        if doc_info.get('pagina_fin') < doc_info.get('pagina_inicio'):
                            raise ValueError(f"pagina_fin debe ser mayor o igual a pagina_inicio")
                        
                        # Validar que tipo_documento sea string
                        if not isinstance(doc_info.get('tipo_documento'), str):
                            raise ValueError(f"tipo_documento debe ser texto")
                    
                    logger.info(f"Usando estructura personalizada recibida del cliente para personal {id_personal}")
                    logger.info(f"Estructura parseada: {estructura_a_usar}")
                except Exception as e:
                    logger.warning(f"Error validando estructura enviada: {e}, usando por defecto")
                    estructura_a_usar = ESTRUCTURA_LEGAJO_DEFAULT
            
            # SEGUNDA OPCIÓN: Si no vino en el formulario, obtener de la BD
            if not estructura_a_usar or estructura_a_usar == ESTRUCTURA_LEGAJO_DEFAULT:
                try:
                    from app.infrastructure.persistence.estructura_repository import EstructuraRepository
                    estructura_bd = EstructuraRepository.obtener_estructura_json(id_personal)
                    if estructura_bd:
                        estructura_a_usar = estructura_bd
                        logger.info(f"Estructura personalizada obtenida desde BD para personal {id_personal}")
                        logger.info(f"Estructura desde BD: {estructura_a_usar}")
                    else:
                        estructura_a_usar = ESTRUCTURA_LEGAJO_DEFAULT
                        logger.info(f"No hay estructura personalizada en BD, usando por defecto para personal {id_personal}")
                except Exception as e:
                    logger.warning(f"Error obteniendo estructura de BD: {e}, usando por defecto")
                    estructura_a_usar = ESTRUCTURA_LEGAJO_DEFAULT
            else:
                logger.info(f"Se recibio estructura personalizada valida del cliente para personal {id_personal}")
            
            logger.info(f"Estructura final a usar para separar PDF: {estructura_a_usar}")

            # Usar el servicio de separación
            pdf_service = PdfSplitService('temp_pdfs')
            resultados = pdf_service.separar_legajo(
                temp_path, 
                estructura_a_usar, 
                id_personal
            )

            # Verificar si hubo error
            if 'error' in resultados:
                logger.error(f"Error al procesar PDF: {resultados['error']}")
                flash(f"Error al procesar PDF: {resultados['error']}", 'danger')
                return redirect(request.url)

            # Procesar los resultados y guardar en el legajo del personal
            archivos_creados = []
            documentos_guardados = 0
            
            logger.info(f"Resultados de separación: {resultados}")
            
            for nombre_doc, info in resultados.items():
                logger.info(f"Procesando {nombre_doc}: {info}")
                
                # Verificar que el documento se separó exitosamente
                if isinstance(info, dict) and info.get('exito') == True:
                    archivo_path = info.get('archivo')
                    nombre_archivo = info.get('nombre_archivo')
                    
                    logger.info(f"Documento exitoso: {nombre_doc}, archivo: {archivo_path}")
                    
                    # Determinar el tipo de documento basado en el nombre
                    # Ej: "01_DNI" -> buscar tipo_documento en la estructura personalizada
                    tipo_documento = None
                    id_seccion = None
                    for doc_key, doc_info in estructura_a_usar.items():
                        if doc_key == nombre_doc:
                            tipo_documento = doc_info.get('tipo_documento', nombre_doc)
                            id_seccion = doc_info.get('id_seccion')
                            logger.info(f"Encontrado en estructura personalizada: {nombre_doc} -> tipo: {tipo_documento}, seccion: {id_seccion}")
                            break
                    
                    if not tipo_documento:
                        logger.warning(f"No encontrado en estructura personalizada, buscando en default")
                        for doc_key, doc_info in ESTRUCTURA_LEGAJO_DEFAULT.items():
                            if doc_key == nombre_doc:
                                tipo_documento = doc_info.get('tipo_documento', nombre_doc)
                                id_seccion = doc_info.get('id_seccion')
                                break
                    
                    if not tipo_documento:
                        tipo_documento = nombre_doc
                    
                    try:
                        # Leer el documento separado
                        with open(archivo_path, 'rb') as f:
                            archivo_binario = f.read()
                        
                        # Obtener el ID del tipo de documento desde la BD
                        # usando el tipo_documento que extraímos de la estructura
                        id_tipo_documento = None
                        try:
                            # Obtener todos los tipos de documento disponibles
                            tipos_disponibles = personal_repo.get_tipos_documento_for_select() if personal_repo else []
                            
                            logger.info(f"Buscando tipo_documento: '{tipo_documento}'")
                            logger.info(f"Tipos disponibles en BD: {tipos_disponibles}")
                            
                            # Si la lista está vacía, intentar obtenerlos directamente
                            if not tipos_disponibles:
                                logger.warning("Lista de tipos vacía, intentando obtener directamente de BD...")
                                try:
                                    from app.database.connector import get_db_read
                                    conn = get_db_read()
                                    cursor = conn.cursor()
                                    cursor.execute("SELECT id_tipo, nombre_tipo FROM tipo_documento ORDER BY nombre_tipo")
                                    tipos_disponibles = [(row.id_tipo, row.nombre_tipo) for row in cursor.fetchall()]
                                    logger.info(f"Tipos obtenidos directamente: {tipos_disponibles}")
                                except Exception as e:
                                    logger.error(f"Error obteniendo tipos directamente: {e}", exc_info=True)
                            
                            # Buscar el tipo por nombre
                            for tipo_id, tipo_nombre in tipos_disponibles:
                                logger.debug(f"  Comparando '{tipo_documento.lower()}' con '{tipo_nombre.lower()}'")
                                if tipo_nombre.lower() == tipo_documento.lower():
                                    id_tipo_documento = tipo_id
                                    logger.info(f"  [FOUND] tipo_id={tipo_id}, tipo_nombre={tipo_nombre}")
                                    break
                            
                            # Si no se encuentra por nombre exacto, intentar por coincidencia parcial
                            if not id_tipo_documento and tipos_disponibles:
                                logger.info("  Intentando coincidencia parcial...")
                                for tipo_id, tipo_nombre in tipos_disponibles:
                                    if tipo_documento.lower() in tipo_nombre.lower() or tipo_nombre.lower() in tipo_documento.lower():
                                        id_tipo_documento = tipo_id
                                        logger.info(f"  [FOUND-PARTIAL] tipo_id={tipo_id}, tipo_nombre={tipo_nombre}")
                                        break
                            
                            # Si aún no hay, usar el primero disponible
                            if not id_tipo_documento and tipos_disponibles:
                                id_tipo_documento = tipos_disponibles[0][0]
                                logger.warning(f"Tipo de documento '{tipo_documento}' no encontrado, usando tipo por defecto: {id_tipo_documento}")
                        
                        except Exception as e:
                            logger.error(f"Error buscando tipo de documento: {e}", exc_info=True)
                            id_tipo_documento = None
                        
                        if not id_tipo_documento:
                            logger.error(f"No se pudo determinar el ID del tipo de documento para: {tipo_documento}")
                            raise ValueError(f"Tipo de documento no válido: {tipo_documento}")
                        
                        # Guardar el documento en la BD usando el servicio de legajo
                        # IMPORTANTE: Los nombres de campos deben coincidir con lo que espera add_document()
                        form_data = {
                            'id_personal': id_personal,
                            'id_tipo': id_tipo_documento,
                            'id_seccion': id_seccion if id_seccion else 1,  # Usar la sección de la estructura personalizada
                            'nombre_archivo': nombre_archivo,
                            'fecha_emision': None,
                            'fecha_vencimiento': None,
                            'descripcion': f'Documento cargado desde PDF: {nombre_doc}',
                            'hash_archivo': None,
                        }
                        logger.info(f"Guardando documento con form_data: {form_data}")
                        
                        # Crear un objeto similar a FileStorage para pasar al servicio
                        class FileStreamWrapper:
                            def __init__(self, filename, stream):
                                self.filename = filename
                                self.stream = stream
                            def read(self):
                                return self.stream
                            def seek(self, pos):
                                pass
                        
                        file_obj = FileStreamWrapper(nombre_archivo, archivo_binario)
                        
                        # Guardar usando el servicio de legajo
                        if legajo_service:
                            legajo_service.upload_document_to_personal(form_data, file_obj, current_user.id)
                            documentos_guardados += 1
                            logger.info(f"Documento guardado en BD: {nombre_doc} (tipo_id: {id_tipo_documento}) para personal {id_personal}")
                        else:
                            logger.warning("LEGAJO_SERVICE no disponible")
                        
                        archivos_creados.append({
                            'nombre': nombre_doc,
                            'archivo': nombre_archivo,
                            'paginas': info.get('paginas'),
                            'tipo': tipo_documento
                        })
                        
                    except Exception as e:
                        logger.error(f"Error guardando documento {nombre_doc}: {e}", exc_info=True)
                        archivos_creados.append({
                            'nombre': nombre_doc,
                            'archivo': nombre_archivo,
                            'paginas': info.get('paginas'),
                            'tipo': tipo_documento,
                            'error': str(e)
                        })
                else:
                    logger.warning(f"Documento no exitoso: {nombre_doc}, info: {info}")

            # Limpiar el archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)

            flash(
                f'PDF procesado exitosamente. {documentos_guardados} documentos separados y guardados.',
                'success'
            )
            logger.info(
                f"Proceso completado para personal {id_personal}: "
                f"{documentos_guardados} documentos guardados exitosamente"
            )

            return redirect(url_for('legajo.listar_personal'))

        except Exception as e:
            logger.error(f"Error en upload_legajo_pdf: {e}", exc_info=True)
            flash('Error al procesar el PDF.', 'danger')
            return redirect(request.url)

    # GET: No se permite acceso directo. Solo POST desde la página del legajo
    # Redirije de vuelta al legajo si llegó por GET
    if personal_id:
        return redirect(url_for('legajo.ver_legajo', personal_id=personal_id))
    else:
        return redirect(url_for('legajo.listar_personal'))


@pdf_bp.route('/api/procesar', methods=['POST'])
@login_required
def procesar_pdf_api():
    """
    Endpoint API para procesar un PDF y retornar JSON con los resultados.
    """
    if current_user.rol not in ['Sistemas', 'RRHH', 'AdministradorLegajos']:
        return jsonify({'error': 'Permiso denegado'}), 403

    try:
        # Verificar que se envió un archivo
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No se seleccionó archivo'}), 400

        file = request.files['pdf_file']
        id_personal = request.form.get('id_personal')

        if not file or not id_personal:
            return jsonify({'error': 'Archivo o personal no especificado'}), 400

        # Guardar temporalmente
        filename = secure_filename(file.filename)
        temp_path = os.path.join('temp_uploads', filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(temp_path)

        # Procesar
        pdf_service = PdfSplitService('temp_pdfs')
        resultados = pdf_service.separar_legajo(
            temp_path,
            ESTRUCTURA_LEGAJO_DEFAULT,
            id_personal
        )

        # Limpiar
        os.remove(temp_path)

        # Retornar JSON
        return jsonify({
            'success': True,
            'documentos': resultados,
            'total': len([r for r in resultados.values() if r.get('exito')])
        })

    except Exception as e:
        logger.error(f"Error en procesar_pdf_api: {e}")
        return jsonify({'error': str(e)}), 500
