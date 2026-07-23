from django.db import models


class AreaAdministrativa(models.Model):
    id_area_administrativa = models.IntegerField(db_column='ID_AREA_ADMINISTRATIVA', primary_key=True)  # Field name made lowercase.
    nombre_area_administrativa = models.CharField(db_column='NOMBRE_AREA_ADMINISTRATIVA', max_length=70, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'area_administrativa'


class Autentificacion(models.Model):
    id_autentificacion = models.BigAutoField(db_column='ID_AUTENTIFICACION', primary_key=True)  # Field name made lowercase.
    codigo_autentificacion = models.CharField(db_column='CODIGO_AUTENTIFICACION', max_length=32, blank=True, null=True)  # Field name made lowercase.
    fecha_autentificacion = models.DateTimeField(db_column='FECHA_AUTENTIFICACION')  # Field name made lowercase.
    fk_usuario_autentificacion = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_USUARIO_AUTENTIFICACION', blank=True, null=True)  # Field name made lowercase.
    fk_estado_autentificacion = models.ForeignKey('EstadoAutentificacion', models.DO_NOTHING, db_column='FK_ESTADO_AUTENTIFICACION', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'autentificacion'


class Comuna(models.Model):
    id_comuna = models.IntegerField(db_column='ID_COMUNA', primary_key=True)  # Field name made lowercase.
    nombre_comuna = models.CharField(db_column='NOMBRE_COMUNA', max_length=60, blank=True, null=True)  # Field name made lowercase.
    fk_region = models.ForeignKey('Region', models.DO_NOTHING, db_column='FK_REGION', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'comuna'


class Consulta(models.Model):
    id_consulta = models.BigAutoField(db_column='ID_CONSULTA', primary_key=True)  # Field name made lowercase.
    asunto_consulta = models.CharField(db_column='ASUNTO_CONSULTA', max_length=120, blank=True, null=True)  # Field name made lowercase.
    fecha_consulta = models.DateTimeField(db_column='FECHA_CONSULTA')  # Field name made lowercase.
    fecha_termino_consulta = models.DateTimeField(db_column='FECHA_TERMINO_CONSULTA', blank=True, null=True)  # Field name made lowercase.
    fk_estado_consulta = models.ForeignKey('EstadoConsulta', models.DO_NOTHING, db_column='FK_ESTADO_CONSULTA', blank=True, null=True)  # Field name made lowercase.
    fk_usuario_consulta = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_USUARIO_CONSULTA', blank=True, null=True)  # Field name made lowercase.
    fk_usuario_administrativo = models.ForeignKey('UsuarioAdministrativo', models.DO_NOTHING, db_column='FK_USUARIO_ADMINISTRATIVO', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'consulta'


class Conversacion(models.Model):
    id_conversacion = models.BigAutoField(db_column='ID_CONVERSACION', primary_key=True)  # Field name made lowercase.
    nombre_conversacion = models.CharField(db_column='NOMBRE_CONVERSACION', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fecha_creacion = models.DateTimeField(db_column='FECHA_CREACION')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'conversacion'


class Documento(models.Model):
    id_documento = models.BigAutoField(db_column='ID_DOCUMENTO', primary_key=True)  # Field name made lowercase.
    nombre_documento = models.CharField(db_column='NOMBRE_DOCUMENTO', max_length=60, blank=True, null=True)  # Field name made lowercase.
    archivo = models.TextField(db_column='ARCHIVO', blank=True, null=True)  # Field name made lowercase.
    fecha_subida_documento = models.DateTimeField(db_column='FECHA_SUBIDA_DOCUMENTO')  # Field name made lowercase.
    fk_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_USUARIO', blank=True, null=True)  # Field name made lowercase.
    fk_estado_documento = models.ForeignKey('EstadoDocumento', models.DO_NOTHING, db_column='FK_ESTADO_DOCUMENTO', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'documento'


class EstadoAutentificacion(models.Model):
    id_estado_autentificacion = models.IntegerField(db_column='ID_ESTADO_AUTENTIFICACION', primary_key=True)  # Field name made lowercase.
    nombre_estado_autentificacion = models.CharField(db_column='NOMBRE_ESTADO_AUTENTIFICACION', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'estado_autentificacion'


class EstadoConsulta(models.Model):
    id_estado_consulta = models.IntegerField(db_column='ID_ESTADO_CONSULTA', primary_key=True)  # Field name made lowercase.
    nombre_estado_consulta = models.CharField(db_column='NOMBRE_ESTADO_CONSULTA', max_length=30, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'estado_consulta'


class EstadoDocumento(models.Model):
    id_estado_documento = models.IntegerField(db_column='ID_ESTADO_DOCUMENTO', primary_key=True)  # Field name made lowercase.
    nombre_estado_documento = models.CharField(db_column='NOMBRE_ESTADO_DOCUMENTO', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'estado_documento'


class Firma(models.Model):
    id_firma = models.BigAutoField(db_column='ID_FIRMA', primary_key=True)  # Field name made lowercase.
    hash_firma = models.CharField(db_column='HASH_FIRMA', max_length=1, blank=True, null=True)  # Field name made lowercase.
    fecha_hora_firma = models.DateTimeField(db_column='FECHA_HORA_FIRMA')  # Field name made lowercase.
    fk_autentificacion = models.ForeignKey(Autentificacion, models.DO_NOTHING, db_column='FK_AUTENTIFICACION', blank=True, null=True)  # Field name made lowercase.
    fk_firma_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_FIRMA_USUARIO', blank=True, null=True)  # Field name made lowercase.
    fk_tipo_firma = models.ForeignKey('TipoFirma', models.DO_NOTHING, db_column='FK_TIPO_FIRMA', blank=True, null=True)  # Field name made lowercase.
    fk_documento = models.ForeignKey(Documento, models.DO_NOTHING, db_column='FK_DOCUMENTO', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'firma'


class Gasto(models.Model):
    id_gasto = models.BigAutoField(db_column='ID_GASTO', primary_key=True)  # Field name made lowercase.
    fecha_gasto = models.DateTimeField(db_column='FECHA_GASTO')  # Field name made lowercase.
    monto_gasto = models.IntegerField(db_column='MONTO_GASTO', blank=True, null=True)  # Field name made lowercase.
    fk_responsable_gasto = models.ForeignKey('UsuarioAdministrativo', models.DO_NOTHING, db_column='FK_RESPONSABLE_GASTO', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gasto'


class Imagenes(models.Model):
    id_imagen = models.BigAutoField(db_column='ID_IMAGEN', primary_key=True)  # Field name made lowercase.
    fk_publicacion = models.ForeignKey('Publicaciones', models.DO_NOTHING, db_column='FK_PUBLICACION', blank=True, null=True)  # Field name made lowercase.
    url_imagen = models.TextField(db_column='URL_IMAGEN', blank=True, null=True)  # Field name made lowercase.
    fecha_subida = models.DateTimeField(db_column='FECHA_SUBIDA')  # Field name made lowercase.
    actualizado_en = models.DateTimeField(db_column='ACTUALIZADO_EN')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'imagenes'


class Mensaje(models.Model):
    id_mensaje = models.BigAutoField(db_column='ID_MENSAJE', primary_key=True)  # Field name made lowercase.
    contenido = models.TextField(db_column='CONTENIDO', blank=True, null=True)  # Field name made lowercase.
    fecha_envio = models.DateTimeField(db_column='FECHA_ENVIO')  # Field name made lowercase.
    fk_conversacion = models.ForeignKey(Conversacion, models.DO_NOTHING, db_column='FK_CONVERSACION')  # Field name made lowercase.
    fk_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_USUARIO')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'mensaje'


class Publicaciones(models.Model):
    id_publicacion = models.BigAutoField(db_column='ID_PUBLICACION', primary_key=True)  # Field name made lowercase.
    fk_usuario_p = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_USUARIO_P', blank=True, null=True)  # Field name made lowercase.
    titulo = models.CharField(db_column='TITULO', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sub_titulo = models.CharField(db_column='SUB_TITULO', max_length=255, blank=True, null=True)  # Field name made lowercase.
    descripcion_publicacion = models.TextField(db_column='DESCRIPCION_PUBLICACION', blank=True, null=True)  # Field name made lowercase.
    fecha_publicacion = models.DateTimeField(db_column='FECHA_PUBLICACION')  # Field name made lowercase.
    actualizado_en = models.DateTimeField(db_column='ACTUALIZADO_EN')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'publicaciones'


class Ranking(models.Model):
    id_ranking = models.BigAutoField(db_column='ID_RANKING', primary_key=True)  # Field name made lowercase.
    fk_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='FK_USUARIO')  # Field name made lowercase.
    total_valoraciones = models.IntegerField(db_column='TOTAL_VALORACIONES', blank=True, null=True)  # Field name made lowercase.
    puntuacion_promedio = models.DecimalField(db_column='PUNTUACION_PROMEDIO', max_digits=3, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ranking'


class Region(models.Model):
    id_region = models.IntegerField(db_column='ID_REGION', primary_key=True)  # Field name made lowercase.
    nombre_region = models.CharField(db_column='NOMBRE_REGION', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'region'


class RolCuentaAdministrativa(models.Model):
    id_rol_cuenta_administrativa = models.IntegerField(db_column='ID_ROL_CUENTA_ADMINISTRATIVA', primary_key=True)  # Field name made lowercase.
    nombre_rol_cuenta_administrativa = models.CharField(db_column='NOMBRE_ROL_CUENTA_ADMINISTRATIVA', max_length=60, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'rol_cuenta_administrativa'


class TipoCuenta(models.Model):
    id_tipo_cuenta = models.AutoField(db_column='ID_TIPO_CUENTA', primary_key=True)  # Field name made lowercase.
    nombre_tipo_cuenta = models.CharField(db_column='NOMBRE_TIPO_CUENTA', max_length=50, blank=True, null=True)  # Field name made lowercase.
    valor_cuenta = models.IntegerField(db_column='VALOR_CUENTA', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tipo_cuenta'


class TipoFirma(models.Model):
    id_tipo_firma = models.IntegerField(db_column='ID_TIPO_FIRMA', primary_key=True)  # Field name made lowercase.
    nombre_tipo_firma = models.CharField(db_column='NOMBRE_TIPO_FIRMA', max_length=40, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tipo_firma'


class Transaccion(models.Model):
    id_transaccion = models.BigAutoField(db_column='ID_TRANSACCION', primary_key=True)  # Field name made lowercase.
    tiempo_transaccion = models.DateTimeField(db_column='TIEMPO_TRANSACCION')  # Field name made lowercase.
    fk_valor_cuenta = models.ForeignKey(TipoCuenta, models.DO_NOTHING, db_column='FK_VALOR_CUENTA', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'transaccion'


class Usuario(models.Model):
    id_usuario = models.BigAutoField(db_column='ID_USUARIO', primary_key=True)  # Field name made lowercase.
    rut_usuario = models.CharField(db_column='RUT_USUARIO', max_length=10, blank=True, null=True)  # Field name made lowercase.
    nombre_usuario = models.CharField(db_column='NOMBRE_USUARIO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    nombre2_usuario = models.CharField(db_column='NOMBRE2_USUARIO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    apellido_usuario = models.CharField(db_column='APELLIDO_USUARIO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    apellido2_usuario = models.CharField(db_column='APELLIDO2_USUARIO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    telefono = models.IntegerField(db_column='TELEFONO')  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=40, blank=True, null=True)  # Field name made lowercase.
    direccion_usuario = models.CharField(db_column='DIRECCION_USUARIO', max_length=80, blank=True, null=True)  # Field name made lowercase.
    fk_transaccion = models.ForeignKey(Transaccion, models.DO_NOTHING, db_column='FK_TRANSACCION', blank=True, null=True)  # Field name made lowercase.
    fk_tipo_cuenta = models.ForeignKey(TipoCuenta, models.DO_NOTHING, db_column='FK_TIPO_CUENTA', blank=True, null=True)  # Field name made lowercase.
    fk_comuna = models.ForeignKey(Comuna, models.DO_NOTHING, db_column='FK_COMUNA', blank=True, null=True)  # Field name made lowercase.
    edad = models.IntegerField(db_column='EDAD')  # Field name made lowercase.
    contraseña = models.CharField(db_column='CONTRASEÑA', max_length=64)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'usuario'


class UsuarioAdministrativo(models.Model):
    id_usuario_administrativo = models.AutoField(db_column='ID_USUARIO_ADMINISTRATIVO', primary_key=True)  # Field name made lowercase.
    rut_usuario_administrativo = models.CharField(db_column='RUT_USUARIO_ADMINISTRATIVO', max_length=10, blank=True, null=True)  # Field name made lowercase.
    nombre_usuario_administrativo = models.CharField(db_column='NOMBRE_USUARIO_ADMINISTRATIVO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    nombre2_usuario_administrativo = models.CharField(db_column='NOMBRE2_USUARIO_ADMINISTRATIVO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    apellido_usuario_administrativo = models.CharField(db_column='APELLIDO_USUARIO_ADMINISTRATIVO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    apellido2_usuario_administrativo = models.CharField(db_column='APELLIDO2_USUARIO_ADMINISTRATIVO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    telefono_usuario_administrativo = models.IntegerField(db_column='TELEFONO_USUARIO_ADMINISTRATIVO')  # Field name made lowercase.
    email_usuario_administrativo = models.CharField(db_column='EMAIL_USUARIO_ADMINISTRATIVO', max_length=40, blank=True, null=True)  # Field name made lowercase.
    fk_rol_cuenta_administrativa = models.ForeignKey(RolCuentaAdministrativa, models.DO_NOTHING, db_column='FK_ROL_CUENTA_ADMINISTRATIVA', blank=True, null=True)  # Field name made lowercase.
    fk_area_administrativa = models.ForeignKey(AreaAdministrativa, models.DO_NOTHING, db_column='FK_AREA_ADMINISTRATIVA', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'usuario_administrativo'


class UsuarioConversacion(models.Model):
    id_usuario_conversacion = models.BigAutoField(db_column='ID_USUARIO_CONVERSACION', primary_key=True)  # Field name made lowercase.
    fk_usuario_c = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='FK_USUARIO_C')  # Field name made lowercase.
    fk_conversacion = models.ForeignKey(Conversacion, models.DO_NOTHING, db_column='FK_CONVERSACION')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'usuario_conversacion'


class Valoracion(models.Model):
    id_valoracion = models.BigAutoField(db_column='ID_VALORACION', primary_key=True)  # Field name made lowercase.
    puntuacion = models.SmallIntegerField(db_column='PUNTUACION')  # Field name made lowercase.
    comentario = models.TextField(db_column='COMENTARIO', blank=True, null=True)  # Field name made lowercase.
    fecha_valoracion = models.DateTimeField(db_column='FECHA_VALORACION')  # Field name made lowercase.
    fk_usuario_emisor = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='FK_USUARIO_EMISOR')  # Field name made lowercase.
    fk_usuario_receptor = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='FK_USUARIO_RECEPTOR', related_name='valoracion_fk_usuario_receptor_set')  # Field name made lowercase.
    fk_publicacion = models.ForeignKey(Publicaciones, models.DO_NOTHING, db_column='FK_PUBLICACION')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'valoracion'
