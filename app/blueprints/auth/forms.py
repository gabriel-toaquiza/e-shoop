from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import Usuario

class FormRegistro(FlaskForm):
    nombre   = StringField('Nombre completo',
                validators=[DataRequired(), Length(min=3, max=100)])

    email    = StringField('Correo electrónico',
                validators=[DataRequired(), Email()])

    password = PasswordField('Contraseña',
                validators=[DataRequired(), Length(min=6)])

    confirm  = PasswordField('Confirmar contraseña',
                validators=[DataRequired(), EqualTo('password',
                message='Las contraseñas no coinciden')])

    submit   = SubmitField('Crear cuenta')

    # Validación personalizada: email único en la BD
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Este correo ya está registrado.')


class FormLogin(FlaskForm):
    email    = StringField('Correo electrónico',
                validators=[DataRequired(), Email()])

    password = PasswordField('Contraseña',
                validators=[DataRequired()])

    remember = BooleanField('Recordarme')

    submit   = SubmitField('Ingresar')