# 🔐 Configuración de Permisos en SQL Server para DIRESA

## Problema
El usuario `DB_USERNAME_WRITE` no tenía permisos `INSERT` en la tabla `usuarios`, lo que impedía crear nuevos usuarios desde la aplicación.

## Solución Implementada
Se agregó una nueva conexión de administrador (`get_db_admin()`) que utiliza `DB_USERNAME_SYSTEMS_ADMIN` con permisos elevados para operaciones de creación de usuarios.

---

## 📋 Permisos Requeridos por Usuario

### 1. **DB_USERNAME_READ** (Usuario de Lectura)
Permisos necesarios:
```sql
GRANT SELECT ON DATABASE::BaseDatosDiresa TO [READ_USER];
```

Tablas principales (CRÍTICO):
- `usuarios` (SELECT) ✅
- `roles` (SELECT) ✅ **IMPORTANTE: Necesario para JOINs**
- `personales` (SELECT)
- `legajo_secciones` (SELECT)
- `bitacora` (SELECT)
- Todas las demás tablas de consulta

### 2. **DB_USERNAME_WRITE** (Usuario de Escritura)
Permisos necesarios:
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON DATABASE::BaseDatosDiresa TO [WRITE_USER];
-- Excepto en tabla 'usuarios' donde SOLO SELECT e INSERT limitado
REVOKE INSERT ON usuarios FROM [WRITE_USER]; -- Si fue otorgado
```

Operaciones permitidas:
- INSERT, UPDATE, DELETE en tablas de datos (personal, legajos, etc.)
- SELECT en todas las tablas
- UPDATE en propias credenciales

### 3. **DB_USERNAME_SYSTEMS_ADMIN** (Usuario Administrador)
Permisos necesarios:
```sql
-- Permisos de administrador en tabla usuarios
GRANT SELECT, INSERT, UPDATE, DELETE ON usuarios TO [SYSTEMS_ADMIN];
GRANT SELECT, INSERT, UPDATE, DELETE ON roles TO [SYSTEMS_ADMIN];

-- Permisos de auditoría
GRANT SELECT, INSERT ON bitacora TO [SYSTEMS_ADMIN];

-- Otros permisos necesarios
GRANT SELECT, INSERT, UPDATE, DELETE ON DATABASE::BaseDatosDiresa TO [SYSTEMS_ADMIN];
```

Operaciones permitidas:
- Crear nuevos usuarios
- Modificar roles de usuarios
- Acceder a auditoría
- Gestión completa de configuración

---

## 🔧 Script SQL para Asignar Permisos

Ejecuta estos comandos como administrador de SQL Server:

```sql
-- Cambiar a la base de datos correcta
USE BaseDatosDiresa;

-- 1. Crear logins si no existen (cambiar contraseñas)
CREATE LOGIN [diresa_read] WITH PASSWORD = 'TuContraseñaSegura123!';
CREATE LOGIN [diresa_write] WITH PASSWORD = 'TuContraseñaSegura456!';
CREATE LOGIN [diresa_admin] WITH PASSWORD = 'TuContraseñaSegura789!';

-- 2. Crear usuarios de base de datos
CREATE USER [diresa_read] FOR LOGIN [diresa_read];
CREATE USER [diresa_write] FOR LOGIN [diresa_write];
CREATE USER [diresa_admin] FOR LOGIN [diresa_admin];

-- 3. Asignar permisos de lectura
GRANT SELECT ON usuarios TO [diresa_read];
GRANT SELECT ON roles TO [diresa_read];  -- ⭐ IMPORTANTE: Necesario para JOINs en find_by_id, find_by_username, etc.
GRANT SELECT ON personales TO [diresa_read];
GRANT SELECT ON legajo_secciones TO [diresa_read];
GRANT SELECT ON bitacora TO [diresa_read];
-- Agregar otras tablas según sea necesario

-- 4. Asignar permisos de escritura
GRANT SELECT, INSERT, UPDATE, DELETE ON personales TO [diresa_write];
GRANT SELECT, INSERT, UPDATE, DELETE ON legajo_secciones TO [diresa_write];
GRANT SELECT, UPDATE ON usuarios TO [diresa_write]; -- Solo lectura y UPDATE
-- No permitir INSERT en usuarios para diresa_write

-- 5. Asignar permisos de administrador
GRANT SELECT, INSERT, UPDATE, DELETE ON usuarios TO [diresa_admin];
GRANT SELECT, INSERT, UPDATE, DELETE ON personales TO [diresa_admin];
GRANT SELECT, INSERT, UPDATE, DELETE ON legajo_secciones TO [diresa_admin];
GRANT SELECT, INSERT, UPDATE, DELETE ON roles TO [diresa_admin];
GRANT SELECT, INSERT ON bitacora TO [diresa_admin];

-- 6. Verificar permisos asignados
SELECT * FROM sys.user_permissions WHERE class_desc = 'OBJECT_OR_COLUMN';
```

---

## ✅ Verificación de Permisos

Para verificar que los permisos fueron asignados correctamente:

```sql
-- Verificar permisos de un usuario específico
SELECT 
    USER_NAME(grantee_principal_id) AS Usuario,
    permission_name AS Permiso,
    class_desc AS Tipo,
    OBJECT_NAME(major_id) AS Tabla
FROM sys.database_permissions
WHERE USER_NAME(grantee_principal_id) = 'diresa_write'
ORDER BY Tabla, Permiso;
```

---

## 🔒 Mejores Prácticas de Seguridad

1. **Cambiar Contraseñas**: Asegurate de usar contraseñas fuertes y únicas
2. **Principio de Menor Privilegio**: Cada usuario solo debe tener los permisos necesarios
3. **Auditoría**: Registra cambios en la tabla `bitacora`
4. **Rotación de Credenciales**: Cambia contraseñas periódicamente
5. **Variables de Entorno**: Mantén credenciales en `.env`, nunca en código

---

## 📝 Variables de Entorno Requeridas

En tu archivo `.env`:

```env
# Base de Datos - Usuario de Lectura
DB_USERNAME_READ=diresa_read
DB_PASSWORD_READ=TuContraseñaSegura123!

# Base de Datos - Usuario de Escritura
DB_USERNAME_WRITE=diresa_write
DB_PASSWORD_WRITE=TuContraseñaSegura456!

# Base de Datos - Usuario Administrador
DB_USERNAME_SYSTEMS_ADMIN=diresa_admin
DB_PASSWORD_SYSTEMS_ADMIN=TuContraseñaSegura789!
```

---

## 🐛 Solución de Problemas

### Error: "The INSERT permission was denied on the object 'usuarios'"
**Solución**: El usuario `DB_USERNAME_WRITE` intenta hacer INSERT en `usuarios`. Use `DB_USERNAME_SYSTEMS_ADMIN` para esta operación (ya implementado en `create_user`).

### Error: "Cannot open database"
**Verificar**:
- Nombre correcto de la base de datos
- El usuario tiene acceso a la base de datos
- El servidor SQL es accesible desde la aplicación

### Error: "Login failed for user"
**Verificar**:
- Credenciales correctas en `.env`
- El usuario existe en SQL Server
- La contraseña es correcta

---

## 📞 Contacto de Soporte

Para problemas con permisos de SQL Server:
1. Contacta con el administrador de base de datos
2. Proporciona el nombre de usuario y tabla afectada
3. Incluye el mensaje de error completo
