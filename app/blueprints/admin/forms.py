from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (StringField, TextAreaField, BooleanField, SubmitField,
                     DecimalField, IntegerField, SelectField, MultipleFileField)
from wtforms.validators import (DataRequired, Length, NumberRange, Optional,
                                ValidationError)
from app.models import Categoria


class FormCategoria(FlaskForm):
    nombre      = StringField('Nombre',
                  validators=[DataRequired(), Length(min=2, max=80)])

    descripcion = TextAreaField('Descripción',
                  validators=[Length(max=200)])

    activa      = BooleanField('Activa', default=True)

    imagen        = FileField('Imagen',
                    validators=[FileAllowed(['jpg', 'jpeg', 'webp'],
                                'Solo se permiten imágenes jpg, jpeg o webp.'),
                                FileSize(max_size=2 * 1024 * 1024,
                                message='La imagen no debe superar los 2 MB.')])

    quitar_imagen = BooleanField('Eliminar la imagen actual')

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


class FormProducto(FlaskForm):
    nombre       = StringField('Nombre',
                   validators=[DataRequired(), Length(min=2, max=150)])

    descripcion  = TextAreaField('Descripción',
                   validators=[Optional(), Length(max=1000)])

    precio       = DecimalField('Precio', places=2,
                   validators=[DataRequired(),
                               NumberRange(min=0, message='El precio no puede ser negativo.')])

    stock        = IntegerField('Stock', default=0,
                   validators=[Optional(),
                               NumberRange(min=0, message='El stock no puede ser negativo.')])

    categoria_id = SelectField('Categoría', coerce=int,
                   validators=[DataRequired()])

    imagen       = FileField('Imagen',
                   validators=[FileAllowed(['jpg', 'jpeg', 'webp'],
                               'Solo se permiten imágenes jpg, jpeg o webp.'),
                               FileSize(max_size=2 * 1024 * 1024,
                               message='La imagen no debe superar los 2 MB.')])

    quitar_imagen = BooleanField('Eliminar la imagen actual')

    imagenes_nuevas = MultipleFileField('Imágenes adicionales (máx. 4)')

    personalizable = BooleanField('Producto personalizable', default=False)

    instrucciones_personalizacion = TextAreaField(
                   'Instrucciones para el cliente',
                   validators=[Optional(), Length(max=500)])

    activo       = BooleanField('Activo', default=True)

    submit       = SubmitField('Guardar')
