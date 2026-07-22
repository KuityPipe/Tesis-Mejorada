# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KeyServ** — a Chilean services marketplace platform with biometric authentication (fingerprint + facial recognition). Built as a thesis project by a team (Felipe, OmaryLuis, luchoo23).

## Active Project

There are three Django project variants (`ProyectoDjango/`, `ProyectoKeyServ/`, `Tesis/`). **`Tesis/` is the canonical, most complete version** and should be the default target for all work. It uses the `notpaper2` MySQL database.

## Commands

### Environment Setup

```powershell
# Activate virtual environment (Python 3.14 / Windows)
.\venv_tesis\Scripts\Activate.ps1

# Install core dependencies (no requirements.txt exists yet)
pip install Django==4.2.1 PyMySQL opencv-python face_recognition pillow fpdf2
```

### Django (main app — run from `Tesis/`)

```powershell
cd Tesis
python manage.py migrate
python manage.py runserver 8000
python manage.py createsuperuser
```

### Flask backends (run independently from project root)

```powershell
# Regions/communes API — exposes /regiones and /comunas/<id_region>
python BackHuella/CONEXION_BD.py

# User registration endpoint
python BackHuella/REGISTRO_BD.py
```

### Biometric scripts

```powershell
python BackHuella/IMAGEN_HUELLA.py          # Fingerprint processing pipeline
python probando_face_recognition/probando_face_recognition.py  # Facial recognition (requires webcam)
python BackHuella/AUTENTIFICACION.py        # Email-based auth flow (requires SMTP)
```

### Database

MySQL must be running locally on port 3306. Credentials in `Tesis/KeyServProject/settings.py`:
- Host: `localhost`, User: `root`, Password: `""`, DB: `notpaper2`

No tests or linting tools are configured in the project.

## Architecture

### Component Map

```
Pag/                        Static HTML frontend (no framework)
  └── *.html                Pages: paginicio, sesion, registroinicio, perfil, huella, chat, reservas, pago
  └── css/                  Stylesheets
  └── imagenes/             Assets

Tesis/                      Main Django project
  ├── KeyServProject/       Settings, WSGI, root URL conf (DB: notpaper2)
  └── KeyServApp/
      ├── models.py         25+ ORM models (see Data Model section)
      ├── views.py          Registration + AJAX commune loader
      └── urls.py           /registro/, /admin/, /ajax/load-comunas/

BackHuella/                 Biometric + document backend (Flask/standalone scripts)
  ├── IMAGEN_HUELLA.py      Fingerprint image pipeline (binarize → thin → prune → hash)
  ├── AUTENTIFICACION.py    Email SMTP auth: sends 5-digit code, compares SHA256
  ├── REGISTRO_BD.py        Flask endpoint for user registration into DB
  ├── CONEXION_BD.py        Flask API: /regiones, /comunas/<id_region>
  └── GUARDAR_DOCUMENTO.py  Upload files, convert to PDF, store in Documento table

probando_face_recognition/
  └── probando_face_recognition.py  OpenCV webcam loop → face_recognition encoding → comparison
```

### Data Flow

**User registration:** HTML form → Django `/registro/` view → SHA256 password hash → `Usuario` model → MySQL

**Login / email auth:** User submits email → `AUTENTIFICACION.py` → random 5-digit code sent via SMTP → code compared as SHA256 hash

**Fingerprint auth:** Image captured → `IMAGEN_HUELLA.py` (binarize, skeletonize, prune minutiae) → SHA256 → stored/compared in `Contraseña dactilar/`

**Facial recognition:** Webcam frames → OpenCV → `face_recognition` library encodes faces → comparison against stored encoding

**Document upload:** File selected via tkinter → PDF conversion (FPDF) → stored in `Documento` table with user FK

### Key Data Models (`Tesis/KeyServApp/models.py`)

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

The `Pag/` HTML files are **not served by Django** — they are standalone static files. The registration form in `registroinicio.html` POSTs to the Django `/registro/` endpoint. The AJAX call for communes (`/ajax/load-comunas/`) is wired in Django's URL conf. The Flask backends (`CONEXION_BD.py`) are called separately and are not integrated into Django routing.

## Known Issues

- No `requirements.txt` — dependencies must be installed manually.
- Three Django project variants exist (`ProyectoDjango`, `ProyectoKeyServ`, `Tesis`); only `Tesis/` is current.
- SMTP credentials and the Django `SECRET_KEY` are hardcoded in source files.
- Passwords are hashed with SHA256 without salt.
- No migration files exist; schema is managed through `makemigrations` + `migrate`.
