# ADR 0004 — Derechos del titular de datos

- **Estado:** aceptada (2026-10-11/12), implementada en `derechos_titular.py` y `api/views.py`.
- **Contexto:** la Ley 21.719 reconoce acceso, rectificación, supresión, oposición, portabilidad y bloqueo, con plazo
  general de respuesta de 30 días corridos.

## Decisión

| Derecho | Cómo se ejerce | Respuesta |
|---|---|---|
| Acceso / portabilidad | `GET /api/auth/mis-datos/` (JSON descargable) | Inmediata |
| Rectificación | Edita su perfil; para lo que no puede cambiar, `POST /api/auth/derechos/` (`RECTIFICACION`) | Solicitud con plazo de 30 días, la resuelve el superusuario en `/admin/` |
| Supresión | `POST /api/auth/eliminar-cuenta/` (pide contraseña; bloqueada si hay contrataciones activas) | **Anonimización**: se borra o vacía lo identificable; se conservan contratos y pagos por obligación tributaria |
| Oposición | `POST /api/auth/derechos/` (`OPOSICION`, `finalidad: biometria`) | Inmediata: se revoca el consentimiento y se borra el vector. Otras oposiciones: revisión manual en 30 días |
| Bloqueo | `POST /api/auth/bloqueo-tratamiento/` | Inmediata y reversible: sus publicaciones salen del catálogo y no puede publicar ni contratar; se conserva la cuenta |

- Cada solicitud queda en `SolicitudTitular` (tipo, estado, fechas, quién resolvió). El dashboard del superusuario muestra
  las pendientes y destaca las vencidas.
- Acceso y supresión son autoservicio y no generan solicitud (la supresión borra incluso las solicitudes y los eventos).

## Consecuencias

- Qué se conserva al eliminar una cuenta y por cuánto tiempo **requiere validación legal** (pospuesta por presupuesto).
- El bloqueo solo se aplica en la API (Ionic); las plantillas Django están en retiro y no lo respetan.
- Atiende las solicitudes manuales una sola persona (el dueño del proyecto); es un riesgo operativo a medida que crezca.
