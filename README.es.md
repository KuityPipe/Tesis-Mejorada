🇬🇧 [English](README.md) | 🇪🇸 Español

# KeyServ

[![Tests](https://github.com/KuityPipe/Tesis-Mejorada/actions/workflows/tests.yml/badge.svg)](https://github.com/KuityPipe/Tesis-Mejorada/actions/workflows/tests.yml)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Angular](https://img.shields.io/badge/Angular-20-DD0031?logo=angular&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue)](LICENSE)

Un marketplace chileno de servicios del hogar con verificación de identidad (Face ID/huella nativos del teléfono, reconocimiento facial por cámara, o una vía sin biometría), construido para cumplir la nueva ley chilena de datos personales (Ley 21.719). Empezó como proyecto de tesis universitaria; hoy se sigue desarrollando como producto real.

![Inicio de KeyServ](assets/imagenes/inicio-keyserv.png)

<img src="assets/imagenes/asistente-keyserv.png" alt="Asistente con IA de KeyServ" width="300">  <img src="assets/imagenes/catalogo-keyserv.jpg" alt="Catálogo" width="520">

## Demo en vivo

**[keyserv.netlify.app](https://keyserv.netlify.app)** — backend en Render (tier gratis, puede tardar ~50s en despertar en el primer request tras un rato inactivo), frontend en Netlify. Catálogo, cuenta/login, contrataciones y búsqueda por geolocalización están en vivo; el asistente con IA (botón flotante) responde preguntas frecuentes y busca en el catálogo. La biometría nativa y el reconocimiento facial no son parte de este demo (para eso, el video, cuando exista). Credenciales demo:

- `cliente.demo@demo.keyserv` / `Demo1234` (cliente)
- `marcelo.gasfiteria@demo.keyserv` / `Demo1234` (proveedor)
- El panel `/admin/` del host de la API no es público; en local, define `DEMO_STAFF_PASSWORD` antes de sembrar para obtener las cuentas `admin` y `moderador`

También corre local en pocos minutos — ver [Cómo correrlo local](#cómo-correrlo-local) abajo.

## Stack

- **Backend**: Django 5.2 + Django REST Framework, PostgreSQL 17
- **Frontend**: Ionic 8 + Angular 20 + Capacitor — un solo código para web, Android e iOS
- **Auth**: JWT hecho a mano (PyJWT), no `djangorestframework-simplejwt` — ver [Decisiones técnicas](#decisiones-técnicas)
- **Pagos**: Transbank Webpay Plus (tarjetas) + Khipu (transferencia bancaria)
- **Biometría**: biometría nativa del dispositivo (Face ID / huella vía Capacitor, principal), reconocimiento facial por cámara con detección de vida por parpadeo (secundaria; solo se guarda un vector de 128 números **cifrado**, nunca una imagen) y una vía sin biometría (código por correo + documento revisado por una persona)
- **Asistente con IA**: preguntas frecuentes + búsqueda en el catálogo con NVIDIA NIM (API compatible con OpenAI, intercambiable); los datos personales se enmascaran antes de salir del servidor y hay un flujo guiado sin IA como respaldo
- **Cumplimiento de la Ley 21.719**: consentimiento, cifrado en reposo, derechos del titular (acceso, rectificación, oposición, bloqueo, supresión), retención automatizada y registro de auditoría — ver [Cumplimiento](#cumplimiento-ley-21719)
- **Ubicación**: búsqueda por geolocalización (posición real del dispositivo vía `@capacitor/geolocation`, distancia Haversine calculada en la API, filtro de radio), con vista previa de mapa + link a Google Maps en cada publicación
- **Tests**: 407 tests de backend + 93 de frontend, todos en verde (más una suite E2E con Playwright que corre contra la app real en CI)

Actualmente coexisten dos frontends: los templates originales renderizados por Django y la nueva app Ionic/Angular, que habla con una API REST hecha con DRF. La migración a Ionic sigue un enfoque "strangler fig" — las pantallas se retiran del app de templates área por área, no en un solo corte grande.

## Arquitectura

```mermaid
flowchart TB
    subgraph CLIENTS["Clientes (migración strangler-fig, coexistiendo)"]
        direction LR
        TPL["Templates Django<br/>auth por sesión"]
        ION["Ionic + Angular<br/>web · Android · iOS vía Capacitor"]
    end

    TPL -. "pantallas retirándose área por área" .-> ION

    subgraph BACKEND["Backend Django"]
        direction LR
        VIEWS["Vistas de templates"]
        API["API REST /api/*<br/>JWT hecho a mano (PyJWT)"]
    end

    TPL --> VIEWS
    ION -- "Bearer token" --> API

    VIEWS --> DB[("PostgreSQL<br/>(Neon)")]
    API --> DB

    VIEWS --> PAY
    API --> PAY
    VIEWS --> BIO
    API --> BIO
    API -- "solo texto enmascarado" --> LLM

    subgraph EXTERNAL["Servicios externos"]
        direction LR
        PAY["Transbank Webpay<br/>+ Khipu"]
        BIO["Biometría<br/>nativa Face ID / huella · rostro por cámara<br/>(vector cifrado) · vía sin biometría"]
        LLM["LLM del asistente<br/>NVIDIA NIM"]
    end
```

## Cumplimiento (Ley 21.719)

KeyServ trata un único dato sensible — el vector derivado del rostro — por lo que el cumplimiento de la ley de datos personales se priorizó antes que el bot y el rediseño. Lo implementado, con la evidencia de cada requisito en una [matriz de cumplimiento](docs/cumplimiento/README.md):

- **Minimización:** no se guardan imágenes del rostro ni huellas; la biometría nativa nunca llega al servidor.
- **Cifrado en reposo** del vector facial con claves rotables ([ADR 0002](docs/adr/0002-cifrado-del-vector-facial.md)) y almacenamiento privado para documentos de identidad y fotos de chat/reseñas.
- **Consentimiento versionado y revocable** antes de cualquier captura del rostro; revocar borra el vector.
- **Verificación de identidad con vigencia** (180 días) y un registro de auditoría que nunca contiene datos biométricos ([ADR 0003](docs/adr/0003-vigencia-y-auditoria-de-verificaciones.md)).
- **Derechos del titular dentro de la app:** descargar, corregir, oponerse, bloquear (reversible) y eliminar ([ADR 0004](docs/adr/0004-derechos-del-titular.md)), con control del plazo de 30 días.
- **Retención automatizada** y un protocolo de respuesta a brechas; borradores de la EIPD, el registro de actividades y la lista de encargados.
- **Ningún dato personal a una IA externa:** el asistente solo ve texto enmascarado y datos públicos del catálogo ([ADR 0005](docs/adr/0005-asistente-con-ia-externa.md)).

Los textos legales son **borradores** técnicos; la revisión de un abogado sigue pendiente (ver los [riesgos residuales](docs/cumplimiento/README.md#riesgos-residuales-y-lo-pendiente)).

## Decisiones técnicas

Algunas de las que defendería en una entrevista:

- **JWT hecho a mano en vez de `djangorestframework-simplejwt`.** El modelo `Usuario` de la app es anterior a la API y no es el `AUTH_USER_MODEL` de Django — `simplejwt` asume `get_user_model()` en varios lugares y no encaja bien. Una capa liviana de JWT (PyJWT para tokens de acceso sin estado + un refresh token opaco, hasheado y revocable) terminó siendo más simple que forzar el modelo de usuario existente para que encajara en una librería.
- **PostgreSQL sobre MySQL.** La tesis originalmente pedía MySQL; una vez que el proyecto pasó de entregable académico a producto, el mejor soporte de PostgreSQL para búsqueda de texto completo (`unaccent`, usado en la búsqueda del catálogo) y su encaje general con Django lo hicieron la mejor opción hacia adelante.
- **Modelo de confianza de la biometría nativa.** Cuando la app verifica identidad vía el Face ID/huella del propio teléfono (`@capgo/capacitor-native-biometric`), la verificación ocurre enteramente dentro del enclave seguro del dispositivo — el servidor estructuralmente no puede verificarla de forma directa. En vez de simular lo contrario, la API confía en una sesión JWT ya autenticada más la atestación de hardware del dispositivo, el mismo modelo de confianza que usan apps tipo banca, en vez de pedir una re-entrada de contraseña redundante que no agregaría seguridad real.
- **Dos pasarelas de pago, no una.** Pagar solo con tarjeta (Webpay) no cubre cómo paga en la práctica una parte importante de los chilenos — la transferencia bancaria directa (Khipu) es lo bastante común como para justificar la integración extra.

## Qué se rompió, y cómo se arregló

El historial de commits y `docs/BACKLOG.md` tienen el detalle completo; tres casos destacan:

- **Una request de 13 minutos que dejaba el servidor colgado para todos, no solo para quien probaba.** La verificación de vida por parpadeo del reconocimiento facial reintentaba con un detector de rostro neuronal mucho más pesado cada vez que el detector rápido no encontraba nada — y con poca luz, eso pasaba en casi todos los frames de una captura. Se encontró probando con un cuarto oscuro real, no con un test unitario. Se arregló sacando el fallback pesado y validando la calidad de imagen *antes* de intentar detectar el rostro, no después.
- **El modo oscuro perdiendo una pelea de CSS contra sí mismo, dos veces.** El propio stylesheet de modo oscuro de Ionic define varias variables de tema bajo un selector más específico (`:root.md`/`:root.ios`) que un `:root` plano, así que la paleta personalizada de la app seguía perdiendo la cascada pese a cargar después en el bundle — invisible leyendo el SCSS, solo se detectó revisando `getComputedStyle` en un navegador real.
- **Un login que "funcionaba" durante meses sin funcionar en realidad.** El template de login enviaba un campo `username` mientras el formulario detrás esperaba `email` — el form/view en aislamiento funcionaba bien (y también en cada test que se saltaba el template), así que nadie lo notó hasta que alguien intentó loguearse por la página real.

## Cómo correrlo local

```bash
# Backend
python -m venv venv
source venv/bin/activate  # o venv\Scripts\Activate.ps1 en Windows
pip install -r requirements.txt
cd codigo/backend/django
cp .env.example .env      # completar credenciales de BD
python manage.py migrate
python manage.py runserver 8000

# Frontend (otra terminal)
cd codigo/frontend/ionic
npm install
npm start                  # sirve en :8100
```

Necesita una instancia local de PostgreSQL (credenciales vía `.env`). Cuentas demo, una vez sembrados los datos: `admin` / `moderador` (staff, clave desde `DEMO_STAFF_PASSWORD`), `cliente.demo@demo.keyserv` / `Demo1234` (cliente), `marcelo.gasfiteria@demo.keyserv` / `Demo1234` (proveedor).

## Sobre el uso de IA

Este proyecto se construyó con Claude Code como par de desarrollo. Cada decisión de arquitectura y producto fue mía (ver [Decisiones técnicas](#decisiones-técnicas) arriba) — revisé y dirigí cada cambio, y verifiqué en vivo cada funcionalidad antes de darla por cerrada, incluyendo correr la app nativa Android en un emulador, probar la integración de pagos contra el sandbox real de Transbank, y probar el reconocimiento facial contra una webcam real. Usar IA para escribir el código me liberó tiempo para las decisiones que son el trabajo de ingeniería real: diseño, seguridad y arquitectura — las partes que puedo defender en una entrevista.

## Roadmap

- Un video corto (flujo de contratación, pago, app nativa Android con biometría)
- Rediseño visual del frontend y revisión de un abogado de los documentos de cumplimiento

## Licencia

[MIT](LICENSE) — permisiva, no impide relicenciar más adelante si esto crece más allá de un proyecto de portafolio.

## Más documentación

El proyecto mantiene documentación de ingeniería inusualmente detallada, escrita a medida que pasaba el trabajo y no después:

- [`docs/INFORME_PROYECTO_KEYSERV.md`](docs/INFORME_PROYECTO_KEYSERV.md) — el informe de proyecto completo: problema, arquitectura y resultados, escrito como continuación de la tesis de 2023 de la que nació este proyecto (también disponible como `docs/INFORME_PROYECTO_KEYSERV.docx`, listo para exportar a PDF)
- [`docs/cumplimiento/README.md`](docs/cumplimiento/README.md) — carpeta de evidencia de cumplimiento y matriz requisito por requisito; [`docs/resumen-mejoras.md`](docs/resumen-mejoras.md) — resumen ejecutivo de las mejoras 2026/27; [`docs/adr/`](docs/adr/) — decisiones de arquitectura
- [`docs/PLAN_MIGRACION_IONIC.md`](docs/PLAN_MIGRACION_IONIC.md) — el plan por fases de la migración de Django a Ionic
- [`docs/BACKLOG.md`](docs/BACKLOG.md) — gaps y decisiones registradas a lo largo del proyecto
- [`docs/DATABASE_DOCUMENTATION.md`](docs/DATABASE_DOCUMENTATION.md) — referencia del modelo de datos
- [Carta Gantt del desarrollo](https://claude.ai/code/artifact/aea584bb-cc91-4a5a-8bf0-238cd886903b) — evidencia de proceso, armada a medida que avanzaba el trabajo y no después
