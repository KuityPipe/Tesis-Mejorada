from django.shortcuts import render
import hashlib
from datetime import datetime
from KeyApp.models import Region, Comuna, Usuario, TipoCuenta, Transaccion

#/////////////////////////////////////$/////////////////////////////////////////
#En esta parte de las Views se mostraran solo para mostrar en HTML y sus estilos
#INICIO - HOME
def mostrarPagInicio(request):
    return render(request, 'KeyApp/paginicio.html')

#REGISTRO USUARIO
def mostrarRegistroInicio(request):
    regiones = Region.objects.all().values()
    return render(request, 'KeyApp/registroinicio.html', { 'reg' : regiones})

#INICIAR SESION
def mostrarIniciarSesion(request):
    return render(request, 'KeyApp/sesion.html')

#INICIO DE SESION USUARIO
def mostrarInicioUsuario(request):
    return render(request, 'KeyApp/sesioninicio.html')

#ACERCA DE NOSOTROS
def mostrarAcercaNosotros(request):
    return render(request, 'KeyApp/Acercadeenosotros.html')

#CHAT
def mostrarChat(request):
    return render(request, 'KeyApp/chat.html')

#CONTACTO
def mostrarContacto(request):
    return render(request, 'KeyApp/contacto.html')

#CREACION PERFIL USUARIO
def mostrarCrearPerfil(request):
    return render(request, 'KeyApp/crearperfil.html')

#EDITAR PERFIL USUARIO
def mostrarEditarPerfil(request):
    return render(request, 'KeyApp/editarperfil.html')

#MOSTRAR PERFIL
def mostrarPerfil(request):
    return render(request, 'KeyApp/perfil.html')

#DETALLE SERVICIO
def mostrarDetalleServicio(request):
    return render(request, 'KeyApp/detalleserv.html')

#HUELLA
def mostrarHuella(request):
    return render(request, 'KeyApp/huella.html')

#PAGO
def mostrarPago(request):
    return render(request, 'KeyApp/pago.html')

#PAGO EXITOSO
def mostrarPagoExitoso(request):
    return render(request, 'KeyApp/pagoexitoso.html')

#PREFERENCIAS CUENTA
def mostrarPreferenciaCuenta(request):
    return render(request, 'KeyApp/preferenciascuenta.html')

#RECUPERAR CUENTA
def mostrarRecuperacionCuenta(request):
    return render(request, 'KeyApp/recuperar.html')

#RESERVA SERVICIO
def mostrarReservaServicio(request):
    return render(request, 'KeyApp/reservas.html')

#///////////////////////$///////////////////////////
#//////////////Funciones Back-End///////////////////
def insertarRegistro(request):
    if request.method == 'POST':
    # Recoger datos del formulario
        rut = request.POST['rut']
        nombre = request.POST['nombre1']
        nombre2 = request.POST['nombre2']
        apellido = request.POST['apellido1']
        apellido2 = request.POST['apellido2']
        edad = request.POST['edad']
        telefono = request.POST['telefono']
        email = request.POST['email']
        region = request.POST['region']
        comuna = request.POST['comuna']
        direccion = request.POST['direccion']
        tipo_cuenta = request.POST['tipo_cuenta']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']

        # Revisar que las contraseñas coincidan
        if password == password_confirm:
            hash_object = hashlib.sha256(password.encode())
            password = hash_object.hexdigest()
        else:
            datosContra = {'errorContra' : 'No coincide la contraseña!'}
            return render(request, 'KeyApp/registroinicio.html', datosContra)

        # Crear timestamp
        timestamp = datetime.now()

        # Crear transacción
        transaccion = Transaccion(tiempo_transaccion=timestamp, fk_valor_cuenta=tipo_cuenta)
        transaccion.save()

        # Crear usuario
        usu = Usuario(rut_usuario=rut, nombre_usuario=nombre, nombre2_usuario=nombre2, apellido_usuario=apellido, apellido2_usuario=apellido2, telefono=telefono, email=email, direccion_usuario=direccion, fk_transaccion=transaccion, fk_tipo_cuenta=tipo_cuenta, fk_comuna=comuna, edad=edad, contrasena=password)
        usu.save()
        datos = { 'correcto' : 'Registro echo correctamente'}
        return render(request, 'form_registrar.html', datos)
        datos = {'errorC' : 'No se puede procesar la solicitud!'}
        return render(request, 'KeyApp/registroinicio.html', datos)





"""from django.http import JsonResponse
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
def comunas_por_region(request, region_id):
    # Aquí va tu lógica para obtener las comunas por region
    return HttpResponse('Esta es la vista de comunas por region.')

#///////////////////////////////////////////////////////////////////////////////////////////////
#Registro Usuarios View
class RegistroInicioView(View):
    def get(self, request):
        return HttpResponse('Hola, esta es la vista de RegistroInicio.')


#///////////////////////////////////////////////////////////////////////////////////////////////
#Inicio Sesion Usuarios
def sesion_view(request):
    # Añade cualquier lógica para tu vista aquí
    return render(request, 'KeyApp/sesion.html')

#///////////////////////////////////////////////////////////////////////////////////////////////
#Registro de Usuarios
def register_view(request):
    if request.method == "POST":
        # Recoger datos del formulario
        rut = request.POST{'rut')
        nombre = request.POST{'nombre1')
        nombre2 = request.POST{'nombre2')
        apellido = request.POST{'apellido1')
        apellido2 = request.POST{'apellido2')
        edad = int(request.POST{'edad'))
        telefono = int(request.POST{'telefono'))
        email = request.POST{'email')
        region = Region.objects{id=int(request.POST{'region')))
        comuna = Comuna.objects{id=int(request.POST{'comuna')))
        direccion = request.POST{'direccion')
        tipo_cuenta = TipoCuenta.objects{id=int(request.POST{'tipo_cuenta')))
        password = request.POST{'password')
        password_confirm = request.POST{'password_confirm')

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
        return render(request, 'KeyApp/registroinicio.html', {
            'regiones': regiones,
            'tipos_cuenta': tipos_cuenta,
        })
        
def load_comunas(request):
    id_region = request.GET{'id_region')
    comunas = Comuna.objects.filter(id_region=id_region).order_by('nombre_comuna')
    comunas_list = list(comunas.values('id', 'nombre_comuna'))
    return JsonResponse(comunas_list, safe=False)

#///////////////////////////////////////////////////////////////////////////////////////////////

"""