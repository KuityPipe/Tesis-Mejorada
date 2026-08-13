from rest_framework import serializers

from ..models import Usuario


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
