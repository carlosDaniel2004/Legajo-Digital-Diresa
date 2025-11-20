# User Deactivation Integration - Implementation Summary

## Overview
Implemented cascading user deactivation/activation workflow where marking a personal record as inactive automatically deactivates the associated user account, and vice versa.

## Changes Made

### 1. **LegajoService Constructor Update**
**File:** `app/application/services/legajo_service.py`

```python
def __init__(self, personal_repository, audit_service, usuario_service=None):
    self._personal_repo = personal_repository
    self._audit_service = audit_service
    self._usuario_service = usuario_service  # NEW: Optional usuario_service injection
```

**Reason:** Allows LegajoService to access user deactivation methods through UsuarioService.

### 2. **delete_personal_by_id() Method Enhancement**
**File:** `app/application/services/legajo_service.py`

**New Functionality:**
- When a personal record is deactivated, the method now:
  1. Finds the associated user by email or DNI
  2. Calls `usuario_repo.deactivate_user(user_id)` to deactivate the account
  3. Logs the cascading deactivation action to the audit trail
  4. Handles errors gracefully without interrupting personal record deactivation

**Error Handling:** If user deactivation fails, it logs the error but continues with personal record deactivation.

### 3. **activate_personal_by_id() Method Enhancement**
**File:** `app/application/services/legajo_service.py`

**New Functionality:**
- Mirror of delete_personal_by_id() for reactivation:
  1. Finds the associated user by email or DNI
  2. Calls `usuario_repo.activate_user(user_id)` to reactivate the account
  3. Logs the cascading reactivation action
  4. Handles errors gracefully

### 4. **Repository Methods (Previously Added)**
**File:** `app/infrastructure/persistence/sqlserver_repository.py`

Both methods are already implemented:

```python
def deactivate_user(self, user_id):
    """Desactiva un usuario por su ID."""
    conn = get_db_write()
    cursor = conn.cursor()
    query = "UPDATE usuarios SET activo = 0 WHERE id_usuario = ?"
    cursor.execute(query, user_id)
    if cursor.rowcount == 0:
        raise ValueError("Usuario no encontrado.")
    conn.commit()

def activate_user(self, user_id):
    """Activa un usuario por su ID."""
    conn = get_db_write()
    cursor = conn.cursor()
    query = "UPDATE usuarios SET activo = 1 WHERE id_usuario = ?"
    cursor.execute(query, user_id)
    if cursor.rowcount == 0:
        raise ValueError("Usuario no encontrado.")
    conn.commit()
```

### 5. **Service Initialization**
**File:** `app/__init__.py`

```python
# Before:
app.config['LEGAJO_SERVICE'] = LegajoService(personal_repo, audit_service)

# After:
app.config['LEGAJO_SERVICE'] = LegajoService(personal_repo, audit_service, app.config['USUARIO_SERVICE'])
```

**Impact:** LegajoService now has access to UsuarioService for user state management.

## Workflow

### Deactivation Flow:
```
Admin marks personal record as inactive
    ↓
delete_personal_by_id() is called
    ↓
Personal record marked as inactive in database
    ↓
Find user by email/DNI
    ↓
Call usuario_repo.deactivate_user(user_id)
    ↓
User account marked as inactive (activo = 0)
    ↓
Audit entries created for both actions
```

### Activation Flow:
```
Admin reactivates personal record
    ↓
activate_personal_by_id() is called
    ↓
Personal record marked as active in database
    ↓
Find user by email/DNI
    ↓
Call usuario_repo.activate_user(user_id)
    ↓
User account marked as active (activo = 1)
    ↓
Audit entries created for both actions
```

## Database Changes
No additional database changes required. The workflow uses existing fields:
- **usuarios.activo** (0 = inactive, 1 = active)
- **personal.estado** or similar status field

## Audit Trail
Each operation creates separate audit entries:
- **Personal deactivation:** `'ELIMINAR (Desactivar)'`
- **Cascading user deactivation:** `'DESACTIVAR (Cascada)'`
- **Personal reactivation:** `'ACTIVAR (Reactivar)'`
- **Cascading user reactivation:** `'ACTIVAR (Cascada)'`
- **Errors:** `'ERROR_DESACTIVACION'` or `'ERROR_REACTIVACION'`

## Testing
Integration test created: `test_user_deactivation.py`

**Test Results:**
✅ LegajoService receives usuario_service
✅ deactivate_user method exists
✅ activate_user method exists
✅ delete_personal_by_id method operational
✅ activate_personal_by_id method operational

## Backward Compatibility
- usuario_service parameter is optional (default=None)
- Existing code without user service integration continues to work
- If usuario_service is not provided, only personal records are affected

## Security Considerations
1. User deactivation cascades automatically - no additional user confirmation needed
2. Audit trail tracks who deactivated the user (the admin who marked personal as inactive)
3. Errors in user deactivation don't block personal record deactivation
4. Database transaction management handled by existing methods

## Future Enhancements (Optional)
1. Add configuration flag to enable/disable cascading deactivation
2. Add email notification when user accounts are deactivated
3. Add batch operations for bulk personal record status changes
4. Add approval workflow for user deactivation
