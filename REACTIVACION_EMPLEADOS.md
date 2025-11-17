# 🔄 Instrucciones para Reactivación de Empleados

## Cambios Realizados

Se ha añadido la funcionalidad de **reactivación de empleados** junto con la desactivación. Ahora:

- ✅ Si un empleado está **ACTIVO** → Se muestra botón **"Desactivar"** (rojo)
- ✅ Si un empleado está **INACTIVO** → Se muestra botón **"Activar"** (verde)

## Componentes Modificados

### 1. **Frontend (Templates - listar_personal.html)**
- Modificado el botón de acción para mostrar/ocultar según estado del empleado
- Añadido un nuevo modal de confirmación para activación
- El modal de desactivación ahora se llama `confirmDeactivateModal`

### 2. **JavaScript (main.js)**
- Añadida lógica para manejar dos modales:
  - `confirmDeactivateModal` → Desactivar empleado
  - `confirmActivateModal` → Activar empleado
- Ambos modales construyen correctamente la URL y configuran el formulario

### 3. **Backend (legajo_routes.py)**
- Nueva ruta: `POST /legajo/personal/<id>/reactivar`
- Maneja la reactivación con decoradores de seguridad
- Audita la acción en la tabla de auditoría

### 4. **Servicio (legajo_service.py)**
- Nuevo método: `activate_personal_by_id(personal_id, activating_user_id)`
- Verifica que el empleado exista
- Registra la acción en auditoría

### 5. **Repositorio (sqlserver_repository.py)**
- Nuevo método: `activate_by_id(personal_id)`
- Llama al stored procedure `sp_reactivar_personal`

## ⚠️ PASO CRÍTICO: Crear el Stored Procedure en SQL Server

**Necesitas ejecutar el siguiente script en tu SQL Server:**

**Ubicación del archivo:** `database_scripts/sp_reactivar_personal.sql`

```sql
CREATE OR ALTER PROCEDURE sp_reactivar_personal
    @id_personal INT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Verificar que el empleado exista
        IF NOT EXISTS (SELECT 1 FROM Personal WHERE id_personal = @id_personal)
        BEGIN
            RAISERROR('El empleado con ID %d no existe.', 16, 1, @id_personal);
            RETURN;
        END
        
        -- Reactivar el empleado
        UPDATE Personal
        SET activo = 1, 
            fecha_actualizacion = GETDATE()
        WHERE id_personal = @id_personal;
        
        -- Log de éxito
        PRINT 'Empleado ID ' + CAST(@id_personal AS VARCHAR(10)) + ' reactivado exitosamente.';
        
    END TRY
    BEGIN CATCH
        -- Capturar y re-lanzar errores
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH;
END;
```

### Cómo ejecutar:

1. Abre **SQL Server Management Studio**
2. Conéctate a tu instancia de SQL Server en Google Cloud
3. Abre una nueva ventana de consulta (Query)
4. Copia y pega el código del script
5. Haz clic en **Execute** (F5)

## 🧪 Pruebas

Una vez ejecutado el script, prueba lo siguiente:

1. **Desactiva un empleado activo:**
   - Ve a la lista de empleados
   - Haz clic en el botón rojo de "Eliminar" (basura)
   - Confirma la desactivación
   - El empleado debe mostrarse como "Inactivo"

2. **Activa un empleado inactivo:**
   - Observa que el botón ahora es **verde** (Activar)
   - Haz clic en el botón verde de "Activar"
   - Confirma la activación
   - El empleado debe mostrarse como "Activo"

3. **Verifica la auditoría:**
   - Las acciones de activación/desactivación deben aparecer en la tabla de auditoría
   - Consulta la tabla `Bitacora` para verificar:
     - Tipo de acción: `ELIMINAR (Desactivar)` o `ACTIVAR (Reactivar)`
     - Usuario que realizó la acción
     - Fecha y hora

## 🔐 Seguridad

- Solo usuarios con rol **`AdministradorLegajos`** pueden activar/desactivar empleados
- Cada acción se audita automáticamente
- Se mantiene el historial completo del empleado (no se elimina nada)

## 📌 Nota Importante

El error 405 que veías anteriormente ha sido **resuelto** junto con esta funcionalidad. El problema era que el JavaScript no estaba configurando correctamente la URL del formulario.

