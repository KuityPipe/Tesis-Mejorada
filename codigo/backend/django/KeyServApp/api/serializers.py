from rest_framework import serializers

from ..models import Imagenes, Publicaciones, Usuario, Valoracion


class LoginSerializer(serializers.Serializer):
    """Espejo de `LoginForm` (forms.py) — la validación real (bloqueo por intentos, `check_password`) vive en la vista, igual que en `sesion_view`."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class UsuarioMeSerializer(serializers.ModelSerializer):
    """Perfil del usuario autenticado — `GET /api/auth/me/`. Nunca incluye `password` ni `encoding_facial` (dato biométrico crudo, y de todos modos en retiro, ver plan de migración)."""

    class Meta:
        model = Usuario
        fields = [
            'id_usuario', 'rut_usuario', 'nombre_usuario', 'nombre2_usuario',
            'apellido_usuario', 'apellido2_usuario', 'telefono', 'email',
            'direccion_usuario', 'edad', 'es_proveedor',
            'verificado_biometricamente', 'foto_perfil', 'areas_servicio',
            'experiencia', 'notificaciones_sonido',
        ]
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
