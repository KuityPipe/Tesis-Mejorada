from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Region, Comuna, Usuario, TipoCuenta, Transaccion
from datetime import datetime
import hashlib
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import JsonResponse
from django.shortcuts import render

#////////////////////////////////////////////////////////////////////////////
def register_view(request):
    regions = Region.objects.all()
    return render(request, 'registroinicio.html', {'regions': regions})

#///////////////////////////////////////////////////////////////////////////////////////////////
#Registro Comunas View
"""def comunas_por_region(request, region_id):
    # Aquí va tu lógica para obtener las comunas por region
    return HttpResponse('Esta es la vista de comunas por region.')"""

#///////////////////////////////////////////////////////////////////////////////////////////////
#Registro Usuarios View
"""class RegistroInicioView(View):
    def get(self, request):
        return HttpResponse('Hola, esta es la vista de RegistroInicio.')"""


#///////////////////////////////////////////////////////////////////////////////////////////////
#Inicio Sesion Usuarios
def sesion_view(request):
    # Añade cualquier lógica para tu vista aquí
    return render(request, 'KeyServApp/sesion.html')

#///////////////////////////////////////////////////////////////////////////////////////////////
#Registro de Usuarios
def register_view(request):
    if request.method == "POST":
        # Recoger datos del formulario
        rut = request.POST.get('rut')
        nombre = request.POST.get('nombre1')
        nombre2 = request.POST.get('nombre2')
        apellido = request.POST.get('apellido1')
        apellido2 = request.POST.get('apellido2')
        edad = int(request.POST.get('edad'))
        telefono = int(request.POST.get('telefono'))
        email = request.POST.get('email')
        region = Region.objects.get(id=int(request.POST.get('region')))
        comuna = Comuna.objects.get(id=int(request.POST.get('comuna')))
        direccion = request.POST.get('direccion')
        tipo_cuenta = TipoCuenta.objects.get(id=int(request.POST.get('tipo_cuenta')))
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Revisar que las contraseñas coincidan
        if password == password_confirm:
            hash_object = hashlib.sha256(password.encode())
            password = hash_object.hexdigest()
        else:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('registro')

        # Crear timestamp
        timestamp = datetime.now()

        # Crear transacción
        transaccion = Transaccion.objects.create(tiempo_transaccion=timestamp, fk_valor_cuenta=tipo_cuenta)

        # Crear usuario
        Usuario.objects.create(rut_usuario=rut, nombre_usuario=nombre, nombre2_usuario=nombre2, apellido_usuario=apellido, apellido2_usuario=apellido2, telefono=telefono, email=email, direccion_usuario=direccion, fk_transaccion=transaccion, fk_tipo_cuenta=tipo_cuenta, fk_comuna=comuna, edad=edad, contrasena=password)

        messages.success(request, 'Usuario creado exitosamente.')
        return redirect('sesion')

    else:  # Si el método es GET, mostramos el formulario
        regiones = Region.objects.all()
        tipos_cuenta = TipoCuenta.objects.all()
        return render(request, 'KeyServApp/registroinicio.html', {
            'regiones': regiones,
            'tipos_cuenta': tipos_cuenta,
        })
        
def load_comunas(request):
    region_id = request.GET.get('region_id')
    comunas = Comuna.objects.filter(region_id=region_id).order_by('nombre_comuna')
    comunas_list = list(comunas.values('id', 'nombre_comuna'))
    return JsonResponse(comunas_list, safe=False)

#///////////////////////////////////////////////////////////////////////////////////////////////

