from django.db import models
import hashlib

class AreaAdministrativa(models.Model):
    ID_AREA_ADMINISTRATIVA = models.IntegerField(primary_key=True)
    NOMBRE_AREA_ADMINISTRATIVA = models.CharField(max_length=70, null=True)

    def __str__(self):
        return self.NOMBRE_AREA_ADMINISTRATIVA


class Autentificacion(models.Model):
    ID_AUTENTIFICACION = models.BigAutoField(primary_key=True)
    CODIGO_AUTENTIFICACION = models.BinaryField(max_length=32, null=True)
    FECHA_AUTENTIFICACION = models.DateTimeField(auto_now_add=True)
    FK_USUARIO_AUTENTIFICACION = models.BigIntegerField(null=True)
    FK_ESTADO_AUTENTIFICACION = models.IntegerField(null=True)

    def __str__(self):
        return str(self.ID_AUTENTIFICACION)


class Comuna(models.Model):
    ID_COMUNA = models.IntegerField(primary_key=True)
    NOMBRE_COMUNA = models.CharField(max_length=60, null=True)
    FK_REGION = models.IntegerField(null=True)

    def __str__(self):
        return self.NOMBRE_COMUNA


class Consulta(models.Model):
    ID_CONSULTA = models.BigAutoField(primary_key=True)
    ASUNTO_CONSULTA = models.CharField(max_length=120, null=True)
    FECHA_CONSULTA = models.DateTimeField(auto_now_add=True)
    FECHA_TERMINO_CONSULTA = models.DateTimeField(null=True)
    FK_ESTADO_CONSULTA = models.IntegerField(null=True)
    FK_USUARIO_CONSULTA = models.BigIntegerField(null=True)
    FK_USUARIO_ADMINISTRATIVO = models.IntegerField(null=True)

    def __str__(self):
        return str(self.ID_CONSULTA)


class Conversacion(models.Model):
    ID_CONVERSACION = models.BigAutoField(primary_key=True)
    NOMBRE_CONVERSACION = models.CharField(max_length=255, null=True)
    FECHA_CREACION = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.ID_CONVERSACION)


class Documento(models.Model):
    ID_DOCUMENTO = models.BigAutoField(primary_key=True)
    NOMBRE_DOCUMENTO = models.CharField(max_length=60, null=True)
    ARCHIVO = models.BinaryField(null=True)
    FECHA_SUBIDA_DOCUMENTO = models.DateTimeField(auto_now_add=True)
    FK_USUARIO = models.BigIntegerField(null=True)
    FK_ESTADO_DOCUMENTO = models.IntegerField(null=True)

    def __str__(self):
        return str(self.ID_DOCUMENTO)


class EstadoAutentificacion(models.Model):
    ID_ESTADO_AUTENTIFICACION = models.IntegerField(primary_key=True)
    NOMBRE_ESTADO_AUTENTIFICACION = models.CharField(max_length=40, null=True)

    def __str__(self):
        return self.NOMBRE_ESTADO_AUTENTIFICACION


class EstadoConsulta(models.Model):
    ID_ESTADO_CONSULTA = models.IntegerField(primary_key=True)
    NOMBRE_ESTADO_CONSULTA = models.CharField(max_length=30, null=True)

    def __str__(self):
        return self.NOMBRE_ESTADO_CONSULTA


class EstadoDocumento(models.Model):
    ID_ESTADO_DOCUMENTO = models.IntegerField(primary_key=True)
    NOMBRE_ESTADO_DOCUMENTO = models.CharField(max_length=40, null=True)

    def __str__(self):
        return self.NOMBRE_ESTADO_DOCUMENTO


class Firma(models.Model):
    ID_FIRMA = models.BigAutoField(primary_key=True)
    HASH_FIRMA = models.BinaryField(max_length=1, null=True)
    FECHA_HORA_FIRMA = models.DateTimeField(auto_now_add=True)
    FK_AUTENTIFICACION = models.BigIntegerField(null=True)
    FK_FIRMA_USUARIO = models.BigIntegerField(null=True)
    FK_TIPO_FIRMA = models.IntegerField(null=True)
    FK_DOCUMENTO = models.BigIntegerField(null=True)

    def __str__(self):
        return str(self.ID_FIRMA)


class Gasto(models.Model):
    ID_GASTO = models.BigAutoField(primary_key=True)
    FECHA_GASTO = models.DateTimeField(auto_now_add=True)
    MONTO_GASTO = models.IntegerField(null=True)
    FK_RESPONSABLE_GASTO = models.IntegerField(null=True)

    def __str__(self):
        return str(self.ID_GASTO)


class Imagenes(models.Model):
    ID_IMAGEN = models.BigAutoField(primary_key=True)
    FK_PUBLICACION = models.BigIntegerField(null=True)
    URL_IMAGEN = models.TextField(null=True)
    FECHA_SUBIDA = models.DateTimeField(auto_now_add=True)
    ACTUALIZADO_EN = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.ID_IMAGEN)


class Mensaje(models.Model):
    ID_MENSAJE = models.BigAutoField(primary_key=True)
    CONTENIDO = models.TextField(null=True)
    FECHA_ENVIO = models.DateTimeField(auto_now_add=True)
    FK_CONVERSACION = models.BigIntegerField()
    FK_USUARIO = models.BigIntegerField()

    def __str__(self):
        return str(self.ID_MENSAJE)


class Publicaciones(models.Model):
    ID_PUBLICACION = models.BigAutoField(primary_key=True)
    FK_USUARIO_P = models.BigIntegerField(null=True)
    TITULO = models.CharField(max_length=255, null=True)
    SUB_TITULO = models.CharField(max_length=255, null=True)
    DESCRIPCION_PUBLICACION = models.TextField(null=True)
    FECHA_PUBLICACION = models.DateTimeField(auto_now_add=True)
    ACTUALIZADO_EN = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.ID_PUBLICACION)


class Ranking(models.Model):
    ID_RANKING = models.BigAutoField(primary_key=True)
    FK_USUARIO = models.BigIntegerField()
    TOTAL_VALORACIONES = models.IntegerField(default=0)
    PUNTUACION_PROMEDIO = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def __str__(self):
        return str(self.ID_RANKING)


class Region(models.Model):
    ID_REGION = models.IntegerField(primary_key=True)
    NOMBRE_REGION = models.CharField(max_length=40, null=True)

    def __str__(self):
        return self.NOMBRE_REGION


class RolCuentaAdministrativa(models.Model):
    ID_ROL_CUENTA_ADMINISTRATIVA = models.IntegerField(primary_key=True)
    NOMBRE_ROL_CUENTA_ADMINISTRATIVA = models.CharField(max_length=60, null=True)

    def __str__(self):
        return self.NOMBRE_ROL_CUENTA_ADMINISTRATIVA


class TipoCuenta(models.Model):
    ID_TIPO_CUENTA = models.IntegerField(primary_key=True)
    NOMBRE_TIPO_CUENTA = models.CharField(max_length=50, null=True)
    VALOR_CUENTA = models.IntegerField(null=True)

    def __str__(self):
        return self.NOMBRE_TIPO_CUENTA


class TipoFirma(models.Model):
    ID_TIPO_FIRMA = models.IntegerField(primary_key=True)
    NOMBRE_TIPO_FIRMA = models.CharField(max_length=40, null=True)

    def __str__(self):
        return self.NOMBRE_TIPO_FIRMA


class Transaccion(models.Model):
    ID_TRANSACCION = models.BigAutoField(primary_key=True)
    TIEMPO_TRANSACCION = models.DateTimeField(auto_now_add=True)
    FK_VALOR_CUENTA = models.IntegerField(null=True)

    def __str__(self):
        return str(self.ID_TRANSACCION)


class Usuario(models.Model):
    ID_USUARIO = models.BigIntegerField(primary_key=True)
    RUT_USUARIO = models.CharField(max_length=10, null=True)
    NOMBRE_USUARIO = models.CharField(max_length=40, null=True)
    NOMBRE2_USUARIO = models.CharField(max_length=40, null=True)
    APELLIDO_USUARIO = models.CharField(max_length=40, null=True)
    APELLIDO2_USUARIO = models.CharField(max_length=40, null=True)
    TELEFONO = models.IntegerField()
    EMAIL = models.CharField(max_length=40, null=True)
    DIRECCION_USUARIO = models.CharField(max_length=80, null=True)
    FK_TRANSACCION = models.BigIntegerField(null=True)
    FK_TIPO_CUENTA = models.IntegerField(null=True)
    FK_COMUNA = models.IntegerField(null=True)
    EDAD = models.IntegerField()
    CONTRASEÑA = models.CharField(max_length=64)

    def __str__(self):
        return str(self.ID_USUARIO)

    def save(self, *args, **kwargs):
        self.CONTRASEÑA = hashlib.sha256(self.CONTRASEÑA.encode()).hexdigest()
        super().save(*args, **kwargs)

class UsuarioAdministrativo(models.Model):
    ID_USUARIO_ADMINISTRATIVO = models.IntegerField(primary_key=True)
    RUT_USUARIO_ADMINISTRATIVO = models.CharField(max_length=10, null=True)
    NOMBRE_USUARIO_ADMINISTRATIVO = models.CharField(max_length=40, null=True)
    NOMBRE2_USUARIO_ADMINISTRATIVO = models.CharField(max_length=40, null=True)
    APELLIDO_USUARIO_ADMINISTRATIVO = models.CharField(max_length=40, null=True)
    APELLIDO2_USUARIO_ADMINISTRATIVO = models.CharField(max_length=40, null=True)
    TELEFONO_USUARIO_ADMINISTRATIVO = models.IntegerField()
    EMAIL_USUARIO_ADMINISTRATIVO = models.CharField(max_length=40, null=True)
    FK_ROL_CUENTA_ADMINISTRATIVA = models.IntegerField(null=True)
    FK_AREA_ADMINISTRATIVA = models.IntegerField(null=True)

    def __str__(self):
        return str(self.ID_USUARIO_ADMINISTRATIVO)


class UsuarioConversacion(models.Model):
    ID_USUARIO_CONVERSACION = models.BigIntegerField(primary_key=True)
    FK_USUARIO_C = models.BigIntegerField()
    FK_CONVERSACION = models.BigIntegerField()

    def __str__(self):
        return str(self.ID_USUARIO_CONVERSACION)


class Valoracion(models.Model):
    ID_VALORACION = models.BigIntegerField(primary_key=True)
    PUNTUACION = models.SmallIntegerField()
    COMENTARIO = models.TextField(null=True)
    FECHA_VALORACION = models.DateTimeField(auto_now_add=True)
    FK_USUARIO_EMISOR = models.BigIntegerField()
    FK_USUARIO_RECEPTOR = models.BigIntegerField()
    FK_PUBLICACION = models.BigIntegerField()

    def __str__(self):
        return str(self.ID_VALORACION)