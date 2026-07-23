"""
Formularios de KeyServ.

NUEVO en Fase 3 — antes no existía `forms.py` y toda la validación se hacía
a mano en `views.py` con `request.POST.get(...)` sin manejo de errores.
Centralizar la validación acá evita, por ejemplo, que un `int()` sobre un
input no numérico tire un error 500 sin control.
"""
from django import forms
from django.contrib.auth.hashers import make_password

from .models import Usuario, Region, Comuna, TipoCuenta, Publicaciones, Valoracion, Mensaje


class RegistroForm(forms.Form):
    """Formulario de registro de un nuevo Usuario (cliente y/o proveedor)."""
    rut = forms.CharField(max_length=10, label='RUT')
    nombre1 = forms.CharField(max_length=40, label='Nombre')
    nombre2 = forms.CharField(max_length=40, required=False, label='Segundo nombre')
    apellido1 = forms.CharField(max_length=40, label='Apellido')
    apellido2 = forms.CharField(max_length=40, required=False, label='Segundo apellido')
    # RNF011 del PDF: "mayor de edad" — se valida en clean_edad().
    edad = forms.IntegerField(min_value=0, max_value=120, label='Edad')
    telefono = forms.IntegerField(label='Teléfono')
    email = forms.EmailField(label='Correo electrónico')
    direccion = forms.CharField(max_length=80, required=False, label='Dirección')
    region = forms.ModelChoiceField(queryset=Region.objects.all(), label='Región')
    comuna = forms.ModelChoiceField(queryset=Comuna.objects.all(), label='Comuna')
    tipo_cuenta = forms.ModelChoiceField(queryset=TipoCuenta.objects.all(), label='Tipo de cuenta')
    es_proveedor = forms.BooleanField(required=False, label='¿Ofreces servicios como proveedor?')
    # RNF010 del PDF: contraseña mínima de 6 caracteres.
    password = forms.CharField(widget=forms.PasswordInput, min_length=6, label='Contraseña')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    def clean_edad(self):
        """RNF011: el usuario debe ser mayor de edad."""
        edad = self.cleaned_data['edad']
        if edad < 18:
            raise forms.ValidationError('Debes ser mayor de edad para registrarte.')
        return edad

    def clean_email(self):
        """Evita registrar dos cuentas con el mismo correo."""
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean(self):
        """Valida que las dos contraseñas ingresadas coincidan."""
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

    def crear_usuario(self, transaccion):
        """Construye y guarda el Usuario a partir de los datos ya validados. `transaccion` es la Transaccion asociada al alta de cuenta."""
        usuario = Usuario(
            rut_usuario=self.cleaned_data['rut'],
            nombre_usuario=self.cleaned_data['nombre1'],
            nombre2_usuario=self.cleaned_data.get('nombre2') or None,
            apellido_usuario=self.cleaned_data['apellido1'],
            apellido2_usuario=self.cleaned_data.get('apellido2') or None,
            edad=self.cleaned_data['edad'],
            telefono=self.cleaned_data['telefono'],
            email=self.cleaned_data['email'],
            direccion_usuario=self.cleaned_data.get('direccion') or None,
            comuna=self.cleaned_data['comuna'],
            tipo_cuenta=self.cleaned_data['tipo_cuenta'],
            es_proveedor=self.cleaned_data.get('es_proveedor', False),
            transaccion=transaccion,
            password=make_password(self.cleaned_data['password']),
        )
        usuario.save()
        return usuario


class LoginForm(forms.Form):
    """Formulario de inicio de sesión (RF003)."""
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')


class PublicacionForm(forms.ModelForm):
    """Formulario para que un proveedor cree/edite una Publicacion de servicio (RF002)."""

    class Meta:
        model = Publicaciones
        fields = ['titulo', 'sub_titulo', 'descripcion_publicacion']


class ValoracionForm(forms.ModelForm):
    """Formulario para calificar a otro usuario tras completar un servicio (caso de uso UML del PDF)."""

    class Meta:
        model = Valoracion
        fields = ['puntuacion', 'comentario']

    def clean_puntuacion(self):
        """La puntuación debe ser una calificación por estrellas válida (1 a 5)."""
        puntuacion = self.cleaned_data['puntuacion']
        if not 1 <= puntuacion <= 5:
            raise forms.ValidationError('La puntuación debe estar entre 1 y 5 estrellas.')
        return puntuacion


class MensajeForm(forms.ModelForm):
    """Formulario para enviar un mensaje dentro de una Conversacion (mensajería, Fase 4)."""

    class Meta:
        model = Mensaje
        fields = ['contenido']
        widgets = {'contenido': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Escribe tu mensaje...'})}


class ReautenticacionForm(forms.Form):
    """
    Confirma que quien aprieta el botón realmente conoce la contraseña de la
    sesión activa — lo exige el BPMN "Proceso de contratación" del PDF
    (PAGE 136-137: "ambos se re-autentican") antes de confirmar/completar
    una Contratacion.
    """
    password = forms.CharField(widget=forms.PasswordInput, label='Confirma tu contraseña')
