# Terceros que procesan datos de KeyServ (borrador)

> Basado en `privacidad.html` y la configuración de despliegue. Pendiente de validar con
> asesoría legal; falta confirmar si existe contrato o DPA con cada proveedor.

| Tercero | Qué ve | Para qué | Notas |
|---|---|---|---|
| Render | Toda la BD y archivos del backend | Hosting del backend (demo) | Plan gratuito; región y contrato por confirmar |
| Netlify | Tráfico del frontend | Hosting del frontend | Solo estáticos; no guarda datos de usuarios |
| Transbank (Webpay) | Datos de tarjeta (nunca pasan por KeyServ), monto | Pagos con tarjeta | Sandbox en la demo; producción exige cuenta de comercio |
| Khipu | Monto y datos de la transferencia | Pagos por transferencia | Sin probar con cuenta real |
| DB-IP | Nada: la base de geolocalización se consulta localmente | Ciudad/país aproximados por IP | Atribución CC-BY requerida |
| Google Maps | IP del navegador del visitante | Mapa embebido de la ubicación del proveedor | Carga desde el navegador del usuario |
| Proveedor SMTP | Email del destinatario y contenido del correo | Recuperación de contraseña | Por confirmar cuál se usa en producción |

Transferencia internacional: Render, Netlify y Google pueden procesar fuera de Chile.
Debe evaluarse y documentarse (A definir).
