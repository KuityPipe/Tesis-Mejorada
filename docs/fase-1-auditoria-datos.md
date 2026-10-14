# Fase 1 — Auditoría de datos sensibles (Ley 21.719)

> Entregable de la Fase 1 del plan de mejoras 2026/27. Orientación técnica, **no asesoría jurídica**.
> Actualizado el 2026-10-12 contra el código en `master`; parte del reconocimiento de `fase-0-reconocimiento.md`
> y deja explícito qué hallazgos ya están corregidos y cuáles siguen abiertos.

## 1. Respuesta a la pregunta de partida: ¿se guardan fotos o huellas en bruto?

**No.** Se verificó en el código y en la base real de desarrollo:

- **Rostro:** el navegador captura una ráfaga de ~2 s; el servidor la procesa en un archivo temporal que se borra en
  el mismo request (`os.remove` en `api/views.py` y `views.py`). De ahí solo se conserva un **vector de 128 números**
  (`Usuario.encoding_facial`), no una imagen. Desde la Fase 2/3 ese vector se guarda **cifrado** (Fernet, `campos.py`).
- **Huella:** el pipeline de huella ya no está conectado a Django (retirado en una fase anterior). No hay huellas en
  ninguna tabla. `codigo/biometria/huella/` es solo código de ejemplo.
- **Biometría nativa (Face ID / huella del teléfono):** el servidor nunca ve el dato; solo recibe "el teléfono aprobó".
- **Lo que sí hay en bruto** son documentos de identidad (vía alternativa sin biometría) y certificados de proveedores,
  en almacenamiento privado, descargables solo por su dueño o el staff.

## 2. Inventario de datos personales

| Dato | Dónde | Sensible | Cifrado / protección | Retención |
|---|---|---|---|---|
| RUT, nombre, apellidos, email, teléfono, dirección, comuna, edad | `Usuario` (Postgres/Neon) | No | Contraseña PBKDF2; el resto en claro en BD (acceso por credenciales de BD) | Mientras la cuenta exista; al eliminarla se anonimiza |
| Foto de perfil, fotos de publicaciones | `media/` (públicas por diseño) | No | — | Hasta eliminar la cuenta / publicación |
| Vector facial | `Usuario.encoding_facial` | **Sí (biométrico)** | **Fernet** (AES-128-CBC + HMAC), claves rotables | Hasta revocar el consentimiento o eliminar la cuenta |
| Consentimiento biométrico (versión, fecha, revocación) | `ConsentimientoBiometrico` | No | — | Se conserva como prueba |
| Eventos de verificación (quién, cuándo, método, resultado) | `EventoVerificacion` | No (sin biometría) | — | 365 días (purga automática) |
| Verificación sin biometría: hash del código, documento de identidad | `VerificacionAlternativa`, `Documento` | Documento de identidad: alto | Almacenamiento privado, descarga autenticada | Documento: hasta eliminar la cuenta |
| Documentos/certificados de proveedor | `media_privado/` | Medio | Almacenamiento privado | Hasta eliminar la cuenta |
| Mensajes de chat (texto e imágenes) | `Mensaje` | No | Imágenes en almacenamiento privado | Chats de trabajos cerrados: 90 días (salvo exportados) |
| Reseñas y fotos de reseñas | `Valoracion`, `ValoracionImagen` | No | Fotos privadas; públicas solo si se aprueban | Hasta eliminar la cuenta |
| Pagos (monto, método, estado) | `Pago` | No (la tarjeta nunca pasa por KeyServ) | — | Obligación tributaria (plazo a definir con asesoría) |
| Accesos sospechosos (IP, ciudad, país, user-agent) | `IntentoAccesoSospechoso` | No | Geolocalización local, sin consultar terceros | 365 días (purga automática) |
| Tokens de sesión (hash) | `TokenSesion` | No | Solo el hash | 30 días tras expirar/revocar (purga automática) |
| Solicitudes de derechos del titular | `SolicitudTitular` | No | — | Se conserva como constancia |

**Logs:** los logs de aplicación identifican por `usuario_id` (no por email en claro); no contienen vectores ni imágenes.
**Respaldos:** los respaldos de Neon (plan gratuito) no se configuran desde este repo; el vector facial va cifrado también ahí.

## 3. Terceros que tratan datos

Ver `docs/cumplimiento/encargados-de-tratamiento.md` (Render, Neon, Netlify, GitHub, Transbank, Khipu, Google Maps, DB-IP,
SMTP). **Transferencia internacional:** Render (Oregón, EE. UU.), Netlify, GitHub y Google pueden procesar fuera de Chile;
Neon aloja la base en São Paulo (Brasil). Pendiente de evaluar con asesoría legal.

## 4. Hallazgos y estado

| # | Hallazgo (Fase 0/1) | Severidad | Estado |
|---|---|---|---|
| 1 | `encoding_facial` sin cifrar y editable en `/admin/` | Crítico | **Corregido**: cifrado Fernet; oculto en admin |
| 2 | Sin enforcement de identidad al contratar/publicar | Crítico | **Corregido** (`EXIGIR_IDENTIDAD_VERIFICADA`, apagado en el demo por diseño) |
| 3 | Sin consentimiento biométrico | Crítico | **Corregido**: consentimiento versionado y revocable |
| 4 | Sin endpoints de derechos del titular | Crítico | **Corregido**: acceso/portabilidad, supresión, rectificación, oposición, bloqueo |
| 5 | Fotos de reseñas públicas y adivinables | Alto | **Corregido**: almacenamiento privado |
| 6 | Sin EIPD, registro de tratamiento ni lista de encargados | Alto | **Borradores hechos** (`docs/legal/`, `docs/cumplimiento/`); falta revisión legal |
| 7 | Retención sin automatizar | Medio | **Corregido**: `mantenimiento_retencion` semanal (GitHub Actions) |
| 8 | Logs con email/IP | Medio | **Corregido** para email (id de usuario); la IP solo se guarda en accesos sospechosos |
| 9 | `Pago.respuesta_bruta` guarda la respuesta cruda del medio de pago | Medio | **Cerrado (2026-10-14)**: se guarda solo una lista de campos permitidos (`respuestas_pago.py`: estado, montos, fechas, códigos de autorización; sin tarjeta, pagador, banco ni enlaces) y la migración `0035` limpió lo ya guardado |
| 10 | Verificación sin vigencia ni auditoría | Medio | **Corregido** (Fase 3): vigencia 180 días y `EventoVerificacion` |
| 11 | `privacidad.html` omitía el RUT y la retención real | Medio | **Corregido** |
| 12 | Respaldos y retención en el proveedor de BD no controlados desde el repo | Bajo | **Abierto**: depende del plan de Neon |
| 13 | Sin protocolo de brechas | Alto | **Borrador hecho** (`docs/legal/protocolo-de-brechas.md`) |

## 5. Brechas frente a la ley que siguen abiertas

1. **Revisión jurídica** de consentimiento, EIPD, registro de tratamiento, plazos de retención y alcance de lo que se
   conserva al eliminar una cuenta (pospuesta por presupuesto).
2. **Contratos/DPA con encargados** y evaluación de transferencia internacional.
3. ~~Filtrar `Pago.respuesta_bruta` (hallazgo 9)~~ — hecho el 2026-10-14.
4. **Entorno de producción real**: hoy solo existe el demo; allí se activarán las claves propias de cifrado
   (`BIOMETRIC_ENCRYPTION_KEYS`) y el enforcement de identidad.
5. La ley entra en vigencia el **2026-12-01**; designar quién atiende solicitudes y brechas (hoy: el dueño del proyecto).
