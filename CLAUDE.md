# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**KeyServ** — Chilean services marketplace with biometric identity verification. Started as a thesis (delivered), now treated as a commercial product / portfolio piece with a 2026-27 improvement plan (Ley 21.719 data-protection compliance + Corfo application).

**Start every session by reading `docs/ESTADO_Y_PROXIMOS_PASOS.md`** (resume point, open problems, pending items per phase), then `docs/PLAN_MAESTRO_2026-27.md` (phases + status table) and `docs/plan-ajustes.md` (every scope change, dated). The original master plan has 7 phases (0 recon, 1 data audit, 2 reinforce verification, 3 hardening, 4 visible compliance, 5 AI bot via NVIDIA NIM, 6 visual redesign, 7 quality/close); its status table, with the concrete remaining gaps per phase, is in `docs/PLAN_MAESTRO_2026-27.md` (full original text is local-only in `docs/privado/`, gitignored). Phases 0–5 and 7 are done (2026-10-12) and Fase 6 is done visually (2026-10-13); legal review, a real production environment and the Android keystore backup are deferred by the owner, and Fase 6's i18n (English), standalone/signals migration and `@defer` were left out on purpose. Working conventions decided by the owner: commit messages in Spanish, work directly on `master` (no per-phase branches; use git tags for milestones instead of a backup branch), ADRs in `docs/adr/`, and Fase 6's visual proposal was approved and implemented (`docs/fase-6/`).

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
python manage.py test KeyServApp --settings=KeyServProject.settings_test   # ~418 tests in ~25 s (MD5 hasher, tests only); without --settings it takes ~12 min because of PBKDF2. tests.py = template views, tests_api.py = REST API
python manage.py test KeyServApp.tests_api.RostroApiTests                       # one class
python manage.py test KeyServApp.tests.ContratacionFlowTests.test_flujo_completo_de_contratacion_y_valoracion   # one method

# frontend (needs Node; v24 installed — reopen the terminal if not on PATH)
cd codigo/frontend/ionic
npm install; npm start                   # ng serve on :8100 (must match CORS_ALLOWED_ORIGINS)
npm test                                 # Karma/Jasmine, HttpClient mocked (~115 tests); CI uses ng test --watch=false --browsers=ChromeHeadlessCI
npm run lint                             # 105 pre-existing `prefer-inject` errors (constructor injection); CI does not run lint
npm run test:e2e                         # Playwright against the REAL app; needs backend running on :8000 with demo data (sembrar_datos_demo); web only
```

Management commands worth knowing: `loaddata catalogos_iniciales` (regions/comunas/catalog tables — required after a fresh `migrate`), `sembrar_datos_demo` (idempotent demo dataset: 24 providers in 24 trades, local CC0 photos from the frontend `assets/fotos`, every publication carries a demo notice; API exposes `proveedor.es_demo` for `@demo.keyserv` accounts; the `admin`/`moderador` staff passwords come from the env var `DEMO_STAFF_PASSWORD` — never hardcode them, the repo is public; without it new staff accounts get a random password. Re-run it locally after changing `FOTO_POR_CATEGORIA`, it also updates already-seeded photo URLs), `configurar_grupo_moderador` (rerun after adding admin models), `probar_correo <destino>` (sends one real email and shows the SMTP error; the app's own mails use `fail_silently=True`, so a bad SMTP config otherwise fails without a trace; the demo on Render has no SMTP, so password recovery and the alternative-verification code never arrive there), `descargar_geoip`, and the retention pair `limpiar_mensajes_antiguos` / `purgar_datos_vencidos`, run together by `mantenimiento_retencion` — scheduled weekly by `.github/workflows/retencion.yml` (GitHub Actions against Neon; needs the repo secret `DATABASE_URL`; manual run defaults to dry-run).

Env vars live in `codigo/backend/django/.env` (gitignored; template `.env.example` at root). Database is **PostgreSQL** (not MySQL; the thesis restriction no longer applies) and needs the `unaccent` extension (created by migration `0009`).

Android build, signed release build, and the Windows/OneDrive/JDK gotchas: see `docs/archivo/CLAUDE_HISTORIAL.md` ("Native Android build", "Known Issues"). Short version: use JDK 21 (not Android Studio's JDK 25) for Gradle, build with `gradlew.bat` directly (`npx cap run` fails here), prefer the `KeyServ_Test2` (API 35) AVD, and back up `android/app/keyserv-release.keystore` + `keystore.properties` outside the repo — losing them means no more updates under `com.keyserv.app`.

## Architecture (the parts that span several files)

**Two frontends coexist (strangler-fig migration).** Server-rendered Django templates (`views.py`, `templates/`) are being retired area by area in favor of the Ionic app talking to a DRF API at `/api/` (`KeyServApp/api/`). Template tests and API tests are deliberately separate modules; each API scenario mirrors one in `tests.py`. The Django admin (`/admin/`) stays on Django permanently.

**Auth is custom, in two layers.** `Usuario` is *not* `AUTH_USER_MODEL`.
- Templates: a lightweight session (`request.session['usuario_id']`, `decorators.login_requerido`), not `django.contrib.auth`.
- API: hand-rolled JWT (PyJWT, not simplejwt — it assumes `get_user_model()`). `api/jwt_utils.py` issues a short stateless access token + an opaque refresh token whose hash is stored in `TokenSesion` (one row per device, revocable). `api/authentication.py` sets `request.user` to a `Usuario` (which has fixed `is_authenticated`/`is_anonymous` properties just to satisfy DRF).
- **API views reuse `views.py` / `vistas_legacy` helpers and Django Forms instead of reimplementing** (login lockout via `_clave_intentos_login`, `RegistroForm`, `EditarPerfilForm`, `ReautenticacionForm`, `_recalcular_ranking`, re-auth rate limits, `Unaccent`…). A plain `Form` accepts `request.data` directly. Keep validation in one place; when you change a form/helper, both frontends change. Trade-off: drf-spectacular can't document Form-backed endpoints.
- Resources a caller doesn't own return **404, not 403**, and log an `IntentoAccesoSospechoso`.
- **Payment data minimization:** `Pago.respuesta_bruta` stores only an allowlist of fields (`respuestas_pago.py`: status, amounts, dates, authorization codes; no card digits, payer name/email, bank or links). Always go through `respuesta_minima()` when saving a gateway response; migration `0035` scrubbed old rows.
- **Registration rules (`RegistroForm`, shared by API and templates):** RUT is normalized (`rut.py`: strips dots, adds the hyphen) and must have a valid check digit (módulo 11) and be unused; the phone is an int32 column, so it's limited to 8–9 digits (no `+56`, else Postgres overflowed into a 500). `acepta_politica` is optional in the form (the template flow has no checkbox) but **required by `POST /api/auth/registro/`**, which stores the date in `Usuario.politica_aceptada_en` (migration `0034`, hand-written like the storage-path ones: don't run `makemigrations`). The Ionic form mirrors the RUT rule in `core/rut.ts`.

**Identity verification (Fase 2/3, the current focus).** Three ways to count as verified, combined in `identidad.identidad_verificada()` — which also requires the verification to be **recent** (`settings.IDENTIDAD_VIGENCIA_DIAS`, default 180; `Usuario.verificado_en` / `VerificacionAlternativa.revisado_en`):
1. Native device biometrics (primary): `POST /api/auth/verificar-biometria-nativa/` just trusts the authenticated JWT and sets `verificado_biometricamente` — Face ID/fingerprint never reaches the server (deliberate trust model).
2. Server-side facial recognition (secondary): a ~2s burst of frames → `biometria.py` → `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` (blink liveness via EAR, quality gate, HOG detector only — a CNN fallback was removed because it stalled the server for minutes in low light). Requires `opencv-python`/`face_recognition`/`dlib-bin`. Gated by versioned consent (`consentimiento.py`, `ConsentimientoBiometrico`; changing the text requires bumping `VERSION`; revoking deletes the vector).
3. Alternative path without biometrics (`verificacion_alternativa.py`, `VerificacionAlternativa`): accepted warning + emailed one-time code + identity document reviewed by staff. Superusers and the Moderador group can approve it in `/admin/` (decision 2026-10-12); every review records `revisado_por`/`revisado_en` and the admin dashboard shows a KPI/panel of requests pending review. API, admin and Ionic exist; the Django-template screen does not (templates are being retired).
- `Usuario.encoding_facial` is encrypted at rest (`campos.py`, Fernet, `BIOMETRIC_ENCRYPTION_KEYS` — first key encrypts, all decrypt; empty = derived from `SECRET_KEY`, acceptable only in dev/demo; losing the key loses all vectors).
- `EXIGIR_IDENTIDAD_VERIFICADA` (default **False**) makes contracting and publishing require verification. Leave off on the demo (no biometrics there); turn on only in real production.
- Every verification attempt/change writes an `EventoVerificacion` via `verificaciones.py` (who/when/method/result, **never biometric data**; purged after 365 days). Key rotation: `manage.py rotar_llaves_biometricas` (guide in `docs/cumplimiento/rotacion-de-llaves.md`).
- Data-subject rights (`derechos_titular.py`): `GET /api/auth/mis-datos/` (export), `eliminar-cuenta` (erasure **by anonymization** — contracts/payments rows are kept for tax retention; scope pending legal validation), `POST /api/auth/derechos/` (rectification / opposition → `SolicitudTitular`, 30-day deadline, surfaced on the superuser dashboard; biometric opposition applies instantly) and `POST /api/auth/bloqueo-tratamiento/` (reversible block: hidden from the catalog, cannot publish or contract; API/Ionic only). See ADR 0004. The legal/compliance texts are technical drafts, not lawyer-approved.

**AI assistant (Fase 5, ADR 0005).** `asistente.py` + `POST /api/asistente/` (public, rate-limited per user/IP) + `shared/asistente` floating widget in Ionic. The model never sees account data: it gets fixed FAQ text, the **masked** chat history (`enmascarar_datos_personales`: RUT, email, phone, long numbers) and public catalog hits that the server searches itself. Provider is any OpenAI-compatible API via `LLM_BASE_URL`/`LLM_API_KEY` (or `NVIDIA_API_KEY`)/`LLM_MODEL`; with no key or on provider failure it falls back to a guided keyword flow. Never log message content; never send biometrics, images or account data to it.

**Contracting & payments.** `Contratacion` BPMN: SOLICITADA → (provider confirms, re-enters password, may set `monto_acordado` or an `ItemPresupuesto` breakdown) CONFIRMADA → (client pays) EN_CURSO → (client completes, re-auth) COMPLETADA → rating. Every transition writes `HistorialEstadoContratacion`. One chat (`Conversacion`) per contratación. `pagos.py`: Webpay Plus (verified against Transbank's public sandbox) and Khipu (complete but never tested live — no sandbox; needs `KHIPU_API_KEY`). Payment return legs land in the Ionic app via `settings.IONIC_FRONTEND_URL`; Webpay confirm endpoint is intentionally unauthenticated (the `token_ws` is the credential); Khipu's webhook never trusts its body and re-queries Khipu.

**Uploads and privacy.** Everything uploaded passes `validators.py` (extension + byte signature + real Pillow decode), optional ClamAV (`antivirus.py`, off by default). `Documento`, chat images and review photos use the private storage in `storage.py` (`base_url=None`, served only through authenticated views) — never the public `media/`.

**Admin.** `admin.py` overrides `AdminSite.get_app_list` to group models into `_CATEGORIAS_ADMIN`; a test fails if a registered model falls into "Otros", so add new models to a category. The "Moderador" group is intentionally narrow (publications, documents, ratings, support cases, suspicious-access alerts, identity-verification reviews — no users, payments, contracts, or chats). `UsuarioAdmin` shows `password`/`encoding_facial` read-only.

**Ionic app layout system (Fase 6, `docs/fase-6/`).** Width/section helpers live in `src/global.scss`: `ks-content-wide` (1200px), `ks-content-cols` (2-column CSS **grid** on `ion-content`'s scroll part from 900px — multi-column overflowed horizontally because the scroll part has a fixed height; `ks-span-all` spans both, `ks-fila-doble` spans two rows, `ks-chat-lateral` is the sticky chat column of the contract detail), `ks-layout-main-side` (main + sticky side column), `ks-bento`, `ks-auth` (brand panel + form), `ks-form-grid`. Shared pieces: `app-verificacion-lateral`, `app-auth-aside`, `app-verif-exito`, `app-asistente`, `app-pub-card` (catalog card with hover preview, or `modo="fila"` list row; adapts via container queries), `app-paginador` (numbered pager, 20 per page — used by Servicios and Mis contrataciones), `app-tema-toggle` (sun/moon in every header), `app-contacto-seccion`, and an `img` error directive. "Acerca de nosotros" and "Contacto" are sections (`#acerca`, `#contacto`) of the home page, not routes (the old URLs redirect); header/footer links go through `shared/desplazamiento.ts`. The header colour bar follows scroll progress (`--ks-barra-x`, set in `app.component.ts`). Editorial look inspired by ideve.cl lives at the end of `global.scss` (display font Bricolage Grotesque, outlined words, split section titles, watermark). Brand teal for buttons is `#0C7F6D` (AA contrast); the vivid `#12A38C`/coral are decoration only. Backup of the pre-redesign look: git tag `pre-rediseno-fase-6`.

**Ionic app: public files and locale.** `src/publico/` is copied to the site root by `angular.json` (robots.txt, sitemap.xml, manifest, icons, og-image); security headers live in `netlify.toml`. The app runs with `LOCALE_ID = es-CL` (`registerLocaleData` in `app.module.ts`), so `number`/`date` pipes give `$25.000` and `13/10/2026`. Every route has a `title` (`<Page> · KeyServ`) and unknown URLs land on `no-encontrado` (`path: '**'`, keep it last in `app-routing.module.ts`). The privacy policy is an Ionic page (`/privacidad`); the Django `/privacidad/` template still exists (Play Store link) and its text must be kept in sync.

**Ionic app.** Pages are still NgModule-style (`standalone: false`, `bootstrapModule`); modernization to standalone/signals was left out of Fase 6 on purpose (risk) and remains optional, route by route. Tokens live in secure storage (`core/almacenamiento-seguro.ts`; on web it falls back to unencrypted localStorage); `Auth.inicializar()` runs as an `APP_INITIALIZER` so guards see tokens synchronously. Theme: `src/theme/variables.scss` maps the navy/teal/coral palette onto Ionic variables (dark-mode block must match `:root, :root.ios, :root.md` specificity or Ionic's own defaults win). Catalog geolocation search (`lat`/`lng`/`radio_km`, Haversine in `api/views.py`) is Ionic/API-only.

## Deployment & CI

- `.github/workflows/tests.yml`: backend (Postgres service), frontend, and e2e (seeds demo data, runs Playwright) jobs on push to `master` and PRs to `master`.
- Live demo: Render `keyserv-api` (branch `master`, Oregon) + Neon Postgres (São Paulo; `DATABASE_URL` is set by hand in Render, `render.yaml` declares no database — Render's free Postgres expires) and Netlify `keyserv.netlify.app`. Status and history of this: `docs/ESTADO_Y_PROXIMOS_PASOS.md`.
- `manage.py migrate` on Render always warns about "changes not reflected in a migration": migrations `0023`/`0025`/`0028` bake the dev machine's absolute path into the private `FileSystemStorage(location=...)`. Harmless; don't re-run `makemigrations` to "fix" it (it would just re-bake the local path).

## Gotchas

- Python 3.14 / Django 5.2 (4.2's template `Context.__copy__` breaks on 3.14). `setuptools<81` is pinned because `face_recognition_models` needs `pkg_resources`; `face_recognition` is installed `--no-deps` alongside `dlib-bin`.
- The repo lives under OneDrive: Gradle builds can fail with `AccessDeniedException` on `android/app/build/` — delete that folder and rebuild.
- Always run backend tests with `--settings=KeyServProject.settings_test` (swaps PBKDF2 for MD5; 12 min → 25 s, same ~418 tests). Never use that settings module outside tests.
- Legacy standalone scripts in `codigo/biometria/huella/` (`REGISTRO_BD`, `AUTENTIFICACION`, `GUARDAR_DOCUMENTO`, `CONEXION_BD`) are broken by design; the Django-side fingerprint flow was removed — only `IMAGEN_HUELLA.py` still runs standalone.
- Docs and commit messages are written in Spanish; the user-facing copy uses Chilean "tú" (not voseo).
- Most source files are **CRLF** (Windows checkout): when editing with scripts, normalize `\r\n` → `\n`, edit, and write back with `\r\n` (an exact-match edit on `\n` text silently fails otherwise). The Bash tool also chokes on heredocs that contain apostrophes in quoted CSS/TS; write such files with the Write tool.
- Visual checks: `playwright-core` from `codigo/frontend/ionic/node_modules` works headless against `:8100` / `:8000` (login with the `@demo.keyserv` accounts, password `Demo1234`) and against the live demo; the Chrome extension is optional.
- Netlify does **not** build a commit that leaves `codigo/frontend/ionic` untouched ("Canceled build due to no content change" is normal); Render only redeploys when `codigo/backend/django/**`, `requirements-render.txt` or `render_build.sh` change. Render also creates GitHub "environments" named `<branch> - <service>`; they are harmless and can be deleted.
- Don't use `git stash` to compare lint baselines in a dirty tree with untracked files: it is easy to lose track; use a clean checkout instead.

## Session log — 2026-10-13/14 (what was done, in order)

Everything below is on `master` (last commit `f075ac9`); details and open items live in `docs/ESTADO_Y_PROXIMOS_PASOS.md`.

1. **Deploy verification.** Render `keyserv-api` deploys `master` (checked: `/api/auth/mis-datos/` → 401); Netlify production branch is `master`. The old `api-ionic-migration - keyserv-*` GitHub environments were deleted and the branch was dropped from `tests.yml`. `NVIDIA_API_KEY` is loaded in Render (`POST /api/asistente/` answers `origen=ia`); the repo secret `DATABASE_URL` works (retention workflow green).
2. **Security.** Admin/moderator passwords were public in the README and the seed: removed, now `DEMO_STAFF_PASSWORD` (set in Render; the old `KeyServ2026!` no longer works).
3. **Visual work (Ionic).** Hero with a tools photo (`hero-oficios.jpg`, CC0) and own photos for Fotografía/Mecánica/Contabilidad (`docs/CREDITOS_IMAGENES.md`); README screenshots retaken from the live demo; "Acerca de nosotros" carousel redone (theme panel + card list, arrows next to the dots, mouse drag, swipe, keyboard, height follows the active slide); "Mi cuenta" in two balanced columns (recent jobs, provider block, last payments, identity verification, tips) with the footer pinned to the bottom (`ks-pie-abajo`); privacy policy as an Ionic page (`/privacidad`, scroll-spy index, animated cards); registration redone (3-step tracker, cards, account-type picker, location summary, password strength, RUT/phone format hints). The home page's contact section (`contacto-seccion`) is a short form (name, email, optional phone appended to the message, subject, message) next to a full-height map with a floating address/contact card; both columns have the same height so no empty space is left. Section 05 (`.ks-prov`, providers) is a photo panel with perks and three steps; keep the gaps between home sections tight (`ks-seccion-prov` / `ks-seccion-cto`) so only the page background never shows between them.
4. **Audit of 20 screens (web + mobile) and fixes.** Phone with `+56` caused a 500 (int32 column) → validated 8–9 digits; RUT check digit + uniqueness (`rut.py`, `core/rut.ts`); required privacy-policy checkbox stored as `politica_aceptada_en` (migration `0034`); 404 page; per-route titles; `es-CL` locale; `robots.txt`/`sitemap.xml`/manifest/icons/Open Graph in `src/publico/`; security headers in `netlify.toml`.
5. **Corfo/business decisions (owner).** Applies as a natural person (Corfo helps with the paperwork if awarded); revenue = 3–5 % commission on each paid service (ads / paid featured listings per category and zone are a later idea); edge = fast, safe payment with verified identity and, if viable, invoices/IVA to the SII. Owner still has to: run the Google Forms survey with real people (employment/informality metrics), build the budget and assumptions, decide on team/advisers and pay a lawyer for the legal review. Neon stays in São Paulo (latency accepted).
6. **Still open (needs an owner decision or external input):** real SMTP (password recovery and the alternative-verification code only print to the console in the demo), Terms and Conditions page (needs legal text), email verification at sign-up, a full CSP on Netlify, the `0 fotos de tu rostro` wording vs. the ID-document path, the policy's "agosto de 2026" date and its duplicate Django copy (Play Store link), and the lint debt.
