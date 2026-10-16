"""
Qué se guarda de la respuesta cruda del medio de pago (`Pago.respuesta_bruta`).

Webpay y Khipu devuelven datos de terceros que KeyServ no necesita: últimos dígitos de la tarjeta (`card_detail`), nombre y
correo de quien paga, banco, enlaces de pago. Se guarda solo una lista de campos permitidos (estado, montos, fechas, códigos
de autorización), suficiente para soporte y auditoría y alineada con minimización de datos de la Ley 21.719.

Módulo sin dependencias de los SDK de pago a propósito: lo importan las vistas y también una migración de datos.
"""

CAMPOS_PERMITIDOS = frozenset({
    # Webpay Plus
    'status', 'response_code', 'authorization_code', 'payment_type_code', 'installments_number', 'amount',
    'transaction_date', 'accounting_date', 'buy_order', 'vci',
    # Khipu
    'payment_id', 'status_detail', 'currency', 'transaction_id', 'conclusion_date', 'receipt_date', 'subject', 'type',
    # Flow
    'flowOrder', 'commerceOrder', 'requestDate',
    # Mercado Pago (nunca el pagador ni la tarjeta)
    'id', 'external_reference', 'transaction_amount', 'currency_id', 'payment_type_id', 'date_approved',
})


def respuesta_minima(respuesta):
    """Devuelve solo los campos permitidos y de valor simple (texto, número, booleano o nulo). No modifica el original."""
    if not isinstance(respuesta, dict):
        return None
    return {
        clave: valor for clave, valor in respuesta.items()
        if clave in CAMPOS_PERMITIDOS and (valor is None or isinstance(valor, (str, int, float, bool)))
    }
