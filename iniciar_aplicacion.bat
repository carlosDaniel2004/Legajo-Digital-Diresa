@echo off
REM -----------------------------------------------------------------
REM --- LANZADOR DE LA APLICACIÓN DE LEGAJO DIGITAL ---
REM -----------------------------------------------------------------
echo Iniciando el servidor de la aplicacion de Legajo Digital...
echo.
echo Este terminal debe permanecer abierto para que la aplicacion funcione.
echo.

REM Obtiene la ruta del directorio donde se encuentra este script.
set "CURRENT_DIR=%~dp0"

REM Navega al directorio del script.
cd /d "%CURRENT_DIR%"

REM Inicia el servidor web de produccion (Waitress) usando el ejecutable del entorno virtual.
REM Esto es mas robusto que activar el venv primero.
start "LegajoDigitalServer" /B .\\venv\\Scripts\\waitress-serve.exe --host=127.0.0.1 --port=8080 "run:app"

REM Espera unos segundos para que el servidor inicie.
timeout /t 5 /nobreak > nul

REM Abre la aplicacion en el navegador por defecto del usuario.
start http://localhost:8080/

REM Mantiene la ventana abierta para mostrar cualquier mensaje del servidor.
echo Servidor iniciado. Puedes cerrar esta ventana para detener la aplicacion.

REM El comando 'pause' es opcional, pero util si el servidor falla al iniciar.
REM pause
