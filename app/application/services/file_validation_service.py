# RUTA: app/application/services/file_validation_service.py
# Servicio de validación segura de archivos

import logging
import os
from typing import Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileValidationService:
    """
    Valida archivos por Magic Number (primeros bytes), no por extensión.
    Previene subidas de malware rebautizado.
    
    Ejemplo:
    - Archivo "malware.exe" rebautizado como "documento.pdf"
    - Extensión sugiere PDF, pero Magic Number revela EXE
    """
    
    # Magic Numbers (primeros bytes) de tipos permitidos
    ALLOWED_MAGIC_NUMBERS = {
        'pdf': [b'%PDF'],
        'jpg': [b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1', b'\xFF\xD8\xFF\xE2', b'\xFF\xD8\xFF\xDB'],
        'jpeg': [b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1', b'\xFF\xD8\xFF\xE2', b'\xFF\xD8\xFF\xDB'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'gif': [b'GIF87a', b'GIF89a'],
        'docx': [b'PK\x03\x04'],  # DOCX (ZIP-based)
        'xlsx': [b'PK\x03\x04'],  # XLSX (ZIP-based)
        'doc': [b'PK\x03\x04'],   # DOC moderno
        'xls': [b'PK\x03\x04'],   # XLS moderno
        'zip': [b'PK\x03\x04'],
        'txt': [b'', b'\xEF\xBB\xBF'],  # UTF-8 BOM o vacío
        'csv': [b'', b'\xEF\xBB\xBF'],
    }
    
    # Extensiones no permitidas (por seguridad)
    FORBIDDEN_EXTENSIONS = {
        'exe', 'com', 'bat', 'cmd', 'pif', 'scr',  # Ejecutables Windows
        'app', 'sh', 'bash',                        # Ejecutables Linux/Mac
        'jar', 'class',                             # Java
        'vbs', 'js', 'ps1',                        # Scripts
        'dll', 'so', 'dylib',                      # Librerías dinámicas
        'zip' if True else '',                     # ZIP puede contener ejecutables
        'rar', '7z',                                # Compresores
        'iso',                                      # Imágenes de disco
    }
    
    # Límites de tamaño por tipo (bytes)
    MAX_FILE_SIZES = {
        'pdf': 50 * 1024 * 1024,      # 50 MB
        'jpg': 25 * 1024 * 1024,      # 25 MB
        'jpeg': 25 * 1024 * 1024,
        'png': 25 * 1024 * 1024,
        'gif': 10 * 1024 * 1024,      # 10 MB
        'docx': 30 * 1024 * 1024,     # 30 MB
        'xlsx': 30 * 1024 * 1024,
        'doc': 30 * 1024 * 1024,
        'xls': 30 * 1024 * 1024,
        'txt': 5 * 1024 * 1024,       # 5 MB
        'csv': 5 * 1024 * 1024,
    }
    
    @staticmethod
    def validate_file(file_obj, allowed_types: list = None) -> Tuple[bool, Optional[str]]:
        """
        Valida un archivo según múltiples criterios.
        
        Args:
            file_obj: Archivo de Flask (request.files['file'])
            allowed_types: Lista de tipos permitidos (ej: ['pdf', 'jpg', 'docx'])
                          Si es None, permite todos excepto FORBIDDEN
        
        Returns:
            (valid: bool, error_message: str or None)
        
        Ejemplos:
            valid, error = FileValidationService.validate_file(file, ['pdf', 'jpg'])
            if not valid:
                flash(error, 'danger')
        """
        
        # 1. Validar que existe archivo
        if not file_obj or file_obj.filename == '':
            return False, "No se seleccionó archivo"
        
        # 2. Obtener extensión
        filename = file_obj.filename.lower()
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
        
        if not ext:
            return False, "Archivo sin extensión no permitido"
        
        # 3. Validar extensión no prohibida
        if ext in FileValidationService.FORBIDDEN_EXTENSIONS:
            logger.warning(f"SEGURIDAD: Intento de subir archivo prohibido: {filename}")
            return False, f"Tipo de archivo no permitido: {ext}"
        
        # 4. Leer primeros bytes del archivo
        file_obj.seek(0)
        file_header = file_obj.read(1024)  # Leer 1KB para análisis
        file_obj.seek(0)  # Resetear posición
        
        if not file_header:
            return False, "Archivo vacío"
        
        # 5. Detectar tipo real (Magic Number)
        detected_type = FileValidationService._detect_file_type(file_header)
        
        # 6. Validar tipo
        if allowed_types:
            if detected_type not in allowed_types:
                logger.warning(
                    f"SEGURIDAD: Magic Number mismatch - Nombre: {filename}, Detectado: {detected_type}"
                )
                return False, f"Tipo de archivo no permitido. Detectado: {detected_type}"
        else:
            # Si no se especifican tipos, usar detectado
            if detected_type is None:
                return False, "Tipo de archivo no reconocido"
        
        # 7. Validar tamaño
        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)  # Resetear
        
        tipo_final = detected_type or (allowed_types[0] if allowed_types else ext)
        max_size = FileValidationService.MAX_FILE_SIZES.get(tipo_final, 50 * 1024 * 1024)
        
        if file_size > max_size:
            mb_limit = max_size / (1024 * 1024)
            return False, f"Archivo demasiado grande (máx {int(mb_limit)} MB)"
        
        # 8. Validar archivo específico si es necesario
        if detected_type == 'pdf':
            valid, error = FileValidationService._validate_pdf(file_header)
            if not valid:
                return False, error
        
        elif detected_type in ['jpg', 'jpeg', 'png', 'gif']:
            valid, error = FileValidationService._validate_image(file_header)
            if not valid:
                return False, error
        
        # ✅ Archivo válido
        return True, None
    
    @staticmethod
    def _detect_file_type(file_bytes: bytes) -> Optional[str]:
        """
        Detecta tipo de archivo por Magic Number.
        
        Returns:
            Tipo detectado (str) o None si no reconocido
        """
        for file_type, magic_numbers in FileValidationService.ALLOWED_MAGIC_NUMBERS.items():
            for magic in magic_numbers:
                if magic and file_bytes.startswith(magic):
                    return file_type
        
        return None
    
    @staticmethod
    def _validate_pdf(file_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validaciones adicionales específicas para PDF.
        """
        # Verificar que empieza y debe tener estructura PDF
        if not file_bytes.startswith(b'%PDF'):
            return False, "PDF inválido (header faltante)"
        
        # Verificar que no contiene javascript (vulnerabilidad común)
        file_sample = file_bytes[:10000]  # Primeros 10KB
        if b'/JavaScript' in file_sample or b'/JS' in file_sample:
            logger.warning("SEGURIDAD: PDF contiene JavaScript (potencial malware)")
            return False, "PDF contiene contenido potencialmente peligroso"
        
        return True, None
    
    @staticmethod
    def _validate_image(file_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validaciones adicionales para imágenes.
        """
        # Las imágenes deben tener header y footer válidos
        if len(file_bytes) < 8:
            return False, "Imagen demasiado pequeña"
        
        # Validaciones específicas por tipo
        if file_bytes.startswith(b'\x89PNG'):
            # PNG debe tener longitud correcta
            if len(file_bytes) < 24:
                return False, "PNG inválido"
        
        elif file_bytes.startswith(b'\xFF\xD8\xFF'):
            # JPEG válido si termina con FFD9
            if not file_bytes.endswith(b'\xFF\xD9'):
                logger.warning("SEGURIDAD: JPEG sin footer válido (posible truncado o malware)")
                # No es error fatal, podría ser archivo legítimo truncado
        
        return True, None
    
    @staticmethod
    def quarantine_file(file_path: str, reason: str = "Archivo sospechoso"):
        """
        Mueve archivo a cuarentena en lugar de borrarlo.
        
        Args:
            file_path: Ruta del archivo
            reason: Razón de la cuarentena
        """
        try:
            quarantine_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                '..',
                'quarantine'
            )
            
            os.makedirs(quarantine_dir, exist_ok=True)
            
            # Crear nombre con timestamp
            filename = os.path.basename(file_path)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
            quarantine_path = os.path.join(quarantine_dir, timestamp + filename)
            
            if os.path.exists(file_path):
                os.rename(file_path, quarantine_path)
                logger.warning(f"SEGURIDAD: Archivo puesto en cuarentena: {quarantine_path} - Razón: {reason}")
            
        except Exception as e:
            logger.error(f"Error al poner archivo en cuarentena: {str(e)}")


class DocumentChecksum:
    """
    Calcula y verifica checksum de documentos para detectar corrupción/modificación.
    """
    
    import hashlib
    
    @staticmethod
    def calculate_checksum(file_obj, algorithm: str = 'sha256') -> str:
        """
        Calcula checksum de un archivo.
        
        Args:
            file_obj: Archivo de Flask
            algorithm: 'md5', 'sha1', 'sha256'
        
        Returns:
            Checksum en hexadecimal
        """
        file_obj.seek(0)
        
        if algorithm == 'md5':
            hasher = DocumentChecksum.hashlib.md5()
        elif algorithm == 'sha1':
            hasher = DocumentChecksum.hashlib.sha1()
        else:  # sha256
            hasher = DocumentChecksum.hashlib.sha256()
        
        # Leer en chunks (más eficiente con archivos grandes)
        while True:
            chunk = file_obj.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
        
        file_obj.seek(0)  # Resetear
        return hasher.hexdigest()
    
    @staticmethod
    def verify_checksum(file_obj, expected_checksum: str, algorithm: str = 'sha256') -> bool:
        """
        Verifica que el checksum de un archivo coincida con el esperado.
        """
        calculated = DocumentChecksum.calculate_checksum(file_obj, algorithm)
        return calculated == expected_checksum
