# ADR 0009 — Calculadora de valorización (gratuita y abierta)

- **Estado:** implementado (bloque 2, 2026-10-23). Decisión del dueño: la calculadora es **gratuita y se usa sin cuenta**. Es la
  puerta de entrada para quien ofrece un oficio y hoy no sabe cuánto cobrar ni cómo se ve eso con boleta de honorarios.
- **Contexto:** el encuadre de la postulación es inclusión laboral y formalización. Poner precio a un trabajo (sin olvidar
  traslado, herramientas, imprevistos, ganancia y la retención de la boleta) es el primer paso para cobrar de forma formal, y es
  útil aunque la persona nunca publique en KeyServ.

## Fórmula

```
C        = Σ materiales + traslado + horas × valor hora × personas + herramientas
P_neto   = C × (1 + imprevistos) × (1 + ganancia)          (por defecto 10 % y 15 %)
P_boleta = P_neto / (1 − r)       con boleta de honorarios;  P_neto sin documento
Total cliente = P_boleta + comisión de KeyServ (comisiones.calcular)
```

`r` es `settings.CALCULADORA_RETENCION_BOLETA` (16 % para 2027, editable por variable de entorno). Es una **estimación**: la
cifra vigente y cómo se trata con materiales dentro de una boleta de honorarios la debe confirmar un contador (hoja
`Pendientes_dueño`).

## Decisiones

1. **El cálculo vive en el servidor** (`calculadora.py`, endpoint público `POST /api/calculadora/calcular/`) y no en el
   navegador, para que la comisión (`comisiones.py`) y la retención sean siempre las que de verdad se aplican; si cambian los
   tramos, la calculadora cambia sola.
2. **Pesos enteros y suma exacta:** cada componente se redondea al peso, imprevistos y ganancia se calculan sobre los enteros y
   la boleta se redondea **hacia arriba**; así la valorización como lista de ítems suma exactamente `P_boleta` y, tras la
   retención, a la persona le quedan al menos los `P_neto` que quería.
3. **Herramientas:** monto, o porcentaje **sobre la mano de obra** (el desgaste suele ir ligado a las horas trabajadas).
4. **Exportación en el servidor** (`calculadora_exportar.py`): PDF con `fpdf2` y planilla `.xlsx` con `openpyxl`, con las
   fórmulas visibles y las celdas de datos en amarillo para editarlas. Las fórmulas de la planilla se comprobaron contra el
   resultado del servidor con un evaluador de Excel independiente. Dependencias nuevas: `openpyxl` (y `fpdf2` en los requisitos
   de Render y CI).
5. **Hoja de presupuesto extendida sin romper nada** (migración `0045`): `ItemPresupuesto` gana `cantidad`, `unidad`,
   `precio_unitario` y `reutilizado` (todos opcionales) y las categorías `HERRAMIENTAS` e `IMPREVISTOS`. `monto` sigue siendo el
   total de la fila; las filas antiguas y el formato anterior de `items` funcionan igual.
6. **Plantillas por cuenta** (`PlantillaValorizacion`, hasta 30; las ajenas dan 404): se cargan en el formulario de confirmar de
   la contratación (`GET /api/calculadora/plantillas/<id>/items/`) y su total pasa a ser el monto acordado. Se incluyen en
   "Mis datos" y se borran al eliminar la cuenta.
7. **Contador anónimo de uso** (`UsoCalculadora`), para `reporte_impacto`: el navegador genera un identificador aleatorio; el
   servidor lo mezcla con `SECRET_KEY` y el mes (SHA-256) y guarda solo ese hash y contadores (valorizaciones, con boleta, con
   material reutilizado). **No guarda IP, cuenta ni lo que se escribió**, no se puede seguir entre meses y se purga a los 13 meses.
   El cálculo en vivo solo cuenta la visita; una **valorización** cuenta cuando se exporta o se guarda como plantilla. El
   reporte suprime meses con menos de 5 visitantes.
8. **Límite de uso** por IP (300 cálculos y 30 exportaciones cada 10 minutos) con la caché, como el asistente.

9. **Dos modos** (2026-10-23): *Normal* (`modo: 'simple'` + `precio_simple`: el precio que quiere recibir, sin imprevistos ni ganancia, solo el efecto de la boleta y la comisión) y *Calculadora de costos* (el desglose completo). El servidor reutiliza la misma fórmula, así que PDF, planilla y plantillas funcionan en ambos; el modo normal se exporta como una sola línea "Servicio".
10. **Confirmar pasa por la calculadora** (2026-10-23): en el detalle del trabajo, "Confirmar contratación" (proveedor, estado Solicitada) navega a `/calculadora?contratacion=<id>`. La página carga el trabajo (solo si es del proveedor y sigue pendiente), muestra `publicacion_precio` como monto sugerido y confirma con `POST /api/contrataciones/<id>/confirmar/` re-ingresando la contraseña: sin `monto` se mantiene el precio de la publicación; con `monto` (y `items` en el modo de costos) se usa el calculado. La contratación expone `publicacion_precio` para esto. El formulario de confirmar del detalle dejó de existir (el de "completar" sigue igual).
11. **IVA como documento opcional y retención explicada** (2026-10-23): `DOCUMENTO_IVA` suma `settings.CALCULADORA_IVA` (19 %) encima del precio neto y **no cuenta en lo que recibe** (se traspasa al SII); la comisión se calcula sobre el total cobrado, IVA incluido. No es el valor por defecto porque la boleta de honorarios, que es el caso de quien se formaliza, **no lleva IVA**: solo aplica a quien tiene inicio de actividades de primera categoría. La retención de honorarios se presenta como un adelanto del impuesto a la renta que se recupera en la declaración anual (no como un costo). Imprevistos y ganancia son opcionales (interruptor + explicación; apagados valen 0). No se modela el crédito fiscal del IVA de las compras: queda indicado en el texto y para un contador.

## Pendiente (ver `Pendientes_dueño`)

- Un contador confirma cómo van los materiales dentro de una boleta de honorarios y la retención vigente.
- Un abogado dice si el identificador aleatorio del navegador cuenta como dato personal (se declara en la política).
- En la app Android la descarga de archivos desde la WebView puede requerir un plugin de Capacitor; la ruta está pensada y probada para la web.
