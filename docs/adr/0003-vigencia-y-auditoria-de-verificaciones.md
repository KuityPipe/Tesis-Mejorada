# ADR 0003 — Vigencia y auditoría de las verificaciones de identidad

- **Estado:** aceptada (2026-10-12), implementada en la migración `0033`.
- **Contexto:** el plan pide bloquear "contratar" y "publicar" si no hay verificación **válida y reciente**, y auditar
  quién verificó, cuándo y con qué resultado **sin guardar datos biométricos en logs**. Hasta ahora la verificación era un
  booleano que nunca caducaba y no quedaba rastro estructurado de los intentos.

## Decisión

1. **Vigencia:** `Usuario.verificado_en` se fija al verificar (nativa o rostro); la vía de respaldo usa
   `VerificacionAlternativa.revisado_en`. `identidad.identidad_verificada()` acepta solo verificaciones dentro de
   `IDENTIDAD_VIGENCIA_DIAS` (180 por defecto, configurable). Un `verificado_biometricamente` sin fecha no cuenta.
2. **Auditoría:** modelo `EventoVerificacion` (usuario, método, acción, resultado, detalle breve, fecha). Se escribe desde
   `verificaciones.py` en todas las vías: registro y verificación de rostro, biometría nativa, revocación del consentimiento,
   código por correo, documento enviado y aprobación/rechazo del staff. **No tiene campos para imágenes, vectores ni
   distancias** (hay un test que fija el esquema). Es de solo lectura y solo para superusuarios en `/admin/`.
3. **Retención:** los eventos se purgan a los 365 días (`purgar_datos_vencidos`), se incluyen en la exportación del titular
   y se borran al eliminar la cuenta.
4. Un fallo al escribir el evento nunca debe tumbar la verificación (se registra en el log y se continúa).

## Consecuencias

- 180 días es una **propuesta técnica** a validar con asesoría legal junto con la política de retención.
- La migración fijó `verificado_en` = fecha de la migración para quienes ya estaban verificados, para no invalidar a
  nadie de golpe.
- Con el enforcement apagado (demo) la vigencia no bloquea nada, pero el campo y los eventos se registran igual.
