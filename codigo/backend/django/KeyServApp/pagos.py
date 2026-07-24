"""
Integración de pagos — RF012 del PDF ("Api de pago asociada").

Combinación elegida con el usuario (dos medios, checkout separado — no un
agregador único): **Webpay Plus** (tarjetas, vía `transbank-sdk`) y
**Khipu** (transferencia bancaria directa, vía su API REST) — ver
`docs/PAGOS.md` para el detalle del flujo completo y por qué se eligió
esta combinación.

Estado de cada uno:
- **Webpay**: se puede probar de punta a punta ahora mismo — usa las
  credenciales públicas de integración que trae el propio SDK
  (`IntegrationCommerceCodes`/`IntegrationApiKeys`), no hace falta ninguna
  cuenta ni credencial real. Solo en `TRANSBANK_ENVIRONMENT=produccion`
  hacen falta `TRANSBANK_COMMERCE_CODE`/`TRANSBANK_API_KEY` reales.
- **Khipu**: el código está completo, pero Khipu no publica un sandbox
  público (a diferencia de Transbank) — hace falta que el dueño del
  proyecto cree su propia cuenta en khipu.com y genere un API key desde
  su panel (Configuración > API) para poder probarlo de verdad. Sin
  `KHIPU_API_KEY` configurado, `KhipuService` falla con un error claro
  (`RuntimeError`) en vez de silencioso.
"""
import logging

import environ
import requests

env = environ.Env()
logger = logging.getLogger(__name__)

KHIPU_API_BASE = 'https://khipu.com/api/3.0'


class TransbankService:
    """
    Envoltorio sobre `transbank-sdk` (Webpay Plus). Se instancia una vez
    por transacción de pago — el registro de negocio vive en el modelo
    `Pago` (`models.py`), esta clase solo habla con la API externa.
    """

    def __init__(self):
        from transbank.webpay.webpay_plus.transaction import Transaction
        from transbank.common.integration_api_keys import IntegrationApiKeys
        from transbank.common.integration_commerce_codes import IntegrationCommerceCodes

        ambiente = env('TRANSBANK_ENVIRONMENT', default='integracion')
        if ambiente == 'produccion':
            commerce_code = env('TRANSBANK_COMMERCE_CODE')
            api_key = env('TRANSBANK_API_KEY')
            self.transaction = Transaction.build_for_production(commerce_code, api_key)
        else:
            # Credenciales públicas de integración — se toman del SDK
            # instalado (no se copian a mano acá, son strings largos y una
            # transcripción mal hecha rompería el pago en silencio).
            self.transaction = Transaction.build_for_integration(
                IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY,
            )

    def iniciar_transaccion(self, monto, orden_compra, session_id, url_retorno):
        """
        Crea la transacción en Transbank. Devuelve (token, url) — el
        siguiente paso NO es un redirect simple: hay que mostrarle al
        usuario un formulario que haga POST de `token_ws=<token>` a esa
        `url` (así lo exige el protocolo de Webpay Plus), ver
        `pago_webpay_redirigir.html`.
        """
        respuesta = self.transaction.create(orden_compra, session_id, monto, url_retorno)
        return respuesta['token'], respuesta['url']

    def confirmar_transaccion(self, token):
        """
        Confirma (commit) la transacción tras volver de Webpay. Devuelve
        la respuesta cruda del SDK — `response_code == 0` y
        `status == 'AUTHORIZED'` es la única combinación que cuenta como
        aprobado, cualquier otra cosa se trata como rechazado.
        """
        return self.transaction.commit(token)


class KhipuService:
    """
    Cliente REST liviano sobre la API v3 de Khipu. Sin SDK de terceros a
    propósito: la documentación pública tiene información contradictoria
    sobre el esquema de autenticación exacto (API key en header `x-api-key`
    vs Basic auth con `receiver_id:secret`) — con un cliente propio y
    chico, si el esquema real difiere una vez que haya cuenta real, es un
    cambio de una línea en `_headers()` en vez de tener que rastrear un
    paquete ajeno.
    """

    def __init__(self):
        self.api_key = env('KHIPU_API_KEY', default=None)

    def _headers(self):
        if not self.api_key:
            raise RuntimeError(
                'KHIPU_API_KEY no configurado. Khipu no tiene sandbox público — hace falta '
                'crear una cuenta real en khipu.com y generar un API key (Configuración > API) '
                'para poder usar esto, incluso para probar.'
            )
        return {'x-api-key': self.api_key}

    def crear_pago(self, monto, asunto, transaction_id, url_retorno, url_cancelacion, url_notificacion):
        """Crea el cobro en Khipu. Devuelve el JSON de respuesta (trae `payment_id` y `payment_url`, entre otros)."""
        respuesta = requests.post(
            f'{KHIPU_API_BASE}/payments',
            headers=self._headers(),
            data={
                'subject': asunto,
                'currency': 'CLP',
                'amount': monto,
                'transaction_id': transaction_id,
                'return_url': url_retorno,
                'cancel_url': url_cancelacion,
                'notify_url': url_notificacion,
            },
            timeout=15,
        )
        respuesta.raise_for_status()
        return respuesta.json()

    def consultar_pago(self, payment_id):
        """
        Reconsulta el estado real de un pago contra Khipu — el cuerpo del
        webhook de notificación NUNCA se usa solo para decidir que un pago
        está aprobado (es la recomendación explícita de Khipu), siempre se
        confirma acá antes de marcar nada como pagado.
        """
        respuesta = requests.get(f'{KHIPU_API_BASE}/payments/{payment_id}', headers=self._headers(), timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()
