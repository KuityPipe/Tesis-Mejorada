# ADR 0007 — Eliminación de cuentas con espera, conservación de evidencia y avisos por correo

- **Estado:** parte **implementada** (espera de 15 días, expiración de solicitudes, primer aviso por correo) y parte **por
  decidir con un abogado** (qué se conserva como evidencia y por cuánto). Decisiones del dueño del 2026-10-15.
- **Contexto:** la supresión (ADR 0004) anonimizaba al instante. El dueño pidió que una cuenta no pueda desaparecer en cuanto
  termina un trabajo —por si hay una queja o un problema entre las partes— y que se pueda conservar información para usarla como
  evidencia si la policía la requiere.

## Decisiones implementadas

1. **Eliminar la cuenta = bloquear y esperar 15 días** (`settings.CUENTA_ELIMINACION_DIAS`). `POST /api/auth/eliminar-cuenta/`
   deja la cuenta bloqueada (fuera del catálogo, sin publicar ni contratar), cierra sus sesiones, cancela sus solicitudes aún
   sin confirmar (para que nadie pueda impedir la supresión solicitándole un servicio) y avisa por correo. Si tiene
   contrataciones **confirmadas o en curso** sigue rechazándola (409). Pasados 15 días, `purgar_datos_vencidos`
   (parte de `mantenimiento_retencion`, semanal) la anonimiza. Desbloquear el tratamiento en "Mis datos" cancela la
   eliminación programada.
2. **Las solicitudes sin respuesta expiran** (`manage.py expirar_solicitudes`, `settings.SOLICITUD_EXPIRA_DIAS`, **7 días por
   defecto: es un valor inicial, ajústalo**): pasan a CANCELADA y se avisa por correo a las dos partes.
3. **Un único punto de avisos por correo** (`notificaciones_correo.avisar`), para que los avisos nuevos se agreguen ahí.

## Pendiente: evidencia para la policía y para quejas (a validar con un abogado)

Lo que ya queda **después** de anonimizar una cuenta: las filas de `Contratacion`, `HistorialEstadoContratacion` y `Pago`
(con la `respuesta_bruta` mínima: estado, montos, códigos de autorización), la `Publicacion` (vaciada) y las valoraciones
(sin comentario). Lo que **se pierde** y podría servir de evidencia:

| Dato | Qué pasa hoy | Riesgo para una investigación |
|---|---|---|
| Identidad (RUT, nombre, correo, teléfono, dirección) | Se anonimiza a los 15 días | Sin identidad, el contrato queda sin autor identificable |
| Chat de la contratación | Se vacía el contenido de los mensajes del usuario al anonimizar; además `limpiar_mensajes_antiguos` borra a los 90 días los chats cerrados que nadie exportó | Se pierde la conversación |
| `IntentoAccesoSospechoso` (IP, ciudad, user-agent) | Se desvincula del usuario al anonimizar; se purga a los 365 días | Se pierde la huella técnica |
| `EventoVerificacion`, documentos de identidad, fotos de valoraciones | Se borran | Se pierde la prueba de qué verificación hubo |

Opciones a discutir con el abogado (no implementadas):

- **A. Retención reforzada para casos marcados ("legal hold"):** un indicador en la cuenta o en la contratación (puesto solo
  por un superusuario, con motivo y fecha) que **impide** anonimizar y purgar chat/eventos mientras dure. Conserva todo
  lo del caso y nada de lo demás. Es la opción más proporcionada.
- **B. Ampliar lo que se conserva siempre** (identidad mínima, chat y logs de los trabajos con pago) por un plazo legal fijo.
  Más simple de operar, pero retiene datos de personas sin ningún conflicto; choca con la minimización de la Ley 21.719 y
  necesita base legal expresa (obligación legal o interés legítimo documentado) y aviso claro en la política.
- **C. Extraer el expediente del caso a un archivo cifrado y aparte** cuando se abre una queja o llega un requerimiento, y
  conservar solo ese expediente.

Preguntas para el abogado: base legal y plazo para conservar datos como evidencia; si basta una queja o hace falta un
requerimiento de autoridad (Fiscalía/policía/tribunal); cómo se atiende ese requerimiento y quién lo responde; cómo se informa
en la política de privacidad; y si el plazo de 15 días es suficiente o debe depender del estado de las quejas abiertas.

Mientras no esté decidido, **no cambiar** los plazos de `limpiar_mensajes_antiguos` (90 días) ni de `purgar_datos_vencidos`
(365 días) sin revisar esta tabla: hoy un chat de un trabajo cancelado puede borrarse a los 90 días aunque exista una queja.

## Pendiente: más avisos por correo (propuesta)

Con `notificaciones_correo.avisar` ya existe el punto de envío. Eventos que propongo avisar, en orden de utilidad. Todos son
informativos y **no llevan datos sensibles** (qué pasó y dónde verlo); ninguno está implementado todavía:

1. Inicio de sesión desde un dispositivo/ubicación nuevo, y **bloqueo por intentos fallidos** ("alguien intentó entrar a tu cuenta").
2. Cambio de contraseña, de correo o de teléfono (y recuperación de contraseña completada).
3. Solicitud recibida por el proveedor, solicitud confirmada o rechazada, contratación cancelada.
4. Pago aprobado (cliente y proveedor) y trabajo marcado como completado.
5. Verificación de identidad próxima a vencer (7 días antes) o vencida.
6. Respuesta a una solicitud de derechos del titular (vence a los 30 días).
7. Intento de eliminar la cuenta (ya implementado) y, antes de anonimizar, un recordatorio el último día.

Depende de tener **SMTP real** (hoy el demo no envía correos): ver `docs/ESTADO_Y_PROXIMOS_PASOS.md`. Para no volverlos
ruido, conviene una preferencia por tipo de aviso en "Preferencias" y no avisar de lo que la persona acaba de hacer ella misma
en la pantalla.
