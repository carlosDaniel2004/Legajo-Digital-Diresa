# Guía de Despliegue en Producción

Esta guía describe los pasos para desplegar la aplicación Legajo Digital en un entorno de producción.

## 1. Requisitos Previos

- Python 3.8 o superior.
- Git.
- Un servidor de base de datos SQL Server.
- Un servidor Windows o Linux.

## 2. Configuración del Entorno

### a. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd legajo_digital_diresa
```

### b. Crear un Entorno Virtual

Es altamente recomendable usar un entorno virtual para aislar las dependencias del proyecto.

```bash
python -m venv venv
```

### c. Activar el Entorno Virtual

- **En Windows:**
  ```bash
  .\venv\Scripts\activate
  ```
- **En Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```

### d. Instalar Dependencias de Producción

Instala únicamente las dependencias necesarias para producción desde `requirements.txt`.

```bash
pip install -r requirements.txt
```

### e. Configurar Variables de Entorno

1.  Copia el archivo de ejemplo `.env.example` a un nuevo archivo llamado `.env`.
    
    ```bash
    copy .env.example .env
    ```
2.  Abre el archivo `.env` y rellena todas las variables con los valores correctos para tu entorno de producción.
    
    -   **`SECRET_KEY`**: Debe ser una cadena larga, aleatoria y secreta. Puedes generar una con Python: `python -c 'import secrets; print(secrets.token_hex())'`.
    -   **`FLASK_DEBUG`**: Asegúrate de que esté en `False`.
    -   **Credenciales de la base de datos y correo**: Rellena con los datos de tu servidor.

## 3. Ejecutar la Aplicación en Producción

### a. En Windows (usando Waitress)

El repositorio incluye un script `iniciar_aplicacion.bat` que utiliza `waitress` para servir la aplicación. Simplemente ejecútalo:

```bash
.\iniciar_aplicacion.bat
```

La aplicación estará disponible en `http://<IP_DEL_SERVIDOR>:5001`.

### b. En Linux (usando Gunicorn)

Para un entorno Linux, `gunicorn` es la opción recomendada.

```bash
gunicorn --bind 0.0.0.0:5001 wsgi:app
```

Para una configuración más robusta, considera ejecutar `gunicorn` como un servicio del sistema (`systemd`).

## 4. Consideraciones Adicionales de Seguridad

-   **Firewall**: Asegúrate de que solo los puertos necesarios (ej. 5001, 80, 443) estén abiertos en el firewall de tu servidor.
-   **HTTPS**: En un entorno de producción real, debes servir la aplicación a través de HTTPS. Para ello, puedes usar un proxy inverso como Nginx o Apache delante de `gunicorn` o `waitress`.
-   **Copias de Seguridad**: Implementa una estrategia de copias de seguridad regulares para tu base de datos.
