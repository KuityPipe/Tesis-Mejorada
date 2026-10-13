# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**KeyServ** — Chilean services marketplace with biometric identity verification. Started as a thesis (delivered), now treated as a commercial product / portfolio piece with a 2026-27 improvement plan (Ley 21.719 data-protection compliance + Corfo application).

**Start every session by reading `docs/ESTADO_Y_PROXIMOS_PASOS.md`** (resume point, open problems, pending items per phase), then `docs/PLAN_MAESTRO_2026-27.md` (phases + status table) and `docs/plan-ajustes.md` (every scope change, dated). Phases 0–3 are done and merged to `master`; Phases 4 (unknown), 5 (bot) and 6 (frontend redesign) are pending — the original master plan text is not in the repo, so don't invent Phase 4/5 scope; ask the user for it.

**Docs policy (repo is public):** `docs/README.md` is the index. There is a single living history/resume doc (`docs/ESTADO_Y_PROXIMOS_PASOS.md`) — overwrite it at the end of a session instead of creating new logs or dated copies. Superseded docs go to `docs/archivo/`. Never commit or push without the user's explicit approval.

The previous, much longer CLAUDE.md (full narrative of Fases 1–8, Android setup, facial-recognition tuning, payments) is preserved at `docs/archivo/CLAUDE_HISTORIAL.md` — grep it when you need that detail. It predates Phases 0–3 of the current plan, so treat it as history, not as current state.

## Layout

```
codigo/backend/django/       Django project (settings in KeyServProject/, app in KeyServApp/) — default target for all work
codigo/frontend/ionic/       Ionic/Angular app (+ Capacitor android/, Playwright e2e/)
codigo/biometria/            Standalone biometric scripts; reconocimiento_facial/ is still used by Django, huella/ is a code sample only
docs/                        Engineering docs (Spanish), indexed in docs/README.md (what is current, what is public-safe). legal/ + cumplimiento/ = Ley 21.719 drafts pending lawyer review. archivo/ = superseded history, don't treat as current. academico/ (thesis) is local-only and gitignored
render.yaml, render_build.sh Render blueprint for the backend demo; codigo/frontend/ionic/netlify.toml for the frontend
venv_tesis/  TesisAntigua/   Local-only, gitignored (venv; raw backup with personal emails)
```

Legacy Django variants were deleted from the tree; recoverable via git tag `legacy-pre-fase3`.

## Commands

```powershell
# backend (PowerShell, from repo root first time)
python -m venv venv_tesis; .\venv_tesis\Scripts\Activate.ps1
pip install -r requirements.txt          # CI uses requirements-ci.txt, Render uses requirements-render.txt (both skip heavy biometrics/Transbank deps)
cd codigo/backend/django
python manage.py migrate
python manage.py runserver 8000          # API docs: /api/docs/ (Swagger), /api/schema/
python manage.py test KeyServApp         # ~340 tests, SLOW (~8 min); tests.py = template views, tests_api.py = REST API
python manage.py test KeyServApp.tests_api.RostroApiTests                       # one class
python manage.py test KeyServApp.tests.ContratacionFlowTests.test_flujo_completo_de_contratacion_y_valoracion   # one method

# frontend (needs Node; v24 installed — reopen the terminal if not on PATH)
cd codigo/frontend/ionic
npm install; npm start                   # ng serve on :8100 (must match CORS_ALLOWED_ORIGINS)
npm test                                 # Karma/Jasmine, HttpClient mocked (~82 tests); CI uses ng test --watch=false --browsers=ChromeHeadlessCI
npm run lint
npm run test:e2e                         # Playwright against the REAL app; needs backend running on :8000 with demo data (sembrar_datos_demo); web only
```

Management commands worth knowing: `loaddata catalogos_iniciales` (regions/comunas/catalog tables — required after a fresh `migrate`), `sembrar_datos_demo` (idempotent demo dataset), `configurar_grupo_moderador` (rerun after adding admin models), `descargar_geoip`, and the retention pair `limpiar_mensajes_antiguos` / `purgar_datos_vencidos`, run together by `mantenimiento_retencion` — **not scheduled anywhere yet** (Render cron is paid).

Env vars live in `codigo/backend/django/.env` (gitignored; template `.env.example` at root). Database is **PostgreSQL** (not MySQL; the thesis restriction no longer applies) and needs the `unaccent` extension (created by migration `0009`).

Android build, signed release build, and the Windows/OneDrive/JDK gotchas: see `docs/archivo/CLAUDE_HISTORIAL.md` ("Native Android build", "Known Issues"). Short version: use JDK 21 (not Android Studio's JDK 25) for Gradle, build with `gradlew.bat` directly (`npx cap run` fails here), prefer the `KeyServ_Test2` (API 35) AVD, and back up `android/app/keyserv-release.keystore` + `keystore.properties` outside the repo — losing them means no more updates under `com.keyserv.app`.

## Architecture (the parts that span several files)

**Two frontends coexist (strangler-fig migration).** Server-rendered Django templates (`views.py`, `templates/`) are being retired area by area in favor of the Ionic app talking to a DRF API at `/api/` (`KeyServApp/api/`). Template tests and API tests are deliberately separate modules; each API scenario mirrors one in `tests.py`. The Django admin (`/admin/`) stays on Django permanently.

**Auth is custom, in two layers.** `Usuario` is *not* `AUTH_USER_MODEL`.
- Templates: a lightweight session (`request.session['usuario_id']`, `decorators.login_requerido`), not `django.contrib.auth`.
- API: hand-rolled JWT (PyJWT, not simplejwt — it assumes `get_user_model()`). `api/jwt_utils.py` issues a short stateless access token + an opaque refresh token whose hash is stored in `TokenSesion` (one row per device, revocable). `api/authentication.py` sets `request.user` to a `Usuario` (which has fixed `is_authenticated`/`is_anonymous` properties just to satisfy DRF).
- **API views reuse `views.py` / `vistas_legacy` helpers and Django Forms instead of reimplementing** (login lockout via `_clave_intentos_login`, `RegistroForm`, `EditarPerfilForm`, `ReautenticacionForm`, `_recalcular_ranking`, re-auth rate limits, `Unaccent`…). A plain `Form` accepts `request.data` directly. Keep validation in one place; when you change a form/helper, both frontends change. Trade-off: drf-spectacular can't document Form-backed endpoints.
- Resources a caller doesn't own return **404, not 403**, and log an `IntentoAccesoSospechoso`.

**Identity verification (Fase 2/3, the current focus).** Three ways to count as verified, combined in `identidad.identidad_verificada()`:
1. Native device biometrics (primary): `POST /api/auth/verificar-biometria-nativa/` just trusts the authenticated JWT and sets `verificado_biometricamente` — Face ID/fingerprint never reaches the server (deliberate trust model).
2. Server-side facial recognition (secondary): a ~2s burst of frames → `biometria.py` → `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` (blink liveness via EAR, quality gate, HOG detector only — a CNN fallback was removed because it stalled the server for minutes in low light). Requires `opencv-python`/`face_recognition`/`dlib-bin`. Gated by versioned consent (`consentimiento.py`, `ConsentimientoBiometrico`; changing the text requires bumping `VERSION`; revoking deletes the vector).
3. Alternative path without biometrics (`verificacion_alternativa.py`, `VerificacionAlternativa`): accepted warning + emailed one-time code + identity document reviewed by staff. Only a superuser (not the Moderador group) can approve it in `/admin/`. API, admin and Ionic exist; the Django-template screen does not (templates are being retired).
- `Usuario.encoding_facial` is encrypted at rest (`campos.py`, Fernet, `BIOMETRIC_ENCRYPTION_KEYS` — first key encrypts, all decrypt; empty = derived from `SECRET_KEY`, acceptable only in dev/demo; losing the key loses all vectors).
- `EXIGIR_IDENTIDAD_VERIFICADA` (default **False**) makes contracting and publishing require verification. Leave off on the demo (no biometrics there); turn on only in real production.
- Data-subject rights (`derechos_titular.py`): `GET /api/auth/mis-datos/` (export) and `eliminar-cuenta` (erasure **by anonymization** — contracts/payments rows are kept for tax retention; scope pending legal validation). The legal/compliance texts are technical drafts, not lawyer-approved.

**Contracting & payments.** `Contratacion` BPMN: SOLICITADA → (provider confirms, re-enters password, may set `monto_acordado` or an `ItemPresupuesto` breakdown) CONFIRMADA → (client pays) EN_CURSO → (client completes, re-auth) COMPLETADA → rating. Every transition writes `HistorialEstadoContratacion`. One chat (`Conversacion`) per contratación. `pagos.py`: Webpay Plus (verified against Transbank's public sandbox) and Khipu (complete but never tested live — no sandbox; needs `KHIPU_API_KEY`). Payment return legs land in the Ionic app via `settings.IONIC_FRONTEND_URL`; Webpay confirm endpoint is intentionally unauthenticated (the `token_ws` is the credential); Khipu's webhook never trusts its body and re-queries Khipu.

**Uploads and privacy.** Everything uploaded passes `validators.py` (extension + byte signature + real Pillow decode), optional ClamAV (`antivirus.py`, off by default). `Documento`, chat images and review photos use the private storage in `storage.py` (`base_url=None`, served only through authenticated views) — never the public `media/`.

**Admin.** `admin.py` overrides `AdminSite.get_app_list` to group models into `_CATEGORIAS_ADMIN`; a test fails if a registered model falls into "Otros", so add new models to a category. The "Moderador" group is intentionally narrow (publications, documents, ratings, support cases, suspicious-access alerts — no users, payments, contracts, or chats). `UsuarioAdmin` shows `password`/`encoding_facial` read-only.

**Ionic app.** Pages are still NgModule-style (`standalone: false`, `bootstrapModule`); modernization to standalone/signals is Fase 6, to be done route by route. Tokens live in secure storage (`core/almacenamiento-seguro.ts`; on web it falls back to unencrypted localStorage); `Auth.inicializar()` runs as an `APP_INITIALIZER` so guards see tokens synchronously. Theme: `src/theme/variables.scss` maps the navy/teal/coral palette onto Ionic variables (dark-mode block must match `:root, :root.ios, :root.md` specificity or Ionic's own defaults win). Catalog geolocation search (`lat`/`lng`/`radio_km`, Haversine in `api/views.py`) is Ionic/API-only.

## Deployment & CI

- `.github/workflows/tests.yml`: backend (Postgres service), frontend, and e2e (seeds demo data, runs Playwright) jobs on push to `master`/`api-ionic-migration` and PRs to `master`.
- Live demo: Render `keyserv-api` (branch `master`, Oregon) + Neon Postgres (São Paulo; `DATABASE_URL` is set by hand in Render, `render.yaml` declares no database — Render's free Postgres expires) and Netlify `keyserv.netlify.app`. Status and history of this: `docs/ESTADO_Y_PROXIMOS_PASOS.md`.
- `manage.py migrate` on Render always warns about "changes not reflected in a migration": migrations `0023`/`0025`/`0028` bake the dev machine's absolute path into the private `FileSystemStorage(location=...)`. Harmless; don't re-run `makemigrations` to "fix" it (it would just re-bake the local path).

## Gotchas

- Python 3.14 / Django 5.2 (4.2's template `Context.__copy__` breaks on 3.14). `setuptools<81` is pinned because `face_recognition_models` needs `pkg_resources`; `face_recognition` is installed `--no-deps` alongside `dlib-bin`.
- The repo lives under OneDrive: Gradle builds can fail with `AccessDeniedException` on `android/app/build/` — delete that folder and rebuild.
- The backend test suite is slow; to iterate use a single class/method, not the full run.
- Legacy standalone scripts in `codigo/biometria/huella/` (`REGISTRO_BD`, `AUTENTIFICACION`, `GUARDAR_DOCUMENTO`, `CONEXION_BD`) are broken by design; the Django-side fingerprint flow was removed — only `IMAGEN_HUELLA.py` still runs standalone.
- Docs and commit messages are written in Spanish; the user-facing copy uses Chilean "tú" (not voseo).
