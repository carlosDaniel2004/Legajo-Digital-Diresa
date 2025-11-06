# RUTA: app/application/forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Regexp, Optional, Email, NumberRange, EqualTo, ValidationError
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, FileField, BooleanField


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Mantenerme conectado')
    submit = SubmitField('Iniciar Sesión')

class TwoFactorForm(FlaskForm):
    code = StringField('Código de 6 dígitos', validators=[
        DataRequired(),
        Length(min=6, max=6, message="El código debe tener 6 dígitos."),
        Regexp('^[0-9]*$', message="El código solo debe contener números.")
    ])
    submit = SubmitField('Verificar y Entrar')

class FiltroPersonalForm(FlaskForm):
    dni = StringField('Buscar por DNI', validators=[Optional(), Length(max=8)])
    nombres = StringField('Buscar por Nombre o Apellidos', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Buscar')

class PersonalForm(FlaskForm):
    """Formulario para crear y editar los datos de una persona."""
    dni = StringField('DNI', validators=[DataRequired(), Length(min=8, max=8, message="El DNI debe tener 8 dígitos.")])
    nombres = StringField('Nombres', validators=[DataRequired(), Length(max=50)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(max=50)])
    
    sexo = SelectField('Sexo', choices=[('', '-- Seleccione --'), ('M', 'Masculino'), ('F', 'Femenino')], validators=[DataRequired()])
    fecha_nacimiento = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[Length(max=20)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email(), Length(max=100)])
    direccion = StringField('Dirección', validators=[Length(max=200)])
    estado_civil = StringField('Estado Civil', validators=[Length(max=20)])
    nacionalidad = StringField('Nacionalidad', validators=[DataRequired(), Length(max=50)], default='Peruana')
    
    id_unidad = SelectField('Unidad Administrativa', coerce=str, validators=[DataRequired(message="Debe seleccionar una unidad.")])
    fecha_ingreso = DateField('Fecha de Ingreso', format='%Y-%m-%d', validators=[DataRequired()])
    
    submit = SubmitField('Registrar Personal')

    def validate_id_unidad(self, field):
        if field.data == '0':
            raise ValidationError('Debe seleccionar una unidad válida.')

class DocumentoForm(FlaskForm):
    id_seccion = SelectField('Sección del Legajo', coerce=int, validators=[NumberRange(min=1, message="Debe seleccionar una sección.")])
    id_tipo = SelectField('Tipo de Documento', coerce=int, validators=[NumberRange(min=1, message="Debe seleccionar un tipo de documento.")])
    descripcion = TextAreaField('Descripción (Opcional)', validators=[Optional(), Length(max=500)])
    archivo = FileField('Seleccionar Archivo', validators=[
        DataRequired(message="Debe seleccionar un archivo."),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'], '¡Solo se permiten archivos PDF, de imagen (PNG, JPG) o de Office (DOCX, XLSX)!')
    ])
    submit = SubmitField('Subir Documento')

# 🚨 CLASE AÑADIDA PARA EL MÓDULO DE SISTEMAS (Gestión de Usuarios) 🚨
class UserManagementForm(FlaskForm):
    """
    Formulario para la creación y edición de usuarios por el Encargado de Sistemas.
    Incluye campos para el rol y la activación.
    """
    # Campos básicos (necesarios en edición y creación)
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email(), Length(max=100)])
    
    # Campo para el Rol (los IDs 1, 3, etc. que verificamos en la BD)
    # Los choices se deben cargar dinámicamente en la ruta 'crear_usuario' o 'editar_usuario'
    id_rol = SelectField('Rol de Acceso', coerce=int, validators=[DataRequired()]) 
    
    # Campo de Contraseña solo para CREAR usuario
    password = PasswordField('Contraseña (Solo para Nuevo Usuario)', validators=[
        Optional(), 
        EqualTo('confirm', message='Las contraseñas deben coincidir.')
    ])
    confirm = PasswordField('Confirmar Contraseña')
    
    # Campo Activo/Inactivo
    activo = BooleanField('Usuario Activo') 
    
    submit = SubmitField('Guardar Cambios')