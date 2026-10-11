# Registro de actividades de tratamiento (borrador) — KeyServ

> Borrador técnico basado en el código real (`docs/fase-0-reconocimiento.md`, §3-4).
> **No es asesoría legal**: base de licitud, plazos y redacción final deben validarse con
> un abogado antes de publicarse. Las celdas "A definir" son decisiones de negocio o
> legales aún no tomadas, no datos que falten por investigar.

| Actividad | Datos | Dónde se guardan | Finalidad | Base de licitud | Retención actual | Retención propuesta |
|---|---|---|---|---|---|---|
| Cuenta de usuario | RUT, nombre, apellidos, email, teléfono, dirección, comuna, edad, foto de perfil | `Usuario` (Postgres); foto en `media/` (público) | Identificar y operar la cuenta | Ejecución del contrato | Indefinida | Mientras la cuenta exista + A definir |
| Autenticación | Hash de contraseña (PBKDF2), hash de refresh token, user-agent | `Usuario`, `TokenSesion` | Acceso seguro | Ejecución del contrato | Tokens expirados no se purgan | Purga automática de expirados |
| Reconocimiento facial | Vector de 128 floats (`encoding_facial`); los frames se descartan tras procesarse | `Usuario.encoding_facial` (JSON, **sin cifrar**) | Verificar identidad al contratar/publicar | **Consentimiento explícito (hoy no se captura)** | Indefinida | Hasta revocar consentimiento o cerrar cuenta |
| Biometría nativa | Ninguno: el dispositivo verifica, el servidor solo guarda el booleano `verificado_biometricamente` | `Usuario` | Verificar identidad | Consentimiento | Indefinida | Igual que la cuenta |
| Documentos y certificados | Archivos subidos por el usuario | `media_privado/` (acceso autenticado) | Acreditar proveedor | Ejecución del contrato | Indefinida | A definir |
| Mensajería por contratación | Texto e imágenes | `Mensaje` | Coordinar el servicio | Ejecución del contrato | Chats cerrados se borran a 90 días **solo si alguien corre el comando a mano**; no borra la imagen del disco | Programar el comando y borrar archivos |
| Pagos | Monto, estado, respuesta cruda del medio de pago | `Pago` | Cobrar y conciliar | Ejecución del contrato; obligación tributaria | Indefinida | Plazo tributario (A definir) y filtrar `respuesta_bruta` |
| Seguridad | IP, ciudad, país, user-agent de accesos sospechosos | `IntentoAccesoSospechoso` | Detectar abuso | Interés legítimo | Sin purga | Purga periódica (p. ej. 12 meses, A definir) |
| Valoraciones | Texto, puntaje, fotos | `Valoracion`, `ValoracionImagen` | Reputación | Ejecución del contrato | Indefinida; fotos en almacenamiento privado, públicas solo si aprobadas (Fase 1) | A definir |

## Brechas contra la Ley 21.719 detectadas

1. Sin consentimiento registrado ni checkbox para biometría.
2. Sin endpoints de acceso, portabilidad ni supresión (hoy se pide por contacto).
3. `encoding_facial` sin cifrar en reposo.
4. `privacidad.html` no menciona que se recolecta el RUT.
5. Retención sin automatizar en varias tablas.
