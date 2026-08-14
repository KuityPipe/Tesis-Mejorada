from django.urls import path

from . import views

app_name = 'KeyServApp_api'

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/registro/', views.RegistroView.as_view(), name='registro'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/perfil/', views.PerfilView.as_view(), name='perfil'),
    path('publicaciones/', views.PublicacionListView.as_view(), name='publicaciones-list'),
    path('publicaciones/<int:pk>/', views.PublicacionDetailView.as_view(), name='publicaciones-detail'),
    path('catalogos/regiones/', views.RegionListView.as_view(), name='catalogo-regiones'),
    path('catalogos/comunas/', views.ComunaListView.as_view(), name='catalogo-comunas'),
    path('catalogos/tipos-cuenta/', views.TipoCuentaListView.as_view(), name='catalogo-tipos-cuenta'),
]
