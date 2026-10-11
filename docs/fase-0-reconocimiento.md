# Fase 0 — Reconocimiento completo de KeyServ

> Entregable de la Fase 0 del plan de mejoras 2026/2027 (cumplimiento Ley 21.719 +
> postulación Corfo). Estado verificado contra el código real en `master` (`1adacb4`),
> no contra lo que afirman `CLAUDE.md` o los docs de fases anteriores — donde hubo
> discrepancia, se documenta explícitamente.
>
> Ver también: `docs/plan-ajustes.md` (ajustes de alcance al plan de fases derivados de
> este reconocimiento).

## 1. Estructura y estado del repo

- Working tree en `master`, limpio, 132 commits desde 2023-03-21.
- `codigo/backend/django/` (Django 5.2 + DRF), `codigo/frontend/ionic/` (Ionic 8 +
  Angular 20 + Capacitor), `codigo/biometria/` (pipelines standalone de huella y rostro).
- `docs/` tenía 18 `.md` + `academico/` (tesis), pero sin `docs/adr/`, `docs/legal/` ni
  `docs/cumplimiento/` — se crearon en esta fase (ver §10).
- Único workflow CI: `.github/workflows/tests.yml` (jobs backend/frontend/E2E en paralelo).
- Deploy real: Render (`keyserv-api`) + Netlify (`keyserv.netlify.app`), demo viva.

### Entorno local — bloqueantes resueltos o detectados en esta fase

- El venv (`venv_tesis`, Python 3.14) tenía instalados Django 5.2.16,
  `face_recognition`/`dlib`/`opencv-python`, `psycopg2-binary`, `transbank-sdk`, pero
  **le faltaban** `djangorestframework`, `django-cors-headers`, `drf-spectacular`,
  `PyJWT`, `whitenoise`, `fpdf2`, `Click`, `dlib-bin` — quedó del período previo a la
  migración a API/Ionic y nunca se resincronizó tras el merge a `master`. `manage.py
  check` fallaba con `ModuleNotFoundError: No module named 'rest_framework'`.
  **Resuelto en esta fase**: `pip install -r requirements.txt` reinstaló todo lo
  faltante; `manage.py check` ahora pasa limpio.
- **No hay Node.js instalado en esta máquina** (ni en PATH ni en rutas típicas de
  nvm/volta/fnm). Bloquea `npm install`/`ng serve`/`ng test`/Playwright E2E — es decir,
  bloquea cualquier trabajo real sobre el frontend Ionic. **Pendiente**: instalar Node
  LTS antes de que cualquier fase necesite tocar o probar el frontend (relevante desde
  la Fase 2 si se ajusta algo de Ionic, e imprescindible para la Fase 6).
- Postgres 17 corre como servicio (`postgresql-keyserv`), BD `keyserv` con 40 tablas y
  datos reales de prueba: 13 usuarios, **1 con `encoding_facial` real guardado** (vector
  de 128 floats), 11 fotos de perfil, documentos reales en `media_privado/`. Importa
  para la Fase 1 (es el dato real a auditar) y la Fase 3 (migración/cifrado) — se debe
  tratar como dato sensible real, no como fixture descartable.

## 2. Dependencias y versiones reales

**Backend** (`requirements.txt` + variantes `-ci`/`-render`, sin `pyproject.toml` ni
lockfile real — mayoría de pines con `>=` sin techo):

| Paquete | Versión/rango |
|---|---|
| Django | `==5.2.16` |
| djangorestframework | `>=3.15` (instalado: 3.18.3) |
| django-cors-headers | `>=4.4` (instalado: 4.9.0) |
| drf-spectacular | `>=0.27` (instalado: 0.30.0) |
| PyJWT | `>=2.9` (instalado: 2.15.1) |
| psycopg2-binary | `>=2.9.9` |
| Pillow | `>=10.3` |
| opencv-python | `>=4.10` |
| dlib-bin | sin pin |
| face_recognition | `==1.3.0` (2020, última versión publicada) |
| transbank-sdk | `>=6.1.0` |
| geoip2 | `>=4.8` |
| whitenoise | `>=6.7` |
| fpdf2 | `==2.7.9` |
| setuptools | `<81` (techo, no piso) |

Inconsistencia real encontrada: `requests` se usa en `pagos.py` (cliente Khipu) pero
**no está declarado en `requirements.txt`** (sí en `-ci`/`-render`). Sin
linter/formatter/pre-commit de ningún tipo en el repo. Sin medición de cobertura.

**Frontend** (`package.json`, con `package-lock.json`):

- Angular **20.3.25** (pinned exacto), CLI/devkit 20.3.28, TypeScript `~5.9.0`.
- **Arquitectura: NgModules clásicos.** `standalone: false` en las 32 páginas, **cero**
  `standalone: true`, cero `signal()`/`computed()`/`effect()`, cero `@if`/`@for`/`@for`
  (control flow antiguo: 198 `*ngIf`, 30 `*ngFor`). Bootstrap vía
  `platformBrowserDynamic().bootstrapModule(AppModule)`, no `bootstrapApplication` — por
  lo que **`withViewTransitions()` no existe todavía** en el router, y tampoco `@defer`.
- Ionic `^8.0.0`, Capacitor `8.5.0`. Plugins instalados y enlazados en Android: cámara,
  geolocation, `@capgo/capacitor-native-biometric`, `capacitor-secure-storage-plugin`,
  más haptics/keyboard/status-bar/app (instalados pero no importados en ningún `.ts`).
- Sin i18n (`@angular/localize` no instalado, `<html lang="en">` con contenido en
  español). Sin NgRx/estado global — todo con RxJS (`BehaviorSubject`).
- `minSdkVersion 24`, `targetSdkVersion 36`, firma de release vía `keystore.properties`
  (gitignored, ya generado).

## 3. Modelos, endpoints, autenticación

- `KeyServApp/models.py`: 31 modelos. PII identificada: `rut_usuario`, nombre/apellidos,
  `telefono`, `email`, `direccion_usuario`, `comuna`, `edad`, `foto_perfil`,
  **`encoding_facial`** (`JSONField`, **sin cifrar**), `Mensaje.contenido`,
  `Documento.archivo`/`archivo_subido`, `Pago.respuesta_bruta` (respuesta cruda del
  medio de pago, sin filtrar), `IntentoAccesoSospechoso` (IP+ciudad+país+user-agent, sin
  retención), `TokenSesion.dispositivo` (user-agent).
- **Ningún campo de ningún modelo está cifrado en reposo.** Lo único irreversible es el
  hash de `password` (PBKDF2 vía `django.contrib.auth.hashers`) y de
  `TokenSesion.refresh_token_hash` (SHA-256).
- Dos sistemas de autenticación en paralelo:
  - **Sesión propia de Django** sobre `Usuario` (`login_requerido` en
    `decorators.py`), para las 42 rutas de plantilla. `Usuario` no es `AUTH_USER_MODEL`.
  - **JWT propio con PyJWT** (`api/jwt_utils.py`, `api/authentication.py`) para las 44
    rutas de la API REST — access token de 20 min + refresh token revocable vía
    `TokenSesion` (solo se persiste el hash, nunca el token en claro).
  - Rate limiting hecho a mano sobre `django.core.cache` (login, recuperación,
    re-autenticación) — nota operativa: sin `CACHES` configurado el backend es
    `LocMemCache`, que no se comparte entre workers de `gunicorn` en producción.
- `KeyServApp/admin.py` → **`UsuarioAdmin` no declara `fields`, `exclude` ni
  `readonly_fields`**, por lo que el formulario de edición en `/admin/` expone y permite
  **editar** `encoding_facial` (128 floats en un textarea JSON) y el hash de `password`.
  Hallazgo crítico (ver §8).
- CORS: el comentario en `settings.py` afirma que está acotado a `/api/*`, pero no hay
  `CORS_URLS_REGEX` configurado — en la práctica aplica a todo el sitio, no solo a la API.

## 4. Flujo biométrico de punta a punta

### Rostro — único flujo biométrico servidor-side activo

- Librerías: `face_recognition` + OpenCV (dlib por debajo), prueba de vida por
  **parpadeo** (Eye Aspect Ratio, umbral 0.21), no la secuencia de 3 fotos de versiones
  anteriores — el diseño actual del repo ya migró a esto.
- Captura: el navegador toma ~16-17 frames JPEG en ~2s (`getUserMedia`/`canvas`), igual
  en Django templates e Ionic, enviados como multipart (`rostro_frames`) a
  `/rostro/registrar|verificar/` o sus equivalentes API (`RostroRegistrarView`/
  `RostroVerificarView`).
- **Los frames se escriben a disco temporal del sistema operativo (no a `MEDIA_ROOT`) y
  se borran siempre en `try/finally`** en las 5 rutas de entrada (2 de plantilla + AJAX
  de pre-validación + 2 de API). Único hueco teórico: un `OSError`/`MemoryError` a mitad
  de escribir el lote podría dejar temporales huérfanos — riesgo real bajo, pero una
  mitigación simple (limpieza periódica del directorio temporal, o escribir todo a un
  directorio dedicado que se pueda purgar) es razonable para la Fase 3.
- El resultado — un vector de 128 floats — se guarda en `Usuario.encoding_facial`
  (`JSONField`), **sin cifrar**. No se expone en ningún serializer de la API
  (`UsuarioMeSerializer` lo excluye explícitamente, por diseño) — pero sí es editable
  desde `/admin/` por el hallazgo de §3.
- **No se loguea ningún dato biométrico** — ni el encoding, ni los frames, ni rutas con
  contenido real. Los logs de este flujo solo registran `usuario_id`. Correcto.
- Biometría nativa (`VerificarBiometriaNativaView`): el servidor nunca recibe datos
  biométricos — confía en el JWT + que el sistema operativo del teléfono ya verificó
  (Face ID/huella nativa). Ya alineado con el enfoque de minimización de datos (opción A
  del plan maestro, "biometría del dispositivo").

### Huella — no conectada a Django en ningún punto

- Confirmado por búsqueda exhaustiva: no hay vista, URL ni import de `procesar_huella`
  desde el backend. Fue retirada explícitamente en una fase anterior (documentado en
  `docs/BACKLOG.md`).
- El pipeline standalone (`codigo/biometria/huella/IMAGEN_HUELLA.py`) sigue siendo
  ejecutable y, si se corre a mano, **escribe 4 PNG + un hash SHA-256 a rutas fijas que
  están committeadas en git** (`Huella Imagen/imagenOutput/*.png`, `Contraseña
  dactilar/CodigoHuella.txt`). Son artefactos de ejemplo hoy, pero el patrón (sobrescribir
  y versionar binarios biométricos) es un hallazgo de higiene de repo, no una brecha de
  producción — no hay flujo real de huella que proteger.

### Brecha de negocio más importante: sin enforcement de identidad

**Hoy nada bloquea contratar ni publicar por falta de verificación de identidad.** Se
leyó el código completo de `contratacion_crear_view` y `publicacion_crear_view`: ninguna
de las dos comprueba `verificado_biometricamente`. La regla de negocio del plan maestro
("al contratar y publicar, la identidad debe verificarse sí o sí") **no existe
todavía** — no se trata de reforzar un gating existente, sino de construirlo desde cero
reusando la verificación que ya funciona. Esto recalibra el alcance real de la Fase 2/3
(ver `docs/plan-ajustes.md`).

### Consentimiento y derechos del titular — prácticamente inexistentes

- **Cero registro de consentimiento en BD** (ningún modelo tiene campo de aceptación) y
  **cero checkbox real**: en Django es un párrafo de texto sin `<input>`; en Ionic ni
  siquiera existe el texto. Ningún flujo pide consentimiento específico antes de
  capturar el rostro.
- **Cero endpoint de exportación o eliminación de datos personales.** Lo más cercano es
  exportar un chat a `.txt` (no es un derecho de acceso general). Eliminar la cuenta hoy
  es "escribinos por contacto, lo procesamos manualmente" — así lo admite
  `privacidad.html` textualmente.
- `privacidad.html` ya existe y es sorprendentemente preciso en lo que describe (128
  floats, imágenes descartadas tras procesarlas, documentos en almacenamiento privado,
  IP vía base local) — con una omisión real: no menciona que se recolecta el RUT.

### Otros hallazgos de seguridad/retención relevantes

- Email en texto claro en logs de registro y de login fallido (junto a la IP en este
  último caso).
- `media/` (fotos de perfil, imágenes de publicaciones y de valoraciones) es público y
  con URL adivinable — incluidas fotos de valoraciones todavía PENDIENTE o RECHAZADA.
- Único borrado automático existente: `limpiar_mensajes_antiguos` (chats cerrados a 90
  días) — y **nadie lo programa**: no hay cron, Celery ni scheduler en el repo, hay que
  correrlo a mano. Tampoco borra `Mensaje.imagen` del disco, solo la fila de BD.
- `IntentoAccesoSospechoso` (IP+ciudad+país+user-agent) crece sin ninguna purga.
- `Pago.respuesta_bruta` guarda la respuesta cruda del medio de pago sin filtrar.

## 5. Tests, CI/CD, deploy

- **290 tests backend** (134 en `tests.py` + 156 en `tests_api.py`, 57 clases) —
  ninguno cubre `validar_captura_rostro_ajax` ni ejercita un caso real de
  suplantación/mismatch facial.
- **77 tests frontend** (Karma/Jasmine), pero **23 de 36 archivos spec son solo el
  "should create" del scaffold** generado por Ionic — incluidos
  `rostro.page.spec.ts`/`biometria.page.spec.ts`. Ningún test ejercita el flujo real de
  cámara/captura.
- **7 tests E2E (Playwright)**: login (3), catálogo (3), 1 de chat de contratación.
  Ninguno toca biometría ni pagos ni el flujo completo de contratación (deliberado, para
  no romper la data demo con transiciones de estado reales).
- CI (`tests.yml`) corre los tres jobs (backend/frontend/E2E) en paralelo contra
  Postgres real — sin medición de cobertura, sin lint, sin matriz de versiones.
- Deploy: Render (backend, free tier) + Netlify (frontend), ambos con filtro de build
  para no redesplegar en cada commit. Variables sensibles (`CORS_ALLOWED_ORIGINS`,
  `IONIC_FRONTEND_URL`) son manuales (`sync: false`). HSTS apagado por defecto incluso en
  producción — decisión deliberada y documentada, no un descuido.

## 6. Documentación existente

18 documentos en `docs/` antes de esta fase (migración a Ionic, backlog vivo, auditoría
Django-vs-Ionic, bitácora de 132 commits, informe de proyecto/tesis, plan de
portafolio) — ninguno menciona la Ley 21.719, una EIPD, ni el bot de la Fase 5 del plan
actual, pero el repo tiene buena disciplina de registro histórico (bitácora, backlog
vivo con estado por ítem). No existían `docs/adr/`, `docs/legal/`, `docs/cumplimiento/`
ni `docs/plan-ajustes.md` — se crean en esta fase, sin convención previa de ADR que
seguir (se introduce recién con este plan).

## 7. Estado visual del frontend

- El sistema de diseño ya existe y está maduro en ambos frontends: paleta
  navy/teal/coral con tokens `--ks-*`, modo claro/oscuro con 3 estados (sistema,
  claro forzado, oscuro forzado), tipografía Quicksand/Nunito.
- En Ionic, la mayoría de páginas (19 de 29 archivos `.scss`) están vacías — el diseño
  vive casi enteramente en `global.scss` (1323 líneas) + `variables.scss` (274), no por
  página individual.
- Lo que el plan maestro pide para la Fase 6 y **no existe hoy**: layouts bento grid,
  container queries, `clamp()` (solo 2 usos puntuales), scroll-driven animations, View
  Transitions, `@defer`, componentes standalone/signals, i18n ES/EN. Accesibilidad hoy es
  baja: 9 `aria-label` en todo el frontend, 0 `role=`, zoom bloqueado en `index.html`
  (`user-scalable=no`).
- Conclusión: la Fase 6 implica, en los hechos, una modernización real de la arquitectura
  de componentes (migrar a standalone/signals donde aporte) además del rediseño visual
  en sí — no es solo un retoque de estilos.

## 8. Deuda técnica y riesgos priorizados

**Crítico**

1. `encoding_facial` (dato biométrico) sin cifrar en reposo, y editable desde `/admin/`.
2. Cero enforcement de verificación de identidad al contratar/publicar.
3. Cero consentimiento explícito capturado para biometría (ni en BD ni en UI).
4. Cero endpoint de derechos del titular (acceso al dato real, portabilidad, supresión).

**Alto**

5. `media/` público y adivinable (fotos de perfil/valoraciones, incluidas no moderadas).
6. Sin EIPD, sin registro de actividades de tratamiento, sin lista de encargados formal.
7. ~~Venv local desincronizado con `requirements.txt`~~ — **resuelto en esta fase.**
8. Sin Node.js instalado — bloquea todo trabajo real de frontend. **Pendiente.**

**Medio**

9. Retención sin automatizar (`limpiar_mensajes_antiguos` no programado; sin purga de
   `IntentoAccesoSospechoso`/`TokenSesion` expirados).
10. Logs con email + IP en texto claro en algunos puntos.
11. CORS realmente abierto a todo el sitio, no solo `/api/*` como dice el comentario.
12. `Pago.respuesta_bruta` sin filtrar.

**Bajo**

13. Artefactos de huella de ejemplo committeados en git (higiene de repo).
14. `requests` no declarado en `requirements.txt` pese a usarse en `pagos.py`.
15. Accesibilidad/i18n del frontend (relevante para la Fase 6, no para cumplimiento legal).

## 9. Plan de fases

Ver `docs/plan-ajustes.md` para los ajustes de alcance propuestos a partir de este
reconocimiento — el orden y la estructura de fases del plan maestro se mantienen.

## 10. Acciones ejecutadas en esta fase

- Reinstaladas las dependencias faltantes del venv (`pip install -r requirements.txt`);
  `manage.py check` pasa limpio.
- Creadas las carpetas `docs/adr/`, `docs/legal/`, `docs/cumplimiento/`.
- Escrito este documento y `docs/plan-ajustes.md`.
- **Pendiente para el usuario o la siguiente sesión**: instalar Node.js (LTS) en esta
  máquina — bloquea cualquier trabajo sobre `codigo/frontend/ionic/`.
