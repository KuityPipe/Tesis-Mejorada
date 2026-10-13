# Registro de actividades de tratamiento (borrador) — KeyServ

> Borrador técnico basado en el código real (`docs/fase-0-reconocimiento.md`, §3-4).
> **No es asesoría legal**: base de licitud, plazos y redacción final deben validarse con
> un abogado antes de publicarse. Las celdas "A definir" son decisiones de negocio o
> legales aún no tomadas, no datos que falten por investigar.

| Actividad | Datos | Dónde se guardan | Finalidad | Base de licitud | Retención | Estado |
|---|---|---|---|---|---|---|
| Cuenta de usuario | RUT, nombre, apellidos, email, teléfono, dirección, comuna, edad, foto de perfil | `Usuario` (Postgres/Neon); foto en `media/` (pública por diseño) | Identificar y operar la cuenta | Ejecución del contrato | Mientras la cuenta exista; al eliminarla se anonimiza | Plazos a validar con asesoría |
| Autenticación | Hash de contraseña (PBKDF2), hash de refresh token, user-agent | `Usuario`, `TokenSesion` | Acceso seguro | Ejecución del contrato | Tokens: 30 días tras expirar/revocar (purga automática) | Hecho |
| Reconocimiento facial | Vector de 128 floats, **cifrado (Fernet)**; los frames se descartan al procesarse | `Usuario.encoding_facial` | Verificar identidad al contratar/publicar | **Consentimiento explícito, versionado y revocable** | Hasta revocar el consentimiento o eliminar la cuenta | Hecho |
| Biometría nativa | Ninguno: el teléfono verifica; el servidor solo guarda el booleano y la fecha de verificación | `Usuario` | Verificar identidad | Consentimiento | Igual que la cuenta; vale 180 días | Hecho |
| Auditoría de verificaciones | Método, acción, resultado, fecha (**sin datos biométricos**) | `EventoVerificacion` | Trazabilidad y detección de abuso | Interés legítimo / obligación de seguridad | 365 días (purga automática) | Hecho |
| Verificación sin biometría | Hash del código enviado por correo, documento de identidad, quién lo revisó y cuándo | `VerificacionAlternativa`, `Documento` (almacenamiento privado) | Verificar identidad sin biometría | Consentimiento (advertencia aceptada) | Hasta eliminar la cuenta | Hecho; plazos a validar |
| Asistente con IA | Texto que escribe la persona **con RUT/correo/teléfono/números largos ya enmascarados**; resultados del catálogo público. Nada de cuentas, biometría ni imágenes | Solo en memoria del navegador; el servidor no guarda el contenido (solo contadores en el log) | Responder dudas y ayudar a encontrar servicios | Interés legítimo / ejecución del contrato (atención al usuario) | No se guarda | Hecho; el enmascarado no es infalible (ADR 0005) |
| Derechos del titular | Tipo de solicitud, detalle, respuesta, fechas | `SolicitudTitular`, `Usuario.tratamiento_bloqueado_en` | Atender rectificación, oposición y bloqueo (30 días) | Obligación legal | Se conserva como constancia; se borra al eliminar la cuenta | Hecho |
| Documentos y certificados | Archivos subidos por el usuario | `media_privado/` (acceso autenticado) | Acreditar proveedor | Ejecución del contrato | Hasta eliminar la cuenta | Hecho |
| Mensajería por contratación | Texto e imágenes | `Mensaje` (imágenes en almacenamiento privado) | Coordinar el servicio | Ejecución del contrato | Chats cerrados: 90 días, salvo exportados (workflow semanal) | Hecho (no alcanza los archivos del disco de Render) |
| Pagos | Monto, estado, respuesta cruda del medio de pago | `Pago` | Cobrar y conciliar | Ejecución del contrato; obligación tributaria | Plazo tributario (A definir) | **Abierto**: filtrar `respuesta_bruta` |
| Seguridad | IP, ciudad, país, user-agent de accesos sospechosos | `IntentoAccesoSospechoso` | Detectar abuso | Interés legítimo | 365 días (purga automática) | Hecho |
| Valoraciones | Texto, puntaje, fotos | `Valoracion`, `ValoracionImagen` (fotos privadas) | Reputación | Ejecución del contrato | Hasta eliminar la cuenta | Hecho |

## Brechas contra la Ley 21.719

Las cinco brechas detectadas en la Fase 0 (consentimiento biométrico, derechos de acceso/portabilidad/supresión,
cifrado del vector facial, mención del RUT en la política y retención sin automatizar) están **corregidas**. Quedan
abiertas: revisión jurídica de todo este registro, contratos con encargados (`encargados-de-tratamiento.md`) y filtrar
`Pago.respuesta_bruta`. Detalle en `docs/fase-1-auditoria-datos.md`.
