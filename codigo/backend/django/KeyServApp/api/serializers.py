from rest_framework import serializers

from ..models import (
    Comuna, Contratacion, Documento, HistorialEstadoContratacion, Imagenes, ItemPresupuesto, Mensaje, Pago,
    Publicaciones, Region, TipoCuenta, Usuario, Valoracion, ValoracionImagen,
)


class LoginSerializer(serializers.Serializer):
    """Espejo de `LoginForm` (forms.py) — la validación real (bloqueo por intentos, `check_password`) vive en la vista, igual que en `sesion_view`."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class UsuarioMeSerializer(serializers.ModelSerializer):
    """
    Perfil del usuario autenticado — `GET /api/auth/me/`. Nunca incluye
    `password` ni `encoding_facial` (dato biométrico crudo, y de todos
    modos en retiro, ver plan de migración).

    `comuna` viene incluido como el pk plano (comportamiento default de
    DRF para una FK en un ModelSerializer) y `region` es un
    `SerializerMethodField` derivado de `comuna.region_id` — ninguno de
    los dos se usa para mostrar el perfil, existen para poder precargar el
    formulario de "editar perfil" en Ionic (cascade región→comuna, mismo
    patrón que `RegistroForm`) sin una segunda request.
    """
    region = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'rut_usuario', 'nombre_usuario', 'nombre2_usuario',
            'apellido_usuario', 'apellido2_usuario', 'telefono', 'email',
            'direccion_usuario', 'edad', 'es_proveedor',
            'verificado_biometricamente', 'foto_perfil', 'areas_servicio',
            'experiencia', 'notificaciones_sonido', 'comuna', 'region',
        ]
        read_only_fields = fields

    def get_region(self, usuario) -> int | None:
        return usuario.comuna.region_id if usuario.comuna else None


class DocumentoPerfilSerializer(serializers.ModelSerializer):
    """
    Un certificado/documento del perfil de proveedor (`Documento` con
    `usuario` set y sin `publicacion`) — solo para listar/borrar desde
    `PerfilProveedorView`/`DocumentoPerfilEliminarView`. Nunca expone el
    archivo en sí: la descarga sigue siendo `documento_descargar_view`
    (sesión de Django), no migrada todavía — este perfil de proveedor no
    tiene aún una pantalla pública que muestre los certificados como
    credenciales, mismo estado que del lado template (ver CLAUDE.md).
    """
    class Meta:
        model = Documento
        fields = ['id_documento', 'nombre_documento', 'fecha_subida_documento']
        read_only_fields = fields


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """Una fila de la línea de tiempo de una Contratacion (`Contratacion.historial_estados`)."""
    class Meta:
        model = HistorialEstadoContratacion
        fields = ['estado', 'fecha']
        read_only_fields = fields


class ItemPresupuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPresupuesto
        fields = ['id_item_presupuesto', 'descripcion', 'categoria', 'monto', 'orden']
        read_only_fields = fields


class ValoracionImagenSerializer(serializers.ModelSerializer):
    """Igual que `ImagenSerializer`/`DocumentoPerfilSerializer`: solo lo necesario para mostrarla, `archivo.url` es relativo a `MEDIA_URL` (mismo criterio ya usado en `ImagenSerializer`)."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = ValoracionImagen
        fields = ['id_valoracion_imagen', 'url', 'estado_moderacion']
        read_only_fields = fields

    def get_url(self, imagen) -> str | None:
        return imagen.archivo.url if imagen.archivo else None


class ValoracionSerializer(serializers.ModelSerializer):
    """Una reseña propia, tal como la ve su emisor/receptor desde el detalle de la Contratacion — a diferencia de `ValoracionSerializer` en el catálogo público, esta SÍ puede estar `PENDIENTE` (el emisor ve su propia reseña con ese estado, mismo criterio que `contratacion_detalle_view`)."""
    imagenes = ValoracionImagenSerializer(many=True, read_only=True)

    class Meta:
        model = Valoracion
        fields = ['id_valoracion', 'puntuacion', 'comentario', 'fecha_valoracion', 'estado_moderacion', 'imagenes']
        read_only_fields = fields


class ResenaRecibidaSerializer(serializers.ModelSerializer):
    """
    `GET /api/perfil/resenas-recibidas/` — equivalente API de la sección
    "Reseñas y calificaciones recibidas" de `perfil.html` (`perfil_view`).
    Nombre distinto a propósito de los otros dos `ValoracionSerializer` ya
    definidos en este archivo (arriba, para la propia reseña embebida en
    una contratación puntual; más abajo, para reseñas ya moderadas de una
    publicación pública) — sumar un tercer uso del mismo nombre solo
    haría más frágil una situación que ya depende de en qué orden Python
    liga cada referencia (atributo de clase vs. dentro de un método).
    Incluye `estado_moderacion` aunque `perfil.html` no lo muestre —
    Ionic sí lo usa para la misma nota "Pendiente de revisión" que ya
    tiene `contratacion/detalle` para la propia reseña dejada.
    """
    usuario_emisor = serializers.CharField(source='usuario_emisor.nombre_usuario', read_only=True)

    class Meta:
        model = Valoracion
        fields = ['id_valoracion', 'puntuacion', 'comentario', 'fecha_valoracion', 'estado_moderacion', 'usuario_emisor']
        read_only_fields = fields


class PagoSerializer(serializers.ModelSerializer):
    """Estado del cobro de una Contratacion — nunca expone `respuesta_bruta`/`token_webpay`/`khipu_payment_id` (detalles internos del medio de pago, no algo que el cliente Ionic necesite)."""
    class Meta:
        model = Pago
        fields = ['id_pago', 'metodo', 'estado', 'monto', 'fecha_creacion', 'fecha_confirmacion']
        read_only_fields = fields


class PagoHistorialSerializer(serializers.ModelSerializer):
    """
    `GET /api/pagos/historial/` — equivalente API de `historial_pagos_view`.
    A diferencia de `PagoSerializer` (embebido en el detalle de UNA
    contratación puntual, donde ya se sabe cuál es), acá hace falta
    `contratacion_id`/`publicacion_titulo` para poder listar varios pagos
    sueltos y enlazar cada uno de vuelta a su contratación, igual que
    `historial_pagos.html` hace con `pago.contratacion.id_contratacion`/
    `pago.contratacion.publicacion.titulo`.
    """
    contratacion_id = serializers.IntegerField(source='contratacion.id_contratacion', read_only=True)
    publicacion_titulo = serializers.CharField(source='contratacion.publicacion.titulo', read_only=True)

    class Meta:
        model = Pago
        fields = [
            'id_pago', 'metodo', 'estado', 'monto', 'fecha_creacion', 'fecha_confirmacion',
            'contratacion_id', 'publicacion_titulo',
        ]
        read_only_fields = fields


class ContratacionListSerializer(serializers.ModelSerializer):
    """`GET /api/contrataciones/` — equivalente API de `reservas_view`. `cliente`/`proveedor` vienen como el pk plano (default de DRF para una FK) — el cliente Ionic decide su propio rol comparando contra `GET /api/auth/me/`, no hay un campo `rol` calculado acá."""
    publicacion_titulo = serializers.CharField(source='publicacion.titulo', read_only=True)
    publicacion_imagen = serializers.SerializerMethodField()
    cliente_nombre = serializers.CharField(source='cliente.nombre_usuario', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre_usuario', read_only=True)
    # Para el grid de reservas.page (Ionic) — mismo dato que `contratacion.valoracion`
    # en reservas.html, para distinguir "Calificar" de "Ya calificaste este trabajo"
    # sin pedir el detalle completo de cada tarjeta.
    tiene_valoracion = serializers.SerializerMethodField()

    class Meta:
        model = Contratacion
        fields = [
            'id_contratacion', 'estado', 'monto_acordado', 'fecha_creacion',
            'publicacion', 'publicacion_titulo', 'publicacion_imagen',
            'cliente', 'cliente_nombre', 'proveedor', 'proveedor_nombre',
            'tiene_valoracion',
        ]
        read_only_fields = fields

    def get_publicacion_imagen(self, contratacion) -> str | None:
        primera = contratacion.publicacion.imagenes.first()
        return primera.url if primera else None

    def get_tiene_valoracion(self, contratacion) -> bool:
        return hasattr(contratacion, 'valoracion') and contratacion.valoracion is not None


class ContratacionDetailSerializer(ContratacionListSerializer):
    """`GET /api/contrataciones/<id>/` — equivalente API de la mitad "detalle" de `contratacion_detalle_view` (todo menos el chat, ver `MensajeSerializer`/`ContratacionMensajesView`)."""
    historial = HistorialEstadoSerializer(source='historial_estados', many=True, read_only=True)
    items_presupuesto = ItemPresupuestoSerializer(many=True, read_only=True)
    valoracion = ValoracionSerializer(read_only=True)
    pago = PagoSerializer(read_only=True)
    # `contratacion_detalle.html` también muestra la descripción e imágenes
    # de la publicación (no solo la portada) — el detalle de contratación
    # es donde tiene sentido revisarlas de nuevo (ej. antes de calificar),
    # no hace falta ir hasta /catalogo/<id> para verlas.
    publicacion_descripcion = serializers.CharField(source='publicacion.descripcion_publicacion', read_only=True)
    publicacion_imagenes = serializers.SerializerMethodField()

    class Meta(ContratacionListSerializer.Meta):
        fields = ContratacionListSerializer.Meta.fields + [
            'historial', 'items_presupuesto', 'valoracion', 'pago',
            'publicacion_descripcion', 'publicacion_imagenes',
        ]
        read_only_fields = fields

    def get_publicacion_imagenes(self, contratacion) -> list[str]:
        return [imagen.url for imagen in contratacion.publicacion.imagenes.all() if imagen.url]


class MensajeSerializer(serializers.ModelSerializer):
    """Un mensaje del chat de una Contratacion — `conversacion`/`usuario` los fija la vista (`ContratacionMensajesView`), nunca el cliente."""
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)

    class Meta:
        model = Mensaje
        fields = ['id_mensaje', 'contenido', 'fecha_envio', 'usuario', 'usuario_nombre']
        read_only_fields = ['id_mensaje', 'fecha_envio', 'usuario', 'usuario_nombre']


class ConversacionResumenSerializer(serializers.Serializer):
    """
    `GET /api/conversaciones/` — equivalente API de `chat_view` (bandeja de
    entrada). No es un `ModelSerializer` a propósito: igual que el
    template, cada fila combina la `Conversacion` con datos calculados
    aparte (no_leidos, último mensaje, contraparte) que no son campos
    reales del modelo — se arman a mano en `ConversacionListView` y este
    serializer solo define la forma de esa lista de dicts.
    """
    id_conversacion = serializers.IntegerField()
    contratacion_id = serializers.IntegerField(allow_null=True)
    publicacion_titulo = serializers.CharField(allow_null=True)
    contratacion_estado = serializers.CharField(allow_null=True)
    contraparte_nombre = serializers.CharField(allow_null=True)
    no_leidos = serializers.IntegerField()
    ultimo_mensaje_contenido = serializers.CharField(allow_null=True)
    ultimo_mensaje_fecha = serializers.DateTimeField(allow_null=True)
    ultimo_mensaje_es_propio = serializers.BooleanField()


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id_region', 'nombre_region']
        read_only_fields = fields


class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = ['id_comuna', 'nombre_comuna', 'region_id']
        read_only_fields = fields


class TipoCuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCuenta
        fields = ['id_tipo_cuenta', 'nombre_tipo_cuenta', 'valor_cuenta']
        read_only_fields = fields


class ImagenSerializer(serializers.ModelSerializer):
    """Una imagen de `Publicaciones.imagenes` — `url` resuelve archivo subido vs URL sembrada (ver `Imagenes.url` en models.py), el cliente no necesita saber cuál es cuál."""
    url = serializers.ReadOnlyField()

    class Meta:
        model = Imagenes
        fields = ['id_imagen', 'url']
        read_only_fields = fields


class ProveedorSerializer(serializers.ModelSerializer):
    """
    Perfil público de un proveedor, tal como se ve embebido en una
    publicación — nunca el perfil completo (`UsuarioMeSerializer` arriba,
    que incluye datos que solo el propio usuario debería ver, como
    `verificado_biometricamente`).

    `comuna`/`ranking` son opcionales (el usuario puede no tener comuna
    cargada, o no tener fila en `Ranking` todavía si nadie lo calificó) —
    se resuelven con `SerializerMethodField` + `getattr(obj, attr, None)`
    en vez de `source='ranking.puntuacion_promedio'` con `default=...`:
    esto último se probó y no aplicaba el default de forma consistente
    entre campos (bug real encontrado en tests_api.py,
    `test_listado_incluye_proveedor_embebido` — `total_valoraciones`
    volvía `None` en vez del `default=0` declarado), así que se prefirió
    esta forma explícita, más fácil de verificar.
    """
    comuna = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    puntuacion_promedio = serializers.SerializerMethodField()
    total_valoraciones = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'nombre_usuario', 'apellido_usuario', 'foto_perfil',
            'comuna', 'region', 'puntuacion_promedio', 'total_valoraciones',
        ]
        read_only_fields = fields

    def get_comuna(self, usuario) -> str | None:
        return usuario.comuna.nombre_comuna if usuario.comuna else None

    def get_region(self, usuario) -> str | None:
        return usuario.comuna.region.nombre_region if usuario.comuna else None

    def get_puntuacion_promedio(self, usuario):
        ranking = getattr(usuario, 'ranking', None)
        return ranking.puntuacion_promedio if ranking else None

    def get_total_valoraciones(self, usuario) -> int:
        ranking = getattr(usuario, 'ranking', None)
        return ranking.total_valoraciones if ranking else 0


class ValoracionSerializer(serializers.ModelSerializer):
    """Una reseña ya moderada (ver `PublicacionDetailSerializer.get_resenas`) — nunca las `PENDIENTE`/`RECHAZADA`, mismo criterio que `publicacion_detalle_view`."""
    usuario_emisor = serializers.CharField(source='usuario_emisor.nombre_usuario', read_only=True)

    class Meta:
        model = Valoracion
        fields = ['id_valoracion', 'puntuacion', 'comentario', 'fecha_valoracion', 'usuario_emisor']
        read_only_fields = fields


class PublicacionListSerializer(serializers.ModelSerializer):
    """`GET /api/publicaciones/` — versión liviana para el listado (una imagen de portada, no todas), equivalente API de `catalogo_view`."""
    proveedor = ProveedorSerializer(source='usuario_publicador', read_only=True)
    imagen_portada = serializers.SerializerMethodField()

    class Meta:
        model = Publicaciones
        fields = [
            'id_publicacion', 'titulo', 'sub_titulo', 'categoria', 'precio',
            'fecha_publicacion', 'imagen_portada', 'proveedor',
        ]
        read_only_fields = fields

    def get_imagen_portada(self, publicacion) -> str | None:
        # `.imagenes` viene con `prefetch_related` desde la vista — `.first()`
        # acá reutiliza esa caché en vez de disparar una query nueva por
        # cada publicación del listado (evitaría el problema N+1 si no).
        primera = publicacion.imagenes.first()
        return primera.url if primera else None


class PublicacionPropiaSerializer(serializers.ModelSerializer):
    """
    `GET /api/publicaciones/mias/` — a diferencia de `PublicacionListSerializer`
    (el catálogo público, siempre `APROBADA`), acá el dueño necesita ver el
    estado real de cada una de sus publicaciones (pendiente/aprobada/
    rechazada), igual que `perfil.html` muestra con `.ks-badge-{{ estado
    |lower }}` — `estado_moderacion_display` es el texto legible
    (`get_estado_moderacion_display()`, no expuesto por defecto en un
    `ModelSerializer`) para no duplicar ese mapeo en el cliente.
    """
    imagen_portada = serializers.SerializerMethodField()
    estado_moderacion_display = serializers.CharField(source='get_estado_moderacion_display', read_only=True)

    class Meta:
        model = Publicaciones
        fields = [
            'id_publicacion', 'titulo', 'categoria', 'precio', 'fecha_publicacion',
            'imagen_portada', 'estado_moderacion', 'estado_moderacion_display',
        ]
        read_only_fields = fields

    def get_imagen_portada(self, publicacion) -> str | None:
        primera = publicacion.imagenes.first()
        return primera.url if primera else None


class PublicacionDetailSerializer(serializers.ModelSerializer):
    """`GET /api/publicaciones/<pk>/` — equivalente API de `publicacion_detalle_view`, sin el estado de "ya la contraté" (eso llega recién en la fase de contrataciones del plan de migración)."""
    proveedor = ProveedorSerializer(source='usuario_publicador', read_only=True)
    imagenes = ImagenSerializer(many=True, read_only=True)
    resenas = serializers.SerializerMethodField()

    class Meta:
        model = Publicaciones
        fields = [
            'id_publicacion', 'titulo', 'sub_titulo', 'descripcion_publicacion',
            'categoria', 'precio', 'fecha_publicacion', 'imagenes', 'proveedor', 'resenas',
        ]
        read_only_fields = fields

    def get_resenas(self, publicacion) -> list:
        resenas = Valoracion.objects.filter(
            publicacion=publicacion, estado_moderacion=Valoracion.APROBADA,
        ).select_related('usuario_emisor').order_by('-fecha_valoracion')
        return ValoracionSerializer(resenas, many=True).data
