#!/usr/bin/env python
"""
Script de prueba para debuggear la app paso a paso
"""

import sys
import logging

# Configurar logging para ver qué está pasando
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

try:
    logger.info("1. Iniciando importaciones...")
    from app import create_app
    
    logger.info("2. Creando app...")
    app = create_app()
    
    logger.info("3. App creada exitosamente")
    logger.info("4. Iniciando servidor...")
    
    from waitress import serve
    serve(app, host='localhost', port=5001, threads=2)
    
except Exception as e:
    logger.error(f"❌ Error: {e}", exc_info=True)
    sys.exit(1)
