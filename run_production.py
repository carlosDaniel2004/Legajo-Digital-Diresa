#!/usr/bin/env python
"""
Script para ejecutar la aplicación en producción usando Waitress.

Uso:
    python run_production.py              # Puerto por defecto: 5001
    python run_production.py 8080         # Puerto personalizado: 8080
    python run_production.py 0.0.0.0 8080 # Host y puerto personalizados
"""

import sys
from waitress import serve
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Configurar host y puerto desde argumentos de línea de comandos
    host = "localhost"  # localhost o 127.0.0.1 para acceder desde este PC
    port = 5001         # Puerto por defecto
    
    # Permitir personalización desde CLI
    if len(sys.argv) > 1:
        try:
            # Si se pasa un solo argumento, es el puerto
            if len(sys.argv) == 2:
                port = int(sys.argv[1])
            # Si se pasan dos argumentos, son host y puerto
            elif len(sys.argv) >= 3:
                host = sys.argv[1]
                port = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Los argumentos deben ser números válidos para el puerto")
            print("Uso: python run_production.py [puerto] o python run_production.py [host] [puerto]")
            sys.exit(1)
    
    # Para producción real, usa 0.0.0.0, pero para desarrollo usa localhost
    actual_host = "0.0.0.0" if len(sys.argv) > 1 and sys.argv[1] not in ["localhost", "127.0.0.1"] else host
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        LEGAJO DIGITAL DIRESA - SERVIDOR DE PRODUCCIÓN        ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    🚀 Servidor: Waitress WSGI
    🌐 Host: {actual_host}
    🔌 Puerto: {port}
    🔒 HTTPS: No (usar con proxy reverso como Nginx)
    📊 Workers: Auto (según CPU disponible)
    
    📍 Accede a: http://{host}:{port}
    
    Presiona CTRL+C para detener el servidor
    ══════════════════════════════════════════════════════════════════
    """)
    
    # Iniciar servidor Waitress
    # Configuración recomendada para producción:
    serve(
        app,
        host=actual_host,
        port=port,
        threads=8,           # Número de threads para manejar conexiones
        channel_timeout=300, # Timeout de conexión (5 minutos)
        log_socket_errors=False,  # Evitar logs de errores de socket SSL
        _quiet=False         # Mostrar logs de acceso
    )
