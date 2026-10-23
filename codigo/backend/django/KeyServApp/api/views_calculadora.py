"""
API de la calculadora de valorización (docs/adr/0009). Las rutas de cálculo y exportación son **públicas**: no piden cuenta y
no guardan nada de quien las usa (solo un contador anónimo, ver `UsoCalculadora`). Las plantillas sí son por cuenta.
"""
import hashlib
import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import calculadora, calculadora_exportar
from ..models import PlantillaValorizacion, UsoCalculadora
from ..views import _obtener_ip_cliente

logger = logging.getLogger(__name__)

VENTANA_SEGUNDOS = 600
LIMITE_CALCULOS = 300       # por IP en 10 minutos: el cálculo se repite mientras la persona escribe
LIMITE_EXPORTACIONES = 30
MAX_PLANTILLAS = 30
MAX_BYTES_PLANTILLA = 20000
_FORMATO_VISITANTE = re.compile(r'^[A-Za-z0-9-]{8,64}$')


def _limitado(request, tipo, limite):
    """Ventana fija por IP; devuelve una `Response` 429 si se agotó, o `None`."""
    clave = f'calculadora:{tipo}:{_obtener_ip_cliente(request)}'
    cache.add(clave, 0, VENTANA_SEGUNDOS)
    if cache.get(clave, 0) >= limite:
        return Response({'detail': 'Has usado la calculadora muchas veces seguidas. Prueba de nuevo en unos minutos.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    try:
        cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, VENTANA_SEGUNDOS)
    return None


def _visitante_anonimo(request, periodo):
    """Identificador del visitante para el contador: el que genera el navegador, mezclado con una sal secreta y el mes."""
    bruto = request.data.get('visitante') if isinstance(request.data, dict) else None
    if not isinstance(bruto, str) or not _FORMATO_VISITANTE.match(bruto):
        bruto = 'sin-identificador'
    return hashlib.sha256(f'{settings.SECRET_KEY}|{periodo}|{bruto}'.encode('utf-8')).hexdigest()


def _registrar_uso(request, resultado, valorizacion):
    """
    Suma al contador anónimo del mes. `valorizacion=False` solo registra la visita (cálculo en vivo); `True` cuenta una
    valorización terminada (exportada o guardada como plantilla). Nunca guarda la IP, la cuenta ni los datos ingresados.
    """
    periodo = timezone.now().strftime('%Y-%m')
    visitante = _visitante_anonimo(request, periodo)
    try:
        uso, _ = UsoCalculadora.objects.get_or_create(periodo=periodo, visitante=visitante)
    except IntegrityError:  # dos solicitudes simultáneas del mismo visitante
        uso = UsoCalculadora.objects.get(periodo=periodo, visitante=visitante)
    if valorizacion:
        uso.valorizaciones += 1
        uso.con_boleta += int(resultado['documento'] == 'BOLETA_HONORARIOS')
        uso.con_reutilizado += int(resultado['tiene_reutilizado'])
        uso.save()


def _error(excepcion):
    return Response({'detail': str(excepcion)}, status=status.HTTP_400_BAD_REQUEST)


class CalculadoraConfigView(APIView):
    """`GET /api/calculadora/config/` — valores por defecto (retención, imprevistos, ganancia) y tramos de comisión."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(calculadora.configuracion_publica())


class CalculadoraCalcularView(APIView):
    """`POST /api/calculadora/calcular/` — desglose de una valorización. Público; registra solo la visita anónima."""
    permission_classes = [AllowAny]

    def post(self, request):
        bloqueo = _limitado(request, 'calcular', LIMITE_CALCULOS)
        if bloqueo:
            return bloqueo
        try:
            resultado = calculadora.calcular(request.data)
        except calculadora.DatosInvalidos as e:
            return _error(e)
        _registrar_uso(request, resultado, valorizacion=False)
        return Response(resultado)


class _CalculadoraExportarView(APIView):
    permission_classes = [AllowAny]
    tipo_contenido = ''
    extension = ''

    def generar(self, datos):
        raise NotImplementedError

    def post(self, request):
        bloqueo = _limitado(request, 'exportar', LIMITE_EXPORTACIONES)
        if bloqueo:
            return bloqueo
        try:
            resultado = calculadora.calcular(request.data)  # valida y, de paso, cuenta la valorización
            contenido = self.generar(request.data)
        except calculadora.DatosInvalidos as e:
            return _error(e)
        _registrar_uso(request, resultado, valorizacion=True)
        respuesta = HttpResponse(contenido, content_type=self.tipo_contenido)
        respuesta['Content-Disposition'] = f'attachment; filename="valorizacion-keyserv.{self.extension}"'
        return respuesta


class CalculadoraExportarPdfView(_CalculadoraExportarView):
    """`POST /api/calculadora/exportar/pdf/` — el resumen en PDF."""
    tipo_contenido = 'application/pdf'
    extension = 'pdf'

    def generar(self, datos):
        return calculadora_exportar.generar_pdf(datos)


class CalculadoraExportarXlsxView(_CalculadoraExportarView):
    """`POST /api/calculadora/exportar/xlsx/` — planilla con fórmulas visibles y editables."""
    tipo_contenido = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    extension = 'xlsx'

    def generar(self, datos):
        return calculadora_exportar.generar_xlsx(datos)


def _plantilla_a_dict(p):
    return {
        'id_plantilla': p.id_plantilla, 'nombre': p.nombre, 'tipo_trabajo': p.tipo_trabajo,
        'datos': p.datos, 'actualizada_en': p.actualizada_en,
    }


class PlantillasValorizacionView(APIView):
    """
    `GET`/`POST /api/calculadora/plantillas/` — plantillas de la cuenta. `POST {nombre, tipo_trabajo, datos}` crea o, si ya
    hay una con ese nombre, la reemplaza (misma cuenta). Máximo `MAX_PLANTILLAS` por cuenta.
    """

    def get(self, request):
        plantillas = PlantillaValorizacion.objects.filter(usuario=request.user)
        return Response([_plantilla_a_dict(p) for p in plantillas])

    def post(self, request):
        nombre = str(request.data.get('nombre') or '').strip()[:60]
        if not nombre:
            return Response({'detail': 'Ponle un nombre a la plantilla.'}, status=status.HTTP_400_BAD_REQUEST)
        datos = request.data.get('datos')
        try:
            resultado = calculadora.calcular(datos)
        except calculadora.DatosInvalidos as e:
            return _error(e)
        if len(str(datos)) > MAX_BYTES_PLANTILLA:
            return Response({'detail': 'La plantilla es demasiado grande.'}, status=status.HTTP_400_BAD_REQUEST)
        existente = PlantillaValorizacion.objects.filter(usuario=request.user, nombre=nombre).first()
        if existente is None and PlantillaValorizacion.objects.filter(usuario=request.user).count() >= MAX_PLANTILLAS:
            return Response({'detail': f'Puedes guardar hasta {MAX_PLANTILLAS} plantillas. Borra alguna para crear otra.'}, status=status.HTTP_400_BAD_REQUEST)
        tipo_trabajo = str(request.data.get('tipo_trabajo') or '').strip()[:60]
        if existente:
            existente.tipo_trabajo, existente.datos = tipo_trabajo, datos
            existente.save()
            plantilla, codigo = existente, status.HTTP_200_OK
        else:
            plantilla = PlantillaValorizacion.objects.create(usuario=request.user, nombre=nombre, tipo_trabajo=tipo_trabajo, datos=datos)
            codigo = status.HTTP_201_CREATED
        _registrar_uso(request, resultado, valorizacion=True)
        return Response(_plantilla_a_dict(plantilla), status=codigo)


class PlantillaValorizacionDetalleView(APIView):
    """`DELETE /api/calculadora/plantillas/<id>/` — borra una plantilla propia (404 si es de otra cuenta)."""

    def delete(self, request, plantilla_id):
        plantilla = get_object_or_404(PlantillaValorizacion, pk=plantilla_id, usuario=request.user)
        plantilla.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlantillaValorizacionItemsView(APIView):
    """`GET /api/calculadora/plantillas/<id>/items/` — la plantilla como filas de la hoja de presupuesto, para cargarla al confirmar."""

    def get(self, request, plantilla_id):
        plantilla = get_object_or_404(PlantillaValorizacion, pk=plantilla_id, usuario=request.user)
        try:
            resultado = calculadora.calcular(plantilla.datos)
        except calculadora.DatosInvalidos as e:  # cambió una regla desde que se guardó
            return _error(e)
        return Response({'items': resultado['items'], 'total': resultado['precio_boleta']})
