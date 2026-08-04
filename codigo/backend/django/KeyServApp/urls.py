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
    path('recuperar/confirmar/<str:token>/', views.recuperar_confirmar_view, name='recuperar_confirmar'),
    path('historial-pagos/', views.historial_pagos_view, name='historial_pagos'),

    # Autenticación
    path('registro/', views.register_view, name='registro'),
    path('sesion/', views.sesion_view, name='sesion'),
    path('logout/', views.logout_view, name='logout'),
    path('ajax/load-comunas/', views.load_comunas, name='ajax_load_comunas'),
    path('ajax/mensajes-no-leidos/', views.mensajes_no_leidos_ajax, name='ajax_mensajes_no_leidos'),

    # Perfil
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/crear/', views.crear_perfil_view, name='crear_perfil'),
    path('perfil/documentos/<int:documento_id>/eliminar/', views.documento_perfil_eliminar_view, name='documento_perfil_eliminar'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    path('perfil/alternar-proveedor/', views.alternar_proveedor_view, name='alternar_proveedor'),

    # Publicaciones / servicios
    path('servicios/', views.catalogo_view, name='catalogo'),
    path('servicios/crear/', views.publicacion_crear_view, name='publicacion_crear'),
    path('documentos/<int:documento_id>/descargar/', views.documento_descargar_view, name='documento_descargar'),
    path('servicios/<int:pk>/', views.publicacion_detalle_view, name='publicacion_detalle'),
    path('servicios/<int:publicacion_id>/contratar/', views.contratacion_crear_view, name='contratacion_crear'),

    # Contrataciones / reservas / valoraciones
    path('reservas/', views.reservas_view, name='reservas'),
    path('contrataciones/<int:contratacion_id>/', views.contratacion_detalle_view, name='contratacion_detalle'),
    path('contrataciones/<int:contratacion_id>/confirmar/', views.contratacion_confirmar_view, name='contratacion_confirmar'),
    path('contrataciones/<int:contratacion_id>/completar/', views.contratacion_completar_view, name='contratacion_completar'),
    path('contrataciones/<int:contratacion_id>/valorar/', views.valoracion_crear_view, name='valoracion_crear'),

    # Biometría
    path('huella/', views.huella_view, name='huella'),
    path('huella/verificar/', views.verificacion_huella_view, name='verificacion_huella'),
    path('rostro/', views.rostro_view, name='rostro'),
    path('rostro/registrar/', views.registro_rostro_view, name='registro_rostro'),
    path('rostro/verificar/', views.verificacion_facial_view, name='verificacion_facial'),
    path('ajax/validar-captura-rostro/', views.validar_captura_rostro_ajax, name='ajax_validar_captura_rostro'),

    # Mensajería
    path('chat/', views.chat_view, name='chat'),
    path('chat/<int:conversacion_id>/', views.conversacion_detalle_view, name='conversacion_detalle'),
    path('chat/<int:conversacion_id>/exportar/', views.conversacion_exportar_view, name='conversacion_exportar'),

    # Pagos (RF012 — Webpay Plus + Khipu, ver pagos.py)
    path('contrataciones/<int:contratacion_id>/pagar/webpay/', views.pago_webpay_iniciar_view, name='pago_webpay_iniciar'),
    path('pagos/webpay/retorno/', views.pago_webpay_retorno_view, name='pago_webpay_retorno'),
    path('contrataciones/<int:contratacion_id>/pagar/khipu/', views.pago_khipu_iniciar_view, name='pago_khipu_iniciar'),
    path('pagos/khipu/notificacion/', views.pago_khipu_notificacion_view, name='pago_khipu_notificacion'),
    path('contrataciones/<int:contratacion_id>/pagar/khipu/retorno/', views.pago_khipu_retorno_view, name='pago_khipu_retorno'),
]
