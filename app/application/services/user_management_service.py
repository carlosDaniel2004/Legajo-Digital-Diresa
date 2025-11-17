# app/application/services/user_management_service.py

from werkzeug.security import generate_password_hash

class UserManagementService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def get_all_users(self):
        """
        Obtiene una lista completa de usuarios y sus roles.
        """
        try:
            users = self.user_repository.get_all_users_with_roles()
            return users, None
        except Exception as e:
            return [], f"Error al obtener la lista de usuarios: {e}"

    def get_user_by_id_for_editing(self, user_id):
        """
        Obtiene los datos de un usuario para la página de edición.
        """
        # Reutilizamos el repositorio de usuario que ya tiene un find_by_id
        return self.user_repository.find_by_id(user_id)

    def get_all_roles_for_select(self):
        """
        Obtiene todos los roles en un formato adecuado para un SelectField.
        """
        roles = self.user_repository.get_all_roles()
        return [(role.id_rol, role.nombre_rol) for role in roles]

    def update_user_role(self, user_id, new_role_id):
        """
        Valida y actualiza el rol de un usuario.
        """
        try:
            self.user_repository.update_user_role(user_id, new_role_id)
            return "El rol del usuario ha sido actualizado correctamente.", "success"
        except Exception as e:
            return f"Error al actualizar el rol: {e}", "danger"
        

    def toggle_user_status(self, user_id, current_admin_id):
        """
        Alterna el estado de un usuario y previene que un administrador se desactive a sí mismo.
        """
        if user_id == current_admin_id:
            return "No puede desactivar su propia cuenta de administrador.", "danger"
        
        try:
            self.user_repository.toggle_user_active_status(user_id)
            return "El estado del usuario ha sido actualizado correctamente.", "success"
        except Exception as e:
            return f"Error al cambiar el estado del usuario: {e}", "danger"

    def update_user_password(self, user_id, new_password):
        """
        Actualiza la contraseña de un usuario.
        """
        try:
            hashed_password = generate_password_hash(new_password)
            self.user_repository.update_user_password(user_id, hashed_password)
            return "La contraseña del usuario ha sido actualizada correctamente.", "success"
        except Exception as e:
            return f"Error al actualizar la contraseña: {e}", "danger"


    def create_new_user(self, form_data):
        """
        Hashea la contraseña y crea un nuevo usuario.
        """
        try:
            username = form_data.get('username')
            email = form_data.get('email')
            role_id = form_data.get('rol')
            password = form_data.get('password')

            # Hashear la contraseña antes de guardarla
            hashed_password = generate_password_hash(password)

            self.user_repository.create_user(username, hashed_password, role_id, email)
            return f"Usuario '{username}' creado exitosamente.", "success"
        except Exception as e:
            # Captura errores específicos de la base de datos, como un username duplicado
            return f"Error al crear el usuario: {e}", "danger"    
        
            