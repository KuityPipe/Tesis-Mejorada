from django.urls import path

from . import views

app_name = 'KeyServApp_api'

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/registro/', views.RegistroView.as_view(), name='registro'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/perfil/', views.PerfilView.as_view(), name='perfil'),
    path('auth/perfil-proveedor/', views.PerfilProveedorView.as_view(), name='perfil-proveedor'),
    path('auth/perfil-proveedor/documentos/', views.DocumentoPerfilListView.as_view(), name='perfil-proveedor-documentos'),
    path('auth/perfil-proveedor/documentos/<int:documento_id>/', views.DocumentoPerfilEliminarView.as_view(), name='perfil-proveedor-documento-eliminar'),
    path('auth/preferencias/', views.PreferenciasView.as_view(), name='preferencias'),
    path('auth/cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar-password'),
    path('auth/recuperar/', views.RecuperarView.as_view(), name='recuperar'),
    path('auth/recuperar/confirmar/<str:token>/', views.RecuperarConfirmarView.as_view(), name='recuperar-confirmar'),
    path('publicaciones/', views.PublicacionListView.as_view(), name='publicaciones-list'),
    path('publicaciones/<int:pk>/', views.PublicacionDetailView.as_view(), name='publicaciones-detail'),
    path('catalogos/regiones/', views.RegionListView.as_view(), name='catalogo-regiones'),
    path('catalogos/comunas/', views.ComunaListView.as_view(), name='catalogo-comunas'),
    path('catalogos/tipos-cuenta/', views.TipoCuentaListView.as_view(), name='catalogo-tipos-cuenta'),
    path('catalogos/categorias/', views.CategoriasListView.as_view(), name='catalogo-categorias'),
]
