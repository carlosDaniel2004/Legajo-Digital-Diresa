# Importa la función que crea y configura la aplicación Flask.
from app import create_app
import os

# Crea una instancia de la aplicación llamando a la factoría.
app = create_app()

# Punto de entrada para ejecutar la aplicación.
# Se activa solo cuando el script es ejecutado directamente.
if __name__ == "__main__":
    # Seguridad: Cargar la configuración de debug desde una variable de entorno.
    # Esto previene que la aplicación se ejecute en modo debug en producción por accidente.
    is_debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5001, debug=is_debug)

