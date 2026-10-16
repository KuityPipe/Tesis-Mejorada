# Análisis de la comisión por tramos

> Escrito el 2026-10-15. Las tarifas de las pasarelas salen de **artículos y guías de terceros** (búsqueda web de ese día,
> con cifras que no siempre coinciden entre sí), no del contrato con cada pasarela. **Confírmalas con Transbank, Flow y
> Mercado Pago antes de fijar precios.** Esto es margen bruto por transacción: no incluye hosting, revisión de identidad,
> soporte ni impuesto a la renta, y no es asesoría tributaria.

## Cómo funciona hoy en el código

La comisión se cobra **encima** del precio acordado y la paga el cliente: paga `servicio + comisión` en la pasarela y el
proveedor recibe el servicio completo (`KeyServApp/comisiones.py`). Se congela en el `Pago` al iniciar el cobro. Los tramos
se cambian sin tocar código con la variable de entorno `COMISION_TRAMOS` (JSON) y `COMISION_MINIMA`.

**Tramos por defecto (mínimo $1.000):**

| Precio del servicio | Comisión |
|---|---|
| hasta $50.000 | 6 % |
| $50.001 a $200.000 | 5 % |
| $200.001 a $500.000 | 4,5 % |
| más de $500.000 | 4 % |

## Lo que cuesta cobrar (tarifas publicadas por terceros, octubre 2026)

| Medio | Costo para el comercio | Fuente |
|---|---|---|
| Webpay Plus, tarjeta de crédito | 2,35 % + IVA (comercios nuevos) | [Digitalízame](https://digitalizame.cl/comisiones-pasarelas-de-pago-chile/), [Comocobro](https://comocobro.cl/medios-de-pago/transbank) |
| Webpay Plus, débito y prepago | 1,75 % + IVA | las mismas |
| Cargo mínimo de Transbank por transacción | UF 0,003515 (crédito), UF 0,002260 (débito), solo si el porcentaje da menos | las mismas |
| Flow, tarjeta | 2,89 % + IVA (abono al 3.er día hábil) o 3,19 % + IVA (día siguiente) | [Guía oficial de Flow](https://web.flow.cl/Gu%C3%ADa%20de%20transferencias%20bancarias%20con%20Flow.pdf) (sin fecha visible) |
| Flow, transferencia (Khipu/Etpay) | 0,99 % + IVA + $100 por transacción | la misma guía |
| Mercado Pago Chile | **no pude encontrar la tarifa**: depende de la configuración de la cuenta | consultar a su ejecutivo |

Otras plataformas de servicios cobran mucho más (Workana hasta 20 %, Fiverr 20 %, Upwork 0 a 15 %, según
[Global66](https://www.global66.com/blog/mejores-plataformas-freelance-chile/)), aunque no son comparables: son
servicios digitales internacionales, no trabajos presenciales con pago contra servicio.

## El hallazgo: 3 % no alcanza para cubrir la pasarela

Con tu idea original (5 % hasta $50.000, 4 % hasta $200.000, 3 % sobre $500.000; para el tramo de $200.000 a $500.000, que
no tenía valor, usé 3,5 %), el margen **se vuelve negativo** pagando con tarjeta en montos altos, porque la pasarela
cobra un porcentaje del total y la comisión de KeyServ baja con el monto. Además la comisión es con IVA incluido: de
cada $100 de comisión, $16 son IVA y no son ingreso.

Supuestos de las tablas: la comisión incluye IVA (se divide por 1,19 para obtener el ingreso); el costo de la pasarela es
el porcentaje publicado sobre el **total** cobrado (servicio + comisión). Se muestran dos escenarios: si KeyServ pudiera
recuperar el IVA que le cobra la pasarela (contribuyente de IVA) y si no. Cifras en pesos chilenos por transacción.

## Margen por transacción (CLP)


### Tramos del dueño (5 / 4 / 3,5* / 3 %) — IVA de la pasarela recuperable
| Medio | $20.000 | $50.000 | $100.000 | $300.000 | $600.000 |
|---|---|---|---|---|---|
| Webpay débito/prepago (1,75%) | +473 | +1.182 | +1.541 | +3.390 | +4.311 |
| Webpay crédito (2,35%) | +347 | +867 | +917 | +1.527 | +603 |
| Flow tarjeta (2,89%) | +233 | +584 | +356 | -150 | -2.734 |
| Flow/Khipu transferencia (0,99% + $100) | +532 | +1.481 | +2.232 | +5.650 | +8.908 |

### Tramos del dueño (5 / 4 / 3,5* / 3 %) — IVA de la pasarela NO recuperable
| Medio | $20.000 | $50.000 | $100.000 | $300.000 | $600.000 |
|---|---|---|---|---|---|
| Webpay débito/prepago (1,75%) | +403 | +1.008 | +1.196 | +2.357 | +2.256 |
| Webpay crédito (2,35%) | +253 | +633 | +453 | +140 | -2.156 |
| Flow tarjeta (2,89%) | +118 | +295 | -215 | -1.855 | -6.128 |
| Flow/Khipu transferencia (0,99% + $100) | +474 | +1.363 | +2.017 | +5.047 | +7.726 |

### Propuesta (6 / 5 / 4,5 / 4 %, mínimo $1.000) — IVA de la pasarela recuperable
| Medio | $20.000 | $50.000 | $100.000 | $300.000 | $600.000 |
|---|---|---|---|---|---|
| Webpay débito/prepago (1,75%) | +637 | +1.594 | +2.364 | +5.858 | +9.248 |
| Webpay crédito (2,35%) | +510 | +1.276 | +1.734 | +3.977 | +5.504 |
| Flow tarjeta (2,89%) | +396 | +989 | +1.167 | +2.284 | +2.134 |
| Flow/Khipu transferencia (0,99% + $100) | +699 | +1.896 | +3.062 | +8.141 | +13.890 |

### Propuesta (6 / 5 / 4,5 / 4 %, mínimo $1.000) — IVA de la pasarela NO recuperable
| Medio | $20.000 | $50.000 | $100.000 | $300.000 | $600.000 |
|---|---|---|---|---|---|
| Webpay débito/prepago (1,75%) | +567 | +1.417 | +2.015 | +4.816 | +7.173 |
| Webpay crédito (2,35%) | +416 | +1.039 | +1.265 | +2.578 | +2.718 |
| Flow tarjeta (2,89%) | +279 | +698 | +591 | +563 | -1.292 |
| Flow/Khipu transferencia (0,99% + $100) | +640 | +1.778 | +2.846 | +7.532 | +12.698 |

## Cómo leer las tablas

- **Tramos del dueño:** negativo en Flow con tarjeta desde $300.000 y en Webpay crédito de $600.000 si el IVA de la
  pasarela no es recuperable. Con ganancias de $300 a $1.500 en montos chicos, tampoco queda margen para sostener el servicio.
- **Propuesta (por defecto):** positiva en casi todos los casos. Sube cerca de un punto cada tramo respecto de tus números, sin
  salir mucho de tu rango de 3 a 5 %, y mantiene tu idea de bajar el porcentaje al subir el monto.
- Lo que más mejora el margen no es el porcentaje sino **el medio de pago**: las transferencias (Khipu o Flow con
  transferencia) cuestan 0,99 % + $100, casi un tercio que la tarjeta. Conviene ofrecerlas primero y destacar su ahorro.

## Decisiones que quedan para ti

1. **Quedarte con la propuesta o con tus tramos.** Para volver a los tuyos: `COMISION_TRAMOS='[[50000,"5"],[200000,"4"],[500000,"3.5"],[null,"3"]]'` y `COMISION_MINIMA=0`.
2. **Quién paga:** hoy el cliente paga la comisión encima. La alternativa es descontarla al proveedor (recibiría menos); es más
   simple de explicar pero suele alejar a los proveedores. Cambiarlo toca `comisiones.aplicar` y los pagos al proveedor.
3. **Si el servicio de un proveedor ya incluye la comisión en su precio** (precio público = precio + comisión), habría que
   mostrar el total en el catálogo; hoy el catálogo muestra el precio sin comisión.
4. **IVA y documentos:** si la comisión lleva IVA y qué boleta o factura se emite es tema de un contador
   (`PLAN_FLUJO_DE_DINERO.md` §4).
5. **Revisar al tener datos reales:** con el volumen real, Transbank y Flow pueden bajar sus tarifas, y con el mix real de
   medios de pago se puede afinar cada tramo. Los tramos son configuración, no código.

## Reproducir y cambiar los supuestos

`python docs/seguimiento/calcular_margen.py` imprime estas tablas. Edita en ese archivo las tarifas (`MEDIOS`), los tramos y los montos.
