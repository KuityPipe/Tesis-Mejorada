from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include  # Asegúrate de importar include aquí

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('KeyServApp.urls')),  # Agrega esto aquí
]

# Sirve las imágenes/documentos subidos (MEDIA_ROOT) en desarrollo — en
# producción esto lo debe servir el servidor web (nginx/etc.), no Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)