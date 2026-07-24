# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KeyServ** — a Chilean services marketplace platform with biometric authentication (fingerprint + facial recognition). Built as a thesis project by a team (Felipe, OmaryLuis, luchoo23); the thesis has since been delivered and the project is being treated as a commercial product going forward.

## Repository Layout

The repo root was reorganized (Fase 1) out of a flat, ad-hoc layout into:

```
docs/                        docs/nuevo (active thesis text), docs/plantilla (thesis PDF), docs/viejo (empty, future) — plus all Fase 2/3 analysis and reference docs
codigo/
  backend/django/            Canonical Django app (formerly Tesis/) — see "Active Project" below
  biometria/huella/          Formerly BackHuella/ (fingerprint pipeline, now importable)
  biometria/reconocimiento_facial/  Formerly probando_face_recognition/ (rewritten, was corrupted)
  viejo/ProyectoDjango/      Legacy Django variant (superseded, kept for reference)
  viejo/ProyectoKeyServ/     Legacy Django variant (empty scaffold, superseded)
  viejo/backup_fase3/        Pre-Fase-3 versions of every refactored file (models.py, views.py, urls.py, admin.py, settings.py, migration, biometric scripts)
  database/                  README + (once Postgres is available) a schema.sql reference — the real schema lives in Django migrations
assets/mockups/pag_html/     Formerly Pag/ — original static HTML prototype (superseded by codigo/backend/django templates)
assets/imagenes/, assets/diagramas/   Empty scaffolds for future assets
.sistema/cache/, logs/, config/       Empty scaffolds for future cache/log/config output
```

Not moved (stay at repo root): `venv_tesis/` (active dev virtualenv — moving it would break its absolute activation paths), `TesisAntigua/` (untracked raw GitHub export/backup containing personal emails; gitignored, not part of the codebase), `CLAUDE.md`. `NuevoLogo.png` and `ImagenConcepto.png` (new Fase 5 brand assets) also landed at the repo root instead of the `assets/imagenes/` scaffold that exists for exactly this — not cleaned up yet, low priority.

A root `.gitignore` was added (Fase 1) and all previously-committed virtualenvs and `__pycache__`/`*.pyc` files were untracked — they still exist on disk but are no longer version-controlled. `.sistema/cache/*` is also gitignored (regenerable scratch output, e.g. PDF text extractions). `codigo/backend/django/media/` (user-uploaded files — publication images/documents) is gitignored as of Fase 5, since it can contain real personal documents uploaded while testing.

## Active Project

There are three Django project variants (`codigo/viejo/ProyectoDjango/`, `codigo/viejo/ProyectoKeyServ/`, `codigo/backend/django/`). **`codigo/backend/django/` is the canonical, most complete version** (formerly `Tesis/`) and should be the default target for all work.

**Database engine changed in Fase 3: PostgreSQL, not MySQL.** The thesis's "MySQL + AWS" restriction only applied to the academic deliverable — the user confirmed it doesn't bind the commercial product going forward. See `docs/RECOMMENDED_ARCHITECTURE.md` for the reasoning.

## Commands

### Environment Setup

```powershell
# Activate virtual environment (Python 3.14 / Windows)
.\venv_tesis\Scripts\Activate.ps1

# Install dependencies (requirements.txt exists as of Fase 3)
pip install -r requirements.txt

# .env already exists at codigo/backend/django/.env (gitignored) — to recreate from scratch:
Copy-Item .env.example codigo\backend\django\.env
```

`venv_tesis` has **Django==5.2.16** (upgraded from 4.2.1 in Fase 4 — see below), django-environ, psycopg2-binary, and Pillow installed and verified (`manage.py check`/`makemigrations`/`migrate`/`test` all run clean). `opencv-python`/`face_recognition` (facial recognition) and `fpdf2` are listed in `requirements.txt` but not installed in this environment — they're heavy and only needed to exercise that specific feature.

**Why Django 5.2 and not 4.2.1** (the version the thesis originally used): Django 4.2's template `Context.__copy__` is incompatible with Python 3.14's `copy.copy()` — every `manage.py test` request that renders a template crashes with `AttributeError: 'super' object has no attribute 'dicts'`. Tried the latest 4.2 LTS patch (4.2.30) first — still broken. 5.2 LTS fixes it cleanly; no application code needed to change. The user explicitly said feel free to change Django/Python versions if it makes things run better/more compatible — don't treat 4.2.1 as sacred. See `docs/FASE4_LOG.md`.

### Django (main app — run from `codigo/backend/django/`)

```powershell
cd codigo/backend/django
python manage.py migrate
python manage.py runserver 8000
python manage.py createsuperuser
python manage.py test KeyServApp   # 91 tests, all passing
python manage.py test KeyServApp.tests.ContratacionFlowTests            # single test class
python manage.py test KeyServApp.tests.ContratacionFlowTests.test_flujo_completo_de_contratacion_y_valoracion  # single test method

# Fase 5 management commands
python manage.py configurar_grupo_moderador          # (re)creates the "Moderador" admin group + scoped permissions — rerun after adding models that moderators should/shouldn't see
python manage.py limpiar_mensajes_antiguos            # deletes chats for jobs closed 90+ days ago, never exported (--dias N, --dry-run)

# Fase 6 management commands
python manage.py descargar_geoip                      # downloads the local DB-IP City Lite database used to geolocate IntentoAccesoSospechoso entries (see Security hardening below)
```

**PostgreSQL is installed and running** — see "Database" below. `migrate` has been run for real, not just validated dry.

### Biometric scripts (standalone, importable)

```powershell
python codigo/biometria/huella/IMAGEN_HUELLA.py                              # Fingerprint pipeline (runs standalone, no hardware needed)
python codigo/biometria/reconocimiento_facial/probando_face_recognition.py   # Facial recognition (requires webcam + opencv-python/face_recognition)
```

Both are now proper importable modules (`procesar_huella()` / `cargar_rostro_conocido()`+`verificar_rostro()`) wired into the Django app via `codigo/backend/django/KeyServApp/biometria.py`, instead of top-level scripts. `AUTENTIFICACION.py`, `REGISTRO_BD.py`, `GUARDAR_DOCUMENTO.py`, `CONEXION_BD.py` remain legacy/deprecated Flask+CLI scripts — see Known Issues.

### Database

PostgreSQL, credentials via environment variables (`.env`, see `.env.example`) — no longer hardcoded in `settings.py`. `codigo/backend/django/KeyServApp/migrations/` was regenerated from scratch against the corrected models in Fase 3 (the old MySQL-era migration is backed up in `codigo/viejo/backup_fase3/`); Fase 5 added incremental migrations `0002`–`0007` on top (chat-per-job fields, `HistorialEstadoContratacion`, `Consulta`/`EstadoConsulta` wiring, publication moderation audit fields).

**PostgreSQL 17 is installed and running** as a Windows service (`postgresql-keyserv`, data dir `C:\pgsql\data`, port 5432) — installed via the portable binaries zip since the official graphical installer failed in this non-interactive environment. `manage.py migrate` has been run against it (all tables exist for real), and the full register→login→ajax-comunas flow was verified end-to-end with a real HTTP request.

**Catalog data is loaded for real**: `KeyServApp/fixtures/catalogos_iniciales.json` (16 Chilean regions, 330 comunas, the 4 real `TipoCuenta` tiers, plus `TipoFirma`/`EstadoAutentificacion`/`EstadoDocumento`) — extracted from an old MySQL dump (`notpaper3`) the user had outside the repo, loaded via `manage.py loaddata catalogos_iniciales`. Deliberately excluded from that import: the dump's `usuario`/`autentificacion`/`documento`/`publicaciones`/`transaccion` rows — throwaway test/dummy data with SHA-256-without-salt password hashes incompatible with the Fase 3 PBKDF2 hasher.

**The dev database is seeded with realistic demo data (Fase 5)**: 12 users, 8 publications across 8 categories, 10 contracts (all 4 states), 14 messages, 6 ratings, 4 support incidents. Demo logins: `admin`/`KeyServ2026!` (superuser), `moderador`/`Moderador2026!` (Moderador group), `cliente.demo@demo.keyserv`/`Demo1234`, `marcelo.gasfiteria@demo.keyserv`/`Demo1234` (and other demo providers/clients on the same password — this data lives only in the local Postgres instance, not in fixtures/migrations, so it doesn't reproduce on a fresh `migrate`).

**`KeyServApp/tests.py` has 91 automated tests** (Fase 4 — was the empty `startapp` stub before; grew through Fase 5/6 security hardening, the `editar_perfil`/`recuperar`/pagination fixes, payments, and the budget-breakdown feature) covering password hashing, registration, login, `load_comunas`, biometria imports, publication moderation, the full contracting flow (request → confirm with re-auth and optional `monto_acordado` override or itemized `ItemPresupuesto` breakdown → pay → complete with re-auth → rate → ranking recalculation), messaging with access control, file-upload validation, suspicious-access logging, the provider toggle, real profile editing, password recovery via signed token, catalog pagination, and Webpay/Khipu payment views (with `TransbankService`/`KhipuService` mocked — the real Transbank SDK call was verified manually against the live integration sandbox instead, see Payments below). Run with `manage.py test KeyServApp`. No new tests were added for the admin roles/moderation dashboard/status history/incidents surface of Fase 5 — see Known Issues.

## Architecture

### Component Map

```
assets/mockups/pag_html/    Static HTML frontend prototype (no framework), superseded by Django templates

codigo/backend/django/      Main Django project
  ├── KeyServProject/       Settings (env-var driven), WSGI, root URL conf (DB: PostgreSQL)
  └── KeyServApp/
      ├── models.py         ~25 ORM models incl. real ForeignKeys, Contratacion, HistorialEstadoContratacion (see Data Model section)
      ├── views.py          Auth (real), publicaciones/contrataciones/valoraciones, chat-per-job, biometric + payment integration points
      ├── forms.py          Registro/Login/Publicacion/Valoracion forms with validation
      ├── decorators.py     `login_requerido` — custom session auth (not django.contrib.auth's user model)
      ├── context_processors.py  Injects `usuario_actual` + unread-message count into every template (custom session, not django.contrib.auth)
      ├── biometria.py      Bridges Django views to codigo/biometria/* scripts
      ├── pagos.py          TransbankService (Webpay Plus, real — tested live against Transbank's public integration sandbox) + KhipuService (transferencia bancaria, code complete but untestable until a real Khipu account exists — no public sandbox)
      ├── validators.py     Byte-signature + extension whitelist + a real Pillow decode for every uploaded image/document (Django's ImageField alone only checks that Pillow can open the file)
      ├── antivirus.py      Optional ClamAV (clamd) scan hook for uploads — off by default (`CLAMAV_HABILITADO=False`), fails open (logs, doesn't block) if the daemon is down
      ├── geolocalizacion.py  Approximate IP geolocation for IntentoAccesoSospechoso via a local DB-IP City Lite database, no third-party lookups (`manage.py descargar_geoip`)
      ├── storage.py        Private `FileSystemStorage` (`base_url=None`) for Documento — forces every read through `documento_descargar_view` instead of a guessable public URL
      ├── admin.py          All models registered; scoped visibility for the "Moderador" group + superuser-only LogEntry audit; overrides `AdminSite.get_app_list` to group ~25 models by task (see Admin & moderation below) instead of Django's default flat per-app list
      ├── management/commands/   `configurar_grupo_moderador`, `limpiar_mensajes_antiguos`, `descargar_geoip` (see Commands)
      ├── static/KeyServApp/css/base.css   Unified design system (navy/teal/coral palette, Quicksand/Nunito) — all templates extend base.html
      ├── templates/admin/   Overrides `index.html`/`base_site.html` to add the pending-approvals dashboard (`_panel_aprobaciones.html`)
      └── urls.py           ~37 routes — every template has a URL

codigo/biometria/huella/    Fingerprint pipeline — IMAGEN_HUELLA.py is a real, working, importable module.
  ├── IMAGEN_HUELLA.py      procesar_huella(): binarize → thin → prune → hash, callable from Django
  ├── AUTENTIFICACION.py    LEGACY — SMTP creds now from env vars, but still CLI/input()-based and depends on the broken CONEXION_BD.cur chain
  ├── REGISTRO_BD.py        LEGACY — broken (see Known Issues), superseded by Django's register_view
  ├── CONEXION_BD.py        LEGACY — its /regiones,/comunas API is redundant with Django's /ajax/load-comunas/
  └── GUARDAR_DOCUMENTO.py  LEGACY — broken, uses a blocking tkinter dialog unsuitable for a server

codigo/biometria/reconocimiento_facial/
  └── probando_face_recognition.py  Rewritten as a valid module: cargar_rostro_conocido()/verificar_rostro() — untested against real hardware in this environment
```

### Data Flow

**User registration:** HTML form → Django `/registro/` → `RegistroForm` validation → `Usuario.set_password()` (PBKDF2 via `django.contrib.auth.hashers`) → PostgreSQL

**Login/logout:** `/sesion/` validates credentials via `Usuario.check_password()` and sets `request.session['usuario_id']` — a custom lightweight session, not `django.contrib.auth`'s login system (see `docs/API_DOCUMENTATION.md` "Notas sobre autenticación"). A real bug fixed in Fase 5: the `sesion.html` template used to submit `username`/`password` fields while `LoginForm` expected `email`/`password`, so login via the UI never actually worked before this session — only the raw view/form did.

**Fingerprint verification:** `/huella/verificar/` → `KeyServApp/biometria.py` → `IMAGEN_HUELLA.procesar_huella()` → SHA-256 hash → marks `Usuario.verificado_biometricamente` (TODO: doesn't yet compare against a stored reference hash).

**Facial recognition:** skeleton only — `verificar_rostro_usuario()` exists but is unwired from any view and untested (no webcam in this environment).

**Publications & moderation:** `Publicaciones.estado_moderacion` gates visibility on `/servicios/` (the catalog, split from the home page in Fase 5 — `/` is now marketing/quick-search, `/servicios/` is the full filterable listing with region/rating/order filters). Publications carry a real `categoria` (predefined list + free-text "Otra") and real uploaded image/document files (Pillow) rather than seeded URLs. Approval leaves an audit trail — `aprobado_por` + `fecha_moderacion` autofill on save, never set by hand. `publicacion_detalle_view` renders an image carousel with clickable thumbnails plus a documents/certifications panel (the model always supported multiple images/documents, it just wasn't rendered before Fase 6). Catalog search (`catalogo_view`) matches `titulo`/`sub_titulo`/`categoria` ignoring accents via Postgres's `unaccent` extension (migration `0009_unaccent_extension`, wrapped in the `Unaccent` `Func` in `views.py`) — most people don't type tildes into a search box.

**Security hardening (Fase 6):** Every uploaded image/document passes through `validators.py` (extension whitelist + byte-signature check + a real Pillow decode, not just "Django could open it") before an optional `antivirus.py` ClamAV scan (off by default in this dev environment). `IntentoAccesoSospechoso` logs any attempt to reach a conversation/contract/document that isn't the requester's, or a brute-force lockout on login/re-authentication/fingerprint verification — including attempts from sessions with no logged-in user at all — with an approximate IP geolocation attached via a local DB-IP City Lite database (`geolocalizacion.py`, downloaded with `manage.py descargar_geoip`; degrades to `(None, None)` if the database isn't present or `GEOIP_HABILITADO=False`), surfaced as an alert in the admin dashboard (attribution footer required by DB-IP's CC-BY license). Identity documents (`Documento`) live in `storage.py`'s private `FileSystemStorage` (`base_url=None`, outside `MEDIA_ROOT`) and are only ever served through the authenticated `documento_descargar_view`. Other real fixes from the same pass: session IDs are cycled on login (session-fixation fix), login/re-auth are rate-limited per (user, action) via the cache, the minimum password length went from 6 to 8 chars reusing `AUTH_PASSWORD_VALIDATORS`, fingerprint verification used to accept a client-supplied file *path* as plain text and pass it straight to `Image.open()` (arbitrary file read) and now requires a real upload, and `/registro/`/`/sesion/` now reject an already-logged-in session instead of silently re-processing it. `SECURE_HSTS_*`/`SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE` activate automatically once `DEBUG=False`, and `/admin/`'s URL is configurable via an env var.

**Contracting (Fase 4/5, payment gate added Fase 6):** `Contratacion` model + full BPMN flow — `contratacion_crear_view` (SOLICITADA, notifies the provider via an auto-created `Conversacion`+`Mensaje`) → `contratacion_confirmar_view` (provider, requires re-entering password, → CONFIRMADA) → **client pays** (`pago_webpay_iniciar_view`/`pago_khipu_iniciar_view`, → EN_CURSO once approved) → `contratacion_completar_view` (client, requires re-entering password, now requires EN_CURSO instead of CONFIRMADA, → COMPLETADA) → `valoracion_crear_view`. Every state transition is recorded in `HistorialEstadoContratacion` with a real timestamp. `contratacion_detalle_view` is a per-job page combining the embedded chat, a 4-step status timeline (Solicitada/Confirmada/Pagada-en curso/Completada), the payment buttons when applicable, and the publication's image gallery. A real bug fixed in Fase 6: a client could re-request the same publication while an earlier request to it was still open — `contratacion_crear_view` now blocks that.

**Ratings:** `valoracion_crear_view` is embedded in `contratacion_detalle.html` as an interactive star picker (Fase 6 — previously a separate generic form page) and only reachable once a `Contratacion` is COMPLETADA. Attached photos (`ValoracionImagen`) go through the same `validators.py` checks as publication images and start `PENDIENTE` moderation — the whole review, not just its photos, is held from public view and excluded from `_recalcular_ranking`'s aggregate until a moderator approves it in `/admin/`.

**Messaging (Fase 4, redesigned in Fase 5):** `Conversacion` is now 1:1 with a `Contratacion` ("chat per job") instead of 1:1 with a pair of users — previously messages from unrelated contracts between the same two people bled into a single thread. `chat_view`/`conversacion_detalle_view` list conversations and view/send messages, access restricted to participants (verified with a third "intruder" user in tests). Conversations can be exported to a `.txt` backup (`conversacion_exportar_view`); `manage.py limpiar_mensajes_antiguos` purges chats for closed jobs after 90 days, but exporting a chat sets `exportado_en` and permanently exempts it from that purge. Near-real-time notifications: the header polls `/ajax/mensajes-no-leidos/` every 15s and plays a Web Audio beep (no external sound file) when the unread badge increases.

**Admin & moderation (Fase 5, reorganized Fase 6):** A native Django "Moderador" group (Groups/Permissions, not a custom role system — see `configurar_grupo_moderador.py`) can view/change publications, incidents (`Consulta`), and documents, and view (not change) contracts/history/messaging/ratings; it cannot see `Usuario`, payments, or other sensitive/infrastructure tables — Django's admin simply omits models with no granted permission. `/admin/` has a custom `index.html` showing a pending-approvals dashboard (unmoderated publications + open incidents). `LogEntry` (Django's native audit log) is registered but restricted to `is_superuser`. Contract start timestamps are `readonly_fields` (visible, immutable) in the admin. Fase 6 replaced Django's default single flat "Keyservapp" block (~25 models in one undifferentiated list) with a task-based grouping — `admin.py` overrides `AdminSite.get_app_list` to bucket models into `_CATEGORIAS_ADMIN` (Solicitudes y moderación / Seguridad / Mensajería / Usuarios y cuentas / Catálogos de referencia / Finanzas e infraestructura / Auditoría; anything unclassified falls into an "Otros" catch-all instead of silently vanishing) without touching any model registration or permission.

**Support:** `/contacto/` now writes to the real `Consulta` model (part of the original thesis schema but unused until Fase 5) instead of being a static page; moderators triage these via `/admin/`.

**Payments (Fase 6):** Real integration, two methods chosen with the user (not Transbank alone — combination picked after researching Chilean gateways): **Webpay Plus** (`pagos.TransbankService`, `transbank-sdk`) for cards, and **Khipu** (`pagos.KhipuService`, plain `requests` — no third-party SDK, since Khipu's public docs had conflicting info on the exact auth scheme and a small in-house client keeps that a one-line fix if wrong) for direct bank transfer. `Publicaciones.precio` (new, migration `0018`) is only a starting reference — client and provider can agree on a different amount over chat before the provider confirms, so `Contratacion.monto_acordado` (new, migration `0020`, set in `contratacion_confirmar_view` from an optional `monto` field next to the re-auth password, defaulting to `publicacion.precio` if left blank or invalid) is what actually gets charged; `publicacion.precio` is never read again after confirmation. The `Pago` model (migration `0019`) tracks each attempt (`metodo`, `estado`: PENDIENTE/PAGADO/RECHAZADO/ANULADO, raw response for audits). Webpay: `pago_webpay_iniciar_view` creates the transaction and renders an auto-submitting form (Transbank's protocol needs a POST of `token_ws` to their URL, not a plain redirect); `pago_webpay_retorno_view` accepts both GET and POST for the return (observed live against the sandbox that Transbank's redirect actually arrives as GET with `token_ws` as a query param, despite docs describing POST) and handles all three cases (`token_ws` approved/declined, `TBK_TOKEN` user-cancelled, neither = timeout). Khipu: `pago_khipu_iniciar_view` redirects to Khipu's hosted payment page; `pago_khipu_notificacion_view` is the webhook (never trusts the webhook body — always re-queries Khipu's `/payments/{id}` before marking anything paid, per Khipu's own guidance); `pago_khipu_retorno_view` double-checks on the user's way back too, for UX (in case the webhook hasn't landed yet). **Webpay was verified end-to-end live** against Transbank's public integration sandbox (no merchant account needed — the SDK ships public test credentials) — a real approved transaction was completed via the actual bank-simulator pages and the `Contratacion` correctly advanced to EN_CURSO. **Khipu could not be tested** — unlike Transbank, Khipu has no public sandbox; it requires a real account (`KHIPU_API_KEY` from khipu.com's dashboard) that only the project owner can create. Without it, `KhipuService` raises a clear `RuntimeError` instead of failing silently or crashing with a 500.

### Key Data Models (`codigo/backend/django/KeyServApp/models.py`)

See `docs/DATABASE_DOCUMENTATION.md` for the complete table/relationship reference (predates Fase 5+ additions below — treat it as a base, not exhaustive). Notable additions: `Contratacion`, `Usuario.es_proveedor`/`Usuario.verificado_biometricamente`, `Publicaciones.estado_moderacion` (Fase 3); `HistorialEstadoContratacion`, `Publicaciones.aprobado_por`/`fecha_moderacion`, `Conversacion` now FK'd to `Contratacion` instead of a user pair, `Conversacion.exportado_en` (Fase 5); `Usuario.foto_perfil`, `IntentoAccesoSospechoso`, `ValoracionImagen.estado_moderacion` (Fase 6, security hardening); `Publicaciones.precio`, `Pago` (Fase 6, payments).

**`ItemPresupuesto` (budget breakdown, uncommitted as of this writing):** a free-form, optional line-item budget breakdown a provider can attach when confirming a `Contratacion` — materials/labor/travel/other — whose sum then replaces the single `monto_acordado` field if any valid rows are submitted, plus `settings.COMISION_PLATAFORMA_PORCENTAJE` (a purely informational platform-commission percentage shown next to it, doesn't actually deduct anything). Wired into `models.py`, `admin.py` (read-only inline on `ContratacionAdmin`), `views.py` (`_parsear_items_presupuesto`, `contratacion_confirmar_view`, `contratacion_detalle_view`), and `contratacion_detalle.html`; migration `0021_itempresupuesto` and 7 tests (`ItemPresupuestoTests`) were added. Still just working-tree changes, not a commit — check `git status`/`git diff` before assuming this shipped.

### Frontend ↔ Backend Integration

The `assets/mockups/pag_html/` HTML files are **not served by Django** — they are a superseded static prototype. All templates under `codigo/backend/django/KeyServApp/templates/KeyServApp/` have a real URL, use `{% static %}` for CSS/images, and use `{% url %}` for internal navigation instead of hardcoded `.html` filenames. As of Fase 5 every page template extends `base.html`/`base.css` (a unified navy/teal/coral design system built for the new logo) instead of each page hand-rolling its own header/nav/CSS — that duplication used to produce inconsistent bugs (e.g. the login-field-name bug above) page by page.

## Known Issues

- `codigo/biometria/huella/REGISTRO_BD.py`, `AUTENTIFICACION.py`, `GUARDAR_DOCUMENTO.py`, `CONEXION_BD.py` remain legacy/broken by design — the Fase 3 architecture decision was to consolidate this logic into Django (`KeyServApp/biometria.py`), not repair these standalone scripts. They still reference `CONEXION_BD.cur`, which doesn't exist.
- The SMTP password that used to be hardcoded in `AUTENTIFICACION.py` was removed in Fase 3 (pulled into an env var) and the user has since rotated the real credential — it's still in git history from Fase 1/2 commits, but no longer valid.
- `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` was rewritten from the byte-dump it used to be, but is unverified against a real webcam (none available in this dev environment). There's also no field yet to persist a user's reference face encoding, so there's nothing real to compare against even once wired up.
- Fingerprint verification (`verificacion_huella_view`) doesn't compare against a stored reference hash — it just confirms the pipeline ran without error and marks the user verified.
- Khipu (`pagos.KhipuService`) has complete, correct-per-docs code but is genuinely untested — Khipu has no public sandbox, unlike Transbank, so it needs the project owner to create a real account and drop `KHIPU_API_KEY` into `.env` before it can be exercised for real. There was also some conflicting public documentation on Khipu's exact current auth scheme (API-key header vs. Basic auth) — if the first real attempt fails with an auth error, check `KhipuService._headers()` in `pagos.py` first.
- Transbank production credentials (`TRANSBANK_COMMERCE_CODE`/`TRANSBANK_API_KEY` for `TRANSBANK_ENVIRONMENT=produccion`) are still blocked on a real merchant account — the integration/sandbox path (default) needs none of this and is fully working.
- `crear_perfil_view` (the extended "habilidades/áreas de servicio" provider profile step) is still honestly labeled "under construction" — `Usuario` has no fields for that yet beyond `es_proveedor`.
- `editar_perfil_view` and `/recuperar/` **now work for real** (previously "under construction" stubs that didn't process submitted data): `editar_perfil_view` is a real `EditarPerfilForm` (`ModelForm`) over the actual `Usuario` fields (name, phone, email, address, región/comuna cascade, and a new `foto_perfil` avatar upload — see `migrations/0017_usuario_foto_perfil.py`); `/recuperar/` sends a signed, expiring (1h) reset link via email (`django.core.signing`, no DB table needed — the token embeds a hash of the current password hash so it self-invalidates on use or after a real password change) to a `EMAIL_BACKEND` that's console-based in DEBUG (prints to the `runserver` terminal) and real SMTP otherwise, reusing the existing `SMTP_*` env vars. Both are rate-limited via the same `cache`-based pattern as login. `Usuario.es_proveedor` (whether you can publish services) used to be stuck at whatever the `/registro/` checkbox set forever, with no way to change it later — fixed with a dedicated `alternar_proveedor_view` (`POST /perfil/alternar-proveedor/`) and a toggle button on `perfil.html`. Past publications stay visible/contractable after opting out; only creating new ones is blocked.
- The catalog (`/servicios/`) now has real pagination (`django.core.paginator.Paginator`, `PUBLICACIONES_POR_PAGINA = 20` in `views.py`) instead of a fixed cap of 40 results with no way to see the rest.
- No automated tests cover the admin group/permissions scoping itself, the task-based admin grouping, or the moderation dashboard UI (`_panel_aprobaciones.html`) — the 91 existing tests exercise the underlying models/views (e.g. `PublicacionYModeracionTests` covers moderation gating) but not this admin-surface layer directly.
- `.vscode/launch.json` still points at a stale pre-reorg path — not fixed, low priority.
