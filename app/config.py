# RUTA: app/config.py (Versión final compatible con tu arquitectura)

import os
from dotenv import load_dotenv

# Hacemos la ruta al .env explícita para evitar problemas
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    """
    Clase de configuración principal. Lee valores desde variables de entorno
    y es compatible con usuarios de BD de lectura y escritura separados.
    """
    # --- CONFIGURACIÓN DE SEGURIDAD DE FLASK ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Seguridad: En un entorno de producción (cuando DEBUG=False), es obligatorio
    # que la SECRET_KEY esté definida. Si no lo está, la aplicación no arrancará.
    if not SECRET_KEY and not DEBUG:
        raise ValueError("CRITICAL: La variable de entorno SECRET_KEY no está configurada para el entorno de producción.")

    # --- CONFIGURACIÓN DE LA BASE DE DATOS (LECTURA/ESCRITURA) ---
    # Carga todas las credenciales desde tu archivo .env
    DB_DRIVER = os.environ.get('DB_DRIVER')
    DB_SERVER = os.environ.get('DB_SERVER')
    DB_DATABASE = os.environ.get('DB_DATABASE')
    
    # Usuario con permisos de escritura (para INSERT, UPDATE, DELETE).
    DB_USERNAME_WRITE = os.environ.get('DB_USERNAME_WRITE')
    DB_PASSWORD_WRITE = os.environ.get('DB_PASSWORD_WRITE')
    
    # Usuario administrador de sistemas (con permisos elevados)
    DB_USERNAME_SYSTEMS_ADMIN = os.environ.get('DB_USERNAME_SYSTEMS_ADMIN')
    DB_PASSWORD_SYSTEMS_ADMIN = os.environ.get('DB_PASSWORD_SYSTEMS_ADMIN')
    
    # Nota: lectura_user no existe en esta BD, se usa DB_USERNAME_WRITE para ambas operaciones
    DB_USERNAME_READ = os.environ.get('DB_USERNAME_WRITE')
    DB_PASSWORD_READ = os.environ.get('DB_PASSWORD_WRITE')

    # Validación de variables de entorno de la BD
    if not all([DB_SERVER, DB_DATABASE, DB_USERNAME_WRITE, DB_PASSWORD_WRITE, DB_USERNAME_READ, DB_PASSWORD_READ]):
        raise ValueError("Error de configuración: Faltan una o más variables de entorno para la base de datos.")

    # --- CONFIGURACIÓN PARA EL ENVÍO DE CORREOS ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') 

    # --- CONFIGURACIÓN PARA LA SUBIDA DE ARCHIVOS ---
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}
    
    # Define el tamaño máximo del archivo en bytes (100 MB)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
