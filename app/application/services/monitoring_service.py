# RUTA: app/application/services/monitoring_service.py

import psutil
import pyodbc
from datetime import datetime
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class MonitoringService:
    """Servicio para monitorear el rendimiento del servidor y la base de datos."""
    
    def __init__(self, personal_repository=None):
        self._personal_repo = personal_repository
    
    def get_system_metrics(self):
        """
        Obtiene métricas del sistema operativo:
        - Uso de CPU
        - Memoria RAM disponible y en uso
        - Espacio en disco
        """
        try:
            # Obtener CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Obtener Memoria
            memory = psutil.virtual_memory()
            ram_total_gb = memory.total / (1024 ** 3)
            ram_available_gb = memory.available / (1024 ** 3)
            ram_used_gb = memory.used / (1024 ** 3)
            ram_percent = memory.percent
            
            # Obtener Disco
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024 ** 3)
            disk_used_gb = disk.used / (1024 ** 3)
            disk_free_gb = disk.free / (1024 ** 3)
            disk_percent = disk.percent
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'cpu_status': self._get_health_status(cpu_percent, 80, 95),
                'ram_total_gb': round(ram_total_gb, 2),
                'ram_used_gb': round(ram_used_gb, 2),
                'ram_available_gb': round(ram_available_gb, 2),
                'ram_percent': round(ram_percent, 2),
                'ram_status': self._get_health_status(ram_percent, 80, 95),
                'disk_total_gb': round(disk_total_gb, 2),
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_free_gb': round(disk_free_gb, 2),
                'disk_percent': round(disk_percent, 2),
                'disk_status': self._get_health_status(disk_percent, 80, 90),
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas del sistema: {e}")
            return self._get_default_metrics()
    
    def get_database_metrics(self):
        """
        Obtiene métricas de la base de datos SQL Server:
        - Conexiones activas
        - Tamaño de la base de datos
        - Estado de la base de datos
        """
        try:
            # Usar la conexión existente del repositorio si está disponible
            if not self._personal_repo:
                return self._get_default_db_metrics()
            
            # Conectar a SQL Server para obtener información de conexiones
            connection_string = self._build_connection_string()
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            # Obtener número de conexiones activas
            cursor.execute("""
                SELECT COUNT(*) as active_connections
                FROM sys.dm_exec_sessions
                WHERE database_id = DB_ID()
            """)
            active_connections = cursor.fetchone()[0]
            
            # Obtener tamaño de la base de datos
            cursor.execute("""
                SELECT 
                    SUM(size) * 8 / 1024 as size_mb
                FROM sys.master_files
                WHERE database_id = DB_ID()
            """)
            db_size_mb = cursor.fetchone()[0]
            db_size_gb = round(db_size_mb / 1024, 2) if db_size_mb else 0
            
            cursor.close()
            conn.close()
            
            return {
                'active_connections': int(active_connections),
                'db_size_gb': db_size_gb,
                'db_status': 'OK',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas de BD: {e}")
            return self._get_default_db_metrics()
    
    def _build_connection_string(self):
        """Construye la cadena de conexión a SQL Server."""
        driver = current_app.config.get('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
        server = current_app.config.get('DB_SERVER')
        database = current_app.config.get('DB_DATABASE')
        username = current_app.config.get('DB_USERNAME_SYSTEMS_ADMIN')
        password = current_app.config.get('DB_PASSWORD_SYSTEMS_ADMIN')
        
        return f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    def _get_health_status(self, percent, warning_threshold=80, critical_threshold=95):
        """Determina el estado de salud basado en un porcentaje."""
        if percent >= critical_threshold:
            return 'crítico'
        elif percent >= warning_threshold:
            return 'advertencia'
        else:
            return 'bueno'
    
    def _get_default_metrics(self):
        """Retorna métricas por defecto cuando hay error."""
        return {
            'cpu_percent': 0,
            'cpu_status': 'desconocido',
            'ram_total_gb': 0,
            'ram_used_gb': 0,
            'ram_available_gb': 0,
            'ram_percent': 0,
            'ram_status': 'desconocido',
            'disk_total_gb': 0,
            'disk_used_gb': 0,
            'disk_free_gb': 0,
            'disk_percent': 0,
            'disk_status': 'desconocido',
        }
    
    def _get_default_db_metrics(self):
        """Retorna métricas de BD por defecto cuando hay error."""
        return {
            'active_connections': 0,
            'db_size_gb': 0,
            'db_status': 'desconocido',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
