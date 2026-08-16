# Plan de portafolio — KeyServ

Decidido el 2026-08-15, con la sesión de investigación que lo respalda. Este documento es el
equivalente para "convertir KeyServ en un portafolio fuerte" de lo que `PLAN_MIGRACION_IONIC.md` es
para la migración a Ionic: el plan vive acá, se ejecuta en sesiones futuras, se va tachando.

## Por qué esto y en este orden (contexto de la decisión)

El usuario está desempleado y busca trabajo — el portafolio es la vía más rápida a ingresos de las
tres que se discutieron (plataforma independiente sostenida con ads, venta/licenciamiento de la
idea, portafolio). Las otras dos (especialmente la plataforma con ads) tienen problemas
estructurales de fondo — arranque en frío de marketplace de dos lados, ingresos por publicidad que
requieren tráfico que no existe todavía, y obligaciones legales reales (Ley 19.628/21.719, Chile)
en el momento en que se manejen datos biométricos de usuarios reales — así que no son un plan de
ingresos a corto plazo. El portafolio sí lo es: el código y la disciplina de proceso ya existen, lo
que falta es **presentación**, no más funcionalidad.

Investigación (ago 2026) sobre qué hace que un portafolio de developer consiga entrevistas — fuentes
completas al final del documento:

- Un README débil o ausente es la razón #1 por la que un proyecto bueno pasa desapercibido — los
  perfiles con README optimizado reciben ~3x más visitas e invitaciones a entrevista.
- Calidad sobre cantidad: 3-5 proyectos pulidos superan a 10 mediocres.
- Un demo en vivo (o al menos un video) quita fricción real — si hay que clonar, instalar Postgres y
  configurar `.env` solo para ver algo, la mayoría de quienes evalúan no lo hace.
- Sobre usar IA: no se trata de ocultarlo ni de sobre-explicarlo — una línea clara sobre **el rol de
  la persona** (qué decidió, qué revisó, qué haría distinto) pesa mucho más que mencionar o no la
  herramienta. El framing correcto es "usé Claude Code como par de desarrollo; cada decisión de
  arquitectura y producto fue mía", no una lista de features generadas.
- Un README que cuenta *problema → qué se rompió → qué se decidió* vale más que una lista de
  funcionalidades — esto es, literalmente, lo que ya hay documentado en `BACKLOG.md` y los commits de
  este proyecto; solo falta extraerlo y presentarlo.

## Diagnóstico actual del repo (sin filtro)

- **No existe ningún `README.md` en la raíz.** Solo `CLAUDE.md` (instrucciones para el agente, no
  para un humano) — quien entra al repo hoy no tiene ni idea de qué está mirando.
- Carpetas vacías (`assets/imagenes/`, `assets/diagramas/`, `.sistema/cache/`) y variantes legacy
  (`codigo/viejo/ProyectoDjango`, `codigo/viejo/ProyectoKeyServ`, `codigo/viejo/backup_fase3`) al
  mismo nivel visual que el proyecto real — confunde cuál es "el" proyecto a evaluar.
- Imágenes de marca sueltas en la raíz (`NuevoLogo.png`, `ImagenConcepto.png`) en vez de en
  `assets/imagenes/` (que ya existe como carpeta, vacía, para exactamente esto).
- `docs/` mezcla la tesis académica (`docs/nuevo`, `docs/plantilla` — PDF y texto de tesis) con
  documentación de ingeniería real (`PLAN_MIGRACION_IONIC.md`, `BACKLOG.md`, esta carpeta) — un
  evaluador técnico no necesita ver la tesis para juzgar el trabajo de ingeniería.
- No hay nada desplegado públicamente — todo corre solo en local (Postgres local, `runserver`,
  `ng serve`).
- No hay CI (GitHub Actions) corriendo los 263 tests backend + 54 frontend automáticamente en cada
  push — señal barata de conseguir y muy valorada por quienes revisan repos técnicamente.

## Nivel 1 — imprescindible (decide si te dan la entrevista)

### 1.1 `README.md` en la raíz

Estructura recomendada, en este orden (según las fuentes: la gente lee los primeros 30 segundos, el
resto es para quien ya se enganchó):

1. **Título + una línea** — qué es KeyServ, en lenguaje de producto, no técnico ("marketplace de
   servicios del hogar con verificación biométrica de identidad").
2. **Screenshot o GIF** del catálogo/detalle de contratación — lo primero que se ve, antes que
   cualquier texto. (`ks-card-grid` del catálogo o el `ks-page-header` de inicio son buenas
   candidatas.)
3. **Demo / video** — link al demo desplegado (Nivel 2) si existe para entonces, si no, al video
   corto (ver 1.3).
4. **Stack** — badges o una lista corta: Django 5.2 + DRF, PostgreSQL, Ionic + Angular + Capacitor,
   JWT hecho a mano, Transbank/Khipu, biometría (huella + reconocimiento facial + nativa).
5. **Decisiones técnicas** (3-5 bullets, no el `CLAUDE.md` entero) — elegir las más defendibles en
   una entrevista: por qué JWT hecho a mano en vez de `simplejwt` (`Usuario` no es
   `AUTH_USER_MODEL`), por qué PostgreSQL sobre MySQL, por qué el trust-model de biometría nativa
   (el server no puede verificar el enclave seguro del teléfono, así que confía en el JWT ya
   autenticado), por qué dos pasarelas de pago (Webpay + Khipu) y no una sola.
6. **"Qué se rompió y cómo se resolvió"** — la sección más fuerte que tiene este proyecto y la que
   más impacto tiene según la investigación. Candidatos reales, ya documentados en `BACKLOG.md`/
   commits, elegir 2-3:
   - El bug del CNN fallback en reconocimiento facial: con luz baja, el detector de rostro se
     colgaba ~13 minutos y bloqueaba el servidor para *todos* los usuarios, no solo el que probaba
     — encontrado probando con luz real, no con un test unitario. Causa raíz + fix documentados en
     `CLAUDE.md`/Known Issues.
   - El bug de especificidad CSS del modo oscuro (dos veces: paleta oscura y luego paleta clara) —
     Ionic's `dark.system.css` le ganaba la cascada a la elección explícita del usuario.
   - El bug de sesión-fixation corregido en el hardening de seguridad (Fase 6).
   - El bug del login real que nunca funcionó por un desalineamiento `username`/`email` entre el
     template y el form — encontrado recién en Fase 5, meses después de "funcionar".
7. **Cómo correrlo local** — comandos reales (ya existen en `CLAUDE.md`, copiar la versión resumida).
8. **Sobre el uso de IA** (ver 1.4, se redacta aparte por su importancia).
9. **Licencia** (ver Nivel 3).

### 1.2 Limpieza de estructura

- Crear `docs/academico/` y mover ahí `docs/nuevo/`, `docs/plantilla/` (contenido de la tesis) —
  deja `docs/` como "documentación de ingeniería" a primera vista.
- Mover `NuevoLogo.png`/`ImagenConcepto.png` a `assets/imagenes/`.
- Evaluar si `codigo/viejo/` conviene quedar en el árbol principal o mover su contenido a un tag/
  branch de git (`legacy-pre-fase3`) y borrarlo del tree activo — más limpio para quien navega el
  repo, sin perder el historial (sigue disponible vía git). **Esto es una decisión a tomar, no
  ejecutar sin confirmar** — implica reescribir qué aparece en `main`/rama activa.
- Confirmar que `TesisAntigua/` (con emails personales) sigue gitignored y nunca se commiteó por
  error — chequeo rápido con `git log --all --full-history -- TesisAntigua` antes de tocar nada.
- Carpetas vacías (`assets/diagramas/`, `.sistema/cache/`): o se llenan con algo real (Nivel 2, ítem
  del diagrama de arquitectura) o se sacan del repo si van a seguir vacías — una carpeta vacía en un
  portafolio lee como "trabajo sin terminar".

### 1.3 Video corto (2-3 min)

Cubre lo que ningún demo en vivo puede mostrarle a un desconocido sin hardware propio: biometría por
cámara/huella, el flujo de pago con Transbank sandbox, la app nativa Android. Guión sugerido:
catálogo → contratar un servicio → chat → confirmar con re-autenticación → pagar (Webpay sandbox) →
completar → calificar → un vistazo rápido a `/admin/` (moderación) → cierre mostrando la app nativa
Android con biometría. Grabar con el navegador + el emulador ya configurado (ambos entornos ya
funcionan, no hace falta setup nuevo).

### 1.4 Sección "Sobre el uso de IA" — cómo redactarla

Según la investigación, el framing que mejor funciona es específico y centrado en el rol de la
persona, no en la herramienta. Borrador base (ajustar tono):

> Este proyecto se construyó con Claude Code como par de desarrollo. Yo tomé cada decisión de
> arquitectura y producto (ver "Decisiones técnicas" arriba), revisé y dirigí cada cambio, y
> verifiqué en vivo cada funcionalidad antes de darla por cerrada — incluyendo probar la app nativa
> Android en un emulador real, la integración de pagos contra el sandbox real de Transbank, y la
> biometría facial contra una webcam real. Usar IA para escribir el código me permitió enfocar mi
> tiempo en decisiones de diseño, seguridad y arquitectura — que es donde está el trabajo de
> ingeniería real, y donde puedo defender cada elección en una entrevista.

Evitar: no mencionar el uso de IA en absoluto (para el estándar de 2026 leería como evasivo), o
listar "funcionalidades generadas por IA" como si fueran logros propios sin filtrar por juicio
humano.

## Nivel 2 — separa esto de "otro portafolio más"

### 2.1 CI con GitHub Actions

Un solo workflow, dos jobs (backend/frontend), corriendo en cada push a `api-ionic-migration` y en
cada PR a `master`. Boceto:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env: { POSTGRES_PASSWORD: postgres }
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.14' }
      - run: pip install -r requirements.txt
      - run: python codigo/backend/django/manage.py test KeyServApp
        env: { DATABASE_URL: postgres://postgres:postgres@localhost:5432/postgres }
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: codigo/frontend/ionic } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npx ng test --watch=false --browsers=ChromeHeadlessCI
        # ChromeHeadlessCI = ChromeHeadless con --no-sandbox, necesario en runners de GitHub
```

Con esto corriendo verde, un badge `![Tests](.../workflows/tests.yml/badge.svg)` va arriba del todo
del README — es la señal más barata y más creíble de disciplina de ingeniería que existe.

### 2.2 Demo desplegado

**Backend: Render. Frontend: Netlify** (decidido con el usuario, 2026-08-16) — sin tarjeta de
crédito, Postgres administrado en Render, `netlify.toml` con el redirect de SPA que necesita el
router de Angular.

**Toda la configuración de deploy ya está lista en el repo (2026-08-16), falta solo la parte que
tiene que hacer el usuario a mano (crear las cuentas, conectar el repo — Claude no puede crear
cuentas de terceros):**

- `render.yaml` (raíz del repo) — Blueprint con el servicio web + una base Postgres. Nombre fijo
  del servicio (`keyserv-api`) para que la URL sea predecible.
- `render_build.sh` (raíz) — instala `requirements-render.txt` (subconjunto sin
  opencv/dlib/face_recognition, mismo criterio que `requirements-ci.txt` — el alcance del demo no
  los necesita), corre `collectstatic`/`migrate`/`loaddata catalogos_iniciales`/
  `sembrar_datos_demo`.
- `KeyServApp/management/commands/sembrar_datos_demo.py` — comando idempotente nuevo: siembra 8
  proveedores (uno por categoría, en las 9 comunas RM ya geocodificadas — así el filtro de radio
  muestra distancias reales) + 3 clientes + 4 contrataciones (una por cada estado del BPMN, con
  historial/chat/pago/reseña según corresponda) + cuentas `admin`/`moderador` de `/admin/`. Cubierto
  por `SembrarDatosDemoCommandTests` (3 tests) — encontró y corrigió un bug real: `loaddata`
  corrido después de la migración 0027 pisa las coordenadas de las comunas con `NULL` (el fixture
  original no las trae); el comando las reaplica él mismo, así que no importa en qué orden corran.
- `settings.py` — `whitenoise` (estáticos, `CompressedManifestStaticFilesStorage`, probado con
  `collectstatic` real sin errores), `DATABASES` acepta `DATABASE_URL` (lo que entrega Render) sin
  romper el `.env` local de siempre, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` se completan solos con
  `RENDER_EXTERNAL_HOSTNAME`, y el backend de correo ya no depende de `DEBUG` (sin esto, `/recuperar/`
  en Render con `DEBUG=False` y sin SMTP real habría respondido 500 en vez de degradar).
- `codigo/frontend/ionic/netlify.toml` + `environment.prod.ts` (con la URL fija de Render ya
  cargada) — build de producción probado local (`npm run build`, sin errores ni warnings de budget).

**Alcance del demo** (decisión ya tomada): catálogo público + cuenta/login + contrataciones + pago
Webpay (sandbox de integración, sin cuenta real) + búsqueda por geolocalización. **Sin** biometría
nativa ni reconocimiento facial ni Khipu (Khipu ya degrada solo con un error claro sin
`KHIPU_API_KEY`, no hace falta deshabilitarlo a mano). El video (1.3) cubre lo que el demo no puede.

**Hecho — desplegado y verificado en vivo, 2026-08-16.** Backend en Render
(`https://keyserv-api.onrender.com`, servicio `keyserv-api`), frontend en Netlify
(`https://keyserv.netlify.app`). Tres problemas reales encontrados y corregidos en el camino, ninguno
anticipado en el plan original:

- **Netlify tomaba `master` como rama de producción por defecto** (el proyecto se conecta al repo
  completo, no a una rama específica al crear el Blueprint como sí pide Render) — y todo el código de
  Ionic vive solo en `api-ionic-migration`, nunca se mergeó a `master`. Build fallaba con "Base
  directory does not exist". Arreglado en Netlify → Project configuration → Build & deploy → Branches
  and deploy contexts → Production branch.
- **CORS bloqueaba todo el sitio** — las dos variables `sync: false` de Render (`CORS_ALLOWED_ORIGINS`/
  `IONIC_FRONTEND_URL`) habían quedado con el placeholder `http://localhost:8100` de las instrucciones
  originales; sin actualizarlas con la URL real de Netlify, cualquier fetch desde el sitio desplegado
  fallaba con "Failed to fetch" (confirmado en la consola del navegador antes de arreglarlo).
- **El sitio de Netlify nacía privado** ("Private by default", feature nueva de Netlify) — solo
  miembros del team podían verlo aunque el deploy funcionara. Project configuration → Visitor access →
  Edit visibility → Public.

Verificado en vivo en el sitio real (no solo curl): catálogo con las 8 publicaciones demo, login real
con `cliente.demo@demo.keyserv`, dashboard mostrando la contratación demo sembrada. Credenciales y URL
ya están en el README.

### 2.3 Diagrama de arquitectura

Una imagen, no un muro de texto — Django+DRF ↔ Ionic/Angular (JWT), con el flujo del "strangler fig"
(templates Django retirándose área por área). Herramientas gratis: [Excalidraw](https://excalidraw.com)
(estilo dibujado a mano, rápido) o [Mermaid](https://mermaid.js.org) embebido directo en el README
(GitHub lo renderiza nativo, sin exportar imagen). Mermaid es la opción de menor fricción — se
mantiene como texto versionado junto al README.

## Nivel 3 — pulido final

- **Licencia**: agregar `LICENSE` (MIT es lo estándar para un portafolio — permisiva, no impide que
  a futuro se relicencie si el proyecto 1 de la conversación original avanza).
- **Badges** en el README: build/tests (de 2.1), stack (Django/Angular/PostgreSQL), licencia.
- **Carta Gantt**: linkear el artifact ya publicado
  (`https://claude.ai/code/artifact/aea584bb-cc91-4a5a-8bf0-238cd886903b`) desde el README como
  evidencia de proceso — recordar compartirlo desde el menú de la página antes, sigue privado por
  defecto.

## Por dónde arrancar mañana

**Nivel 1, en este orden**: 1.2 (limpieza de estructura) antes que 1.1 (README) — escribir el README
sobre una estructura que se va a reordenar después duplica trabajo. Luego 1.1, luego 1.4 (la sección
de IA se redacta con calma, no se improvisa). 1.3 (video) puede ir en paralelo o al final, no bloquea
nada.

## Fuentes

- [Developer Portfolio Guide 2026 (Hakia)](https://hakia.com/skills/building-portfolio/)
- [Building a Developer Portfolio in 2026: What Actually Gets Attention (Hyperskill)](https://hyperskill.org/blog/post/building-a-developer-portfolio-in-2026-what-actually-gets-attention)
- [The Right Way to List AI-Assisted Projects (CoreCV)](https://blog.corecv.ai/ai-projects-resume/)
- [Building a Portfolio That Shows Your Skills, Not Just AI (Vibe Coder)](https://blog.vibecoder.me/building-a-portfolio-that-shows-your-skills-not-just-ai)
- [The Complete Software Engineer Portfolio Guide + 24 Examples (CareerFoundry)](https://careerfoundry.com/en/blog/web-development/software-engineer-portfolio/)
- [What to include on project READMEs as a beginner in tech (Isabel Costa)](https://isabelcosta.github.io/posts/how-to-showcase-projects-on-readmes/)
- [Monorepo: Hands-On Guide (Aviator)](https://www.aviator.co/blog/monorepo-a-hands-on-guide-for-managing-repositories-and-microservices/)
- [Platforms with a real free tier for developers in 2026 (Render)](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026)
- [Deploying a Django App on Railway/Render/Heroku Free Tier (Medium)](https://medium.com/@gulsaba.fiha/deploying-a-django-app-on-railway-render-heroku-free-tier-in-2025-a-complete-guide-for-lazy-fb2a4ef5191b)
- [Automating Django Tests with GitHub Actions (Honeybadger)](https://www.honeybadger.io/blog/django-test-github-actions/)
- [django-pytest-github-actions example repo](https://github.com/MattSegal/django-pytest-github-actions/blob/master/.github/workflows/tests.yml)
