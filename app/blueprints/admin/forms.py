from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from wtforms.validators import ValidationError
from app.models import Categoria


class FormCategoria(FlaskForm):
    nombre      = StringField('Nombre',
                  validators=[DataRequired(), Length(min=2, max=80)])

    descripcion = TextAreaField('Descripción',
                  validators=[Length(max=200)])

    activa      = BooleanField('Activa', default=True)

    submit      = SubmitField('Guardar')

    def __init__(self, categoria_original=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guarda la categoría que se está editando para permitir su propio nombre
        self.categoria_original = categoria_original

    # Validación: el nombre debe ser único (menos el de la propia categoría en edición)
    def validate_nombre(self, nombre):
        categoria = Categoria.query.filter_by(nombre=nombre.data).first()
        if categoria and (self.categoria_original is None
                          or categoria.id != self.categoria_original.id):
            raise ValidationError('Ya existe una categoría con ese nombre.')
