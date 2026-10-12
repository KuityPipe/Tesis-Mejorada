# Estado del proyecto y próximos pasos

> Punto de retoma. Última actualización: 2026-10-11, al cierre de la sesión. Complementa
> `docs/PLAN_MAESTRO_2026-27.md` (plan y estado por fase) y `docs/plan-ajustes.md` (cambios de alcance).

## Dónde quedamos

- **2026-10-12:** reordenamiento de documentación (sin commitear): índice `docs/README.md`, docs superados movidos a `docs/archivo/`, `docs/academico/` fuera de git (queda en local), `CLAUDE.md` condensado. Falta decidir con el usuario si se commitea.

- `master` (local y GitHub) está en `a0f2526` + este documento. Fases 0, 1, 2 y 3 hechas y mergeadas.
- Tests al cierre: backend 341 OK (1 omitido), frontend 82 OK, CI de GitHub en verde (backend, frontend, e2e).
- Las ramas `fase-0-reconocimiento`, `fase-1-auditoria`, `fase-2-identidad` solo existen en la máquina local; todo su contenido ya está en `master`.
- Node.js LTS ya instalado en la máquina de desarrollo (v24). En una terminal nueva puede hacer falta reabrirla para que esté en el PATH.

## Problema abierto: el demo en Render está caído (prioridad 1 de mañana)

- **Síntoma (2026-10-11):** `keyserv-api.onrender.com` devuelve 500 en los endpoints que usan la BD
  (`/api/publicaciones/`, `/api/catalogos/regiones/`) y funciona en los que no (`/api/catalogos/categorias/`, `/api/schema/`).
  El frontend (`keyserv.netlify.app`) carga bien.
- **Hipótesis (no confirmada, sin acceso a logs):** la Postgres gratuita de Render (`keyserv-db`, creada ~2026-08-17) expiró.
- **Además:** Render despliega la rama **`api-ionic-migration`** (commit `b83d70f`), no `master`. Por eso las migraciones
  0029–0032 y el código de las Fases 2/3 **no están en el demo**.

### Plan acordado: base gratuita externa (Neon) en vez de la de Render

1. Confirmar en el panel de Render el estado de `keyserv-db` y los logs de `keyserv-api`.
2. Crear un proyecto en Neon (Postgres gratuito) y copiar su cadena de conexión (`postgresql://...?sslmode=require`).
3. En el servicio `keyserv-api` de Render, definir `DATABASE_URL` a mano con esa cadena. Hoy `render.yaml` la toma de
   `fromDatabase: keyserv-db`; hay que cambiarla a `sync: false` y quitar el bloque `databases:` para que Render no recree la suya.
4. Cambiar la rama del servicio a `master` (Settings → Branch).
5. Completar las variables que son manuales: `CORS_ALLOWED_ORIGINS` e `IONIC_FRONTEND_URL` (URL de Netlify).
6. Redeploy: `render_build.sh` corre `migrate`, `loaddata catalogos_iniciales` y `sembrar_datos_demo` en ese orden.
7. Verificar: catálogo responde 200 y las rutas nuevas (`/api/auth/mis-datos/`, etc.) responden 401 sin token (no 404).
8. Opcional: definir `BIOMETRIC_ENCRYPTION_KEYS` (ver abajo). En la demo no hay rostros registrados, así que no es crítico.

Nota: la extensión `unaccent` que usa el buscador del catálogo la crea la migración `0009`; Neon permite `CREATE EXTENSION unaccent`.

## Pendientes por fase

**Fase 2/3 — cierre**
- Definir `BIOMETRIC_ENCRYPTION_KEYS` (clave Fernet, distinta de `SECRET_KEY`) en producción real y respaldarla fuera de la BD.
  Generar con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- Encender `EXIGIR_IDENTIDAD_VERIFICADA=True` solo en producción real (la demo no tiene biometría).
- Programar `manage.py mantenimiento_retencion` (el cron de Render es de pago; alternativa: GitHub Actions con la BD externa, o un cron externo).
- La vía alternativa sin biometría existe en API, admin e Ionic; falta la pantalla en las plantillas Django (en retiro).
- Revisión de un abogado: texto del consentimiento (`KeyServApp/consentimiento.py`), advertencia (`verificacion_alternativa.py`),
  EIPD (`docs/legal/`), registro de tratamiento y encargados (`docs/cumplimiento/`), y qué se conserva al eliminar una cuenta.
- `privacidad.html` no menciona que se recolecta el RUT.
- Tests de rechazo facial con rostros distintos (hueco heredado de la Fase 0).

**Fases 4, 5 y 6**
- Fase 4 y el bot (Fase 5): el plan maestro original no está en el repo; `PLAN_MAESTRO_2026-27.md` es una reconstrucción y
  las marca como pendientes de reconstruir. **Pegar el texto original del plan para completarlas.**
- Fase 6 (rediseño): migrar a standalone components/signals y control flow nuevo, accesibilidad (zoom bloqueado en
  `index.html`, pocos `aria-label`), i18n ES/EN, bento grid, View Transitions. Ahora Node está disponible para probar Ionic.

## Ideas rápidas de mejora

- Suite del backend lenta (~8 min): probar `MD5PasswordHasher` solo en la configuración de tests, `--parallel` y `--keepdb`.
  Medir antes con `--timing`.
- Respaldar fuera del repo el keystore de Android (`android/app/keyserv-release.keystore` y `keystore.properties`).
