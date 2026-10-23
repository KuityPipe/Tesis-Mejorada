# ADR 0010 — Boleta de honorarios, fase 1: el proveedor la emite en sii.cl y KeyServ registra el folio

- **Estado:** implementado (bloque 3, 2026-10-23). Decisión del dueño: en la fase 1 el proveedor emite su boleta en sii.cl y
  KeyServ solo **registra el folio**. La integración directa con el SII queda para después.
- **Contexto:** la formalización es el fin de la postulación (oficios → ingreso formal y trazable). Emitir boletas desde la
  plataforma exige integración con el SII, tratamiento tributario de la comisión y, probablemente, ser un emisor autorizado: nada
  de eso está resuelto. Registrar el folio da una constancia y un indicador sin prometer lo que el sistema no hace.

## Decisiones

1. **KeyServ no emite boletas ni consulta el SII.** Ningún texto de la app, de la política ni de la postulación dice o sugiere
   que KeyServ emite boletas. La pantalla lo repite: "KeyServ no emite boletas ni comprueba el folio con el SII".
2. **Modelo `BoletaHonorarios`** (migración `0046`): una por contratación (`OneToOne`), con `proveedor`, `folio` (solo dígitos,
   hasta 12), `fecha_emision` opcional y `es_primera_boleta`. Restricción única `(proveedor, folio)`: el mismo folio no se
   declara dos veces. Una cuenta solo puede marcar **una** boleta como su primera.
3. **Quién y cuándo:** `PUT /api/contrataciones/<id>/boleta/` solo para el proveedor de esa contratación (el cliente recibe 403,
   un tercero 404) y solo con el trabajo **pagado** (`Pago` en estado `PAGADO`; si no, 409 `trabajo_no_pagado`). El folio se puede
   corregir y quitar (`DELETE`).
4. **Qué ve cada parte:** el cliente ve el folio y la fecha (para revisarlos en el SII); la respuesta sobre "primera boleta" es solo
   del proveedor. El detalle de la contratación trae `boleta: {folio, fecha_emision}`.
5. **Datos:** el folio y la fecha aparecen en "Mis datos". Al anonimizar una cuenta **se conserva** (como los pagos y contratos): es
   un dato tributario del trabajo y, anonimizada la cuenta, ya no se liga a una persona.
6. **Reporte** (`reporte_impacto`): proveedores con boleta, servicios con boleta, primeras boletas y % de servicios pagados con
   boleta, solo agregados y suprimiendo grupos de menos de 5 proveedores; sin cuentas demo. Se rotula como "declarado por el
   proveedor, sin verificar con el SII".

## Límites conocidos

- El folio es declarado, no verificado: alguien podría escribir un número cualquiera. Por eso la cifra se presenta como
  "boletas registradas", no como "boletas emitidas".
- Fase 2 (futura, requiere contador y probablemente abogado): verificar el folio con el SII o emitir desde la plataforma.
