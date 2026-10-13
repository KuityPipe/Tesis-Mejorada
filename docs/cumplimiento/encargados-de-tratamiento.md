# Terceros que procesan datos de KeyServ (borrador)

> Basado en `privacidad.html` y la configuración de despliegue. Pendiente de validar con
> asesoría legal; falta confirmar si existe contrato o DPA con cada proveedor.

| Tercero | Qué ve | Para qué | Notas |
|---|---|---|---|
| Render | Todo lo que procesa el backend y los archivos del disco | Hosting del backend (demo) | Plan gratuito; región Oregón (EE. UU.); contrato por confirmar |
| Neon | Toda la base de datos (incluye el vector facial, cifrado) | Postgres gestionado (demo) | Plan gratuito; región São Paulo (Brasil); contrato por confirmar |
| GitHub (Actions) | El secreto `DATABASE_URL` y acceso a la BD durante el job de retención semanal | Código, CI y tareas de retención | Corre en servidores de GitHub; el secreto está cifrado en el repositorio |
| Netlify | Tráfico del frontend | Hosting del frontend | Solo estáticos; no guarda datos de usuarios |
| NVIDIA (NIM) | Mensajes del asistente **ya enmascarados** (sin RUT, correo, teléfono ni números largos) y resultados del catálogo público | Modelo de lenguaje del asistente | API gratuita de prototipo, con límites; sin clave el asistente funciona sin IA; revisar términos y retención de NVIDIA antes de producción |
| Transbank (Webpay) | Datos de tarjeta (nunca pasan por KeyServ), monto | Pagos con tarjeta | Sandbox en la demo; producción exige cuenta de comercio |
| Khipu | Monto y datos de la transferencia | Pagos por transferencia | Sin probar con cuenta real |
| DB-IP | Nada: la base de geolocalización se consulta localmente | Ciudad/país aproximados por IP | Atribución CC-BY requerida |
| Google Maps | IP del navegador del visitante | Mapa embebido de la ubicación del proveedor | Carga desde el navegador del usuario |
| Proveedor SMTP | Email del destinatario y contenido del correo | Recuperación de contraseña | Por confirmar cuál se usa en producción |

Transferencia internacional: Render (EE. UU.), Neon (Brasil), Netlify, GitHub, NVIDIA y Google pueden procesar fuera de Chile.
Debe evaluarse y documentarse (A definir).
