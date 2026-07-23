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
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


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

    def __str__(self):
        return self.nombre_region or str(self.id_region)


class Comuna(models.Model):
    """Comuna de Chile, pertenece a una Región."""
    id_comuna = models.IntegerField(primary_key=True, db_column='ID_COMUNA')
    nombre_comuna = models.CharField(max_length=60, null=True, db_column='NOMBRE_COMUNA')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=True, db_column='FK_REGION')

    class Meta:
        db_table = 'COMUNA'

    def __str__(self):
        return self.nombre_comuna or str(self.id_comuna)


class TipoCuenta(models.Model):
    """Tier de cuenta (free, individual, pyme, empresa)."""
    id_tipo_cuenta = models.IntegerField(primary_key=True, db_column='ID_TIPO_CUENTA')
    nombre_tipo_cuenta = models.CharField(max_length=50, null=True, db_column='NOMBRE_TIPO_CUENTA')
    valor_cuenta = models.IntegerField(null=True, db_column='VALOR_CUENTA')

    class Meta:
        db_table = 'TIPO_CUENTA'

    def __str__(self):
        return self.nombre_tipo_cuenta or str(self.id_tipo_cuenta)


class EstadoAutentificacion(models.Model):
    """Estado posible de un intento de autentificación (ej. pendiente/verificado/fallido)."""
    id_estado_autentificacion = models.IntegerField(primary_key=True, db_column='ID_ESTADO_AUTENTIFICACION')
    nombre_estado_autentificacion = models.CharField(max_length=40, null=True, db_column='NOMBRE_ESTADO_AUTENTIFICACION')

    class Meta:
        db_table = 'ESTADO_AUTENTIFICACION'

    def __str__(self):
        return self.nombre_estado_autentificacion or str(self.id_estado_autentificacion)


class EstadoConsulta(models.Model):
    """Estado de una consulta/ticket de soporte."""
    id_estado_consulta = models.IntegerField(primary_key=True, db_column='ID_ESTADO_CONSULTA')
    nombre_estado_consulta = models.CharField(max_length=30, null=True, db_column='NOMBRE_ESTADO_CONSULTA')

    class Meta:
        db_table = 'ESTADO_CONSULTA'

    def __str__(self):
        return self.nombre_estado_consulta or str(self.id_estado_consulta)


class EstadoDocumento(models.Model):
    """Estado de un documento subido (ej. pendiente de revisión/aprobado/rechazado)."""
    id_estado_documento = models.IntegerField(primary_key=True, db_column='ID_ESTADO_DOCUMENTO')
    nombre_estado_documento = models.CharField(max_length=40, null=True, db_column='NOMBRE_ESTADO_DOCUMENTO')

    class Meta:
        db_table = 'ESTADO_DOCUMENTO'

    def __str__(self):
        return self.nombre_estado_documento or str(self.id_estado_documento)


class TipoFirma(models.Model):
    """Tipo de firma digital aplicada a un documento."""
    id_tipo_firma = models.IntegerField(primary_key=True, db_column='ID_TIPO_FIRMA')
    nombre_tipo_firma = models.CharField(max_length=40, null=True, db_column='NOMBRE_TIPO_FIRMA')

    class Meta:
        db_table = 'TIPO_FIRMA'

    def __str__(self):
        return self.nombre_tipo_firma or str(self.id_tipo_firma)


class RolCuentaAdministrativa(models.Model):
    """Rol interno de un usuario administrativo (ej. moderador, soporte, superadmin)."""
    id_rol_cuenta_administrativa = models.IntegerField(primary_key=True, db_column='ID_ROL_CUENTA_ADMINISTRATIVA')
    nombre_rol_cuenta_administrativa = models.CharField(max_length=60, null=True, db_column='NOMBRE_ROL_CUENTA_ADMINISTRATIVA')

    class Meta:
        db_table = 'ROL_CUENTA_ADMINISTRATIVA'

    def __str__(self):
        return self.nombre_rol_cuenta_administrativa or str(self.id_rol_cuenta_administrativa)


class AreaAdministrativa(models.Model):
    """Área/departamento interno al que pertenece un usuario administrativo."""
    id_area_administrativa = models.IntegerField(primary_key=True, db_column='ID_AREA_ADMINISTRATIVA')
    nombre_area_administrativa = models.CharField(max_length=70, null=True, db_column='NOMBRE_AREA_ADMINISTRATIVA')

    class Meta:
        db_table = 'AREA_ADMINISTRATIVA'

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

    class Meta:
        db_table = 'USUARIO'

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

    def __str__(self):
        return str(self.id_autentificacion)


class Consulta(models.Model):
    """Ticket de soporte/consulta que un Usuario levanta hacia el equipo administrativo."""
    id_consulta = models.BigAutoField(primary_key=True, db_column='ID_CONSULTA')
    asunto_consulta = models.CharField(max_length=120, null=True, db_column='ASUNTO_CONSULTA')
    fecha_consulta = models.DateTimeField(auto_now_add=True, db_column='FECHA_CONSULTA')
    fecha_termino_consulta = models.DateTimeField(null=True, blank=True, db_column='FECHA_TERMINO_CONSULTA')
    estado_consulta = models.ForeignKey(EstadoConsulta, on_delete=models.PROTECT, null=True, db_column='FK_ESTADO_CONSULTA')
    usuario_consulta = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, db_column='FK_USUARIO_CONSULTA')
    usuario_administrativo = models.ForeignKey(UsuarioAdministrativo, on_delete=models.SET_NULL, null=True, db_column='FK_USUARIO_ADMINISTRATIVO')

    class Meta:
        db_table = 'CONSULTA'

    def __str__(self):
        return str(self.id_consulta)


class Conversacion(models.Model):
    """Hilo de mensajería entre dos o más Usuarios (ver UsuarioConversacion para los participantes)."""
    id_conversacion = models.BigAutoField(primary_key=True, db_column='ID_CONVERSACION')
    nombre_conversacion = models.CharField(max_length=255, null=True, db_column='NOMBRE_CONVERSACION')
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_CREACION')

    class Meta:
        db_table = 'CONVERSACION'

    def __str__(self):
        return self.nombre_conversacion or str(self.id_conversacion)


class UsuarioConversacion(models.Model):
    """Tabla puente: qué Usuarios participan en qué Conversacion."""
    id_usuario_conversacion = models.BigAutoField(primary_key=True, db_column='ID_USUARIO_CONVERSACION')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='FK_USUARIO_C')
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, db_column='FK_CONVERSACION')

    class Meta:
        db_table = 'USUARIO_CONVERSACION'
        unique_together = (('usuario', 'conversacion'),)

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

    def __str__(self):
        return str(self.id_mensaje)


class Publicaciones(models.Model):
    """Publicación de un servicio ofrecido por un Usuario (proveedor)."""
    id_publicacion = models.BigAutoField(primary_key=True, db_column='ID_PUBLICACION')
    usuario_publicador = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, related_name='publicaciones', db_column='FK_USUARIO_P')
    titulo = models.CharField(max_length=255, null=True, db_column='TITULO')
    sub_titulo = models.CharField(max_length=255, null=True, blank=True, db_column='SUB_TITULO')
    descripcion_publicacion = models.TextField(null=True, db_column='DESCRIPCION_PUBLICACION')
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

    class Meta:
        db_table = 'PUBLICACIONES'

    def __str__(self):
        return self.titulo or str(self.id_publicacion)


class Imagenes(models.Model):
    """Imagen asociada a una Publicacion."""
    id_imagen = models.BigAutoField(primary_key=True, db_column='ID_IMAGEN')
    publicacion = models.ForeignKey(Publicaciones, on_delete=models.CASCADE, null=True, related_name='imagenes', db_column='FK_PUBLICACION')
    url_imagen = models.TextField(null=True, db_column='URL_IMAGEN')
    fecha_subida = models.DateTimeField(auto_now_add=True, db_column='FECHA_SUBIDA')
    actualizado_en = models.DateTimeField(auto_now=True, db_column='ACTUALIZADO_EN')

    class Meta:
        db_table = 'IMAGENES'

    def __str__(self):
        return str(self.id_imagen)


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
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FECHA_CREACION')
    fecha_actualizacion = models.DateTimeField(auto_now=True, db_column='FECHA_ACTUALIZACION')

    class Meta:
        db_table = 'CONTRATACION'

    def __str__(self):
        return f'Contratación #{self.id_contratacion} ({self.estado})'


class Valoracion(models.Model):
    """Calificación por estrellas + comentario que un Usuario deja sobre otro tras un servicio."""
    id_valoracion = models.BigAutoField(primary_key=True, db_column='ID_VALORACION')
    puntuacion = models.SmallIntegerField(db_column='PUNTUACION')
    comentario = models.TextField(null=True, blank=True, db_column='COMENTARIO')
    fecha_valoracion = models.DateTimeField(auto_now_add=True, db_column='FECHA_VALORACION')
    usuario_emisor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='valoraciones_emitidas', db_column='FK_USUARIO_EMISOR')
    usuario_receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='valoraciones_recibidas', db_column='FK_USUARIO_RECEPTOR')
    publicacion = models.ForeignKey(Publicaciones, on_delete=models.CASCADE, db_column='FK_PUBLICACION')

    class Meta:
        db_table = 'VALORACION'

    def __str__(self):
        return str(self.id_valoracion)


class Ranking(models.Model):
    """Agregado (promedio + total) de las Valoracion recibidas por un Usuario. Se recalcula en cada nueva Valoracion."""
    id_ranking = models.BigAutoField(primary_key=True, db_column='ID_RANKING')
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='ranking', db_column='FK_USUARIO')
    total_valoraciones = models.IntegerField(default=0, db_column='TOTAL_VALORACIONES')
    puntuacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0, db_column='PUNTUACION_PROMEDIO')

    class Meta:
        db_table = 'RANKING'

    def __str__(self):
        return str(self.id_ranking)


class Documento(models.Model):
    """Documento subido por un Usuario (ej. certificado de antecedentes, título)."""
    id_documento = models.BigAutoField(primary_key=True, db_column='ID_DOCUMENTO')
    nombre_documento = models.CharField(max_length=60, null=True, db_column='NOMBRE_DOCUMENTO')
    archivo = models.BinaryField(null=True, db_column='ARCHIVO')
    fecha_subida_documento = models.DateTimeField(auto_now_add=True, db_column='FECHA_SUBIDA_DOCUMENTO')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, db_column='FK_USUARIO')
    estado_documento = models.ForeignKey(EstadoDocumento, on_delete=models.PROTECT, null=True, db_column='FK_ESTADO_DOCUMENTO')

    class Meta:
        db_table = 'DOCUMENTO'

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

    def __str__(self):
        return str(self.id_gasto)
