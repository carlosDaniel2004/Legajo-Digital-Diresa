
# Sistema de Legajo Digital - DIRESA Pasco

Este es un sistema de gestión de legajos digitales desarrollado en Python con el framework Flask, siguiendo una arquitectura en capas para asegurar su mantenibilidad y escalabilidad.

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

-   **Python 3.8+**: [Descargar Python](https://www.python.org/downloads/)
-   **Microsoft ODBC Driver for SQL Server**: Necesario para que la librería `pyodbc` pueda comunicarse con la base de datos. [Descargar ODBC Driver](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
-   **Git**: Para clonar el repositorio. [Descargar Git](https://git-scm.com/downloads)
-   **SQL Server**: Una instancia de SQL Server (puede ser Express, Developer o una versión completa).

## 2. Guía de Instalación

Sigue estos pasos para configurar el entorno de desarrollo local.

### 2.1. Clonar el Repositorio

Abre una terminal y clona el repositorio desde GitHub:

```bash
git clone https://github.com/carlosDaniel2004/LEGAJO-DIGITAL.git
cd LEGAJO-DIGITAL
```

### 2.2. Crear y Activar el Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto en un entorno virtual.

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual (en Windows con PowerShell)
.\venv\Scripts\Activate.ps1
```

### 2.3. Instalar Dependencias

Con el entorno virtual activado, instala todas las librerías de Python necesarias:

```bash
pip install -r requirements.txt
```

### 2.4. Configurar la Base de Datos

1.  Abre SQL Server Management Studio (o tu cliente de SQL preferido).
2.  Ejecuta el script `BD0409.sql` (o el script de base de datos más reciente) para crear la base de datos `BaseDatosDiresa`, las tablas, los procedimientos almacenados y los roles.

### 2.5. Configurar las Variables de Entorno

La aplicación se configura mediante un archivo `.env`.

1.  En la raíz del proyecto, crea un archivo llamado `.env`.
2.  Copia y pega el siguiente contenido en el archivo, **ajustando los valores** a tu configuración local.

    ```dotenv
    # Clave secreta para la aplicación Flask (puedes generar una nueva)
    SECRET_KEY='tu-clave-secreta-aqui'

    # Configuración de la Base de Datos
    DB_DRIVER='{ODBC Driver 17 for SQL Server}'
    DB_SERVER='localhost'  # O la dirección de tu instancia de SQL Server
    DB_DATABASE='BaseDatosDiresa'

    # Credenciales para el usuario de la aplicación (con permisos limitados)
    DB_USERNAME='sistemas_admin' # O el usuario que corresponda al rol
    DB_PASSWORD='S1stemaasAdmin2025' # La contraseña del usuario de la aplicación

    # Credenciales para scripts de mantenimiento (con permisos elevados)
    DB_USERNAME_SA='sa' # O un usuario con privilegios de administrador
    DB_PASSWORD_SA='tu-contraseña-de-sa'

    # Configuración de Email (opcional, para 2FA)
    MAIL_SERVER='smtp.gmail.com'
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME='tu-correo@gmail.com'
    MAIL_PASSWORD='tu-contraseña-de-aplicacion-de-gmail'
    ```

## 3. Ejecutar la Aplicación

Una vez que todo está configurado, puedes iniciar el servidor de desarrollo de Flask:

```bash
python run.py
```

La aplicación estará disponible en tu navegador en la dirección `http://127.0.0.1:5000`.

## 4. Ejecutar Scripts de Utilidad

El proyecto incluye scripts en la raíz para tareas de mantenimiento:

-   **`resetearEmail.py`**: Para cambiar el email de un usuario directamente en la base de datos.
-   **`reset_password_direct.py`**: Para resetear la contraseña de un usuario.

Para ejecutarlos, asegúrate de tener el entorno virtual activado y usa:

```bash
python nombre_del_script.py
```
