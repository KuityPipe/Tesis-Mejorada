🇬🇧 English | 🇪🇸 [Español](README.es.md)

# KeyServ

[![Tests](https://github.com/KuityPipe/Tesis-Mejorada/actions/workflows/tests.yml/badge.svg)](https://github.com/KuityPipe/Tesis-Mejorada/actions/workflows/tests.yml)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Angular](https://img.shields.io/badge/Angular-20-DD0031?logo=angular&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A Chilean home-services marketplace with biometric identity verification (native Face ID/fingerprint, webcam facial recognition, or a no-biometrics fallback), built to comply with Chile's new personal-data law (Ley 21.719). Started as a university thesis project, now being developed as a real product.

![KeyServ home page](assets/imagenes/inicio-keyserv.png)

<img src="assets/imagenes/asistente-keyserv.png" alt="KeyServ AI assistant" width="300">  <img src="assets/imagenes/catalogo-keyserv.png" alt="Catálogo" width="520">

## Live demo

**[keyserv.netlify.app](https://keyserv.netlify.app)** — backend on Render (free tier, may take ~50s to wake up on the first request after inactivity), frontend on Netlify. Catalog, account/login, contracting and geolocation search are live; the AI assistant (floating button) answers FAQs and searches the catalog. Native biometrics and facial recognition aren't part of this demo (see the video instead, once it exists). Demo logins:

- `cliente.demo@demo.keyserv` / `Demo1234` (client)
- `marcelo.gasfiteria@demo.keyserv` / `Demo1234` (provider)
- The `/admin/` panel on the API host is not public; locally, set `DEMO_STAFF_PASSWORD` before seeding to get the `admin` and `moderador` accounts

It also runs locally in a few minutes — see [Running locally](#running-locally) below.

## Stack

- **Backend**: Django 5.2 + Django REST Framework, PostgreSQL 17
- **Frontend**: Ionic 8 + Angular 20 + Capacitor — one codebase for web, Android and iOS
- **Auth**: hand-rolled JWT (PyJWT), not `djangorestframework-simplejwt` — see [Technical decisions](#technical-decisions)
- **Payments**: Transbank Webpay Plus (cards) + Khipu (bank transfer)
- **Biometrics**: native device biometrics (Face ID / fingerprint via Capacitor, primary), webcam facial recognition with blink-liveness detection (secondary; only an **encrypted** 128-number vector is stored, never an image), and a no-biometrics fallback (email code + document reviewed by a person)
- **AI assistant**: FAQ + catalog search through NVIDIA NIM (OpenAI-compatible API, swappable); personal data is masked before leaving the server and a no-AI guided flow is the fallback
- **Data-protection compliance (Ley 21.719)**: consent, encryption at rest, data-subject rights (access, rectification, opposition, blocking, erasure), automated retention, audit log — see [Compliance](#compliance-ley-21719)
- **Location**: geolocation-based search (real device position via `@capacitor/geolocation`, Haversine distance computed in the API, radius filter), with a map preview + Google Maps link on each listing
- **Tests**: 407 backend tests + 93 frontend tests, both green (plus a Playwright E2E suite running against the real app in CI)

Two frontends currently coexist: the original Django server-rendered templates and the new Ionic/Angular app, talking to a DRF REST API. The Ionic migration follows a strangler-fig approach — screens are retired from the template app one area at a time, not in one big cutover.

## Architecture

```mermaid
flowchart TB
    subgraph CLIENTS["Clients (strangler-fig migration, coexisting)"]
        direction LR
        TPL["Django templates<br/>session auth"]
        ION["Ionic + Angular<br/>web · Android · iOS via Capacitor"]
    end

    TPL -. "screens retiring area by area" .-> ION

    subgraph BACKEND["Django backend"]
        direction LR
        VIEWS["Template views"]
        API["REST API /api/*<br/>hand-rolled JWT (PyJWT)"]
    end

    TPL --> VIEWS
    ION -- "Bearer token" --> API

    VIEWS --> DB[("PostgreSQL<br/>(Neon)")]
    API --> DB

    VIEWS --> PAY
    API --> PAY
    VIEWS --> BIO
    API --> BIO
    API -- "masked text only" --> LLM

    subgraph EXTERNAL["External services"]
        direction LR
        PAY["Transbank Webpay<br/>+ Khipu"]
        BIO["Biometrics<br/>native Face ID / fingerprint · webcam face<br/>(encrypted vector) · no-biometrics fallback"]
        LLM["Assistant LLM<br/>NVIDIA NIM"]
    end
```

## Compliance (Ley 21.719)

KeyServ handles one sensitive datum — the vector derived from a face — so data-protection compliance was prioritised ahead of the bot and the redesign. What's implemented, with the evidence for each requirement in a [compliance matrix](docs/cumplimiento/README.md):

- **Data minimisation:** no face images or fingerprints are stored; native biometrics never reach the server.
- **Encryption at rest** of the face vector with rotatable keys ([ADR 0002](docs/adr/0002-cifrado-del-vector-facial.md)), private storage for identity documents and chat/review photos.
- **Versioned, revocable consent** before any face capture; revoking deletes the vector.
- **Identity verification that expires** (180 days) with an audit trail that never contains biometric data ([ADR 0003](docs/adr/0003-vigencia-y-auditoria-de-verificaciones.md)).
- **Data-subject rights in the app:** download, rectify, oppose, block (reversible) and delete ([ADR 0004](docs/adr/0004-derechos-del-titular.md)), with a 30-day deadline tracker.
- **Automated retention** and a breach-response protocol; drafts of the DPIA, record of processing activities and processor list.
- **No personal data to external AI:** the assistant only sees masked text and public catalog data ([ADR 0005](docs/adr/0005-asistente-con-ia-externa.md)).

The legal texts are technical **drafts**; a lawyer's review is still pending (see [residual risks](docs/cumplimiento/README.md#riesgos-residuales-y-lo-pendiente)).

## Technical decisions

A few of the calls I'd defend in an interview:

- **Hand-rolled JWT instead of `djangorestframework-simplejwt`.** The app's `Usuario` model predates the API and isn't Django's `AUTH_USER_MODEL` — `simplejwt` assumes `get_user_model()` in several places and doesn't fit cleanly. A small JWT layer (PyJWT for stateless access tokens + an opaque, hashed, revocable refresh token) turned out simpler than bending the app's user model to fit a library.
- **PostgreSQL over MySQL.** The thesis brief originally specified MySQL; once the project moved past the academic deliverable, PostgreSQL's stronger support for full-text search (`unaccent`, used in the catalog search) and general fit for a Django app made it the better default going forward.
- **Native biometrics trust model.** When the app verifies identity via the phone's own Face ID/fingerprint (`@capgo/capacitor-native-biometric`), the check happens entirely inside the device's secure enclave — the server structurally cannot verify it directly. Rather than pretend otherwise, the API trusts an already-authenticated JWT session plus the device's hardware attestation, the same trust model banking-style apps use, instead of requiring a redundant password re-entry that wouldn't add real security.
- **Two payment gateways, not one.** Card payments alone (Webpay) don't cover how a meaningful share of Chileans actually pay for services — direct bank transfer (Khipu) is common enough to be worth the extra integration.

## What broke, and how it got fixed

The commit history and `docs/BACKLOG.md` have the full trail; three stand out:

- **A 13-minute request that froze the server for every user, not just the one testing it.** The facial-recognition liveness check retried with a much heavier neural face detector whenever the fast detector found nothing — which, in low light, was almost every frame of a capture burst. Found only by testing with a real dark room, not a unit test. Fixed by dropping the heavy fallback and checking image quality *before* attempting face detection, not after.
- **Dark mode losing a CSS fight with itself, twice.** Ionic's own dark-mode stylesheet defines several theme variables under a more specific selector (`:root.md`/`:root.ios`) than a plain `:root` override, so the app's custom palette kept losing the cascade despite loading later in the bundle — invisible from reading the SCSS, only caught by checking `getComputedStyle` in a real browser.
- **A login that "worked" for months without actually working.** The login template submitted a `username` field while the form behind it expected `email` — the raw form/view worked fine in isolation (and in every test that bypassed the template), so nothing caught it until someone tried logging in through the actual page.

## Running locally

```bash
# Backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cd codigo/backend/django
cp .env.example .env      # then fill in DB credentials
python manage.py migrate
python manage.py runserver 8000

# Frontend (separate terminal)
cd codigo/frontend/ionic
npm install
npm start                  # serves on :8100
```

Needs a local PostgreSQL instance (connection details via `.env`). Demo accounts, once seeded: `admin` / `moderador` (staff, password from `DEMO_STAFF_PASSWORD`), `cliente.demo@demo.keyserv` / `Demo1234` (client), `marcelo.gasfiteria@demo.keyserv` / `Demo1234` (provider).

## About AI usage

This project was built with Claude Code as a development pair. Every architecture and product decision was mine (see [Technical decisions](#technical-decisions) above) — I reviewed and directed each change, and verified each feature live before considering it done, including running the native Android app on an emulator, testing the payment integration against Transbank's real sandbox, and testing facial recognition against a real webcam. Using AI to write the code freed up my time for the decisions that are the actual engineering work: design, security, and architecture — the parts I can defend in an interview.

## Roadmap

- A short video walkthrough (contracting flow, payment, native Android app with biometrics)
- Visual redesign of the frontend and a lawyer's review of the compliance documents

## License

[MIT](LICENSE) — permissive, doesn't block relicensing later if this ever grows past a portfolio project.

## Further reading

The project keeps unusually detailed engineering docs, written as the work happened rather than after the fact:

- [`docs/INFORME_PROYECTO_KEYSERV.md`](docs/INFORME_PROYECTO_KEYSERV.md) — the fuller project report (Spanish): problem statement, architecture, and results, structured as the continuation of the original 2023 thesis this project started from (also available as `docs/INFORME_PROYECTO_KEYSERV.docx`, ready to export to PDF)
- [`docs/cumplimiento/README.md`](docs/cumplimiento/README.md) — compliance evidence folder and requirement-by-requirement matrix; [`docs/resumen-mejoras.md`](docs/resumen-mejoras.md) — executive summary of the 2026/27 improvements; [`docs/adr/`](docs/adr/) — architecture decisions
- [`docs/PLAN_MIGRACION_IONIC.md`](docs/PLAN_MIGRACION_IONIC.md) — the phased plan for the Django-to-Ionic migration
- [`docs/BACKLOG.md`](docs/BACKLOG.md) — tracked gaps and decisions across the project
- [`docs/DATABASE_DOCUMENTATION.md`](docs/DATABASE_DOCUMENTATION.md) — data model reference
- [Development timeline (Gantt chart)](https://claude.ai/code/artifact/aea584bb-cc91-4a5a-8bf0-238cd886903b) — process evidence, built alongside the work rather than after the fact
