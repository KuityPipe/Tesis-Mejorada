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

Not moved (stay at repo root): `venv_tesis/` (active dev virtualenv — moving it would break its absolute activation paths), `TesisAntigua/` (untracked raw GitHub export/backup containing personal emails; gitignored, not part of the codebase), `CLAUDE.md`.

A root `.gitignore` was added (Fase 1) and all previously-committed virtualenvs and `__pycache__`/`*.pyc` files were untracked — they still exist on disk but are no longer version-controlled. `.sistema/cache/*` is also gitignored (regenerable scratch output, e.g. PDF text extractions).

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

# Copy and fill in environment variables (SECRET_KEY, DB_*, SMTP_*, TRANSBANK_*)
Copy-Item .env.example codigo\backend\django\.env
```

`venv_tesis` currently has Django==4.2.1, django-environ, psycopg2-binary, and Pillow installed and verified (`manage.py check`/`makemigrations` both run clean). `opencv-python`/`face_recognition` (facial recognition) and `fpdf2` are listed in `requirements.txt` but not installed in this environment — they're heavy and only needed to exercise that specific feature.

### Django (main app — run from `codigo/backend/django/`)

```powershell
cd codigo/backend/django
python manage.py migrate
python manage.py runserver 8000
python manage.py createsuperuser
```

**No PostgreSQL server is available in this dev environment** (port 5432 closed) — `manage.py check` and `makemigrations` were validated without a live DB, but `migrate` has not been run against real data yet. See `docs/SETUP_INSTRUCTIONS.md` for standing up Postgres (local install or a free managed tier).

### Biometric scripts (standalone, importable)

```powershell
python codigo/biometria/huella/IMAGEN_HUELLA.py                              # Fingerprint pipeline (runs standalone, no hardware needed)
python codigo/biometria/reconocimiento_facial/probando_face_recognition.py   # Facial recognition (requires webcam + opencv-python/face_recognition)
```

Both are now proper importable modules (`procesar_huella()` / `cargar_rostro_conocido()`+`verificar_rostro()`) wired into the Django app via `codigo/backend/django/KeyServApp/biometria.py`, instead of top-level scripts. `AUTENTIFICACION.py`, `REGISTRO_BD.py`, `GUARDAR_DOCUMENTO.py`, `CONEXION_BD.py` remain legacy/deprecated Flask+CLI scripts — see Known Issues.

### Database

PostgreSQL, credentials via environment variables (`.env`, see `.env.example`) — no longer hardcoded in `settings.py`. `codigo/backend/django/KeyServApp/migrations/0001_initial.py` was regenerated from scratch against the corrected models (the old MySQL-era migration is backed up in `codigo/viejo/backup_fase3/`).

No automated tests are configured yet (`tests.py` files are still empty stubs) — see `docs/DEVELOPMENT_ROADMAP.md` for what to test first.

## Architecture

### Component Map

```
assets/mockups/pag_html/    Static HTML frontend prototype (no framework), superseded by Django templates

codigo/backend/django/      Main Django project
  ├── KeyServProject/       Settings (env-var driven), WSGI, root URL conf (DB: PostgreSQL)
  └── KeyServApp/
      ├── models.py         ~25 ORM models incl. real ForeignKeys + new Contratacion (see Data Model section)
      ├── views.py          Auth (real), publicaciones/contrataciones/valoraciones, biometric + payment integration points
      ├── forms.py          Registro/Login/Publicacion/Valoracion forms with validation
      ├── decorators.py     `login_requerido` — custom session auth (not django.contrib.auth's user model)
      ├── biometria.py      Bridges Django views to codigo/biometria/* scripts
      ├── pagos.py          TransbankService skeleton (NotImplementedError until merchant credentials exist)
      ├── admin.py          All models registered
      └── urls.py           24 routes — every template now has a URL (was 2 of ~18 before Fase 3)

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

**Login/logout:** `/sesion/` validates credentials via `Usuario.check_password()` and sets `request.session['usuario_id']` — a custom lightweight session, not `django.contrib.auth`'s login system (see `docs/API_DOCUMENTATION.md` "Notas sobre autenticación").

**Fingerprint verification:** `/huella/verificar/` → `KeyServApp/biometria.py` → `IMAGEN_HUELLA.procesar_huella()` → SHA-256 hash → marks `Usuario.verificado_biometricamente` (TODO: doesn't yet compare against a stored reference hash).

**Facial recognition:** skeleton only — `verificar_rostro_usuario()` exists but is unwired from any view and untested (no webcam in this environment).

**Publications & moderation:** `Publicaciones.estado_moderacion` (new field) gates visibility on the home page — BPMN "Crear publicación" from the thesis PDF required this and it didn't exist before Fase 3.

**Contracting:** new `Contratacion` model + `contratacion_crear_view` create the request; the full BPMN flow (notify provider, force re-authentication of both parties, trigger payment) is still TODO.

**Payments:** `pagos.TransbankService` is a full skeleton, not wired to any real Transbank API call — blocked on merchant credentials.

### Key Data Models (`codigo/backend/django/KeyServApp/models.py`)

See `docs/DATABASE_DOCUMENTATION.md` for the complete table/relationship reference. Notable Fase 3 additions: `Contratacion` (didn't exist), `Usuario.es_proveedor`/`Usuario.verificado_biometricamente`, `Publicaciones.estado_moderacion`.

### Frontend ↔ Backend Integration

The `assets/mockups/pag_html/` HTML files are **not served by Django** — they are a superseded static prototype. All 18 templates under `codigo/backend/django/KeyServApp/templates/KeyServApp/` now have a real URL (Fase 3 completed `urls.py`), use `{% static %}` for CSS/images (moved to `KeyServApp/static/KeyServApp/`), and use `{% url %}` for internal navigation instead of hardcoded `.html` filenames.

## Known Issues

- `codigo/biometria/huella/REGISTRO_BD.py`, `AUTENTIFICACION.py`, `GUARDAR_DOCUMENTO.py`, `CONEXION_BD.py` remain legacy/broken by design — the Fase 3 architecture decision was to consolidate this logic into Django (`KeyServApp/biometria.py`), not repair these standalone scripts. They still reference `CONEXION_BD.cur`, which doesn't exist.
- **The SMTP password that used to be hardcoded in `AUTENTIFICACION.py` was removed and should be rotated** — it was exposed in git history (Fase 1/2 commits) before being pulled into an env var in Fase 3. Removing it from the current file does not remove it from history.
- `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` was rewritten from the byte-dump it used to be, but is unverified against a real webcam (none available in this dev environment).
- `manage.py migrate` has not been run — no PostgreSQL server is available in this environment. `check`/`makemigrations` were validated.
- No automated tests exist yet.
- `publicacion_crear_view` renders a placeholder template (`crearperfil.html`) — no dedicated "create publication" page exists among the templates inherited from the thesis.
- `.vscode/launch.json` still points at a stale pre-reorg path — not fixed, low priority.
