"""
Formularios de KeyServ.

NUEVO en Fase 3 — antes no existía `forms.py` y toda la validación se hacía
a mano en `views.py` con `request.POST.get(...)` sin manejo de errores.
Centralizar la validación acá evita, por ejemplo, que un `int()` sobre un
input no numérico tire un error 500 sin control.
"""
from types import SimpleNamespace

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password

from .models import Consulta, Usuario, Region, Comuna, TipoCuenta, Publicaciones, Valoracion, Mensaje


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
    # RNF010 del PDF pedía mínimo 6 — se subió a 8 (mínimo real que además
    # aplica AUTH_PASSWORD_VALIDATORS.MinimumLengthValidator en settings.py,
    # ver clean() más abajo) y se sumó validación de fondo: contraseñas de la
    # lista de las más comunes, solo numéricas, o muy parecidas a tu propio
    # nombre/correo quedan rechazadas — antes "123456a" pasaba sin problema.
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Contraseña')
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
        """Valida que las dos contraseñas coincidan y que la contraseña sea real (reusa AUTH_PASSWORD_VALIDATORS de settings.py, no reglas propias)."""
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Las contraseñas no coinciden.')

        if password:
            # SimpleNamespace con los nombres de atributo que esperan los
            # validators nativos (username/first_name/last_name/email) —
            # Usuario no los tiene con esos nombres (nombre_usuario, etc.),
            # por eso el mapeo a mano en vez de pasar un Usuario real.
            usuario_para_similitud = SimpleNamespace(
                username='',
                email=cleaned.get('email', ''),
                first_name=cleaned.get('nombre1', ''),
                last_name=cleaned.get('apellido1', ''),
            )
            try:
                password_validation.validate_password(password, user=usuario_para_similitud)
            except forms.ValidationError as error:
                self.add_error('password', error)

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


class RecuperarForm(forms.Form):
    """Paso 1 de /recuperar/: identifica la cuenta por correo + teléfono (no solo correo, para no convertir el formulario en una forma fácil de confirmar qué correos están registrados) antes de mandar el enlace de restablecimiento."""
    email = forms.EmailField(label='Correo electrónico')
    telefono = forms.IntegerField(label='Número de teléfono')


class NuevaPasswordForm(forms.Form):
    """Paso 2 de /recuperar/: elegir la nueva contraseña, con la misma validación de fondo que RegistroForm."""
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='Nueva contraseña')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    def __init__(self, *args, usuario=None, **kwargs):
        self._usuario = usuario
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if password:
            usuario_para_similitud = SimpleNamespace(
                username='',
                email=getattr(self._usuario, 'email', '') or '',
                first_name=getattr(self._usuario, 'nombre_usuario', '') or '',
                last_name=getattr(self._usuario, 'apellido_usuario', '') or '',
            )
            try:
                password_validation.validate_password(password, user=usuario_para_similitud)
            except forms.ValidationError as error:
                self.add_error('password', error)
        return cleaned


class EditarPerfilForm(forms.ModelForm):
    """
    Edición real de los datos del Usuario — antes `editarperfil.html` tenía
    campos (habilidades, precio, disponibilidad, galería...) que nunca
    existieron en el modelo, así que el formulario no guardaba nada. Ahora
    son solo los campos reales que ya existen en `Usuario`, más `region`
    (no es un campo del modelo, solo maneja el cascadeo de comuna en el
    template, igual que en `registroinicio.html`).
    """
    region = forms.ModelChoiceField(queryset=Region.objects.all(), label='Región')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # `direccion_usuario` no tiene `blank=True` en el modelo (a diferencia
        # de nombre2/apellido2/foto_perfil), aunque sí acepta NULL en la base
        # — RegistroForm ya la trata como opcional (`direccion`, required=False)
        # y acá debe ser consistente con eso.
        self.fields['direccion_usuario'].required = False

    class Meta:
        model = Usuario
        fields = [
            'nombre_usuario', 'nombre2_usuario', 'apellido_usuario', 'apellido2_usuario',
            'telefono', 'email', 'direccion_usuario', 'region', 'comuna', 'foto_perfil',
        ]
        labels = {
            'nombre_usuario': 'Primer nombre', 'nombre2_usuario': 'Segundo nombre',
            'apellido_usuario': 'Primer apellido', 'apellido2_usuario': 'Segundo apellido',
            'telefono': 'Teléfono', 'email': 'Correo electrónico',
            'direccion_usuario': 'Dirección', 'comuna': 'Comuna', 'foto_perfil': 'Foto de perfil',
        }

    def clean_email(self):
        """Evita que dos cuentas terminen con el mismo correo (pero permite que el usuario se guarde a sí mismo sin cambiar nada)."""
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email


# Lista de categorías predefinida (RF002 + pedido del usuario: si el
# servicio no encaja en ninguna, "Otra" habilita el campo de texto libre).
# El moderador ve la categoría final (predefinida o escrita a mano) al
# revisar la publicación — no hay un flujo de aprobación aparte para la
# categoría en sí.
CATEGORIAS_PUBLICACION = [
    'Gasfitería', 'Electricidad', 'Jardinería', 'Limpieza del hogar',
    'Pintura', 'Carpintería', 'Mudanzas', 'Cerrajería',
    'Cuidado de mascotas', 'Clases particulares', 'Belleza y bienestar',
    'Tecnología y soporte',
]
OTRA_CATEGORIA = 'Otra'


class PublicacionForm(forms.ModelForm):
    """
    Formulario para que un proveedor cree/edite una Publicacion de servicio
    (RF002) — incluye categoría (con opción "Otra" de texto libre). Las
    fotos y documentos NO son campos de este form (los <input type="file"
    multiple> viven directo en el template, con name="imagenes"/"documentos")
    porque Django no tiene un FileField que acepte varios archivos — se leen
    con `request.FILES.getlist(...)` y se validan uno por uno en
    `publicacion_crear_view`, mismo patrón que las fotos de una Valoracion.
    """
    categoria = forms.ChoiceField(
        choices=[(c, c) for c in CATEGORIAS_PUBLICACION] + [(OTRA_CATEGORIA, 'Otra (especificar abajo)')],
        label='Categoría',
    )
    categoria_otra = forms.CharField(max_length=60, required=False, label='Especifica la categoría')

    class Meta:
        model = Publicaciones
        fields = ['titulo', 'sub_titulo', 'descripcion_publicacion', 'categoria']

    def clean(self):
        """Si eligió "Otra", la categoría real es lo que escribió en el campo de texto libre."""
        cleaned = super().clean()
        if cleaned.get('categoria') == OTRA_CATEGORIA:
            categoria_otra = (cleaned.get('categoria_otra') or '').strip()
            if not categoria_otra:
                self.add_error('categoria_otra', 'Escribe la categoría si elegiste "Otra".')
            else:
                cleaned['categoria'] = categoria_otra
        return cleaned


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


class ContactoForm(forms.ModelForm):
    """
    Formulario de /contacto/ — antes la página era 100% estática (no enviaba
    a ningún lado); ahora crea una Consulta real que el equipo de moderación/
    admin ve en el panel de incidencias. `nombre_contacto`/`email_contacto`
    solo son obligatorios si nadie inició sesión (si hay sesión, se usan los
    datos de `Usuario`).
    """
    class Meta:
        model = Consulta
        fields = ['asunto_consulta', 'descripcion', 'nombre_contacto', 'email_contacto']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 5})}
        labels = {'asunto_consulta': 'Asunto', 'descripcion': 'Cuéntanos qué pasó'}

    def __init__(self, *args, requiere_datos_contacto=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not requiere_datos_contacto:
            self.fields['nombre_contacto'].widget = forms.HiddenInput()
            self.fields['email_contacto'].widget = forms.HiddenInput()
        else:
            self.fields['nombre_contacto'].required = True
            self.fields['email_contacto'].required = True
