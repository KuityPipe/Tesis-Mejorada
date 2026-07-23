# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KeyServ** — a Chilean services marketplace platform with biometric authentication (fingerprint + facial recognition). Built as a thesis project by a team (Felipe, OmaryLuis, luchoo23); the thesis has since been delivered and the project is being treated as a commercial product going forward.

## Repository Layout

The repo root was reorganized (Fase 1) out of a flat, ad-hoc layout into:

```
docs/                        docs/nuevo (active thesis text), docs/plantilla (thesis template PDF), docs/viejo (empty, future)
codigo/
  backend/django/            Canonical Django app (formerly Tesis/) — see "Active Project" below
  biometria/huella/          Formerly BackHuella/ (Flask + fingerprint scripts)
  biometria/reconocimiento_facial/  Formerly probando_face_recognition/
  viejo/ProyectoDjango/      Legacy Django variant (superseded, kept for reference)
  viejo/ProyectoKeyServ/     Legacy Django variant (empty scaffold, superseded)
assets/mockups/pag_html/     Formerly Pag/ — original static HTML prototype (superseded by codigo/backend/django templates)
assets/imagenes/, assets/diagramas/   Empty scaffolds for future assets
.sistema/cache/, logs/, config/       Empty scaffolds for future cache/log/config output
```

Not moved (stay at repo root): `venv_tesis/` (active dev virtualenv — moving it would break its absolute activation paths), `TesisAntigua/` (untracked raw GitHub export/backup containing personal emails; gitignored, not part of the codebase), `CLAUDE.md`.

A root `.gitignore` was added and all previously-committed virtualenvs (`codigo/backend/django/venv`, `codigo/viejo/ProyectoKeyServ/venv`, `codigo/biometria/reconocimiento_facial/fr-venv`) and `__pycache__`/`*.pyc` files were untracked (`git rm --cached`) — they still exist on disk but are no longer version-controlled.

## Active Project

There are three Django project variants (`codigo/viejo/ProyectoDjango/`, `codigo/viejo/ProyectoKeyServ/`, `codigo/backend/django/`). **`codigo/backend/django/` is the canonical, most complete version** (formerly `Tesis/`) and should be the default target for all work. It uses the `notpaper2` MySQL database.

## Commands

### Environment Setup

```powershell
# Activate virtual environment (Python 3.14 / Windows)
.\venv_tesis\Scripts\Activate.ps1

# Install core dependencies (no requirements.txt exists yet)
pip install Django==4.2.1 PyMySQL Flask flask-mysqldb opencv-python face_recognition pillow fpdf2
```

### Django (main app — run from `codigo/backend/django/`)

```powershell
cd codigo/backend/django
python manage.py migrate
python manage.py runserver 8000
python manage.py createsuperuser
```

### Flask backends (run independently from project root)

```powershell
# Regions/communes API — exposes /regiones and /comunas/<id_region>
python codigo/biometria/huella/CONEXION_BD.py

# User registration endpoint
python codigo/biometria/huella/REGISTRO_BD.py
```

### Biometric scripts

```powershell
python codigo/biometria/huella/IMAGEN_HUELLA.py          # Fingerprint processing pipeline
python codigo/biometria/reconocimiento_facial/probando_face_recognition.py  # Facial recognition (requires webcam)
python codigo/biometria/huella/AUTENTIFICACION.py        # Email-based auth flow (requires SMTP)
```

### Database

MySQL must be running locally on port 3306. Credentials in `codigo/backend/django/KeyServProject/settings.py`:
- Host: `localhost`, User: `root`, Password: `""`, DB: `notpaper2`

No tests or linting tools are configured in the project.

## Architecture

### Component Map

```
assets/mockups/pag_html/    Static HTML frontend prototype (no framework), superseded by Django templates
  └── *.html                Pages: paginicio, sesion, registroinicio, perfil, huella, chat, reservas, pago
  └── css/                  Stylesheets
  └── imagenes/             Assets

codigo/backend/django/      Main Django project
  ├── KeyServProject/       Settings, WSGI, root URL conf (DB: notpaper2)
  └── KeyServApp/
      ├── models.py         25+ ORM models (see Data Model section)
      ├── views.py          Registration + AJAX commune loader
      └── urls.py           /registro/, /admin/, /ajax/load-comunas/

codigo/biometria/huella/    Biometric + document backend (Flask/standalone scripts)
  ├── IMAGEN_HUELLA.py      Fingerprint image pipeline (binarize → thin → prune → hash)
  ├── AUTENTIFICACION.py    Email SMTP auth: sends 5-digit code, compares SHA256
  ├── REGISTRO_BD.py        Flask endpoint for user registration into DB
  ├── CONEXION_BD.py        Flask API: /regiones, /comunas/<id_region>
  └── GUARDAR_DOCUMENTO.py  Upload files, convert to PDF, store in Documento table

codigo/biometria/reconocimiento_facial/
  └── probando_face_recognition.py  OpenCV webcam loop → face_recognition encoding → comparison
```

### Data Flow

**User registration:** HTML form → Django `/registro/` view → SHA256 password hash → `Usuario` model → MySQL

**Login / email auth:** User submits email → `AUTENTIFICACION.py` → random 5-digit code sent via SMTP → code compared as SHA256 hash

**Fingerprint auth:** Image captured → `IMAGEN_HUELLA.py` (binarize, skeletonize, prune minutiae) → SHA256 → stored/compared in `Contraseña dactilar/`

**Facial recognition:** Webcam frames → OpenCV → `face_recognition` library encodes faces → comparison against stored encoding

**Document upload:** File selected via tkinter → PDF conversion (FPDF) → stored in `Documento` table with user FK

### Key Data Models (`codigo/backend/django/KeyServApp/models.py`)

| Model | Purpose |
|---|---|
| `Usuario` | Core user: personal info, phone, email, SHA256 password, region/commune FK |
| `UsuarioAdministrativo` | Admin users with role field |
| `Autentificacion` | Auth attempt log with timestamps |
| `Publicaciones` | Service listings |
| `Mensaje` / `Conversacion` | Chat system |
| `Valoracion` / `Ranking` | Star ratings and reputation |
| `Documento` / `Firma` | Documents and digital signatures |
| `Transaccion` | Account transactions |
| `TipoCuenta` | Account tiers (free, individual, SME, enterprise) |
| `Region` / `Comuna` | Chilean geographic data (loaded via AJAX in registration form) |
| `EstadoAutentificacion`, `EstadoConsulta`, `EstadoDocumento` | Status enums |

### Frontend ↔ Backend Integration

The `assets/mockups/pag_html/` HTML files are **not served by Django** — they are a superseded static prototype. The registration form in `registroinicio.html` POSTs to the Django `/registro/` endpoint. The AJAX call for communes (`/ajax/load-comunas/`) is wired in Django's URL conf. The Flask backends (`CONEXION_BD.py`) are called separately and are not integrated into Django routing.

## Known Issues

- No `requirements.txt` — dependencies must be installed manually.
- Three Django project variants exist (`codigo/viejo/ProyectoDjango`, `codigo/viejo/ProyectoKeyServ`, `codigo/backend/django`); only `codigo/backend/django/` is current.
- SMTP credentials and the Django `SECRET_KEY` are hardcoded in source files.
- Passwords are hashed with SHA256 without salt.
- No migration files exist; schema is managed through `makemigrations` + `migrate`.
- `REGISTRO_BD.py`, `AUTENTIFICACION.py`, and `GUARDAR_DOCUMENTO.py` all do `cursora = CONEXION_BD.cur`, but the `pymysql` connection that defines `cur` in `CONEXION_BD.py` is inside a triple-quoted (commented-out) block — as committed, these three scripts raise `AttributeError` on import and cannot run until that connection code is restored.
- `CONEXION_BD.py` points at a MySQL database named `notpaper`, while the Django app in `codigo/backend/django/` uses `notpaper2` — the Flask backends and the Django app are not reading/writing the same schema.
- `CONEXION_BD.py` starts its Flask dev server with `app.run(debug=True, port=3306)`, the same port MySQL listens on; this needs a different port to run alongside a local MySQL instance.
- `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` is not valid Python source — its contents are a flat comma-separated dump of decimal byte values, not text — so it cannot be run as documented until it's re-saved as actual source.
- `.vscode/launch.json` still points at the pre-reorg path `/workspaces/ProyectoTesis/Pag/paginicio.html`, which no longer exists (page moved to `assets/mockups/pag_html/paginicio.html`) — not fixed as part of Fase 1, needs updating before that debug config is used again.
- `venv_tesis/` (the active virtualenv) currently only has `pip` installed — Django and the rest of the dependencies listed above still need to be installed into it before `manage.py` commands will work.
