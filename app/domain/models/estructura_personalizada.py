# RUTA: app/domain/models/estructura_personalizada.py
"""
Modelo para almacenar la estructura personalizada del legajo por personal.
Permite que cada empleado tenga su propia estructura de documentos.
"""

from datetime import datetime


class EstructuraPersonalizada:
    """
    Representa la estructura personalizada del legajo para un personal específico.
    Se almacena en la BD para persistencia permanente.
    """
    
    def __init__(self, id_estructura=None, id_personal=None, estructura_json=None, 
                 fecha_creacion=None, fecha_actualizacion=None):
        self.id_estructura = id_estructura
        self.id_personal = id_personal
        self.estructura_json = estructura_json  # JSON serializado con la estructura
        self.fecha_creacion = fecha_creacion or datetime.now()
        self.fecha_actualizacion = fecha_actualizacion or datetime.now()
    
    def __repr__(self):
        return f"<EstructuraPersonalizada personal_id={self.id_personal}>"
