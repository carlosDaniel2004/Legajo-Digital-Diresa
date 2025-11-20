# Importa la función que crea y configura la aplicación Flask.
from app import create_app
import os

# Crea una instancia de la aplicación llamando a la factoría.
app = create_app()

# Punto de entrada para ejecutar la aplicación.
# Se activa solo cuando el script es ejecutado directamente.
if __name__ == "__main__":
    # ADVERTENCIA: Este es un servidor de desarrollo.
    # No lo uses en un entorno de producción.
    # Para producción, utiliza un servidor WSGI como Gunicorn o Waitress.
    app.run(host='0.0.0.0', port=5001, debug=True)

