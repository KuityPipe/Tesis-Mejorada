# KeyServ — Plan de mejoras 2026/2027 (Ley 21.719 + postulación Corfo)

> **Constancia en el repo, para no perder el plan al cambiar de equipo.**
> Esta versión fue **reconstruida** a partir de `docs/fase-0-reconocimiento.md` y
> `docs/plan-ajustes.md`, no es el texto original del plan maestro. Las fases 0, 1, 2/3, 5
> y 6 están respaldadas por esos documentos; **la Fase 4 y los detalles de la Fase 5 (bot)
> no se pudieron reconstruir** y están marcados como pendientes. Si tienes el texto
> original, pégalo aquí o reemplaza este archivo.
>
> Cambios de alcance: ver `docs/plan-ajustes.md` (registro vivo). Estado: tabla al final.

## Principios

- Cumplimiento de la Ley 21.719 (datos personales, biometría como dato sensible) va
  **antes** que bot y rediseño.
- Reusar lo que ya funciona (rostro servidor-side con prueba de vida por parpadeo,
  biometría nativa del dispositivo); no construir paralelo.
- Cada cambio de alcance se registra en `docs/plan-ajustes.md` con fecha y justificación.

## Fases

| Fase | Tema | Contenido |
|---|---|---|
| 0 | Reconocimiento | Estado real del repo, deuda y riesgos priorizados → `docs/fase-0-reconocimiento.md` |
| 1 | Auditoría | Hallazgos baratos y de bajo riesgo; inventario de datos; documentos de cumplimiento (registro de actividades de tratamiento, lista de encargados en `docs/cumplimiento/`; EIPD en `docs/legal/`) |
| 2 | Identidad | Enforcement de verificación de identidad al contratar y publicar (hoy **no existe**), comparando plataformas: PC/notebook, celular, respaldo sin biometría |
| 3 | Biometría y datos | Cifrado de `encoding_facial`, consentimiento explícito (BD + UI), derechos del titular (exportar, suprimir), retención automatizada |
| 4 | _Pendiente de reconstruir_ | — |
| 5 | Bot | _Detalle pendiente de reconstruir_ |
| 6 | Rediseño del frontend | Bento grid, container queries, `clamp()`, View Transitions, `@defer`, standalone/signals, i18n ES/EN, accesibilidad; modernización ruta por ruta (strangler fig) |

## Backlog priorizado (de la Fase 0)

**Crítico:** `encoding_facial` sin cifrar y editable en `/admin/` · cero enforcement de
identidad · cero consentimiento biométrico · cero endpoints de derechos del titular.
**Alto:** `media/` público y adivinable · sin EIPD/registro de tratamiento/encargados.
**Medio:** retención sin automatizar (`limpiar_mensajes_antiguos` no programado, sin purga
de `IntentoAccesoSospechoso`/`TokenSesion`) · logs con email/IP · `Pago.respuesta_bruta`.
**Bajo:** accesibilidad/i18n (Fase 6).

Orden sugerido dentro de 2/3: consentimiento y cifrado **antes** del enforcement (no tiene
sentido forzar captura de rostro sin consentimiento).

## Estado

| Ítem | Estado |
|---|---|
| Fase 0 reconocimiento | Hecho (2026-10-10) |
| Venv local resincronizado | Hecho |
| Node.js LTS en esta máquina | Instalado (v24.20, 2026-10-10); reabrir terminal para PATH |
| `UsuarioAdmin`: `password`/`encoding_facial` solo lectura | Hecho (Fase 1) |
| `CORS_URLS_REGEX` acotado a `/api/*` | Hecho (Fase 1) |
| `requests` en `requirements.txt` | Hecho (Fase 1) |
| Logs sin email en claro (hash corto) | Hecho (Fase 1) |
| Artefactos de huella fuera de git (`.gitignore`) | Hecho (Fase 1) |
| `media/`: fotos de reseñas a almacenamiento privado (opción A; chat y documentos ya lo estaban) | Hecho (Fase 1) |
| Registro de tratamiento y lista de encargados (borradores, `docs/cumplimiento/`) | Hecho, falta validación legal |
| EIPD borrador (`docs/legal/eipd-reconocimiento-facial.md`) | Hecho; decisiones de producto tomadas, falta revisión legal y firma |
| Rama `fase-0-reconocimiento` fusionada a `master` local (sin push) | Hecho; backend 290 OK, frontend 77 OK |
| Fase 2/3 · consentimiento biométrico (modelo versionado, gating en rostro, revocar borra el vector; Django + API + Ionic) | Hecho, pendiente de revisión legal del texto |
| Fase 2 · cifrado de `encoding_facial` | Pendiente |
| Fase 2 · enforcement de identidad al contratar/publicar | Pendiente |
| Fase 2 · vía alternativa sin biometría con MFA + advertencia | Pendiente |
| Fase 3 · exportar/eliminar datos del titular, retención automatizada | Pendiente |
| Fases 4–6 | Pendientes |
