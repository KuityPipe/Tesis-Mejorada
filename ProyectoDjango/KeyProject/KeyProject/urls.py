from django.contrib import admin
from django.urls import path, include  # Asegúrate de importar include aquí
from KeyApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    #//////////////////////Vistas de las paginas/////////////////////
    path('', views.mostrarPagInicio), #paginicio.html
    path('registroinicio', views.mostrarRegistroInicio), #registroinicio.html
    path('sesion', views.mostrarIniciarSesion), #seson.html
    path('sesioninicio', views.mostrarInicioUsuario),#sesioninicio.html
    path('Acercadeenosotros', views.mostrarAcercaNosotros),#acercadenosotros.html
    path('chat', views.mostrarChat),#chat.html
    path('contacto', views.mostrarContacto),#contacto.html
    path('crearperfil', views.mostrarCrearPerfil),#crearperfil.html
    path('editarperfil', views.mostrarEditarPerfil),# editarperfil.html
    path('perfil', views.mostrarPerfil),# perfil.html
    path('detalleserv', views.mostrarDetalleServicio),# detalleserv.html
    path('huella', views.mostrarHuella),# huella.html
    path('pago', views.mostrarPago),# pago.html
    path('pagoexitoso', views.mostrarPagoExitoso),# pagoexitoso.html
    path('preferenciascuenta', views.mostrarPreferenciaCuenta),#preferenciascuenta.html
    path('recuperar', views.mostrarRecuperacionCuenta),# recuperar.html
    path('reservas', views.mostrarReservaServicio),# reservas.html
    #/////////////////////Back-End URL/////////////////////////////////////
    path('insertarRegistro', views.insertarRegistro)
]