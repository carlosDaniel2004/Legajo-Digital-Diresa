# RUTA: app/infrastructure/persistence/estructura_repository.py
"""
Repositorio para manejar las operaciones de BD relacionadas con estructura personalizada.
"""

import json
import logging
from datetime import datetime
from app.database.connector import get_db_write, get_db_read
from app.domain.models.estructura_personalizada import EstructuraPersonalizada

logger = logging.getLogger(__name__)


class EstructuraRepository:
    """
    Maneja las operaciones de BD para estructura personalizada del legajo.
    """
    
    @staticmethod
    def obtener_estructura_personal(id_personal):
        """
        Obtiene la estructura personalizada de un personal desde la BD.
        
        Args:
            id_personal: ID del personal
            
        Returns:
            EstructuraPersonalizada o None si no existe
        """
        try:
            conn = get_db_read()
            cursor = conn.cursor()
            
            query = """
                SELECT id_estructura, id_personal, estructura_json, 
                       fecha_creacion, fecha_actualizacion
                FROM estructura_personalizada
                WHERE id_personal = ?
            """
            
            cursor.execute(query, (id_personal,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return EstructuraPersonalizada(
                    id_estructura=row[0],
                    id_personal=row[1],
                    estructura_json=row[2],
                    fecha_creacion=row[3],
                    fecha_actualizacion=row[4]
                )
            return None
        except Exception as e:
            logger.error(f"Error al obtener estructura personalizada para personal {id_personal}: {e}")
            return None
    
    @staticmethod
    def guardar_estructura_personal(id_personal, estructura_dict):
        """
        Guarda o actualiza la estructura personalizada de un personal.
        
        Args:
            id_personal: ID del personal
            estructura_dict: Diccionario con la estructura
            
        Returns:
            True si se guardó exitosamente, False si hubo error
        """
        try:
            conn = get_db_write()
            cursor = conn.cursor()
            
            estructura_json = json.dumps(estructura_dict)
            ahora = datetime.now()
            
            # Intentar actualizar primero
            update_query = """
                UPDATE estructura_personalizada
                SET estructura_json = ?,
                    fecha_actualizacion = ?
                WHERE id_personal = ?
            """
            
            cursor.execute(update_query, (estructura_json, ahora, id_personal))
            
            # Si no actualizó nada, insertar
            if cursor.rowcount == 0:
                insert_query = """
                    INSERT INTO estructura_personalizada 
                    (id_personal, estructura_json, fecha_creacion, fecha_actualizacion)
                    VALUES (?, ?, ?, ?)
                """
                cursor.execute(insert_query, (id_personal, estructura_json, ahora, ahora))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Estructura personalizada guardada para personal {id_personal}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar estructura personalizada para personal {id_personal}: {e}")
            return False
    
    @staticmethod
    def obtener_estructura_json(id_personal):
        """
        Obtiene solo el JSON de estructura personalizada.
        
        Args:
            id_personal: ID del personal
            
        Returns:
            dict con la estructura o None
        """
        estructura = EstructuraRepository.obtener_estructura_personal(id_personal)
        if estructura and estructura.estructura_json:
            try:
                return json.loads(estructura.estructura_json)
            except json.JSONDecodeError:
                logger.error(f"Error al parsear JSON para personal {id_personal}")
                return None
        return None
    
    @staticmethod
    def eliminar_estructura_personal(id_personal):
        """
        Elimina la estructura personalizada de un personal.
        
        Args:
            id_personal: ID del personal
            
        Returns:
            True si se eliminó, False en caso contrario
        """
        try:
            conn = get_db_write()
            cursor = conn.cursor()
            
            query = "DELETE FROM estructura_personalizada WHERE id_personal = ?"
            cursor.execute(query, (id_personal,))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Estructura personalizada eliminada para personal {id_personal}")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar estructura personalizada para personal {id_personal}: {e}")
            return False
