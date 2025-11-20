@echo off
REM Script para ejecutar la aplicación en producción con Waitress
REM Autor: Legajo Digital DIRESA
REM Fecha: Noviembre 2025

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║      LEGAJO DIGITAL DIRESA - SERVIDOR DE PRODUCCION         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Activar el virtual environment
call venv\Scripts\activate.bat

REM Verificar que Waitress está instalado
pip show waitress >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Waitress no está instalado
    echo Instálalo con: pip install waitress
    pause
    exit /b 1
)

REM Ejecutar con parámetros personalizables
if "%1"=="" (
    echo 🚀 Iniciando servidor en http://0.0.0.0:5001
    python run_production.py
) else if "%2"=="" (
    echo 🚀 Iniciando servidor en http://0.0.0.0:%1
    python run_production.py %1
) else (
    echo 🚀 Iniciando servidor en http://%1:%2
    python run_production.py %1 %2
)

pause
