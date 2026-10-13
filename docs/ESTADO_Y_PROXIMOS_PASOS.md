# Estado del proyecto y próximos pasos

> Punto de retoma. Última actualización: 2026-10-11, al cierre de la sesión. Complementa
> `docs/PLAN_MAESTRO_2026-27.md` (plan y estado por fase) y `docs/plan-ajustes.md` (cambios de alcance).

## Dónde quedamos

- **2026-10-12:** reordenamiento de documentación (sin commitear): índice `docs/README.md`, docs superados movidos a `docs/archivo/`, `docs/academico/` fuera de git (queda en local), `CLAUDE.md` condensado. Falta decidir con el usuario si se commitea.

- `master` (local y GitHub) está en `a0f2526` + este documento. Fases 0, 1, 2 y 3 hechas y mergeadas.
- Tests al cierre: backend 341 OK (1 omitido), frontend 82 OK, CI de GitHub en verde (backend, frontend, e2e).
- Las ramas `fase-0-reconocimiento`, `fase-1-auditoria`, `fase-2-identidad` solo existen en la máquina local; todo su contenido ya está en `master`.
- Node.js LTS ya instalado en la máquina de desarrollo (v24). En una terminal nueva puede hacer falta reabrirla para que esté en el PATH.

## Demo en Render: resuelto (2026-10-12)

- La Postgres gratuita de Render había expirado. Ahora la base es **Neon** (proyecto en São Paulo, rama `production`) y `DATABASE_URL` se define a mano en Render (`render.yaml` ya no declara `databases:`).
- El servicio `keyserv-api` (Oregon) despliega la rama `master`; migraciones 0029–0032 y las rutas nuevas (`/api/auth/mis-datos/` → 401 sin token) están en vivo. Catálogo 200.
- Latencia: API en Oregon + base en São Paulo → `/api/publicaciones/` tarda ~3,5 s. Decisión del usuario: se deja así, es solo un demo (si molesta: crear la base de Neon en `aws-us-west-2`).
- Si vuelve a fallar: revisar `DATABASE_URL` y los logs de Render. Opcional: ping cada 10 min (UptimeRobot) contra `/api/catalogos/categorias/` evita el arranque en frío, pero consume horas de cómputo de Neon.

## Pospuesto a propósito (decisión del usuario, 2026-10-12)

- **Respaldo del keystore de Android** (`android/app/keyserv-release.keystore` + `keystore.properties`): se hace desde el PC de torre, donde está Android Studio.
- **Revisión legal por un abogado** (consentimiento, EIPD, registro de tratamiento, qué se conserva al eliminar una cuenta): sin presupuesto por ahora.
- **Entorno de producción real**: no existe, solo el demo/prototipo. Hasta entonces `BIOMETRIC_ENCRYPTION_KEYS` y `EXIGIR_IDENTIDAD_VERIFICADA` quedan sin tocar.

- **2026-10-13:** el frontend de Netlify llevaba congelado desde antes de la Fase 2: el comando `ignore` de `netlify.toml` cancelaba cada build ("Canceled build due to no content change"). Se quitó; Netlify construye en cada push. Verificar que el bundle publicado incluya `app-asistente`.

## Pendientes por fase

**Fase 2/3 — cierre**
- Definir `BIOMETRIC_ENCRYPTION_KEYS` (clave Fernet, distinta de `SECRET_KEY`) en producción real y respaldarla fuera de la BD.
  Generar con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- Encender `EXIGIR_IDENTIDAD_VERIFICADA=True` solo en producción real (la demo no tiene biometría).
- Retención: workflow semanal listo (`.github/workflows/retencion.yml`). **Falta cargar el secreto `DATABASE_URL` (cadena de Neon) en GitHub → Settings → Secrets and variables → Actions** y probarlo una vez a mano (Actions → Retención de datos → Run workflow, dry-run).
- La vía alternativa sin biometría existe en API, admin (superusuario y Moderador, con registro y aviso en el dashboard) e Ionic; la pantalla en las plantillas Django se omite (en retiro).
- Revisión de un abogado: texto del consentimiento (`KeyServApp/consentimiento.py`), advertencia (`verificacion_alternativa.py`),
  EIPD (`docs/legal/`), registro de tratamiento y encargados (`docs/cumplimiento/`), y qué se conserva al eliminar una cuenta.
- (Hecho 2026-10-12) `privacidad.html` menciona el RUT y los tests de rechazo facial (vectores sintéticos; la detección sobre imágenes reales sigue siendo prueba manual).
- Tras el próximo deploy en Render: `migrate` aplica `0033`; si la base de Neon ya tenía usuarios verificados, la migración les fija `verificado_en`.

**Plan maestro original (7 fases, ver `PLAN_MAESTRO_2026-27.md`; texto completo local en `docs/privado/`)**
- Fases 0–4: **hechas** (2026-10-12). Cerradas ese día: documento de auditoría (`fase-1-auditoria-datos.md`), ADRs 0001–0004 con diagrama, vigencia de 180 días y `EventoVerificacion`, `rotar_llaves_biometricas` + guía, "Mis datos" completo (rectificación, oposición, bloqueo), retención visible en `privacidad.html`, protocolo de brechas.
- **Fase 5 (asistente con IA): hecha** (2026-10-12, ADR 0005, CI en verde). Modelo principal `google/gemma-4-31b-it` (5–20 s), respaldo `meta/llama-3.2-11b-vision-instruct`, y flujo guiado sin IA. **Pendiente del dueño: cargar `NVIDIA_API_KEY` en Render** (Environment de `keyserv-api`); los modelos ya son el valor por defecto. Límites: plan gratuito de NVIDIA con cupo; la mayoría de los modelos del catálogo responden 404 al chat; el enmascarado por patrones no es infalible.
- **Fase 7: hecha** (2026-10-12, CI en verde): `docs/cumplimiento/README.md` (matriz requisito → evidencia), `docs/resumen-mejoras.md`, READMEs renovados, consentimiento v2 (informa el período), E2E del asistente y de "Mis datos".
- **Fase 6 (rediseño visual): la única pendiente.** El plan exige una **propuesta visual aprobada antes de implementar** (dirección de arte, paleta, componentes clave). Preguntas para el dueño: ¿estilo serio/corporativo o cercano/amigable?, ¿se conserva la paleta navy/teal/coral?, ¿qué pantallas priorizar (inicio, catálogo, verificación)? Después: standalone components + signals, accesibilidad (zoom bloqueado en `index.html`, `aria-label`), i18n ES/EN, bento grid, View Transitions, `@defer`.
- Convención decidida por el dueño: commits en español, directo a `master`, tags para hitos (`pre-cierre-fases-1-4`).
- Límites conocidos de lo cerrado: el bloqueo del tratamiento solo aplica a la API/Ionic (las plantillas Django están en retiro); la vía alternativa no tiene pantalla en las plantillas; la verificación vencida solo bloquea si `EXIGIR_IDENTIDAD_VERIFICADA=True` (apagado en el demo); los tests E2E de navegador de fallos de verificación no se hicieron porque el demo tiene el enforcement apagado (hay tests de backend).

## Ideas rápidas de mejora

- Suite del backend: hecho. `KeyServProject/settings_test.py` (hasher MD5) baja 341 tests de 12 min 48 s a 22,6 s; CI lo usa. Queda como opción `--parallel`/`--keepdb`, ya no necesario.
- Respaldar fuera del repo el keystore de Android (`android/app/keyserv-release.keystore` y `keystore.properties`).
