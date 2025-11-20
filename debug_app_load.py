#!/usr/bin/env python
"""
Test para debuggear qué paso de create_app se cuelga
"""

import sys
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_step(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f">> {name}...")
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"✅ {name} - {elapsed:.2f}s")
                return result
            except Exception as e:
                logger.error(f"❌ {name} falló: {e}", exc_info=True)
                sys.exit(1)
        return wrapper
    return decorator

@test_step("Importación de Flask")
def test_1():
    from flask import Flask
    return Flask

@test_step("Importación de config")
def test_2():
    from app.config import Config
    return Config

@test_step("Importación de extensiones")
def test_3():
    from flask_login import LoginManager
    from flask_wtf.csrf import CSRFProtect
    from flask_mail import Mail
    return (LoginManager, CSRFProtect, Mail)

@test_step("Importación de servicios")
def test_4():
    from app.application.services.usuario_service import UsuarioService
    return UsuarioService

@test_step("Importación de repositorios")
def test_5():
    from app.infrastructure.persistence.sqlserver_repository import SqlServerUsuarioRepository
    return SqlServerUsuarioRepository

@test_step("Creación de app con create_app()")
def test_6():
    from app import create_app
    app = create_app()
    return app

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("INICIANDO TESTS DE CARGA DE APP")
    logger.info("=" * 60)
    
    test_1()
    test_2()
    test_3()
    test_4()
    test_5()
    test_6()
    
    logger.info("=" * 60)
    logger.info("✅ TODOS LOS TESTS PASARON")
    logger.info("=" * 60)
