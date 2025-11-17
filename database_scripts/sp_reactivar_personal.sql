-- =====================================================
-- Stored Procedure: sp_reactivar_personal
-- Descripción: Reactiva un empleado previamente desactivado
-- Autor: Sistema de Legajo Digital
-- Fecha: 2025-11-17
-- =====================================================

USE [BaseDatosDiresa]
GO

IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'sp_reactivar_personal')
BEGIN
    DROP PROCEDURE [dbo].[sp_reactivar_personal];
END
GO

CREATE PROCEDURE [dbo].[sp_reactivar_personal]
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
        SET activo = 1
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
GO
