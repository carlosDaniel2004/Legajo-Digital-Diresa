import os
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SolicitudService:
    def __init__(self, solicitud_repository):
        self.solicitud_repo = solicitud_repository

    def get_all_pending(self):
        return self.solicitud_repo.get_pending_requests()

    def process_request(self, request_id, action):
        return self.solicitud_repo.process_request(request_id, action)

    def registrar_solicitud_cambio(self, id_usuario, id_documento, motivo, archivo):
        """
        Guarda el archivo en una carpeta temporal y registra la solicitud en BD.
        """
        try:
            # 1. Validar y Guardar archivo físico
            if not archivo:
                raise ValueError("El archivo es requerido")

            filename = secure_filename(archivo.filename)
            # Definir ruta de carga (asegúrate de que esta carpeta exista o créala)
            upload_folder = os.path.join(current_app.root_path, 'presentation/static/uploads/temp_requests')
            os.makedirs(upload_folder, exist_ok=True)
            
            ruta_guardado = os.path.join(upload_folder, filename)
            archivo.save(ruta_guardado)
            
            # Ruta relativa para guardar en BD
            ruta_relativa = f"uploads/temp_requests/{filename}"

            # 2. Llamar al repositorio para insertar en BD
            data = {
                'id_usuario_solicitante': id_usuario,
                'id_documento_original': id_documento,
                'motivo': motivo,
                'ruta_nuevo_archivo': ruta_relativa,
                'tipo_solicitud': 'CAMBIO_DOCUMENTO'
            }
            
            return self.solicitud_repo.crear_solicitud(data)

        except Exception as e:
            logger.error(f"Error en servicio registrar_solicitud_cambio: {e}")
            raise