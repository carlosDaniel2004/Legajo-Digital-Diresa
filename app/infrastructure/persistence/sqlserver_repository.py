# RUTA: app/infrastructure/persistence/sqlserver_repository.py

from app.database.connector import get_db_read, get_db_write
from app.domain.models.usuario import Usuario
from app.domain.models.personal import Personal
from app.domain.repositories.i_usuario_repository import IUsuarioRepository
from app.domain.repositories.i_personal_repository import IPersonalRepository
from app.domain.repositories.i_auditoria_repository import IAuditoriaRepository
from app.utils.pagination import SimplePagination

def _row_to_dict(cursor, row):
    # LÍNEA CORREGIDA: Eliminada la indentación inconsistente y caracteres invisibles (U+00A0)
    if not row: return None
    # Función de utilidad para convertir una fila del cursor a un diccionario
    return dict(zip([column[0] for column in cursor.description], row))

class SqlServerUsuarioRepository(IUsuarioRepository):
    
    # -------------------------------------------------------------
    # MÉTODO PARA LISTAR USUARIOS (Corregido para usar p_obtener_usuarios_para_gestion)
    # -------------------------------------------------------------
    def find_all_users_with_roles(self):
        """
        Obtiene la lista completa de usuarios con sus roles y estados para 
        la tabla de Gestión de Usuarios.
        """
        conn = get_db_read()
        cursor = conn.cursor()
        
        query = "{CALL sp_listar_todos_los_usuarios}" 
        cursor.execute(query)
        
        results = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # --- CORRECCIÓN: Construcción manual y segura de objetos ---
        # Esto previene errores si el SP no devuelve todas las columnas esperadas.
        usuarios = []
        for data in results:
            if data:
                usuario = Usuario(
                    id_usuario=data.get('id_usuario'),
                    username=data.get('username'),
                    id_rol=data.get('id_rol'),  # Si 'id_rol' no existe, pasará None
                    password_hash=data.get('password_hash'),
                    activo=data.get('activo'),
                    email=data.get('email'),
                    nombre_rol=data.get('nombre_rol'),
                    nombre_completo=data.get('nombre_completo'),
                    ultimo_login=data.get('ultimo_login')
                )
                usuarios.append(usuario)
        return usuarios

    def find_by_id(self, user_id):
        conn = get_db_read()
        cursor = conn.cursor()
        query = "{CALL sp_obtener_usuario_por_id(?)}"
        cursor.execute(query, user_id)
        row_dict = _row_to_dict(cursor, cursor.fetchone())
        return Usuario(**row_dict) if row_dict else None

    def find_by_username_with_email(self, username):
        conn = get_db_read()
        cursor = conn.cursor()
        query = "{CALL sp_obtener_usuario_por_username(?)}"
        cursor.execute(query, username)
        row_dict = _row_to_dict(cursor, cursor.fetchone())
        return Usuario(**row_dict) if row_dict else None

    def set_2fa_code(self, user_id, hashed_code, expiry_date):
        conn = get_db_write()
        cursor = conn.cursor()
        query = "UPDATE usuarios SET two_factor_code = ?, two_factor_expiry = ? WHERE id_usuario = ?"
        cursor.execute(query, hashed_code, expiry_date, user_id)
        conn.commit()

    def clear_2fa_code(self, user_id):
        conn = get_db_write()
        cursor = conn.cursor()
        query = "UPDATE usuarios SET two_factor_code = NULL, two_factor_expiry = NULL WHERE id_usuario = ?"
        cursor.execute(query, user_id)
        conn.commit()

    def update_password_hash(self, username, new_hash):
        conn = get_db_write()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_actualizar_password_usuario(?, ?)}", username, new_hash)
        conn.commit()     

    def update_last_login(self, user_id):
        """Llama a un SP para actualizar la fecha del último login."""
        conn = get_db_write()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_actualizar_ultimo_login(?)}", user_id)
        conn.commit()

# --- REPOSITORIO DE PERSONAL ---
class SqlServerPersonalRepository(IPersonalRepository):
    # ... (Métodos de personal) ...

    def check_dni_exists(self, dni):
        """Verifica si un DNI ya existe en la tabla de personal."""
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM personal WHERE dni = ?", dni)
        return cursor.fetchone() is not None

    def get_all_documents_with_expiration(self):
        """Llama al SP para obtener todos los documentos activos con fecha de vencimiento."""
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_listar_documentos_con_vencimiento}")
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]


    def find_document_by_id(self, document_id):
        """
        Llama al SP para obtener los datos de un único documento por su ID.
        """
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_obtener_documento_por_id(?)}", document_id)
        return cursor.fetchone()

    def delete_document_by_id(self, document_id):
        """
        Llama al SP para la eliminación lógica de un documento.
        """
        conn = get_db_write()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_eliminar_documento_logico(?)}", document_id)
        conn.commit()


    def find_tipos_documento_by_seccion(self, id_seccion):
        """
        Llama a un procedimiento almacenado para obtener los tipos de documento 
        asociados a una sección.
        """
        conn = get_db_read()
        cursor = conn.cursor()
        
        cursor.execute("{CALL sp_listar_tipos_documento_por_seccion(?)}", id_seccion)
        
        # Devuelve una lista de diccionarios, ideal para ser convertida a JSON
        return [{"id": row.id_tipo, "nombre": row.nombre_tipo} for row in cursor.fetchall()]


    # Llama a un SP para obtener la lista de documentos de un empleado.
    def find_documents_by_personal_id(self, personal_id):
        conn = get_db_read()
        cursor = conn.cursor()
        # Este SP debe devolver la lista de documentos para un id_personal.
        cursor.execute("{CALL sp_listar_documentos_por_personal(?)}", personal_id)
        # Se asume que el SP devuelve filas que se pueden mapear al modelo Documento.
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

    def get_full_legajo_by_id(self, personal_id):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_obtener_legajo_completo_por_personal(?)}", personal_id)
        
        # El primer resultado es la información del personal.
        personal_info = _row_to_dict(cursor, cursor.fetchone())
        if not personal_info:
            return None # Si no hay datos personales, el legajo no existe.

        legajo = {"personal": personal_info}
        
        # Se procesan los siguientes conjuntos de resultados.
        if cursor.nextset(): legajo["estudios"] = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        if cursor.nextset(): legajo["capacitaciones"] = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        if cursor.nextset(): legajo["contratos"] = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        if cursor.nextset(): legajo["historial_laboral"] = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        if cursor.nextset(): legajo["licencias"] = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        if cursor.nextset(): legajo["documentos"] = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
            
        return legajo
    
    # Llama a un SP para listar, filtrar y paginar al personal.
    def get_all_paginated(self, page, per_page, filters):
        conn = get_db_read()
        cursor = conn.cursor()
        dni_filter = filters.get('dni') if filters else None
        nombres_filter = filters.get('nombres') if filters else None
        
        cursor.execute("{CALL sp_listar_personal_paginado(?, ?, ?, ?)}", page, per_page, dni_filter, nombres_filter)
        results = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        cursor.nextset()
        total = cursor.fetchone()[0]
        return SimplePagination(results, page, per_page, total)

    # Llama a un SP para crear un nuevo registro de personal.
    def create(self, form_data):
        conn = get_db_write()
        cursor = conn.cursor()
        params = (form_data.get('dni'), form_data.get('nombres'), form_data.get('apellidos'), form_data.get('sexo'),
                  form_data.get('fecha_nacimiento'), form_data.get('direccion'), form_data.get('telefono'),
                  form_data.get('email'), form_data.get('estado_civil'), form_data.get('nacionalidad'),
                  form_data.get('id_unidad'), form_data.get('fecha_ingreso'))
        cursor.execute("{CALL sp_registrar_personal(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}", params)
        new_id = cursor.fetchone()[0]
        conn.commit()
        return new_id
    
    # Llama a un SP para añadir un documento.
    def add_document(self, doc_data, file_bytes):
        conn = get_db_write()
        cursor = conn.cursor()
        params = (
            doc_data.get('id_personal'), 
            doc_data.get('id_tipo'), 
            doc_data.get('id_seccion'),
            doc_data.get('nombre_archivo'), 
            doc_data.get('fecha_emision'), 
            doc_data.get('fecha_vencimiento'),
            doc_data.get('descripcion'), 
            file_bytes, 
            doc_data.get('hash_archivo')
        )
        cursor.execute("{CALL sp_subir_documento(?, ?, ?, ?, ?, ?, ?, ?, ?)}", params)
        conn.commit()
    
    # Métodos para obtener listas para los formularios SelectField.
    def get_unidades_for_select(self):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("SELECT id_unidad, nombre FROM unidad_administrativa ORDER BY nombre")
        return [(row.id_unidad, row.nombre) for row in cursor.fetchall()]

    def get_secciones_for_select(self):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("SELECT id_seccion, nombre_seccion FROM legajo_secciones ORDER BY id_seccion")
        return [(row.id_seccion, row.nombre_seccion) for row in cursor.fetchall()]

    def get_tipos_documento_by_seccion(self, seccion_id):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_listar_tipos_documento_por_seccion(?)}", seccion_id)
        return [(row.id_tipo, row.nombre_tipo) for row in cursor.fetchall()]


    def get_tipos_documento_for_select(self):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("SELECT id_tipo, nombre_tipo FROM tipo_documento ORDER BY nombre_tipo")
        return [(row.id_tipo, row.nombre_tipo) for row in cursor.fetchall()]

    # Implementación del método de actualización.
    def update(self, personal_id, form_data):
        conn = get_db_write()
        cursor = conn.cursor()
        # Llama a un SP para actualizar los datos del personal.
        params = (
            personal_id,
            form_data.get('dni'),
            form_data.get('nombres'),
            form_data.get('apellidos'),
            form_data.get('sexo'),
            form_data.get('fecha_nacimiento'),
            form_data.get('direccion'),
            form_data.get('telefono'),
            form_data.get('email'),
            form_data.get('estado_civil'),
            form_data.get('nacionalidad'),
            form_data.get('id_unidad'),
            form_data.get('fecha_ingreso')
        )
        cursor.execute("{CALL sp_actualizar_personal(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}", params)
        conn.commit()


    # Llama a un SP para obtener todos los datos necesarios para el reporte general.
    def get_all_for_report(self):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_generar_reporte_general_personal}")
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]     
    
    # Llama al SP para el borrado suave (desactivación) de un empleado.
    def delete_by_id(self, personal_id):
        conn = get_db_write()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_eliminar_personal(?)}", personal_id)
        conn.commit()
        
    def find_by_id(self, personal_id):
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_obtener_personal_por_id(?)}", personal_id)
        row = cursor.fetchone()
        return Personal.from_dict(_row_to_dict(cursor, row)) if row else None

    def get_tipos_documento_by_seccion(self, id_seccion):
        """
        Llama a un SP para obtener los tipos de documento asociados a una sección
        y los devuelve en un formato ideal para JSON.
        """
        conn = get_db_read()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_listar_tipos_documento_por_seccion(?)}", id_seccion)
        # Devuelve directamente una lista de diccionarios
        return [{"id": row.id_tipo, "nombre": row.nombre_tipo} for row in cursor.fetchall()]      

    def count_empleados_por_unidad(self):
        """
        Realiza una consulta para contar el número de empleados activos
        en cada unidad administrativa.
        """
        conn = get_db_read()
        cursor = conn.cursor()
        query = """
            SELECT ua.nombre AS nombre_unidad, COUNT(p.id_personal) AS cantidad
            FROM unidad_administrativa ua
            JOIN personal p ON ua.id_unidad = p.id_unidad
            WHERE p.activo = 1
            GROUP BY ua.nombre
            ORDER BY cantidad DESC;
        """
        cursor.execute(query)
        # Devuelve una lista de diccionarios, ideal para gráficos.
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

    def count_empleados_por_estado(self):
        """Cuenta el número de empleados activos e inactivos."""
        conn = get_db_read()
        cursor = conn.cursor()
        query = """
            SELECT 
                CASE WHEN activo = 1 THEN 'Activos' ELSE 'Inactivos' END AS estado,
                COUNT(id_personal) AS cantidad
            FROM personal
            GROUP BY activo;
        """
        cursor.execute(query)
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

    def count_empleados_por_sexo(self):
        """Cuenta el número de empleados por sexo."""
        conn = get_db_read()
        cursor = conn.cursor()
        query = """
            SELECT 
                CASE WHEN sexo = 'M' THEN 'Masculino' WHEN sexo = 'F' THEN 'Femenino' ELSE 'No especificado' END AS sexo,
                COUNT(id_personal) AS cantidad
            FROM personal
            GROUP BY sexo;
        """
        cursor.execute(query)
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

# --- REPOSITORIO DE AUDITORÍA ---
# Implementación completa y corregida del repositorio de auditoría.
class SqlServerAuditoriaRepository(IAuditoriaRepository):
    # Llama a un SP para registrar un evento en la bitácora.
    def log_event(self, id_usuario, modulo, accion, descripcion, detalle_json=None):
        conn = get_db_write()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_registrar_bitacora(?, ?, ?, ?, ?)}", id_usuario, modulo, accion, descripcion, detalle_json)
        conn.commit()

    # Obtiene los logs de forma paginada.
    def get_all_logs_paginated(self, page, per_page):
        conn = get_db_read()
        cursor = conn.cursor()
        # Llama a un SP que maneja la paginación de la tabla bitacora.
        cursor.execute("{CALL sp_listar_bitacora_paginada(?, ?)}", page, per_page)
        # Procesa los resultados.
        results = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        # Obtiene el total de registros para los controles de paginación.
        cursor.nextset()
        total = cursor.fetchone()[0]
        return SimplePagination(results, page, per_page, total)
    

# RUTA: app/infrastructure/persistence/sqlserver_repository.py

import pyodbc
import os
import subprocess
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

def _row_to_dict(cursor, row):
    """Función auxiliar para convertir una fila de base de datos en un diccionario."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

class SqlServerBackupRepository:
    
    # --- SECCIÓN DE BACKUPS (Tu código funcional, sin cambios) ---
    def run_db_backup(self, db_name, file_path):
        try:
            db_server = os.getenv('DB_SERVER')
            db_username = os.getenv('DB_USERNAME_SA') 
            db_password = os.getenv('DB_PASSWORD_SA')
            if not all([db_server, db_username, db_password]):
                raise ValueError("Variables de BD no configuradas en .env")
            backup_query = f"BACKUP DATABASE [{db_name}] TO DISK = N'{file_path}' WITH STATS = 10;"
            sqlcmd_command = ["sqlcmd", "-S", db_server, "-U", db_username, "-P", db_password, "-Q", backup_query, "-b"]
            process = subprocess.run(sqlcmd_command, capture_output=True, text=True, timeout=120, check=False)
            if process.returncode == 0:
                print("---[ÉXITO]: sqlcmd completó el backup correctamente.")
                return True
            else:
                error_message = (f"!!! FALLO CRÍTICO DE SQLCMD:\n"
                                 f"CÓDIGO: {process.returncode}\nERROR: {process.stderr}\nSALIDA: {process.stdout}")
                print(error_message)
                raise Exception("Fallo en la ejecución de sqlcmd.")
        except Exception as e:
            print(f"!!! ERROR INESPERADO en run_db_backup: {e}")
            raise

    def get_backup_history(self):
        try:
            from app.database.connector import get_db_read
            conn = get_db_read()
            cursor = conn.cursor()
            query = """
            SELECT TOP 5 fecha_hora AS fecha_registro, modulo, descripcion, 'FULL' AS Tipo, '5.5 GB' AS Tamanio, 'Éxito' AS Estado
            FROM bitacora WHERE accion IN ('BACKUP', 'COPIA_SEGURIDAD') ORDER BY fecha_registro DESC;
            """
            cursor.execute(query)
            return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"!!! ERROR al obtener historial de backups: {e}")
            return []

    # --- SECCIÓN DE MANEJO DE ERRORES (Añadida anteriormente) ---
    def registrar_error(self, modulo, descripcion, usuario_id=None):
        conn = None
        try:
            from app.database.connector import get_db_write
            conn = get_db_write()
            cursor = conn.cursor()
            sql = "INSERT INTO bitacora (fecha_hora, accion, modulo, descripcion, id_usuario) VALUES (GETDATE(), ?, ?, ?, ?)"
            cursor.execute(sql, 'ERROR', modulo, descripcion, usuario_id)
            conn.commit()
        except Exception as e:
            print(f"!!! FALLO AL REGISTRAR ERROR EN LA BITÁCORA: {e}")
            if conn:
                conn.rollback()

    def obtener_historial_errores(self):
        try:
            from app.database.connector import get_db_read
            conn = get_db_read()
            cursor = conn.cursor()
            query = """
            SELECT TOP 50 b.fecha_hora, b.modulo, b.descripcion, u.username AS usuario
            FROM bitacora b LEFT JOIN usuarios u ON b.id_usuario = u.id_usuario
            WHERE b.accion = 'ERROR' ORDER BY b.fecha_hora DESC;
            """
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"!!! ERROR OBTENIENDO HISTORIAL DE ERRORES: {e}")
            return []

    # --- NUEVA LÓGICA PARA EL BORRADO SUAVE (SOFT DELETE) ---

    def solicitar_eliminacion_documento(self, documento_id, solicitante_id):
        """
        Realiza un borrado suave: cambia el estado del documento y crea una solicitud.
        Todo dentro de una única transacción para garantizar la consistencia.
        """
        conn = None
        try:
            from app.database.connector import get_db_write
            conn = get_db_write()
            cursor = conn.cursor()

            # 1. Obtener los detalles del documento antes de hacer nada
            # Nos aseguramos de obtener la llave primaria de legajo (id_legajo)
            cursor.execute("SELECT id_legajo, nombre_archivo, ruta_archivo FROM documentos WHERE id_documento = ?", documento_id)
            doc_row = cursor.fetchone()
            if not doc_row:
                raise Exception(f"No se encontró el documento con ID {documento_id}.")
            
            id_legajo, nombre_archivo, ruta_archivo = doc_row

            # Inicia la transacción
            conn.autocommit = False

            # 2. Actualizar el estado del documento para "ocultarlo"
            sql_update = "UPDATE documentos SET estado = 'PENDIENTE_ELIMINACION' WHERE id_documento = ?"
            cursor.execute(sql_update, documento_id)

            # 3. Insertar el registro en la tabla de solicitudes para que el admin de sistemas lo vea
            sql_insert_solicitud = """
            INSERT INTO solicitudes_eliminacion 
            (id_documento, nombre_documento, ruta_archivo, id_legajo, solicitado_por_id, estado)
            VALUES (?, ?, ?, ?, ?, 'PENDIENTE')
            """
            cursor.execute(sql_insert_solicitud, documento_id, nombre_archivo, ruta_archivo, id_legajo, solicitante_id)

            # Si todo fue bien, confirma la transacción
            conn.commit()
            print(f"---[INFO]: Solicitud de eliminación creada para el documento ID {documento_id}")
            return True

        except Exception as e:
            print(f"!!! FALLO EN SOLICITUD DE ELIMINACIÓN: {e}")
            if conn:
                conn.rollback() # Si algo falla, deshace todos los cambios
            return False
        finally:
            if conn:
                conn.autocommit = True # Restaura el modo autocommit


# --- REPOSITORIO DE SOLICITUDES DE MODIFICACIÓN ---
class SqlServerSolicitudRepository: 
    
    def get_pending_requests(self):
        """
        Llama al SP para obtener la lista de solicitudes PENDIENTES.
        """
        conn = get_db_read()
        cursor = conn.cursor()
        
        # 🔑 CORRECCIÓN: Llamada al SP de gestión con el parámetro 'LISTAR' 🔑
        # Asumimos que el SP requiere un parámetro de acción ('LISTAR') y un ID (None)
        query = "{CALL sp_gestionar_solicitud_modificacion(?, ?)}"
        
        # El SP debe estar programado para devolver el listado cuando 'LISTAR' es el primer parámetro
        cursor.execute(query, 'LISTAR', None) 
        
        results = [_row_to_dict(cursor, row) for row in cursor.fetchall()]
        
        # Nota: Aquí deberías mapear los resultados a un objeto Solicitud,
        # pero devolveremos el diccionario para simplificar y pasar a la plantilla.
        return results

    def process_request(self, request_id, action):
        """
        Procesa (APRUEBA/RECHAZA) una solicitud por su ID.
        """
        conn = get_db_write()
        cursor = conn.cursor()
        
        # 🔑 CORRECCIÓN: Llamada al SP de gestión para APROBAR/RECHAZAR 🔑
        # 'action' será 'APROBAR' o 'RECHAZAR' desde la ruta de Flask
        query = "{CALL sp_gestionar_solicitud_modificacion(?, ?)}"
        
        # El SP debe recibir la acción (APROBAR/RECHAZAR) y el ID de la solicitud
        cursor.execute(query, action.upper(), request_id) 
        conn.commit()
        
        # El SP debe actualizar el campo de Legajo si es aprobación.
        # Asumimos que el SP maneja la lógica de actualización/rechazo.
        return True
