from django.contrib import admin
from django.urls import path, include  # Asegúrate de importar include aquí

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('KeyServApp.urls')),  # Agrega esto aquí
]