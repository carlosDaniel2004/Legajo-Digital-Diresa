# Documentación Técnica del Sistema de Legajo Digital

Este documento proporciona una descripción detallada de la arquitectura, componentes y flujos de trabajo del sistema de Legajo Digital. Está diseñado para servir como guía de referencia para los desarrolladores y arquitectos de software.

## Tabla de Contenidos

1.  [Arquitectura General](#1-arquitectura-general)
2.  [Capa de Dominio (`app/domain`)](#2-capa-de-dominio-appdomain)
3.  [Capa de Aplicación (`app/application`)](#3-capa-de-aplicación-appapplication)
4.  [Capa de Infraestructura (`app/infrastructure`)](#4-capa-de-infraestructura-appinfrastructure)
5.  [Capa de Presentación (`app/presentation`)](#5-capa-de-presentación-apppresentation)
6.  [Configuración y Arranque](#6-configuración-y-arranque)
7.  [Flujo de una Solicitud](#7-flujo-de-una-solicitud)

## 1. Arquitectura General

El sistema está construido siguiendo una **Arquitectura en Capas (Layered Architecture)**, un diseño que promueve la **Separación de Responsabilidades (Separation of Concerns)**. Esta arquitectura está fuertemente influenciada por los principios de **Domain-Driven Design (DDD)** y **Clean Architecture**.

El objetivo principal es aislar la lógica de negocio (el dominio) de las tecnologías externas (como la base de datos o la interfaz de usuario). Esto hace que el sistema sea más fácil de mantener, probar y escalar.

La estructura se puede visualizar como una serie de capas concéntricas, donde las dependencias fluyen hacia adentro:

- **Capa de Presentación**: La interfaz de usuario (UI).
- **Capa de Aplicación**: Orquesta los casos de uso.
- **Capa de Dominio**: El corazón de la lógica de negocio.
- **Capa de Infraestructura**: Implementaciones técnicas (base de datos, APIs, etc.).

![Diagrama de Arquitectura en Capas](https://i.imgur.com/s9b4s2P.png)

### Principios Clave:

- **Regla de Dependencia**: El código fuente solo puede tener dependencias que apunten hacia adentro. Nada en una capa interna puede saber nada sobre una capa externa. Por ejemplo, el dominio no sabe qué base de datos se está utilizando.
- **Abstracción**: Las capas externas (como la infraestructura) implementan interfaces (contratos) definidas en las capas internas (el dominio). Esto permite intercambiar implementaciones sin afectar la lógica de negocio.

## 2. Capa de Dominio (`app/domain`)

Esta capa es el **corazón de la aplicación**. Contiene toda la lógica de negocio, las reglas y las entidades que son independientes de cualquier tecnología externa. No sabe nada sobre la base de datos, la web o cualquier otro detalle de implementación.

### 2.1. Modelos (`app/domain/models`)

Este directorio contiene las **Entidades de Negocio**. Son clases de Python que representan los conceptos fundamentales del sistema.

-   `usuario.py`: Representa a un usuario del sistema, con sus credenciales, roles y estado.
-   `personal.py`: Modela a un empleado de la organización, conteniendo toda su información personal.
-   `contrato.py`: Define la relación contractual de un empleado, incluyendo tipo, fechas y condiciones.
-   `documento.py`: Representa un documento físico o digital asociado a un legajo.
-   `legajo_seccion.py`: Modela la estructura y secciones que componen el legajo de un empleado.
-   `rol.py`: Define los roles y permisos dentro de la aplicación (ej. RRHH, Sistemas).
-   `solicitud_modificacion.py`: Representa una solicitud de un usuario para cambiar un dato en un legajo, que requiere aprobación.
-   *(y otros modelos que definen conceptos como `capacitacion`, `estudio`, `licencia`, etc.)*

### 2.2. Repositorios (`app/domain/repositories`)

Este directorio contiene las **Interfaces de Repositorio**. Una interfaz es un "contrato" que define qué operaciones de datos se pueden realizar con los modelos del dominio, pero no cómo se realizan. Esto es clave para la abstracción.

-   `i_usuario_repository.py`: Define métodos como `buscar_por_username`, `crear_usuario`, `actualizar_rol`, etc.
-   `i_personal_repository.py`: Define métodos para buscar, crear y actualizar la información del personal.
-   `i_auditoria_repository.py`: Define cómo se deben registrar los eventos de auditoría en el sistema.

Estas interfaces aseguran que la capa de aplicación pueda solicitar datos sin conocer los detalles de la base de datos subyacente.

## 3. Capa de Aplicación (`app/application`)

Esta capa actúa como un **orquestador**. No contiene lógica de negocio, sino que dirige a los objetos del dominio para que la ejecuten en respuesta a las solicitudes de la capa de presentación. Es el puente entre la UI y el Dominio.

### 3.1. Servicios (`app/application/services`)

Los servicios de aplicación implementan los **casos de uso** del sistema. Cada servicio encapsula una funcionalidad específica.

-   `usuario_service.py`: Maneja la lógica relacionada con la autenticación, 2FA (Two-Factor Authentication) y la gestión de sesiones de usuario.
-   `user_management_service.py`: Se encarga de los casos de uso administrativos sobre usuarios, como la creación, actualización de roles y cambio de estado.
-   `legajo_service.py`: Orquesta las operaciones sobre los legajos del personal, como la obtención de datos completos, la adición de documentos, etc.
-   `audit_service.py`: Proporciona una interfaz sencilla para que el resto de la aplicación pueda registrar eventos de auditoría importantes.
-   `email_service.py`: Abstrae el envío de correos electrónicos, como los códigos de 2FA o notificaciones.
-   `backup_service.py`: Contiene la lógica para ejecutar y registrar las copias de seguridad de la base de datos.
-   `solicitud_service.py`: Gestiona la creación y procesamiento de solicitudes de modificación de datos.
-   `workflow_service.py`: Maneja la lógica de los flujos de aprobación para las solicitudes.

### 3.2. Formularios (`app/application/forms.py`)

Este archivo define las clases de formularios utilizando la librería `Flask-WTF`. Su responsabilidad es:

1.  **Definir los campos** que se mostrarán en la interfaz de usuario.
2.  **Validar los datos** enviados por el usuario (ej. que un email tenga el formato correcto, que un campo requerido no esté vacío).

Esto asegura que los datos que llegan a los servicios de aplicación ya han sido limpiados y validados, evitando que lógica de validación de UI contamine las capas internas.

## 4. Capa de Infraestructura (`app/infrastructure` y `app/database`)

Esta capa contiene las **implementaciones concretas** de las tecnologías externas. Es el "cómo" se hacen las cosas que las capas internas solo definen.

### 4.1. Persistencia (`app/infrastructure/persistence`)

Aquí es donde se implementan las interfaces de repositorio definidas en el dominio.

-   `sqlserver_repository.py`: Esta clase contiene el código **específico para SQL Server**. Implementa las interfaces como `IUsuarioRepository` y traduce sus métodos (`buscar_por_username`) a consultas SQL (`SELECT * FROM Usuario WHERE username = ?`). Si el día de mañana se decidiera migrar a PostgreSQL, solo habría que crear un nuevo archivo `postgresql_repository.py` que implemente las mismas interfaces, sin tocar el dominio ni la aplicación.

### 4.2. Conector de Base de Datos (`app/database/connector.py`)

Este componente se encarga de una única responsabilidad: **gestionar la conexión con la base de datos**.

-   Lee la cadena de conexión desde la configuración de la aplicación.
-   Utiliza la librería `pyodbc` para establecer y mantener un pool de conexiones.
-   Proporciona métodos para obtener una conexión activa y ejecutar consultas, gestionando transacciones (commit, rollback) y el cierre de conexiones.

Abstrae el manejo de la conexión para que los repositorios no tengan que preocuparse por los detalles de bajo nivel de `pyodbc`.

## 5. Capa de Presentación (`app/presentation`)

Esta es la capa más externa, responsable de interactuar con el usuario final. En esta aplicación web, se encarga de manejar las peticiones HTTP y renderizar las plantillas HTML.

### 5.1. Rutas (`app/presentation/routes`)

Las rutas definen los endpoints (URLs) de la aplicación. El código está organizado en **Blueprints** de Flask, que permiten agrupar rutas por funcionalidad, manteniendo el código ordenado.

-   `auth_routes.py`: Maneja las URLs de autenticación, como `/login`, `/logout` y `/verify_2fa`.
-   `sistemas_routes.py`: Contiene los endpoints para el panel de administración del sistema (gestión de usuarios, auditoría, backups, etc.).
-   `rrhh_routes.py`: Define las rutas para el personal de Recursos Humanos, como la visualización de legajos y la gestión de personal.
-   `legajo_routes.py`: Rutas relacionadas con la gestión específica del contenido de un legajo.
-   `report_routes.py`: Endpoints para la generación de reportes.

Las funciones dentro de estos archivos actúan como **controladores**: reciben la petición, la delegan al servicio de aplicación correspondiente y, con el resultado, seleccionan y renderizan la plantilla adecuada.

### 5.2. Plantillas (`app/presentation/templates`)

Este directorio contiene los archivos HTML que conforman la interfaz de usuario. Se utiliza el motor de plantillas **Jinja2**, que permite:

-   **Herencia de plantillas**: Se define una `base.html` o `dashboard.html` con la estructura común (header, footer, sidebar), y las páginas específicas heredan de ella, rellenando solo los bloques de contenido.
-   **Lógica simple**: Permite usar bucles (`for`), condicionales (`if`) y mostrar variables pasadas desde el controlador (ej. `{{ current_user.username }}`).
-   **Reutilización de componentes**: Se pueden crear componentes pequeños (como `_form_helpers.html`) e incluirlos en varias páginas.

### 5.3. Archivos Estáticos (`app/presentation/static`)

Contiene los archivos que no cambian, como:

-   `css`: Hojas de estilo para dar formato y diseño a la aplicación.
-   `js`: Archivos JavaScript para la interactividad en el lado del cliente.
-   `img`: Imágenes y otros recursos gráficos.

### 5.4. Seguridad en el Frontend (CSRF)

Para proteger la aplicación contra ataques de Falsificación de Peticiones en Sitios Cruzados (CSRF), se utiliza la extensión `Flask-WTF`.

-   **Inclusión del Token**: Todos los formularios que realizan una acción de modificación de datos (`POST`, `PUT`, `DELETE`) deben incluir un token CSRF. Esto se logra añadiendo `{{ form.hidden_tag() }}` o un campo oculto `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
-   **Modales y JavaScript**: Se debe prestar especial atención a los formularios dentro de modales que se envían mediante JavaScript. Es fundamental que el token CSRF esté presente en el formulario del modal. La ausencia de este token resultará en un error `400 Bad Request`.

## 6. Configuración y Arranque

Estos archivos son responsables de inicializar y configurar la aplicación Flask, así como de ensamblar todas las capas.

-   `run.py`: Es el **punto de entrada** para ejecutar la aplicación. Su única responsabilidad es importar la función `create_app` y poner en marcha el servidor de desarrollo de Flask.

-   `config.py`: Define una clase `Config` que contiene todas las variables de configuración de la aplicación, como las claves secretas, la cadena de conexión a la base de datos, y la configuración del servidor de correo. Carga variables sensibles desde un archivo `.env` para no exponerlas en el código fuente.

-   `app/__init__.py`: Contiene la función `create_app()`, que actúa como una **fábrica de la aplicación**. Este es un patrón muy importante en Flask que permite crear múltiples instancias de la aplicación con diferentes configuraciones (por ejemplo, para producción, desarrollo o pruebas). Sus responsabilidades son:
    1.  Crear la instancia principal de la aplicación Flask.
    2.  Cargar la configuración desde el objeto `Config`.
    3.  Inicializar las extensiones de Flask (como `LoginManager` para la sesión de usuario).
    4.  **Realizar la Inyección de Dependencias**: Aquí es donde se "cablea" todo el sistema. Se crean las instancias de los repositorios (la implementación de SQL Server) y los servicios, inyectando las dependencias necesarias en cada uno (por ejemplo, se le pasa el repositorio de usuarios al servicio de usuarios).
    5.  Registrar los **Blueprints** de las rutas.

## 7. Flujo de una Solicitud

Para consolidar la comprensión de la arquitectura, sigamos el viaje de una petición a través del sistema.

**Caso de Uso**: Un usuario de RRHH solicita ver el legajo completo de un empleado con un DNI específico.

1.  **Petición HTTP (Navegador)**: El usuario hace clic en un enlace, generando una petición `GET` a la URL `/rrhh/ver_legajo/12345678`.

2.  **Capa de Presentación (Rutas)**:
    -   Flask recibe la petición.
    -   El blueprint de RRHH en `rrhh_routes.py` captura esta URL con una regla como `@rrhh_blueprint.route('/ver_legajo/<dni>')`.
    -   La función controladora asociada, `ver_legajo(dni)`, se ejecuta.

3.  **Capa de Aplicación (Servicios)**:
    -   El controlador no contiene lógica. Delega inmediatamente la tarea a un servicio de aplicación: `legajo_service.obtener_legajo_completo(dni)`.
    -   El `legajo_service` orquesta la operación. Podría, por ejemplo, llamar primero al `audit_service` para registrar el intento de acceso.

4.  **Capa de Dominio (Interfaces de Repositorio)**:
    -   El `legajo_service` necesita obtener los datos del empleado. Para ello, invoca un método de la **interfaz** de repositorio que tiene inyectada: `self.personal_repo.buscar_por_dni(dni)`.
    -   Es importante destacar que el servicio **no sabe** que está hablando con SQL Server. Solo conoce el contrato definido por la interfaz.

5.  **Capa de Infraestructura (Implementación del Repositorio)**:
    -   El motor de inyección de dependencias (configurado en `app/__init__.py`) determinó que `self.personal_repo` es una instancia de `SqlServerRepository`.
    -   Se ejecuta el método `buscar_por_dni` en `sqlserver_repository.py`, que construye y ejecuta la consulta SQL: `SELECT * FROM Personal WHERE dni = ?`.

6.  **Retorno de Datos y Modelado (Dominio)**:
    -   La base de datos devuelve los datos crudos.
    -   El `SqlServerRepository` utiliza estos datos para construir una instancia del modelo de dominio `Personal` (definido en `app/domain/models/personal.py`).

7.  **Flujo de Retorno**:
    -   El objeto `Personal` viaja de vuelta a través de las capas: Infraestructura -> Aplicación -> Presentación.

8.  **Renderizado (Presentación)**:
    -   La función controladora `ver_legajo(dni)` recibe el objeto `Personal`.
    -   Llama a `render_template('rrhh/ver_legajo_completo.html', personal=objeto_personal)`, pasando el objeto a la plantilla.
    -   Jinja2 utiliza los datos del objeto para rellenar el HTML.

9.  **Respuesta HTTP (Navegador)**: El servidor envía el HTML renderizado de vuelta al navegador del usuario, que ve la página completa del legajo.

---

Este flujo asegura que todas las solicitudes sean manejadas de manera consistente y que la lógica de negocio esté centralizada en los servicios de aplicación y el dominio.

---

### 9.2. Módulos de RRHH y Legajos (`rrhh_routes.py` y `legajo_routes.py`)

Estos dos módulos forman el núcleo funcional de la gestión de legajos. `rrhh_routes.py` se centra en las vistas de alto nivel para el personal de Recursos Humanos, mientras que `legajo_routes.py` maneja las operaciones detalladas de CRUD (Crear, Leer, Actualizar, Eliminar) sobre los legajos y sus componentes.

#### 9.2.1. Listado y Consulta de Personal (Rol: RRHH, AdminLegajos, Sistemas)

-   **Ruta Principal**: `/personal` (accesible desde `rrhh/personal` o `legajo/personal`)
-   **Función**: `listar_personal()`
-   **Descripción**: Muestra una lista paginada de todo el personal registrado. Permite filtrar por DNI y nombres. También muestra el estado de los documentos de cada empleado (si tienen documentos vencidos o por vencer).
-   **Flujo de Datos**:
    1.  El controlador llama a `legajo_service.get_all_personal_paginated()` para obtener la lista de empleados.
    2.  También llama a `legajo_service.check_document_status_for_all_personal()` para obtener las alertas de documentos.
    3.  Ambos métodos de servicio llaman a sus respectivos procedimientos almacenados en el repositorio (`sp_listar_personal_paginado` y `sp_listar_documentos_con_vencimiento`).
    4.  La plantilla `admin/listar_personal.html` o `rrhh/listar_personal.html` renderiza la tabla.

#### 9.2.2. Creación de un Nuevo Legajo (Rol: AdminLegajos)

-   **Ruta Principal**: `/personal/nuevo`
-   **Función**: `crear_personal()`
-   **Descripción**: Presenta un formulario (`PersonalForm`) para registrar a un nuevo empleado en el sistema.
-   **Flujo de Datos**:
    1.  Al cargar la página, se llama a `legajo_service.get_unidades_for_select()` para poblar el menú desplegable de unidades administrativas.
    2.  Tras enviar el formulario, el controlador llama a `legajo_service.register_new_personal()`.
    3.  El servicio invoca al procedimiento `sp_registrar_personal` en el repositorio y luego registra la acción en la bitácora a través del `audit_service`.

#### 9.2.3. Visualización de un Legajo Completo (Rol: RRHH, AdminLegajos, Sistemas)

-   **Ruta Principal**: `/personal/<id>`
-   **Función**: `ver_legajo()`
-   **Descripción**: Muestra una vista detallada de toda la información de un empleado, incluyendo sus datos personales, contratos, estudios, documentos, etc.
-   **Flujo de Datos**:
    1.  El controlador llama a `legajo_service.get_personal_details()`, **pasando el `personal_id` y el objeto `current_user`**.
    2.  El servicio primero obtiene todos los datos del legajo desde el repositorio (usando `sp_obtener_legajo_completo_por_personal`).
    3.  Luego, **realiza una validación de permisos**, asegurando que el rol del `current_user` (`RRHH`, `AdminLegajos`, o `Sistemas`) esté autorizado para ver el legajo solicitado. Esto actúa como una segunda capa de seguridad además de los decoradores de ruta.
    4.  La plantilla `admin/ver_legajo_completo.html` organiza y muestra toda esta información.

#### 9.2.4. Gestión de Documentos (Rol: AdminLegajos)

-   **Ruta Principal**: `/personal/<id>/documento/subir` (y otras para eliminar/ver)
-   **Función**: `subir_documento()`, `eliminar_documento()`, `visualizar_documento()`
-   **Descripción**: Permite añadir, eliminar (lógicamente) y visualizar los archivos adjuntos en el legajo de un empleado.
-   **Flujo de Datos (Subida)**:
    1.  El formulario de subida (`DocumentoForm`) se procesa en la ruta `subir_documento()`.
    2.  Se llama a `legajo_service.upload_document_to_personal()`, que valida el archivo (tamaño, tipo), calcula su hash y lo pasa al repositorio.
    3.  El repositorio ejecuta `sp_subir_documento` para guardar el archivo en la base de datos.
    4.  La acción se registra en la bitácora.

#### 9.2.5. Exportación a Excel (Rol: RRHH, AdminLegajos, Sistemas)

-   **Ruta Principal**: `/personal/exportar/general`
-   **Función**: `exportar_lista_general_excel()`
-   **Descripción**: Genera y descarga un archivo Excel con un reporte completo de todo el personal.
-   **Flujo de Datos**:
    1.  El controlador llama a `legajo_service.generate_general_report_excel()`.
    2.  El servicio obtiene los datos del repositorio (usando `sp_generar_reporte_general_personal`) y utiliza la librería `openpyxl` para construir el archivo Excel en memoria.
    3.  La acción se audita y el archivo se envía al navegador para su descarga.

---

### 9.3. Módulo de Autenticación (`auth_routes.py`)

Este módulo es responsable de gestionar la identidad y el acceso de los usuarios. Maneja el inicio de sesión, la verificación en dos pasos (2FA) y el cierre de sesión.

#### 9.3.1. Inicio de Sesión

-   **Ruta Principal**: `/login`
-   **Función**: `login()`
-   **Descripción**: Presenta el formulario de inicio de sesión y procesa las credenciales del usuario.
-   **Flujo de Datos**:
    1.  El usuario envía su nombre de usuario y contraseña a través del `LoginForm`. El formulario ahora incluye una opción "Mantenerme conectado" (`remember_me`).
    2.  El controlador llama a `usuario_service.attempt_login()`.
    3.  El servicio busca al usuario y verifica la contraseña.
    4.  Si las credenciales son correctas, el servicio genera un código 2FA y lo envía por correo.
    5.  El ID del usuario y el valor de `remember_me` se guardan en la sesión, y se redirige a la página de verificación 2FA.

#### 9.3.2. Verificación en Dos Pasos (2FA)

-   **Ruta Principal**: `/login/verify`
-   **Función**: `verify_2fa()`
-   **Descripción**: Pide al usuario el código de 6 dígitos enviado a su correo para completar el inicio de sesión.
-   **Flujo de Datos**:
    1.  El usuario introduce el código en el `TwoFactorForm`.
    2.  El controlador llama a `usuario_service.verify_2fa_code()`.
    3.  El servicio compara el código introducido con el hash guardado en la base de datos y verifica que no haya expirado.
    4.  Si el código es **incorrecto**, se muestra un mensaje de error.
    5.  Si el código es **correcto**, se completa el proceso:
        -   Se actualiza la fecha de `ultimo_login`.
        -   Se inicia la sesión del usuario con `login_user(user, remember=valor_guardado)`. Si la opción "Mantenerme conectado" fue marcada, la sesión será persistente.
        -   Se limpia la sesión de 2FA.
        -   Se redirige al usuario a la ruta raíz (`/`).

#### 9.3.3. Enrutamiento Post-Login

-   **Ruta Principal**: `/`
-   **Función**: `index()`
-   **Descripción**: Actúa como un enrutador inteligente después de que el usuario ha iniciado sesión.
-   **Flujo de Datos**:
    1.  El decorador `@login_required` asegura que solo usuarios autenticados puedan acceder.
    2.  La función inspecciona el rol del `current_user`.
    3.  Redirige al usuario al dashboard que le corresponde (`sistemas.dashboard`, `rrhh.inicio_rrhh`, etc.).
    4.  Esto resuelve el bucle de redirección que ocurría anteriormente y centraliza la lógica de enrutamiento post-login.

#### 9.3.4. Cierre de Sesión

-   **Ruta Principal**: `/logout`
-   **Función**: `logout()`
-   **Descripción**: Cierra la sesión activa del usuario.
-   **Flujo de Datos**:
    1.  El controlador llama a la función `logout_user()` de Flask-Login, que elimina los datos del usuario de la sesión.
    2.  Se muestra un mensaje de confirmación.
    3.  Se redirige al usuario a la página de login.

---

## 10. Configuración y Variables de Entorno

La configuración de la aplicación se gestiona a través de un archivo `.env` en la raíz del proyecto, que es cargado por el objeto `Config` en `config.py`.

-   **`SECRET_KEY`**: Una cadena larga y aleatoria usada por Flask para firmar criptográficamente las sesiones de usuario. Es vital para la seguridad.
-   **`DB_DRIVER`**: El driver de ODBC que se usará para la conexión. Generalmente `{ODBC Driver 17 for SQL Server}`.
-   **`DB_SERVER`**: La dirección IP o el nombre de host de la instancia de SQL Server.
-   **`DB_DATABASE`**: El nombre de la base de datos a la que se conectará la aplicación.
-   **`DB_USERNAME` / `DB_PASSWORD`**: Las credenciales del usuario de la aplicación. Este usuario debe tener los permisos mínimos necesarios definidos en los scripts de roles de la base de datos.
-   **`DB_USERNAME_SA` / `DB_PASSWORD_SA`**: Credenciales de un usuario con privilegios elevados (como `sa` o un administrador). Se utilizan exclusivamente para scripts de mantenimiento que se ejecutan fuera de la aplicación, como `resetearEmail.py`.
-   **`MAIL_*`**: Variables para configurar el servidor de correo SMTP, necesarias para enviar los códigos de la autenticación en dos pasos (2FA).

## 11. Componentes Principales y Utilidades

El proyecto cuenta con varios componentes transversales que dan soporte a toda la aplicación.

### 11.1. Decoradores (`app/decorators.py`)

-   **`@role_required(*roles)`**: Este es el decorador de seguridad principal de la aplicación. Se coloca encima de una definición de ruta para restringir el acceso solo a los usuarios que posean uno de los roles especificados. Si un usuario no cumple con el requisito, se le muestra un mensaje de error y se le redirige.

-   **`@limiter.limit`**: Proveniente de la extensión `Flask-Limiter`, este decorador se aplica a rutas sensibles (especialmente `login` y `verify_2fa`) para limitar el número de peticiones que una IP puede realizar en un periodo de tiempo. Es la defensa principal contra ataques de fuerza bruta y escaneo de credenciales.

### 11.2. Conector de Base de Datos (`app/database/connector.py`)

-   Este módulo abstrae la gestión de la conexión a la base de datos. Utiliza la librería `pyodbc` para crear y gestionar un "pool" de conexiones. Su principal responsabilidad es proporcionar una conexión funcional al resto de la aplicación (específicamente a los repositorios) sin que estos necesiten conocer los detalles de la cadena de conexión.

### 11.3. Paginación (`app/utils/pagination.py`)

-   **`SimplePagination`**: Una clase de utilidad que encapsula la lógica de la paginación. Recibe la lista de resultados de la página actual, el número de página, los elementos por página y el total de registros. Con esta información, calcula automáticamente si hay una página siguiente/anterior y genera los números de página para los controles de navegación, simplificando enormemente el código en las plantillas.

### 11.4. Filtros de Plantilla Personalizados

-   **`localtime`**: Para solucionar discrepancias de zona horaria entre el servidor de base de datos (que opera en UTC) y los usuarios locales, se ha definido un filtro de plantilla personalizado en `app/__init__.py`. Este filtro, `| localtime`, se puede aplicar a cualquier objeto de fecha y hora en las plantillas Jinja2 para convertirlo a la zona horaria de Perú (UTC-5) antes de mostrarlo, asegurando que los usuarios siempre vean la hora correcta.

## 12. Estructura del Frontend

El frontend está construido con un sistema de plantillas Jinja2 y utiliza el framework Bootstrap para el diseño responsivo.

### 12.1. Herencia de Plantillas

La estructura de herencia es clave para evitar la duplicación de código HTML.

1.  **`base.html`**: Es la plantilla raíz. Define la estructura HTML básica (`<html>`, `<head>`, `<body>`), enlaza los archivos CSS y JS principales, y define los bloques (`block`) que las plantillas hijas pueden sobrescribir.
2.  **`dashboard.html`**: Hereda de `base.html`. Define la estructura visual común para todas las páginas internas del sistema, incluyendo la barra de navegación superior (header), la barra lateral (sidebar) y el pie de página (footer). Define un bloque `dashboard_content` para que las páginas específicas inserten su contenido.
3.  **Páginas de Módulo (ej. `sistemas/auditoria.html`)**: Heredan de `dashboard.html` y solo necesitan rellenar el bloque `dashboard_content` con su contenido específico (tablas, formularios, etc.), reutilizando toda la estructura circundante.

### 12.2. Activos Estáticos (`app/presentation/static`)

-   **`css/`**: Contiene las hojas de estilo. `prototipo_style.css` es el archivo principal con los estilos personalizados de la aplicación.
-   **`js/`**: Archivos JavaScript para la interactividad del cliente.
-   **`img/`**: Logos e imágenes utilizados en la interfaz.

### 12.3. Seguridad en el Frontend (CSRF)

Para proteger la aplicación contra ataques de Falsificación de Peticiones en Sitios Cruzados (CSRF), se utiliza la extensión `Flask-WTF`.

-   **Inclusión del Token**: Todos los formularios que realizan una acción de modificación de datos (`POST`, `PUT`, `DELETE`) deben incluir un token CSRF. Esto se logra añadiendo `{{ form.hidden_tag() }}` o un campo oculto `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
-   **Modales y JavaScript**: Se debe prestar especial atención a los formularios dentro de modales que se envían mediante JavaScript. Es fundamental que el token CSRF esté presente en el formulario del modal. La ausencia de este token resultará en un error `400 Bad Request`.

## 13. Estrategia de Manejo de Errores y Logging

La aplicación emplea una estrategia de manejo de errores robusta y en varias capas para garantizar la estabilidad y facilitar la depuración.

-   **Validación de Formularios**: Los errores de entrada del usuario (campos vacíos, formatos incorrectos) se capturan a través de `Flask-WTF` y se muestran junto al campo correspondiente en el formulario.

-   **Excepciones de Negocio**: Errores esperados (ej. "DNI ya existe") se capturan en los controladores (`try...except`) y se muestran al usuario a través de mensajes `flash`, proporcionando feedback claro.

-   **Manejadores de Errores Globales**: La aplicación utiliza un sistema centralizado para manejar errores HTTP comunes, como 404 (No Encontrado) y 500 (Error Interno del Servidor).
    -   **`app/presentation/routes/error_routes.py`**: Este módulo define manejadores de errores a nivel de aplicación usando `@error_bp.app_errorhandler`.
    -   **`app/presentation/templates/errors/`**: Contiene plantillas HTML personalizadas (`404.html`, `500.html`) que se muestran al usuario, ofreciendo una experiencia más amigable que las páginas de error por defecto.

-   **Logging Profesional en Archivos**: Para errores inesperados (excepciones no controladas), el sistema está configurado para no exponer detalles técnicos al usuario. En su lugar:
    1.  Se muestra la página genérica `500.html`.
    2.  El traceback completo del error se registra en un archivo de log. Esta configuración se realiza en `app/__init__.py` y utiliza `logging.handlers.RotatingFileHandler`.
    3.  Los logs se guardan en el directorio `logs/app.log`, rotando automáticamente para evitar que el archivo crezca indefinidamente. Esto es crucial para el diagnóstico de problemas en un entorno de producción.

## 14. Consideraciones para Despliegue en Producción

Para llevar esta aplicación a un entorno de producción, se deben considerar los siguientes puntos:

-   **Servidor WSGI**: El servidor de desarrollo de Flask (`app.run()`) no es adecuado para producción. Se debe utilizar un servidor WSGI robusto como **Gunicorn** (en Linux) o **Waitress** (en Windows).
-   **Variables de Entorno**: El archivo `.env` no debe subirse al repositorio de código. En un servidor de producción, estas variables se deben configurar directamente en el sistema operativo o a través del panel de control del servicio de hosting.
-   **Modo Debug**: La variable `DEBUG` de Flask debe estar establecida en `False` en producción para evitar la exposición de información sensible de depuración.
-   **Gestión de Activos Estáticos**: Para un mejor rendimiento, se podría configurar un servidor web como Nginx para servir los archivos estáticos directamente, liberando al servidor de la aplicación de esa tarea.
-   **Seguridad de la Base de Datos**: Asegurarse de que la base de datos no sea accesible públicamente desde internet y que el usuario de la aplicación tenga únicamente los permisos definidos en los roles, siguiendo el principio de mínimo privilegio. Es crucial verificar que el usuario de la BD tenga permisos de `EXECUTE` sobre todos los procedimientos almacenados que la aplicación necesita invocar.

---
