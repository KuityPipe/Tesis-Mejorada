# ADR 0005 — Asistente con IA externa (NVIDIA NIM)

- **Estado:** aceptada (2026-10-12), implementada en `KeyServApp/asistente.py`, `POST /api/asistente/` y el widget
  `shared/asistente` de Ionic.
- **Contexto:** se quiere un asistente que responda preguntas frecuentes y ayude a encontrar servicios, usando la API
  gratuita de NVIDIA NIM (prototipo; con límites de uso y velocidad). Restricción dura del plan: **ningún dato personal ni
  biométrico se envía a servicios externos de IA**.

## Decisión

1. **El modelo no conoce a la persona ni toca la base de datos.** Recibe: reglas y preguntas frecuentes (texto fijo en
   el servidor), el historial de la conversación **enmascarado** y, si corresponde, resultados del **catálogo público**
   que busca el servidor (título, categoría, precio, comuna; solo publicaciones aprobadas y de cuentas sin bloqueo).
   Nunca recibe correo, teléfono, RUT, datos de la cuenta, biometría ni imágenes.
2. **Enmascarado antes de salir:** RUT (con o sin puntos), correos, teléfonos chilenos y números largos
   (tarjetas/documentos) se reemplazan por una marca (`enmascarar_datos_personales`). Hay tests de lo que realmente se
   envía al proveedor.
3. **La clave nunca va al frontend.** Proxy en Django; proveedor intercambiable por variables de entorno
   (`LLM_BASE_URL`, `LLM_API_KEY` o `NVIDIA_API_KEY`, `LLM_MODEL`). Sin clave, o si el proveedor falla, responde un
   **flujo guiado sin IA** (palabras clave sobre las mismas preguntas frecuentes) y el catálogo sigue funcionando.
4. **Límites:** historial de 8 mensajes, 500 caracteres por mensaje, `max_tokens` 400, timeout de 20 s y tope de uso por
   ventana de 10 minutos (30 por usuario, 10 por IP si no hay sesión).
5. **Transparencia:** aviso visible dentro del widget ("servicio de IA externo, no escribas datos personales") y mención
   en la política de privacidad, el registro de actividades y la lista de encargados.
6. **Sin registro del contenido:** los logs solo guardan el origen (IA/guiado), cuántos datos se ocultaron y cuántos
   servicios se mostraron. El historial vive en memoria del navegador y no se guarda.
7. Defensa contra *prompt injection*: el prompt de sistema ordena ignorar instrucciones del usuario que intenten cambiar
   las reglas, y solo se aceptan los roles `user`/`assistant` del cliente (un `system` enviado por el cliente se descarta).

## Consecuencias

- El enmascarado por patrones **no es infalible** (un dato personal escrito de forma inusual podría pasar); por eso el aviso
  pide no compartir datos personales. Es un riesgo residual a revisar con asesoría legal.
- NVIDIA es un nuevo encargado de tratamiento fuera de Chile (transferencia internacional de mensajes enmascarados).
- El plan gratuito tiene límites y puede cambiar su catálogo de modelos; por eso el modelo y el proveedor son configurables.
