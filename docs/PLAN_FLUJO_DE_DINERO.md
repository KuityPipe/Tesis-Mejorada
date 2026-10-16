# Plan del flujo de dinero — comisión, pago al proveedor, reembolsos y documentos tributarios

> **Solo plan. No hay código de nada de esto y no se implementa hasta que el dueño decida.** Escrito el 2026-10-15 con una
> búsqueda web ese mismo día; las fuentes son artículos, documentación y proveedores de servicio (varias secundarias), así que
> **todo lo comercial, legal y tributario de este documento hay que confirmarlo con Transbank/la pasarela y con un contador o
> abogado** antes de actuar. Lo que no pude confirmar lo marco como tal.

## 1. Qué existe y qué falta

Decisión del dueño: ingreso por **comisión de 3–5 % por servicio pagado** (publicidad o destacados, más adelante).

| Pieza | Estado en el código |
|---|---|
| Cobro al cliente (Webpay Plus, Khipu) | **Existe.** Todo entra a **un único** código de comercio / cuenta de KeyServ (`Pago`, `pagos.py`) |
| Comisión | **No existe.** `COMISION_PLATAFORMA_PORCENTAJE` (5 %) solo se muestra de forma informativa junto al presupuesto; no se descuenta de nada |
| Pago al proveedor (payout) | **No existe.** El dinero queda en la cuenta de KeyServ; pasarlo al proveedor sería una transferencia manual y sin registro |
| Reembolsos / cancelación de un trabajo pagado | **No existe.** Cancelar una contratación `EN_CURSO` responde 409 `requiere_soporte`; un pago aprobado sobre una contratación cancelada solo deja un `logger.warning` |
| Disputas | **No existe** (hay chat y valoraciones, nada que retenga el dinero) |
| Boleta/factura y registro para el SII | **No existe** |

El hueco más serio: hoy **KeyServ recibe plata ajena y no tiene cómo devolverla ni entregarla con trazabilidad**.

> **Actualización 2026-10-15:** Flow y Mercado Pago ya están integrados como **medios de cobro adicionales** (checkout), no como split ni marketplace: siguen entrando a una única cuenta de KeyServ. Lo de abajo sobre repartir el dinero entre proveedores sigue pendiente. Mercado Pago es además el candidato natural para la opción C (split).

## 2. Opciones de recaudación

### A. Recaudar todo en KeyServ y transferir al proveedor (lo que existe + payouts)
Un solo comercio en Webpay/Khipu; KeyServ descuenta su comisión y transfiere el neto a la cuenta bancaria del proveedor.
- **A favor:** no cambia la integración actual; sirve con cualquier pasarela; controla cuándo se libera el dinero (útil para disputas).
- **En contra:** KeyServ pasa a **mantener fondos de terceros** (ver §5: lo más delicado legal y tributariamente); hay que construir
  y operar payouts (cuentas bancarias de proveedores, conciliación, errores de transferencia); el riesgo de fraude y contracargos
  recae en KeyServ.

### B. Webpay Plus Mall (Transbank)
Según la [documentación de Transbank](https://www.transbankdevelopers.cl/documentacion/webpay-plus), un "mall" agrupa
tiendas hijas: cada una tiene su **propio código de comercio**, una compra puede traer varias transacciones (una por tienda) y se
confirman/consultan por separado (una puede aprobarse y otra rechazarse). Hay códigos de prueba en integración.
- **A favor:** el dinero de cada proveedor se abona a su propio comercio, sin que KeyServ lo custodie (según fuentes
  secundarias; **no lo pude confirmar en la documentación oficial** y tampoco cómo se cobra la comisión del marketplace).
- **En contra / dudas:** cada proveedor tendría que ser **cliente de Transbank** con su propio código (contrato, evaluación y
  costos de comercio por proveedor, lo que para personas naturales o informales que son el público objetivo suena inviable); la
  comisión de KeyServ no queda resuelta por el mall; Khipu no tiene equivalente. **Preguntar a Transbank directamente** si ofrecen
  un esquema de marketplace con comisión y proveedores personas naturales.

### C. Pasarela con split de pagos
El split reparte el pago en la propia transacción (cada parte recibe su porción directo, sin pasar por la cuenta de la plataforma).
- **Mercado Pago** opera marketplaces en Chile con vinculación OAuth de los vendedores y comisión de la plataforma
  ([integración](https://www.blackend.dev/integracion-mercado-pago-chile)); lo que encontré son fuentes de integradores, **hay que revisar la
  documentación oficial** para confirmar disponibilidad, comisiones, plazos de liberación y si acepta vendedores sin giro.
- **Flow y Khipu:** no encontré fuentes que confirmen que soporten split ([guía](https://marketing4ecommerce.cl/pasarelas-de-pagos-online/)).
  Hay que consultarles.
- **A favor:** si la pasarela es la que retiene y reparte, KeyServ **no mantiene fondos de terceros** y la comisión queda
  resuelta en el mismo flujo. **En contra:** cambiar de pasarela (el demo usa Webpay/Khipu) y depender de sus condiciones para
  proveedores.

### Comparación resumida

| | Custodia de fondos por KeyServ | Comisión resuelta | Cambia la integración actual | Proveedores sin empresa | Dato clave a confirmar |
|---|---|---|---|---|---|
| A. Recaudar y transferir | **Sí** | Sí (la descuentas tú) | Poco | Sí | Encuadre legal de custodiar fondos (§5) |
| B. Webpay Plus Mall | No | No resuelta | Medio | Dudoso (cada uno necesita comercio Transbank) | Si Transbank acepta esto para personas naturales y cómo se cobra la comisión |
| C. Split (Mercado Pago u otra) | No | Sí | Alto (otra pasarela) | A confirmar | Condiciones para vendedores y plazos de pago |

**Mi lectura (no es asesoría):** el camino con menos riesgo legal es C o B si resultan viables para proveedores informales; A es el
más rápido de construir y el más expuesto. Para decidir, lo útil es **hacer tres consultas por escrito** (Transbank, Mercado Pago y
Flow/Khipu) con la misma pregunta: "marketplace de servicios, proveedores personas naturales, comisión del 3–5 %, ¿qué producto
y qué contrato?".

## 3. Modelo de datos mínimo (para cualquier opción)

Nada de esto existe; es lo mínimo para operar con trazabilidad. Los datos bancarios son sensibles: guardarlos cifrados
(`campos.py`, Fernet) o, mejor, no guardarlos si la pasarela los gestiona.

- **Comisión** (en `Pago` o `Contratacion`, fijada **al confirmar el monto** y nunca recalculada): `comision_porcentaje`,
  `comision_monto`, `monto_neto_proveedor`. Hoy `monto_acordado` es lo que se cobra y no se vuelve a leer `publicacion.precio`;
  la comisión debe congelarse igual.
- **`CuentaPago` del proveedor:** titular, RUT, banco, tipo y número de cuenta (cifrado), verificada sí/no. Con split/mall esto
  lo reemplaza la vinculación con la pasarela (un identificador, no una cuenta).
- **`Liquidacion` (payout):** proveedor, `pago` asociado, `monto`, estado (`PENDIENTE` → `LIBERADA` → `PAGADA` | `FALLIDA` |
  `RETENIDA`), `fecha_liberacion`, `referencia_transferencia`. Regla a decidir: liberar N días después de `COMPLETADA` si no hay disputa.
- **`Reembolso`:** `pago`, `monto` (total o parcial), motivo, estado, quién lo pidió y quién lo aprobó, `referencia_pasarela`. Es
  lo que hoy falta detrás del 409 `requiere_soporte` y del aviso de "pago aprobado sobre una contratación cancelada".
- **`Disputa`:** `contratacion`, quién la abrió, motivo, estado, resolución (a favor de cliente / proveedor / parcial) y quién
  resolvió. Mientras esté abierta, la `Liquidacion` queda `RETENIDA` (conecta con el hold de evidencia de [ADR 0007](adr/0007-retencion-evidencia-y-avisos.md)).
- **`DocumentoTributario`:** tipo (boleta/factura/nota de crédito), folio, fecha, monto, referencia a `Pago` o `Liquidacion`,
  estado ante el SII. Las notas de crédito son necesarias en cada reembolso.
- **Libro de movimientos** (inmutable, solo se agrega): cada entrada/salida de dinero con su referencia, para conciliar con el
  estado de cuenta y poder demostrar adónde fue cada peso. Es la pieza que más se subestima.

Cambios de flujo asociados: la cancelación de una contratación pagada pasa a generar un `Reembolso` (aprobado por una persona al
inicio); `_procesar_pago_aprobado` sobre una contratación cancelada debe abrir un reembolso automático en vez de solo registrar un aviso.

## 4. Documentos tributarios y SII (a validar con un contador)

Lo que encontré, con fuentes y sin garantía:
- La Ley 21.210 y la [Resolución Exenta N° 74/2020 del SII](https://www.sii.cl/normativa_legislacion/resoluciones/2020/reso74.pdf) hicieron
  **obligatoria la boleta electrónica de ventas y servicios**, con el IVA desglosado y envío diario del resumen al SII.
- Según un resumen del [Oficio SII N° 1850 de 2021](https://transtecnia.cl/noticias/precisan-tratamiento-tributario-del-comercio-electronico-denominado-marketplace/)
  (no pude leer el oficio completo): en un marketplace el SII distingue la **intermediación** de la **venta/servicio** que hace
  el vendedor; la plataforma es intermediaria, y **su comisión está afecta a IVA** y se respalda con boleta o factura afecta. Verificarlo en sii.cl.
- Para emitir boletas o facturas, KeyServ necesita **inicio de actividades** (hoy el dueño postula a Corfo como persona natural),
  y hay que decidir en qué régimen y con qué giro.
- Qué documento recibe el cliente por el **servicio** del proveedor (boleta de honorarios del proveedor, su boleta, o ninguno si
  es informal) y si KeyServ debe retener algo: **pregunta abierta, de contador**.

## 5. Decisiones legales y tributarias que necesitan asesor

1. **Custodia de fondos de terceros (opción A).** La [Ley Fintech 21.521](https://www.ey.com/es_cl/technical/tax/ey-tax-alert-chile/ley-fintech-preguntas-y-respuestas)
   regula servicios financieros que deben inscribirse en el Registro de Prestadores de la CMF
   ([NCG 502](https://www.cmfchile.cl/normativa/ncg_502_2024.pdf)); entre ellos la iniciación de pagos, cuyos proveedores no
   pueden mantener los dineros de los clientes. **No pude determinar si un marketplace que cobra y luego transfiere cae bajo
   esta ley o bajo otra norma de pagos**, ni qué excepciones aplican. Es la pregunta de mayor riesgo: **abogado especialista**.
2. **Emisión de documentos y IVA de la comisión**, y cómo documentar el servicio del proveedor (§4): **contador**.
3. **Retenciones de impuestos** sobre lo que se paga a los proveedores, si corresponden: **contador**.
4. **Términos y Condiciones** del marketplace (hoy no existen): quién responde por el servicio, plazos de liberación del dinero,
   política de reembolsos y disputas, comisión y su IVA: **abogado**.
5. **Contracargos y fraude:** quién asume un contracargo de tarjeta cuando el dinero ya se pagó al proveedor (en A, KeyServ).
6. **Datos bancarios de proveedores** como datos personales: base legal, plazo de conservación y encargados (se suman a la lista
   de [encargados](cumplimiento/README.md)).
7. **Evidencia para investigaciones** sobre movimientos de dinero: se enlaza con el [ADR 0007](adr/0007-retencion-evidencia-y-avisos.md).

## 6. Orden sugerido (cuando el dueño decida)

1. Consultas por escrito a Transbank, Mercado Pago y Flow/Khipu (§2) y a un contador/abogado (§5): sin esto cualquier código es apuesta.
2. Elegir opción de recaudación y fijar la regla de liberación del dinero y de reembolsos (decisión de negocio).
3. Implementar primero lo que no depende de la opción: comisión congelada al confirmar, `Reembolso` manual aprobado por una
   persona, libro de movimientos y las pantallas de reembolso/cancelación (cierran el 409 `requiere_soporte`).
4. Luego payouts o split según la opción, y por último la emisión de documentos tributarios.
5. Todo esto detrás de pruebas con la **integración/sandbox** de la pasarela elegida; Khipu sigue sin sandbox público.

## 7. Qué no hace este plan

No elige proveedor, no fija tarifas ni plazos legales, no sustituye una asesoría y no estima costos de desarrollo ni de
cumplimiento. Esas cifras dependen de las respuestas de §6.1.
