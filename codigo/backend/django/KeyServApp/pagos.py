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
import hashlib
import hmac
import logging

import environ
import requests

env = environ.Env()
logger = logging.getLogger(__name__)

KHIPU_API_BASE = 'https://khipu.com/api/3.0'
FLOW_API_BASE = {'sandbox': 'https://sandbox.flow.cl/api', 'produccion': 'https://www.flow.cl/api'}
MERCADOPAGO_API_BASE = 'https://api.mercadopago.com'


def metodos_disponibles():
    """
    Qué medios de pago están configurados en este entorno (para que la app solo ofrezca los que funcionan). Webpay
    siempre: sin credenciales usa las públicas de integración de Transbank.
    """
    return {
        'webpay': True,
        'khipu': bool(env('KHIPU_API_KEY', default=None)),
        'flow': bool(env('FLOW_API_KEY', default=None) and env('FLOW_SECRET_KEY', default=None)),
        'mercadopago': bool(env('MERCADOPAGO_ACCESS_TOKEN', default=None)),
    }


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


class FlowService:
    """
    Cliente REST liviano de Flow (flow.cl), que agrupa Webpay, Servipag, transferencia y otros en una sola pasarela.
    Tiene sandbox público (`sandbox.flow.cl`, con cuenta de pruebas gratuita): `FLOW_AMBIENTE=sandbox` (por defecto)
    o `produccion`, con `FLOW_API_KEY` y `FLOW_SECRET_KEY` del panel de Flow.

    Cada llamada se firma con HMAC-SHA256 sobre los parámetros ordenados alfabéticamente y concatenados como
    `nombrevalor`, con la clave secreta. **Escrito según la documentación pública de Flow tal como se conoce, pero
    sin probarse contra el sandbox real** (hacen falta credenciales de una cuenta del dueño): si la primera
    prueba real falla por firma o por un campo, revisar `_firmar` y los parámetros de `crear_pago` primero.
    """

    def __init__(self):
        self.api_key = env('FLOW_API_KEY', default=None)
        self.secret_key = env('FLOW_SECRET_KEY', default=None)
        self.base = FLOW_API_BASE.get(env('FLOW_AMBIENTE', default='sandbox'), FLOW_API_BASE['sandbox'])

    def _verificar_configuracion(self):
        if not (self.api_key and self.secret_key):
            raise RuntimeError(
                'FLOW_API_KEY / FLOW_SECRET_KEY no configurados. Crea una cuenta de pruebas en sandbox.flow.cl y copia '
                'las claves de su panel (Mi cuenta > Integraciones) para poder pagar con Flow.'
            )

    def _firmar(self, parametros):
        cadena = ''.join(f'{clave}{parametros[clave]}' for clave in sorted(parametros))
        return hmac.new(self.secret_key.encode('utf-8'), cadena.encode('utf-8'), hashlib.sha256).hexdigest()

    def crear_pago(self, monto, asunto, orden_comercio, email, url_retorno, url_confirmacion):
        """Crea el cobro. Devuelve `{url, token, flowOrder}`; el pago se hace en `url?token=<token>`."""
        self._verificar_configuracion()
        parametros = {
            'apiKey': self.api_key, 'commerceOrder': orden_comercio, 'subject': asunto, 'currency': 'CLP',
            'amount': monto, 'email': email, 'urlConfirmation': url_confirmacion, 'urlReturn': url_retorno,
        }
        parametros['s'] = self._firmar(parametros)
        respuesta = requests.post(f'{self.base}/payment/create', data=parametros, timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()

    def url_de_pago(self, respuesta):
        return f'{respuesta["url"]}?token={respuesta["token"]}'

    def consultar_pago(self, token):
        """Estado real del pago. `status`: 1 pendiente, 2 pagada, 3 rechazada, 4 anulada. Es lo único que se cree: el POST de confirmación solo trae el token."""
        self._verificar_configuracion()
        parametros = {'apiKey': self.api_key, 'token': token}
        parametros['s'] = self._firmar(parametros)
        respuesta = requests.get(f'{self.base}/payment/getStatus', params=parametros, timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()


class MercadoPagoService:
    """
    Cliente REST liviano de Mercado Pago Checkout Pro (preferencias + redirección a su página de pago). Funciona con
    el `MERCADOPAGO_ACCESS_TOKEN` de una cuenta de **pruebas** (`TEST-...`, del panel de desarrolladores de Mercado Pago
    Chile) o de producción; con credenciales de prueba se paga con las tarjetas y usuarios de prueba de Mercado Pago.

    Como con Flow y Khipu, **no se probó contra el entorno real** (faltan las credenciales del dueño): si algo falla,
    mirar primero el cuerpo de la respuesta de `crear_preferencia`.
    """

    def __init__(self):
        self.access_token = env('MERCADOPAGO_ACCESS_TOKEN', default=None)

    def _headers(self):
        if not self.access_token:
            raise RuntimeError(
                'MERCADOPAGO_ACCESS_TOKEN no configurado. Crea una aplicación en el panel de desarrolladores de Mercado '
                'Pago Chile y copia su Access Token de prueba para poder pagar con Mercado Pago.'
            )
        return {'Authorization': f'Bearer {self.access_token}'}

    def crear_preferencia(self, monto, titulo, referencia, email, url_retorno, url_notificacion):
        """Crea la preferencia de pago. Devuelve el JSON (trae `id` e `init_point`, la URL a la que redirigir)."""
        cuerpo = {
            'items': [{'title': titulo[:250], 'quantity': 1, 'unit_price': monto, 'currency_id': 'CLP'}],
            'payer': {'email': email},
            'external_reference': referencia,
            'back_urls': {'success': url_retorno, 'failure': url_retorno, 'pending': url_retorno},
            'notification_url': url_notificacion,
        }
        if url_retorno.startswith('https://'):
            # Mercado Pago rechaza `auto_return` con back_urls que no son https (p. ej. localhost en desarrollo).
            cuerpo['auto_return'] = 'approved'
        respuesta = requests.post(f'{MERCADOPAGO_API_BASE}/checkout/preferences', headers=self._headers(), json=cuerpo, timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()

    def consultar_pago(self, payment_id):
        respuesta = requests.get(f'{MERCADOPAGO_API_BASE}/v1/payments/{payment_id}', headers=self._headers(), timeout=15)
        respuesta.raise_for_status()
        return respuesta.json()

    def buscar_pago(self, referencia):
        """El pago más relevante de una `external_reference` (uno aprobado si hay, si no el más reciente), o `None`."""
        respuesta = requests.get(
            f'{MERCADOPAGO_API_BASE}/v1/payments/search', headers=self._headers(), timeout=15,
            params={'external_reference': referencia, 'sort': 'date_created', 'criteria': 'desc'},
        )
        respuesta.raise_for_status()
        resultados = respuesta.json().get('results') or []
        aprobados = [r for r in resultados if r.get('status') == 'approved']
        return (aprobados or resultados or [None])[0]
