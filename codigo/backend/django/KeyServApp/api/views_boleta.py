"""
Registro del folio de la boleta de honorarios (bloque 3, docs/adr/0010). **Fase 1: sin integración con el SII.** El proveedor emite
su boleta en sii.cl y aquí solo declara el folio; KeyServ no emite boletas ni verifica el folio.
"""
import logging
import re
from datetime import date

from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import BoletaHonorarios, Pago
from .views import _contratacion_de_participante_api

logger = logging.getLogger(__name__)

_FOLIO = re.compile(r'^\d{1,12}$')


def _datos_proveedor(boleta):
    return {
        'folio': boleta.folio, 'fecha_emision': boleta.fecha_emision,
        'es_primera_boleta': boleta.es_primera_boleta, 'registrada_en': boleta.registrada_en,
    }


def _trabajo_pagado(contratacion):
    pago = getattr(contratacion, 'pago', None)
    return bool(pago and pago.estado == Pago.PAGADO)


class ContratacionBoletaView(APIView):
    """
    `GET`/`PUT`/`DELETE /api/contrataciones/<id>/boleta/`. Solo el proveedor la registra, y solo en un trabajo ya pagado.
    El cliente puede leer el folio y la fecha (para revisarlos en el SII), nunca la respuesta sobre "primera boleta".
    """

    def get(self, request, contratacion_id):
        contratacion = _contratacion_de_participante_api(request, contratacion_id)
        boleta = getattr(contratacion, 'boleta', None)
        if request.user != contratacion.proveedor:
            return Response({'boleta': {'folio': boleta.folio, 'fecha_emision': boleta.fecha_emision} if boleta else None, 'puede_registrar': False})
        tiene_primera = BoletaHonorarios.objects.filter(proveedor=request.user, es_primera_boleta=True).exclude(contratacion=contratacion).exists()
        return Response({
            'boleta': _datos_proveedor(boleta) if boleta else None,
            'puede_registrar': _trabajo_pagado(contratacion),
            'ya_tiene_primera_boleta': tiene_primera,
        })

    def put(self, request, contratacion_id):
        contratacion = _contratacion_de_participante_api(request, contratacion_id)
        if request.user != contratacion.proveedor:
            return Response({'detail': 'Solo el proveedor puede registrar la boleta de este trabajo.'}, status=status.HTTP_403_FORBIDDEN)
        if not _trabajo_pagado(contratacion):
            return Response({'detail': 'Puedes registrar la boleta cuando el trabajo ya esté pagado.', 'code': 'trabajo_no_pagado'}, status=status.HTTP_409_CONFLICT)

        errores = {}
        folio = str(request.data.get('folio') or '').strip()
        if not _FOLIO.match(folio):
            errores['folio'] = ['El folio es el número de tu boleta: solo dígitos (hasta 12).']
        fecha = None
        bruto_fecha = request.data.get('fecha_emision')
        if bruto_fecha:
            try:
                fecha = date.fromisoformat(str(bruto_fecha))
            except ValueError:
                errores['fecha_emision'] = ['Escribe la fecha como AAAA-MM-DD.']
            else:
                if fecha > timezone.localdate():
                    errores['fecha_emision'] = ['La fecha de emisión no puede ser futura.']
                elif fecha < timezone.localtime(contratacion.fecha_creacion).date():
                    errores['fecha_emision'] = ['La boleta no puede ser anterior a la solicitud del trabajo.']
        respuesta = request.data.get('es_primera_boleta')
        if respuesta not in ('SI', 'NO'):
            errores['es_primera_boleta'] = ['Responde si es tu primera boleta (Sí o No).']
        if errores:
            return Response(errores, status=status.HTTP_400_BAD_REQUEST)

        existente = getattr(contratacion, 'boleta', None)
        otras = BoletaHonorarios.objects.filter(proveedor=request.user).exclude(contratacion=contratacion)
        if otras.filter(folio=folio).exists():
            return Response({'folio': ['Ya registraste ese folio en otro trabajo.']}, status=status.HTTP_400_BAD_REQUEST)
        es_primera = respuesta == 'SI'
        if es_primera and otras.filter(es_primera_boleta=True).exists():
            return Response({'es_primera_boleta': ['Ya marcaste otra boleta como tu primera.']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if existente:
                existente.folio, existente.fecha_emision, existente.es_primera_boleta = folio, fecha, es_primera
                existente.save()
                boleta, codigo = existente, status.HTTP_200_OK
            else:
                boleta = BoletaHonorarios.objects.create(
                    contratacion=contratacion, proveedor=request.user, folio=folio, fecha_emision=fecha, es_primera_boleta=es_primera,
                )
                codigo = status.HTTP_201_CREATED
        except IntegrityError:  # dos solicitudes simultáneas con el mismo folio
            return Response({'folio': ['Ya registraste ese folio en otro trabajo.']}, status=status.HTTP_400_BAD_REQUEST)
        logger.info('Boleta registrada: contratacion_id=%s proveedor=%s primera=%s', contratacion_id, request.user.id_usuario, es_primera)
        return Response({'boleta': _datos_proveedor(boleta)}, status=codigo)

    def delete(self, request, contratacion_id):
        contratacion = _contratacion_de_participante_api(request, contratacion_id)
        if request.user != contratacion.proveedor:
            return Response({'detail': 'Solo el proveedor puede quitar la boleta de este trabajo.'}, status=status.HTTP_403_FORBIDDEN)
        boleta = getattr(contratacion, 'boleta', None)
        if boleta:
            boleta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
