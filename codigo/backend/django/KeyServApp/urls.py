from django.urls import path
from . import views

app_name = 'KeyServApp'

urlpatterns = [
    path('registro/', views.register_view, name='registro'),
    #path('registroinicio/', views.RegistroInicioView.as_view(), name='registroinicio'),
    path('ajax/load-comunas/', views.load_comunas, name='ajax_load_comunas'),
    #path('comunas_por_region/<int:region_id>/', views.comunas_por_region, name='comunas_por_region'),
    #path('sesion/', views.sesion_view, name='sesion'), 

    # otras rutas van aquí...
]