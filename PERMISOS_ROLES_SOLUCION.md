# 🔐 Solución Rápida: Error 229 - Permisos en Tabla ROLES

## ❌ El Problema

```
Error al obtener usuario por ID 10: The SELECT permission was denied 
on the object 'roles', database 'BaseDatosDiresa'
```

**Causa**: El usuario de lectura (`diresa_read`) no tiene permiso `SELECT` en la tabla `roles`.

---

## ✅ La Solución (2 opciones)

### **Opción 1: Comando SQL Directo (Rápido)**

Abre **SQL Server Management Studio** como administrador y ejecuta:

```sql
USE BaseDatosDiresa;
GRANT SELECT ON roles TO [diresa_read];
```

**¡Listo!** El error desaparecerá inmediatamente.

---

### **Opción 2: Script SQL Completo (Recomendado)**

1. Abre **SQL Server Management Studio**
2. Ve a: `Archivo > Abrir > Archivo`
3. Selecciona: `fix_permissions_roles.sql` (en la raíz del proyecto)
4. Haz clic en **Ejecutar** (o presiona F5)

Este script:
- ✅ Muestra permisos actuales
- ✅ Otorga el permiso faltante
- ✅ Verifica que se otorgó correctamente

---

## 📋 Permisos Mínimos Requeridos para READ_USER

La tabla `roles` es **CRÍTICA** porque se usa en:
- Búsqueda de usuarios por ID
- Búsqueda de usuarios por username
- Búsqueda de usuarios por email
- Cualquier JOIN que obtenga información del rol

**Tabla de Permisos necesarios:**

| Tabla | Permiso | ¿Por qué? |
|-------|---------|-----------|
| `usuarios` | SELECT | Login, obtener datos de usuario |
| `roles` | SELECT | ⭐ JOINs para obtener nombre_rol |
| `personales` | SELECT | Datos de empleados |
| `legajo_secciones` | SELECT | Información de legajos |
| `bitacora` | SELECT | Auditoría de acciones |

---

## 🔍 Verificación

Para confirmar que el permiso fue otorgado:

```sql
USE BaseDatosDiresa;

-- Ver permisos de diresa_read
SELECT 
    USER_NAME(grantee_principal_id) AS Usuario,
    permission_name AS Permiso,
    OBJECT_NAME(major_id) AS Tabla
FROM sys.database_permissions
WHERE USER_NAME(grantee_principal_id) = 'diresa_read'
ORDER BY Tabla;
```

Deberías ver una fila con:
- **Usuario**: diresa_read
- **Permiso**: SELECT
- **Tabla**: roles

---

## 🚨 Si el Error Persiste

Si después de otorgar el permiso el error sigue:

1. **Cierra todas las conexiones activas** a la base de datos
2. **Reinicia la aplicación Flask**
3. **Intenta de nuevo**

Si aún falla, verifica:
```sql
-- Confirmar que el usuario existe
SELECT * FROM sys.sysusers WHERE name = 'diresa_read';

-- Ver estado del usuario
SELECT state_desc FROM sys.database_principals 
WHERE name = 'diresa_read';
```

---

## 📞 Contacto

Para problemas adicionales de permisos, revisa:
- `SQL_PERMISSIONS.md` - Guía completa de permisos
- `fix_permissions_roles.sql` - Script de corrección

**El permiso SELECT en `roles` es esencial para que la aplicación funcione correctamente.**
