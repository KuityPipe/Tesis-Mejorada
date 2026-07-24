"""
Modelos de datos de KeyServ.

Refactor Fase 3: se preservan los nombres de columna en MAYÚSCULA del
diccionario de datos original de la tesis (vía `db_column`), pero los
atributos Python pasan a snake_case (más idiomático en Django) y se
agregan relaciones `ForeignKey` reales donde antes había enteros sueltos
(esto es lo que permitía que `load_comunas`/`region_id` fallaran en la
versión anterior). Como todavía no existe una base de datos con datos
reales, se aprovecha para corregir también las primary keys que deberían
autoincrementar (`AutoField`/`BigAutoField`) en vez de quedar como enteros
manuales.

Ver codigo/viejo/backup_fase3/KeyServApp/models.py para la versión previa.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from .storage import almacenamiento_documentos
from .validators import validar_documento, validar_imagen


# ---------------------------------------------------------------------------
# Catálogos / tablas de referencia (PK manual: se cargan con datos fijos,
# ej. las 16 regiones de Chile, no autoincrementan)
# ---------------------------------------------------------------------------

class Region(models.Model):
    """Región geográfica de Chile (catálogo fijo)."""
    id_region = models.IntegerField(primary_key=True, db_column='ID_REGION')
    nombre_region = models.CharField(max_length=40, null=True, db_column='NOMBRE_REGION')

    class Meta:
        db_table = 'REGION'
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'

    def __str__(self):
        return self.nombre_region or str(self.id_region)


class Comuna(models.Model):
    """Comuna de Chile, pertenece a una Región."""
    id_comuna = models.IntegerField(primary_key=True, db_column='ID_COMUNA')
    nombre_comuna = models.CharField(max_length=60, null=True, db_column='NOMBRE_COMUNA')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=True, db_column='FK_REGION')

    class Meta:
        db_table = 'COMUNA'
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'

    def __str__(self):
        return self.nombre_comuna or str(self.id_comuna)


class TipoCuenta(models.Model):
    """Tier de cuenta (free, individual, pyme, empresa)."""
    id_tipo_cuenta = models.IntegerField(primary_key=True, db_column='ID_TIPO_CUENTA')
    nombre_tipo_cuenta = models.CharField(max_length=50, null=True, db_column='NOMBRE_TIPO_CUENTA')
    valor_cuenta = models.IntegerField(null=True, db_column='VALOR_CUENTA')

    class Meta:
        db_table = 'TIPO_CUENTA'
        verbose_name = 'Tipo de cuenta'
        verbose_name_plural = 'Tipos de cuenta'

    def __str__(self):
        return self.nombre_tipo_cuenta or str(self.id_tipo_cuenta)


class EstadoAutentificacion(models.Model):
    """Estado posible de un intento de autentificación (ej. pendiente/verificado/fallido)."""
    id_estado_autentificacion = models.IntegerField(primary_key=True, db_column='ID_ESTADO_AUTENTIFICACION')
    nombre_estado_autentificacion = models.CharField(max_length=40, null=True, db_column='NOMBRE_ESTADO_AUTENTIFICACION')

    class Meta:
        db_table = 'ESTADO_AUTENTIFICACION'
        verbose_name = 'Estado de autentificación'
        verbose_name_plural = 'Estados de autentificación'

    def __str__(self):
        return self.nombre_estado_autentificacion or str(self.id_estado_autentificacion)


class EstadoConsulta(models.Model):
    """Estado de una consulta/ticket de soporte."""
    id_estado_consulta = models.IntegerField(primary_key=True, db_column='ID_ESTADO_CONSULTA')
    nombre_estado_consulta = models.CharField(max_length=30, null=True, db_column='NOMBRE_ESTADO_CONSULTA')

    class Meta:
        db_table = 'ESTADO_CONSULTA'
        verbose_name = 'Estado de consulta'
        verbose_name_plural = 'Estados de consulta'

    def __str__(self):
        return self.nombre_estado_consulta or str(self.id_estado_consulta)


class EstadoDocumento(models.Model):
    """Estado de un documento subido (ej. pendiente de revisión/aprobado/rechazado)."""
    id_estado_documento = models.IntegerField(primary_key=True, db_column='ID_ESTADO_DOCUMENTO')
    nombre_estado_documento = models.CharField(max_length=40, null=True, db_column='NOMBRE_ESTADO_DOCUMENTO')

    class Meta:
        db_table = 'ESTADO_DOCUMENTO'
        verbose_name = 'Estado de documento'
        verbose_name_plural = 'Estados de documento'

    def __str__(self):
        return self.nombre_estado_documento or str(self.id_estado_documento)


class TipoFirma(models.Model):
    """Tipo de firma digital aplicada a un documento."""
    id_tipo_firma = models.IntegerField(primary_key=True, db_column='ID_TIPO_FIRMA')
    nombre_tipo_firma = models.CharField(max_length=40, null=True, db_column='NOMBRE_TIPO_FIRMA')

    class Meta:
        db_table = 'TIPO_FIRMA'
        verbose_name = 'Tipo de firma'
        verbose_name_plural = 'Tipos de firma'

    def __str__(self):
        return self.nombre_tipo_firma or str(self.id_tipo_firma)


class RolCuentaAdministrativa(models.Model):
    """Rol interno de un usuario administrativo (ej. moderador, soporte, superadmin)."""
    id_rol_cuenta_administrativa = models.IntegerField(primary_key=True, db_column='ID_ROL_CUENTA_ADMINISTRATIVA')
    nombre_rol_cuenta_administrativa = models.CharField(max_length=60, null=True, db_column='NOMBRE_ROL_CUENTA_ADMINISTRATIVA')

    class Meta:
        db_table = 'ROL_CUENTA_ADMINISTRATIVA'
        verbose_name = 'Rol de cuenta administrativa'
        verbose_name_plural = 'Roles de cuenta administrativa'

    def __str__(self):
        return self.nombre_rol_cuenta_administrativa or str(self.id_rol_cuenta_administrativa)


class AreaAdministrativa(models.Model):
    """Área/departamento interno al que pertenece un usuario administrativo."""
    id_area_administrativa = models.IntegerField(primary_key=True, db_column='ID_AREA_ADMINISTRATIVA')
    nombre_area_administrativa = models.CharField(max_length=70, null=True, db_column='NOMBRE_AREA_ADMINISTRATIVA')

    class Meta:
        db_table = 'AREA_ADMINISTRATIVA'
        verbose_name = 'Área administrativa'
        verbose_name_plural = 'Áreas administrativas'

    def __str__(self):
        return self.nombre_area_administrativa or str(self.id_area_administrativa)


# ---------------------------------------------------------------------------
# Transaccionales (PK autoincremental)
# ---------------------------------------------------------------------------

class Transaccion(models.Model):
    """Registro de una transacción de cuenta (ej. al contratar/renovar un TipoCuenta)."""
    id_transaccion = models.BigAutoField(primary_key=True, db_column='ID_TRANSACCION')
    tiempo_transaccion = models.DateTimeField(auto_now_add=True, db_column='TIEMPO_TRANSACCION')
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.PROTECT, null=True, db_column='FK_VALOR_CUENTA')

    class Meta:
        db_table = 'TRANSACCION'
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'

    def __str__(self):
        return str(self.id_transaccion)


class Usuario(models.Model):
    """
    Usuario final de la plataforma (cliente y/o proveedor de servicios).

    `password` guarda el hash (no el texto plano) — usar siempre
    `set_password()`/`check_password()`, nunca asignar el campo directo,
    para no repetir el bug de la versión anterior (que re-hasheaba el
    hash en cada `.save()`).
    """
    id_usuario = models.BigAutoField(primary_key=True, db_column='ID_USUARIO')
    rut_usuario = models.CharField(max_length=10, null=True, db_column='RUT_USUARIO')
    nombre_usuario = models.CharField(max_length=40, null=True, db_column='NOMBRE_USUARIO')
    nombre2_usuario = models.CharField(max_length=40, null=True, blank=True, db_column='NOMBRE2_USUARIO')
    apellido_usuario = models.CharField(max_length=40, null=True, db_column='APELLIDO_USUARIO')
    apellido2_usuario = models.CharField(max_length=40, null=True, blank=True, db_column='APELLIDO2_USUARIO')
    telefono = models.IntegerField(db_column='TELEFONO')
    email = models.CharField(max_length=40, null=True, unique=True, db_column='EMAIL')
    direccion_usuario = models.CharField(max_length=80, null=True, db_column='DIRECCION_USUARIO')
    transaccion = models.ForeignKey(Transaccion, on_delete=models.SET_NULL, null=True, db_column='FK_TRANSACCION')
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.PROTECT, null=True, db_column='FK_TIPO_CUENTA')
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT, null=True, db_column='FK_COMUNA')
    edad = models.IntegerField(db_column='EDAD')
    password = models.CharField(max_length=128, db_column='CONTRASEÑA')
    # Distingue los dos actores del PDF (Cliente / Proveedor de servicios, PAGE 137-141).
    # Un mismo Usuario puede ser ambos (no es excluyente).
    es_proveedor = models.BooleanField(default=False, db_column='ES_PROVEEDOR')
    verificado_biometricamente = models.BooleanField(default=False, db_column='VERIFICADO_BIOMETRICAMENTE')
    # NUEVO: antes el perfil solo mostraba un avatar con la inicial del
    # nombre — foto real, opcional, subida desde /perfil/editar/.
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True, validators=[validar_imagen], db_column='FOTO_PERFIL')

    class Meta:
        db_table = 'USUARIO'
        # "Usuario (cliente/proveedor)" y no solo "Usuario": en /admin/ convive
        # con el User nativo de Django (cuentas de staff que hacen login al
        # panel) — ambos se llamarían "Usuario(s)" a secas si no se distinguen,
        # justo la confusión que se pidió evitar entre soporte/moderadores.
        verbose_name = 'Usuario (cliente/proveedor)'
        verbose_name_plural = 'Usuarios (clientes/proveedores)'

    def __str__(self):
        return f'{self.nombre_usuario} {self.apellido_usuario}'.strip() or str(self.id_usuario)

    def set_password(self, raw_password):
        """Hashea `raw_password` con el hasher configurado (PBKDF2/Argon2) y lo guarda en `password`."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Compara `raw_password` contra el hash guardado. Devuelve True/False."""
        return check_password(raw_password, self.password)


class UsuarioAdministrativo(models.Model):
    """Usuario interno (staff) con acceso administrativo — distinto de Usuario (clientes/proveedores)."""
    id_usuario_administrativo = models.BigAutoField(primary_key=True, db_column='ID_USUARIO_ADMINISTRATIVO')
    rut_usuario_administrativo = models.CharField(max_length=10, null=True, db_column='RUT_USUARIO_ADMINISTRATIVO')
    nombre_usuario_administrativo = models.CharField(max_length=40, null=True, db_column='NOMBRE_USUARIO_ADMINISTRATIVO')
    nombre2_usuario_administrativo = models.CharField(max_length=40, null=True, blank=True, db_column='NOMBRE2_USUARIO_ADMINISTRATIVO')
    apellido_usuario_administrativo = models.CharField(max_length=40, null=True, db_column='APELLIDO_USUARIO_ADMINISTRATIVO')
    apellido2_usuario_administrativo = models.CharField(max_length=40, null=True, blank=True, db_column='APELLIDO2_USUARIO_ADMINISTRATIVO')
    telefono_usuario_administrativo = models.IntegerField(db_column='TELEFONO_USUARIO_ADMINISTRATIVO')
    email_usuario_administrativo = models.CharField(max_length=40, null=True, db_column='EMAIL_USUARIO_ADMINISTRATIVO')
    rol_cuenta_administrativa = models.ForeignKey(RolCuentaAdministrativa, on_delete=models.PROTECT, null=True, db_column='FK_ROL_CUENTA_ADMINISTRATIVA')
    area_administrativa = models.ForeignKey(AreaAdministrativa, on_delete=models.PROTECT, null=True, db_column='FK_AREA_ADMINISTRATIVA')

    class Meta:
        db_table = 'USUARIO_ADMINISTRATIVO'
        verbose_name = 'Usuario administrativo'
        verbose_name_plural = 'Usuarios administrativos'

    def __str__(self):
        return f'{self.nombre_usuario_administrativo} {self.apellido_usuario_administrativo}'.strip() or str(self.id_usuario_administrativo)


class Autentificacion(models.Model):
    """Registro histórico de cada intento de autentificación (login/código SMTP/biometría)."""
    id_autentificacion = models.BigAutoField(primary_key=True, db_column='ID_AUTENTIFICACION')
    codigo_autentificacion = models.BinaryField(max_length=32, null=True, db_column='CODIGO_AUTENTIFICACION')
    fecha_autentificacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_AUTENTIFICACION')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, db_column='FK_USUARIO_AUTENTIFICACION')
    estado_autentificacion = models.ForeignKey(EstadoAutentificacion, on_delete=models.PROTECT, null=True, db_column='FK_ESTADO_AUTENTIFICACION')

    class Meta:
        db_table = 'AUTENTIFICACION'
        verbose_name = 'Autentificación'
        verbose_name_plural = 'Autentificaciones'

    def __str__(self):
        return str(self.id_autentificacion)


class Consulta(models.Model):
    """
    Ticket de soporte/incidencia que alguien levanta hacia el equipo
    administrativo (panel de moderación/admin — "incidencias o problemas
    con el servicio"). Existía en el esquema desde la tesis pero nunca se
    usaba: no tenía cuerpo de mensaje (`descripcion`, nuevo) ni datos de
    contacto para quien escribe sin sesión iniciada (`nombre_contacto`/
    `email_contacto`, nuevos) — hoy se conecta de verdad desde /contacto/.
    """
    id_consulta = models.BigAutoField(primary_key=True, db_column='ID_CONSULTA')
    asunto_consulta = models.CharField(max_length=120, null=True, db_column='ASUNTO_CONSULTA')
    descripcion = models.TextField(null=True, blank=True, db_column='DESCRIPCION')
    nombre_contacto = models.CharField(max_length=80, null=True, blank=True, db_column='NOMBRE_CONTACTO')
    email_contacto = models.CharField(max_length=80, null=True, blank=True, db_column='EMAIL_CONTACTO')
    fecha_consulta = models.DateTimeField(auto_now_add=True, db_column='FECHA_CONSULTA')
    fecha_termino_consulta = models.DateTimeField(null=True, blank=True, db_column='FECHA_TERMINO_CONSULTA')
    estado_consulta = models.ForeignKey(EstadoConsulta, on_delete=models.PROTECT, null=True, db_column='FK_ESTADO_CONSULTA')
    usuario_consulta = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True, db_column='FK_USUARIO_CONSULTA')
    usuario_administrativo = models.ForeignKey(UsuarioAdministrativo, on_delete=models.SET_NULL, null=True, blank=True, db_column='FK_USUARIO_ADMINISTRATIVO')

    class Meta:
        db_table = 'CONSULTA'
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'

    def __str__(self):
        return self.asunto_consulta or str(self.id_consulta)


class Conversacion(models.Model):
    """
    Hilo de mensajería (ver UsuarioConversacion para los participantes).

    NUEVO: antes era una conversación por PAR DE USUARIOS, compartida entre
    todos sus trabajos (poco ordenado — mezclaba mensajes de contrataciones
    distintas). Ahora es 1:1 con una Contratacion puntual ("chat del
    trabajo"), decisión tomada con el usuario para que quede más ordenado.
    """
    id_conversacion = models.BigAutoField(primary_key=True, db_column='ID_CONVERSACION')
    nombre_conversacion = models.CharField(max_length=255, null=True, db_column='NOMBRE_CONVERSACION')
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_CREACION')
    contratacion = models.OneToOneField(
        'Contratacion', on_delete=models.CASCADE, null=True, blank=True,
        related_name='conversacion', db_column='FK_CONTRATACION',
    )
    # Backup/retención de mensajes: exportar marca esta fecha, y el comando
    # `limpiar_mensajes_antiguos` NUNCA borra una conversación ya exportada
    # (ver KeyServApp/management/commands/limpiar_mensajes_antiguos.py).
    exportado_en = models.DateTimeField(null=True, blank=True, db_column='EXPORTADO_EN')

    class Meta:
        db_table = 'CONVERSACION'
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'

    def __str__(self):
        return self.nombre_conversacion or str(self.id_conversacion)


class UsuarioConversacion(models.Model):
    """Tabla puente: qué Usuarios participan en qué Conversacion."""
    id_usuario_conversacion = models.BigAutoField(primary_key=True, db_column='ID_USUARIO_CONVERSACION')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='FK_USUARIO_C')
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, db_column='FK_CONVERSACION')
    # NUEVO: marca hasta cuándo este usuario leyó la conversación — permite
    # calcular mensajes no leídos para las alertas del dashboard (/inicio/).
    ultimo_leido = models.DateTimeField(null=True, blank=True, db_column='ULTIMO_LEIDO')

    class Meta:
        db_table = 'USUARIO_CONVERSACION'
        unique_together = (('usuario', 'conversacion'),)
        verbose_name = 'Participante de conversación'
        verbose_name_plural = 'Participantes de conversación'

    def __str__(self):
        return str(self.id_usuario_conversacion)


class Mensaje(models.Model):
    """Mensaje individual dentro de una Conversacion."""
    id_mensaje = models.BigAutoField(primary_key=True, db_column='ID_MENSAJE')
    contenido = models.TextField(null=True, db_column='CONTENIDO')
    fecha_envio = models.DateTimeField(auto_now_add=True, db_column='FECHA_ENVIO')
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, db_column='FK_CONVERSACION')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='FK_USUARIO')

    class Meta:
        db_table = 'MENSAJE'
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return str(self.id_mensaje)


class Publicaciones(models.Model):
    """Publicación de un servicio ofrecido por un Usuario (proveedor)."""
    id_publicacion = models.BigAutoField(primary_key=True, db_column='ID_PUBLICACION')
    usuario_publicador = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, related_name='publicaciones', db_column='FK_USUARIO_P')
    titulo = models.CharField(max_length=255, null=True, db_column='TITULO')
    sub_titulo = models.CharField(max_length=255, null=True, blank=True, db_column='SUB_TITULO')
    descripcion_publicacion = models.TextField(null=True, db_column='DESCRIPCION_PUBLICACION')
    # NUEVO: categoría del servicio — el form ofrece una lista predefinida
    # (ver forms.CATEGORIAS_PUBLICACION) más una opción "Otra" de texto libre;
    # este campo queda como texto plano para admitir ambos casos. El
    # moderador ve la categoría (incluida la escrita a mano) al aprobar.
    categoria = models.CharField(max_length=60, null=True, blank=True, db_column='CATEGORIA')
    # NUEVO: precio del servicio en pesos chilenos (CLP, sin decimales — no
    # existía ningún campo de precio en el esquema heredado de la tesis).
    # Requerido para poder cobrar de verdad al contratar (ver pagos.py).
    precio = models.PositiveIntegerField(null=True, blank=True, db_column='PRECIO')
    fecha_publicacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_PUBLICACION')
    actualizado_en = models.DateTimeField(auto_now=True, db_column='ACTUALIZADO_EN')
    # Flujo de moderación descrito en el BPMN "Crear publicación" del PDF (PAGE 135-136):
    # toda publicación nace pendiente y requiere aprobación antes de ser visible en la búsqueda.
    PENDIENTE, APROBADA, RECHAZADA = 'PENDIENTE', 'APROBADA', 'RECHAZADA'
    ESTADOS_MODERACION = [
        (PENDIENTE, 'Pendiente de revisión'),
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
    ]
    estado_moderacion = models.CharField(max_length=10, choices=ESTADOS_MODERACION, default=PENDIENTE, db_column='ESTADO_MODERACION')
    # NUEVO: constancia de quién aprobó/rechazó la publicación y cuándo —
    # pedido explícito del usuario ("dejar constancia de qué moderador hizo
    # un cambio de estado"). Se autocompletan en PublicacionesAdmin.save_model,
    # nunca a mano — por eso no aparecen en PublicacionForm (el proveedor no
    # los toca).
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='publicaciones_moderadas', db_column='FK_APROBADO_POR',
    )
    fecha_moderacion = models.DateTimeField(null=True, blank=True, db_column='FECHA_MODERACION')

    class Meta:
        db_table = 'PUBLICACIONES'
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'

    def __str__(self):
        return self.titulo or str(self.id_publicacion)


class Imagenes(models.Model):
    """Imagen asociada a una Publicacion."""
    id_imagen = models.BigAutoField(primary_key=True, db_column='ID_IMAGEN')
    publicacion = models.ForeignKey(Publicaciones, on_delete=models.CASCADE, null=True, related_name='imagenes', db_column='FK_PUBLICACION')
    # `url_imagen` se mantiene para las imágenes sembradas como URL externa
    # (fixtures/demo); `archivo` es el campo real para lo que suba un
    # proveedor desde el formulario de creación de publicación.
    url_imagen = models.TextField(null=True, blank=True, db_column='URL_IMAGEN')
    archivo = models.ImageField(upload_to='publicaciones/imagenes/', null=True, blank=True, db_column='ARCHIVO', validators=[validar_imagen])
    fecha_subida = models.DateTimeField(auto_now_add=True, db_column='FECHA_SUBIDA')
    actualizado_en = models.DateTimeField(auto_now=True, db_column='ACTUALIZADO_EN')

    class Meta:
        db_table = 'IMAGENES'
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'

    def __str__(self):
        return str(self.id_imagen)

    @property
    def url(self):
        """URL a mostrar sea cual sea el origen de la imagen (archivo subido o URL externa sembrada)."""
        if self.archivo:
            return self.archivo.url
        return self.url_imagen


class Contratacion(models.Model):
    """
    NUEVO (Fase 3, esqueleto). Representa que un cliente contrató a un
    proveedor para una Publicacion puntual — es el modelo que faltaba para
    soportar el BPMN "Proceso de contratación" del PDF (PAGE 136-137):
    colaborador en espera -> match con cliente -> ambos se re-autentican
    -> tras el trabajo, calificación por estrellas.

    TODO: el flujo completo (notificar al proveedor, forzar re-autenticación
    de ambas partes antes de confirmar, disparar la creación de Valoracion
    al cerrar) todavía no está implementado — ver views_contratacion.py.
    """
    id_contratacion = models.BigAutoField(primary_key=True, db_column='ID_CONTRATACION')
    publicacion = models.ForeignKey(Publicaciones, on_delete=models.CASCADE, related_name='contrataciones', db_column='FK_PUBLICACION')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='contrataciones_como_cliente', db_column='FK_CLIENTE')
    proveedor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='contrataciones_como_proveedor', db_column='FK_PROVEEDOR')

    SOLICITADA, CONFIRMADA, EN_CURSO, COMPLETADA, CANCELADA = (
        'SOLICITADA', 'CONFIRMADA', 'EN_CURSO', 'COMPLETADA', 'CANCELADA',
    )
    ESTADOS_CONTRATACION = [
        (SOLICITADA, 'Solicitada por el cliente'),
        (CONFIRMADA, 'Confirmada por el proveedor'),
        (EN_CURSO, 'Servicio en curso'),
        (COMPLETADA, 'Completada'),
        (CANCELADA, 'Cancelada'),
    ]
    estado = models.CharField(max_length=12, choices=ESTADOS_CONTRATACION, default=SOLICITADA, db_column='ESTADO')
    # NUEVO: el precio de la Publicacion es solo un punto de partida — cliente
    # y proveedor pueden acordar un monto distinto charlando por el chat
    # antes de que el proveedor confirme. Se fija recién al confirmar
    # (contratacion_confirmar_view), y es lo que se cobra de verdad en
    # pago_webpay_iniciar_view/pago_khipu_iniciar_view — nunca se vuelve a
    # leer publicacion.precio después de este punto.
    monto_acordado = models.PositiveIntegerField(null=True, blank=True, db_column='MONTO_ACORDADO')
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_CREACION')
    fecha_actualizacion = models.DateTimeField(auto_now=True, db_column='FECHA_ACTUALIZACION')

    class Meta:
        db_table = 'CONTRATACION'
        verbose_name = 'Contratación'
        verbose_name_plural = 'Contrataciones'

    def __str__(self):
        return f'Contratación #{self.id_contratacion} ({self.estado})'


class HistorialEstadoContratacion(models.Model):
    """
    NUEVO: registro de cada cambio de estado de una Contratacion, con fecha.
    `fecha_actualizacion` de Contratacion se pisa en cada save() y no alcanza
    para mostrar una línea de tiempo real (cuándo se solicitó, cuándo se
    confirmó, cuándo se completó/canceló) — pedido explícito del usuario para
    dejar claro el tiempo del trabajo. Se agrega una fila cada vez que
    contratacion_crear_view / contratacion_confirmar_view /
    contratacion_completar_view cambian el estado.
    """
    id_historial = models.BigAutoField(primary_key=True, db_column='ID_HISTORIAL')
    contratacion = models.ForeignKey(Contratacion, on_delete=models.CASCADE, related_name='historial_estados', db_column='FK_CONTRATACION')
    estado = models.CharField(max_length=12, choices=Contratacion.ESTADOS_CONTRATACION, db_column='ESTADO')
    fecha = models.DateTimeField(auto_now_add=True, db_column='FECHA')

    class Meta:
        db_table = 'HISTORIAL_ESTADO_CONTRATACION'
        ordering = ['fecha']
        verbose_name = 'Historial de estado de contratación'
        verbose_name_plural = 'Historial de estados de contratación'

    def __str__(self):
        return f'Contratación #{self.contratacion_id}: {self.estado} ({self.fecha:%Y-%m-%d %H:%M})'


class Pago(models.Model):
    """
    NUEVO: registro de un cobro real al cliente para pasar una Contratacion
    de CONFIRMADA a EN_CURSO (RF012 del PDF, "Api de pago asociada" — antes
    `pagos.py` era un esqueleto que solo tiraba NotImplementedError). Dos
    medios de pago posibles, elegidos con el usuario: Webpay Plus
    (tarjetas, vía transbank-sdk) y Khipu (transferencia bancaria directa,
    vía su API REST) — ver KeyServApp/pagos.py.
    """
    id_pago = models.BigAutoField(primary_key=True, db_column='ID_PAGO')
    contratacion = models.OneToOneField(
        Contratacion, on_delete=models.CASCADE, related_name='pago', db_column='FK_CONTRATACION',
    )
    monto = models.PositiveIntegerField(db_column='MONTO')

    WEBPAY, KHIPU = 'WEBPAY', 'KHIPU'
    METODOS_PAGO = [(WEBPAY, 'Webpay Plus'), (KHIPU, 'Khipu')]
    metodo = models.CharField(max_length=10, choices=METODOS_PAGO, db_column='METODO')

    PENDIENTE, PAGADO, RECHAZADO, ANULADO = 'PENDIENTE', 'PAGADO', 'RECHAZADO', 'ANULADO'
    ESTADOS_PAGO = [
        (PENDIENTE, 'Pendiente'), (PAGADO, 'Pagado'),
        (RECHAZADO, 'Rechazado'), (ANULADO, 'Anulado/cancelado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS_PAGO, default=PENDIENTE, db_column='ESTADO')

    # Identificadores del medio externo — solo se completa el que aplica
    # según `metodo`. `orden_compra` es el "buy_order" que exige Transbank
    # (máx. 26 caracteres, ver views._generar_orden_compra).
    orden_compra = models.CharField(max_length=26, null=True, blank=True, db_column='ORDEN_COMPRA')
    token_webpay = models.CharField(max_length=64, null=True, blank=True, db_column='TOKEN_WEBPAY')
    khipu_payment_id = models.CharField(max_length=64, null=True, blank=True, db_column='KHIPU_PAYMENT_ID')

    # Respuesta cruda del medio de pago (commit de Webpay / consulta de
    # Khipu) — solo para auditoría/soporte, nunca se lee para decidir nada
    # en el código (esa decisión ya quedó tomada en `estado`).
    respuesta_bruta = models.JSONField(null=True, blank=True, db_column='RESPUESTA_BRUTA')

    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_CREACION')
    fecha_confirmacion = models.DateTimeField(null=True, blank=True, db_column='FECHA_CONFIRMACION')

    class Meta:
        db_table = 'PAGO'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f'Pago #{self.id_pago} — {self.get_metodo_display()} ({self.get_estado_display()})'


class Valoracion(models.Model):
    """Calificación por estrellas + comentario que un Usuario deja sobre otro tras un servicio."""
    id_valoracion = models.BigAutoField(primary_key=True, db_column='ID_VALORACION')
    puntuacion = models.SmallIntegerField(db_column='PUNTUACION')
    comentario = models.TextField(null=True, blank=True, db_column='COMENTARIO')
    fecha_valoracion = models.DateTimeField(auto_now_add=True, db_column='FECHA_VALORACION')
    usuario_emisor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='valoraciones_emitidas', db_column='FK_USUARIO_EMISOR')
    usuario_receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='valoraciones_recibidas', db_column='FK_USUARIO_RECEPTOR')
    publicacion = models.ForeignKey(Publicaciones, on_delete=models.CASCADE, db_column='FK_PUBLICACION')
    # NUEVO: antes solo se sabía "el cliente X calificó la publicación Y" —
    # no alcanzaba para saber si un trabajo PUNTUAL ya fue calificado (un
    # mismo cliente puede recontratar el mismo servicio más adelante). Ligarla
    # 1:1 a la Contratacion resuelve eso, mismo patrón que Conversacion.
    contratacion = models.OneToOneField(
        Contratacion, on_delete=models.CASCADE, null=True, blank=True,
        related_name='valoracion', db_column='FK_CONTRATACION',
    )
    # NUEVO: no solo las fotos adjuntas se moderan — la reseña completa
    # (puntuación + comentario) puede ser difamatoria o abusiva, así que
    # pasa por el mismo flujo que Publicaciones antes de mostrarse en
    # público o contar para el Ranking del receptor. El emisor sigue viendo
    # su propia reseña igual (con un aviso de "pendiente"), solo se oculta
    # del resto de la gente hasta que un moderador la aprueba.
    PENDIENTE, APROBADA, RECHAZADA = 'PENDIENTE', 'APROBADA', 'RECHAZADA'
    ESTADOS_MODERACION = [
        (PENDIENTE, 'Pendiente de revisión'),
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
    ]
    estado_moderacion = models.CharField(max_length=10, choices=ESTADOS_MODERACION, default=PENDIENTE, db_column='ESTADO_MODERACION')
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='valoraciones_moderadas', db_column='FK_APROBADO_POR',
    )
    fecha_moderacion = models.DateTimeField(null=True, blank=True, db_column='FECHA_MODERACION')

    class Meta:
        db_table = 'VALORACION'
        verbose_name = 'Valoración'
        verbose_name_plural = 'Valoraciones'

    def __str__(self):
        return str(self.id_valoracion)

    @property
    def imagenes_aprobadas(self):
        """Fotos adjuntas ya moderadas — lo único que se muestra fuera del propio autor (ver ValoracionImagen)."""
        return self.imagenes.filter(estado_moderacion=ValoracionImagen.APROBADA)


class ValoracionImagen(models.Model):
    """
    Foto adjunta a una Valoracion (evidencia del trabajo realizado). Pasa por
    moderación antes de mostrarse en público — mismo criterio que
    Publicaciones.estado_moderacion: nadie quiere que un cliente enojado
    pueda subir una foto dañina sin revisión.
    """
    PENDIENTE, APROBADA, RECHAZADA = 'PENDIENTE', 'APROBADA', 'RECHAZADA'
    ESTADOS_MODERACION = [
        (PENDIENTE, 'Pendiente de revisión'),
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
    ]
    id_valoracion_imagen = models.BigAutoField(primary_key=True, db_column='ID_VALORACION_IMAGEN')
    valoracion = models.ForeignKey(Valoracion, on_delete=models.CASCADE, related_name='imagenes', db_column='FK_VALORACION')
    archivo = models.ImageField(upload_to='valoraciones/imagenes/', db_column='ARCHIVO', validators=[validar_imagen])
    fecha_subida = models.DateTimeField(auto_now_add=True, db_column='FECHA_SUBIDA')
    estado_moderacion = models.CharField(max_length=10, choices=ESTADOS_MODERACION, default=PENDIENTE, db_column='ESTADO_MODERACION')

    class Meta:
        db_table = 'VALORACION_IMAGEN'
        verbose_name = 'Imagen de valoración'
        verbose_name_plural = 'Imágenes de valoración'

    def __str__(self):
        return f'Imagen de valoración #{self.valoracion_id}'


class Ranking(models.Model):
    """Agregado (promedio + total) de las Valoracion recibidas por un Usuario. Se recalcula en cada nueva Valoracion."""
    id_ranking = models.BigAutoField(primary_key=True, db_column='ID_RANKING')
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='ranking', db_column='FK_USUARIO')
    total_valoraciones = models.IntegerField(default=0, db_column='TOTAL_VALORACIONES')
    puntuacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0, db_column='PUNTUACION_PROMEDIO')

    class Meta:
        db_table = 'RANKING'
        verbose_name = 'Ranking'
        verbose_name_plural = 'Rankings'

    def __str__(self):
        return str(self.id_ranking)


class Documento(models.Model):
    """Documento subido por un Usuario (ej. certificado de antecedentes, título) — o, desde Fase 5, adjunto a una Publicacion (ej. certificación del servicio)."""
    id_documento = models.BigAutoField(primary_key=True, db_column='ID_DOCUMENTO')
    nombre_documento = models.CharField(max_length=60, null=True, db_column='NOMBRE_DOCUMENTO')
    archivo = models.BinaryField(null=True, db_column='ARCHIVO')
    # NUEVO: archivo real subido (el campo `archivo` de arriba es legado —
    # BinaryField en la fila de la BD, del diseño original de la tesis; los
    # documentos nuevos van a `archivo_subido`, en filesystem via MEDIA_ROOT).
    archivo_subido = models.FileField(upload_to='publicaciones/documentos/', storage=almacenamiento_documentos, null=True, blank=True, db_column='ARCHIVO_SUBIDO', validators=[validar_documento])
    fecha_subida_documento = models.DateTimeField(auto_now_add=True, db_column='FECHA_SUBIDA_DOCUMENTO')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, db_column='FK_USUARIO')
    publicacion = models.ForeignKey(Publicaciones, on_delete=models.CASCADE, null=True, blank=True, related_name='documentos', db_column='FK_PUBLICACION')
    estado_documento = models.ForeignKey(EstadoDocumento, on_delete=models.PROTECT, null=True, db_column='FK_ESTADO_DOCUMENTO')

    class Meta:
        db_table = 'DOCUMENTO'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return self.nombre_documento or str(self.id_documento)


class Firma(models.Model):
    """Firma digital aplicada sobre un Documento, ligada a la Autentificacion que la validó."""
    id_firma = models.BigAutoField(primary_key=True, db_column='ID_FIRMA')
    hash_firma = models.BinaryField(null=True, db_column='HASH_FIRMA')
    fecha_hora_firma = models.DateTimeField(auto_now_add=True, db_column='FECHA_HORA_FIRMA')
    autentificacion = models.ForeignKey(Autentificacion, on_delete=models.SET_NULL, null=True, db_column='FK_AUTENTIFICACION')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, db_column='FK_FIRMA_USUARIO')
    tipo_firma = models.ForeignKey(TipoFirma, on_delete=models.PROTECT, null=True, db_column='FK_TIPO_FIRMA')
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, null=True, db_column='FK_DOCUMENTO')

    class Meta:
        db_table = 'FIRMA'
        verbose_name = 'Firma'
        verbose_name_plural = 'Firmas'

    def __str__(self):
        return str(self.id_firma)


class Gasto(models.Model):
    """Gasto operativo registrado por un usuario administrativo (contabilidad interna)."""
    id_gasto = models.BigAutoField(primary_key=True, db_column='ID_GASTO')
    fecha_gasto = models.DateTimeField(auto_now_add=True, db_column='FECHA_GASTO')
    monto_gasto = models.IntegerField(null=True, db_column='MONTO_GASTO')
    responsable_gasto = models.ForeignKey(UsuarioAdministrativo, on_delete=models.SET_NULL, null=True, db_column='FK_RESPONSABLE_GASTO')

    class Meta:
        db_table = 'GASTO'
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'

    def __str__(self):
        return str(self.id_gasto)


class IntentoAccesoSospechoso(models.Model):
    """
    Registro de intentos de acceder a un recurso (conversación, contratación,
    documento) del que el usuario NO es parte — se genera solo en los puntos
    donde una vista deniega acceso por "no participás en esto", nunca en un
    error común de la app. Sirve para notar reconocimiento manual de IDs
    (alguien probando /chat/11/, /chat/12/, ... a ver cuál le abre) antes de
    que se convierta en un problema real — ver views._registrar_intento_sospechoso.

    `pais`/`ciudad` vienen de una base GeoIP local (DB-IP City Lite, ver
    geolocalizacion.py) — no de un servicio externo: no se manda la IP de
    nadie a un tercero en cada evento. Quedan en None si la base no está
    descargada, o si la IP es privada/local (todo el desarrollo cae acá,
    127.0.0.1 no geolocaliza a ningún lado real). `usuario` puede ser None:
    esto también se genera para quien NO tiene sesión iniciada (ej. alguien
    agotando los intentos de login sin ser todavía nadie identificado).
    """
    id_intento = models.BigAutoField(primary_key=True, db_column='ID_INTENTO')
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, db_column='FK_USUARIO')
    fecha = models.DateTimeField(auto_now_add=True, db_column='FECHA')
    ip = models.GenericIPAddressField(null=True, blank=True, db_column='IP')
    pais = models.CharField(max_length=100, null=True, blank=True, db_column='PAIS')
    ciudad = models.CharField(max_length=100, null=True, blank=True, db_column='CIUDAD')
    user_agent = models.CharField(max_length=255, null=True, blank=True, db_column='USER_AGENT')
    ruta = models.CharField(max_length=255, db_column='RUTA')
    recurso = models.CharField(max_length=40, db_column='RECURSO')
    recurso_id = models.CharField(max_length=40, null=True, blank=True, db_column='RECURSO_ID')
    detalle = models.CharField(max_length=255, null=True, blank=True, db_column='DETALLE')

    class Meta:
        db_table = 'INTENTO_ACCESO_SOSPECHOSO'
        ordering = ['-fecha']
        verbose_name = 'Intento de acceso sospechoso'
        verbose_name_plural = 'Intentos de acceso sospechoso'

    def __str__(self):
        return f'{self.usuario or "anónimo"} → {self.recurso} #{self.recurso_id} ({self.fecha:%Y-%m-%d %H:%M})'
