from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include  # Asegúrate de importar include aquí
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/', include('KeyServApp.api.urls')),
    # Schema OpenAPI (fuente del cliente TypeScript generado en el
    # frontend Ionic, ver plan de migración) + una UI navegable para
    # probar endpoints a mano en desarrollo.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('', include('KeyServApp.urls')),  # Agrega esto aquí
]

# Sirve las imágenes/documentos subidos (MEDIA_ROOT) en desarrollo — en
# producción esto lo debe servir el servidor web (nginx/etc.), no Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)