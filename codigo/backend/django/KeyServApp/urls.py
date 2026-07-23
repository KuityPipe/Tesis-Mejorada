"""
Rutas de KeyServ.

Refactor Fase 3: antes solo había 2 rutas activas (`registro/`,
`ajax/load-comunas/`); el resto de las 18 páginas heredadas de la tesis no
tenían URL asignada (RF007 del PDF: "sin errores de enlace entre botones" —
no se puede cumplir si la mayoría de los botones no llevan a ningún lado).
Los nombres de ruta acá abajo son los que usan los `{% url %}` de los
templates tras el arreglo de enlaces de esta misma fase.
"""
from django.urls import path

from . import views

app_name = 'KeyServApp'

urlpatterns = [
    # Páginas simples
    path('', views.paginicio_view, name='paginicio'),
    path('acerca-de-nosotros/', views.acerca_de_nosotros_view, name='acerca_de_nosotros'),
    path('contacto/', views.contacto_view, name='contacto'),
    path('inicio/', views.sesion_iniciada_view, name='sesion_iniciada'),
    path('preferencias-cuenta/', views.preferencias_cuenta_view, name='preferencias_cuenta'),
    path('recuperar/', views.recuperar_view, name='recuperar'),
    path('tarjeta-credito/', views.tarjeta_credito_view, name='tarjeta_credito'),

    # Autenticación
    path('registro/', views.register_view, name='registro'),
    path('sesion/', views.sesion_view, name='sesion'),
    path('logout/', views.logout_view, name='logout'),
    path('ajax/load-comunas/', views.load_comunas, name='ajax_load_comunas'),

    # Perfil
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/crear/', views.crear_perfil_view, name='crear_perfil'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),

    # Publicaciones / servicios
    path('servicios/crear/', views.publicacion_crear_view, name='publicacion_crear'),
    path('servicios/<int:pk>/', views.publicacion_detalle_view, name='publicacion_detalle'),
    path('servicios/<int:publicacion_id>/contratar/', views.contratacion_crear_view, name='contratacion_crear'),

    # Contrataciones / reservas / valoraciones
    path('reservas/', views.reservas_view, name='reservas'),
    path('contrataciones/<int:contratacion_id>/confirmar/', views.contratacion_confirmar_view, name='contratacion_confirmar'),
    path('contrataciones/<int:contratacion_id>/completar/', views.contratacion_completar_view, name='contratacion_completar'),
    path('contrataciones/<int:contratacion_id>/valorar/', views.valoracion_crear_view, name='valoracion_crear'),

    # Biometría
    path('huella/', views.huella_view, name='huella'),
    path('huella/verificar/', views.verificacion_huella_view, name='verificacion_huella'),

    # Mensajería
    path('chat/', views.chat_view, name='chat'),
    path('chat/<int:conversacion_id>/', views.conversacion_detalle_view, name='conversacion_detalle'),

    # Pagos
    path('pago/', views.pago_view, name='pago'),
    path('pago/exitoso/', views.pago_exitoso_view, name='pago_exitoso'),
]
