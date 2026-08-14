# Plan de migración del frontend a Ionic — KeyServ

Este documento reemplaza al "plan de migración" que se había discutido en una
sesión anterior y nunca quedó escrito en el repo — se perdió al resumirse la
conversación. Para que no vuelva a pasar, queda acá, versionado junto con el
código, y se referencia desde `CLAUDE.md`.

## Objetivo

Migrar el frontend completo (hoy templates de Django) a una app Ionic/Angular
que corra en **web, Android e iOS desde un solo código fuente** (vía
Capacitor), dejando Django como backend puro: API REST + admin/moderación.
Además de la razón de producto, esto es un entregable de portafolio — el
código Ionic/Angular queda comentado explicando qué hace cada pieza
específica del framework (decorators, DI, RxJS, guards, interceptors), no
solo el "por qué" de las decisiones de negocio.

## Stack elegido: Ionic + Angular + Capacitor

Confirmado con investigación actual (agosto 2026), no solo la recomendación
original:

- **Ionic** da los componentes de UI (ya se ven en `login.page.html`:
  `ion-input`, `ion-list`, etc.) que se adaptan al look nativo de iOS/Android
  automáticamente. Es la opción más rápida de arrancar para un equipo que ya
  sabe desarrollo web (Angular/TypeScript) — que es el perfil del equipo acá
  — a costa de rendimiento algo menor que Flutter en animaciones muy
  exigentes, irrelevante para un marketplace de servicios (formularios,
  listados, chat, no juegos ni animaciones 3D).
- **Capacitor** es el puente a nativo (reemplazo moderno de Cordova) — mismo
  código Angular corre en el navegador y, empaquetado, como app Android/iOS
  real con acceso a cámara, biometría del dispositivo, etc. Ya está en
  `package.json` (`@capacitor/core`, `@capacitor/app`, `@capacitor/haptics`,
  `@capacitor/keyboard`, `@capacitor/status-bar`) y `capacitor.config.ts`
  desde el scaffold inicial.
- Se descartó Flutter (Dart, curva de aprendizaje nueva para el equipo,
  sin ganancia real para este tipo de app) y React Native (hubiera
  significado reescribir la lógica de UI en JSX en vez de reusar el
  vocabulario de templates que el equipo ya tiene de Django).

Fuentes: [Flutter vs React Native vs Ionic 2025](https://medium.com/@kodekx-solutions/flutter-vs-react-native-vs-ionic-choosing-the-best-cross-platform-approach-in-2025-d365e06c0296), [Ionic vs Flutter vs React Native (Radixweb, 2026)](https://radixweb.com/blog/flutter-vs-ionic), [Capacitor + Angular patterns](https://claudeskills.info/skills/capawesome-team/skills/capacitor-angular/).

## Principio guía: strangler fig, no big-bang

La migración es **incremental por dominio funcional**, nunca un corte único:
cada fase agrega pantallas Ionic que hablan con `/api/*` y dejan de usarse
las vistas-template equivalentes recién cuando esa pantalla ya funciona
migrada — nunca antes. Esto permite parar entre fases con algo que sirve
(el sitio Django sigue andando en paralelo todo el proceso) y no exige que
toda la migración quede lista para tener valor. La regla práctica: **empezar
por los dominios de menor acoplamiento y menor riesgo, dejar el núcleo
transaccional (pagos, contrataciones) para cuando el patrón ya esté
probado.**

Fuente: [Strangler Fig Pattern](https://en.wikipedia.org/wiki/Strangler_fig_pattern).

## Qué NO migra

`/admin/` (Django admin, con el agrupamiento por tarea y el dashboard de
moderación ya construidos — ver CLAUDE.md "Admin & moderation") se queda tal
cual. Reconstruir un panel de administración/moderación en Ionic no aporta
nada — es una herramienta interna para moderadores/staff, no para los
usuarios finales que van a instalar la app.

## Nota de seguridad que cambia una decisión ya tomada

`Auth` (`codigo/frontend/ionic/src/app/core/auth.ts`) guarda los tokens en
`localStorage` hoy. Investigación (agosto 2026) confirma que **ni
`localStorage` ni `@capacitor/preferences` son aceptables para un JWT en una
build nativa real** — ambos son texto plano sin cifrar en el dispositivo.
Para producción nativa hace falta un plugin de almacenamiento seguro real
(Keychain en iOS / Keystore en Android) — candidatos: `@capacitor-community/secure-storage`
o Ionic Identity Vault (este último además da biometría de desbloqueo de
sesión, relevante para RF001 de KeyServ). Esto se resuelve en la Fase 6
(Hardening), no antes — mientras el target es solo el navegador de
desarrollo, `localStorage` alcanza y no vale la pena la complejidad todavía.

Fuente: [Secure Token Storage: Best Practices for Mobile Developers](https://capgo.app/blog/secure-token-storage-best-practices-for-mobile-developers/), [Capacitor Security guide](https://capacitorjs.com/docs/guides/security).

## Fases

### Fase 1 — Fundación de autenticación ✅ (commits `c18a711`, `ef5f775`)

API JWT hecha a mano (`KeyServApp/api/`, ver CLAUDE.md "API + Ionic
migration") + pantalla de login en Ionic + guard/interceptor + página
protegida mínima mostrando el perfil real. Verificado en vivo contra el
backend real vía `curl` (login + me con cuenta demo). Objetivo cumplido:
probar que el esquema JWT + CORS + DRF funciona de punta a punta antes de
construir nada más encima.

### Fase 2 — Catálogo público ✅

Backend: `GET /api/publicaciones/` (paginado, `PageNumberPagination`,
filtros `q`/`region`/`calificacion`/`orden` — mismos que `catalogo_view`,
reusando `Unaccent` de `views.py`) y `GET /api/publicaciones/<pk>/`
(equivalente de `publicacion_detalle_view`, incluye imágenes y reseñas ya
moderadas). Ambos `AllowAny` — públicos de verdad, decidido con el usuario.
Ionic: `catalogo.page` (listado con `ion-infinite-scroll`, decidido con el
usuario en vez de paginación por botones — más natural en mobile) y
`catalogo/detalle.page` (`/catalogo/:id`). `''` ahora redirige a `/catalogo`
en vez de `/home` — el catálogo es la landing pública, `/home` quedó para
después de loguearse. Verificado en vivo contra el backend real (demo data,
8 publicaciones) vía `curl` — igual que en Fase 1, sin poder clickear en el
navegador de verdad (extensión de Chrome desconectada).

### Fase 3 — Cuenta de usuario (en progreso)

Cinco piezas relativamente aisladas — se migran y prueban una por una, no
depende de que el resto ya esté hecho:

- **Registro ✅** — `POST /api/auth/registro/` reusa `RegistroForm`
  (forms.py) directamente en vez de duplicar sus reglas en un serializer
  aparte (mismo criterio que `LoginView` reusando el bloqueo de intentos).
  Catálogos de referencia públicos nuevos (`/api/catalogos/regiones/`,
  `/comunas/?region=<id>`, `/tipos-cuenta/`) alimentan los `<ion-select>`
  del formulario Ionic (`registro.page`, cascada región→comuna igual que
  `/ajax/load-comunas/`). Sin auto-login tras registrarse, a propósito
  (mismo criterio que `register_view`: "cuenta creada, ahora iniciá
  sesión"). Verificado en vivo por `curl`: registro → login con la cuenta
  recién creada, y el caso de error (`__all__` cuando las contraseñas no
  coinciden).
- **Editar perfil ✅** — `PUT /api/auth/perfil/` reusa `EditarPerfilForm`
  (`ModelForm`) directamente, mismo criterio que el registro — incluida su
  validación de email duplicado (excluyendo al propio usuario) y el manejo
  de `foto_perfil` (`ImageField` opcional, sube por `multipart/form-data`
  vía `request.FILES`, se deja intacta si no se manda una nueva). Se
  extendió `UsuarioMeSerializer` con `comuna`/`region` (antes no estaban)
  para poder precargar el cascade región→comuna del formulario Ionic
  (`perfil/editar/editar.page`) sin una request aparte. Verificado en vivo
  por `curl` contra la cuenta demo real (GET con los campos nuevos, PUT
  cambiando dirección/comuna, restaurado después para no dejar los datos
  demo mutados).
- ⏳ Recuperación de contraseña, perfil de proveedor, preferencias — sin empezar.

### Fase 4 — Núcleo transaccional

Contrataciones (crear → confirmar → pagar → completar → valorar),
mensajería por trabajo (`Conversacion`/`Mensaje`), pagos (Webpay/Khipu). Es
la parte de mayor riesgo (dinero real, estado con muchas transiciones) por
eso se deja para después de validar el patrón en fases más simples. Los
pagos necesitan atención especial en nativo: el flujo de redirect a
Transbank/Khipu no puede ser una navegación de página completa como en web
— en Capacitor se resuelve con el plugin `@capacitor/browser` (ventana
in-app) en vez de `window.location`.

### Fase 5 — Biometría nativa

Reemplaza el reconocimiento facial pesado que hoy corre en el servidor
(`opencv-python`/`dlib-bin`/`face_recognition`, ver CLAUDE.md Known Issues)
por biometría nativa del dispositivo (Face ID / huella del teléfono) vía un
plugin Capacitor. Esto es lo que permite retirar todo ese stack de
dependencias del backend, como ya estaba anotado en `requirements.txt`. La
huella dactilar actual (`codigo/biometria/huella/`) es un pipeline propio
distinto a la huella del sistema operativo — decidir en su momento si
también se reemplaza por la biometría nativa del teléfono o se mantiene
aparte.

### Fase 6 — Identidad visual

La app Ionic corre hoy con el tema por defecto de `ionic start` (grises/
azules genéricos), no con la paleta navy/teal/coral + tipografía Quicksand/
Nunito que ya tiene el sitio Django (`base.css`) — decisión explícita del
usuario (2026-08-13): terminar de portar toda la funcionalidad primero
(Fases 1-5) y recién ahí hacer una pasada de diseño completa, en vez de
ir maquillando pantalla por pantalla a medida que se construyen. Portar
la paleta a `src/theme/variables.scss` (las variables `--ion-color-*` de
Ionic), tipografía, logo, y revisar cada pantalla ya construida contra el
diseño del sitio Django.

### Fase 7 — Hardening de producción

Almacenamiento seguro real de tokens (ver nota de seguridad arriba),
endpoint de refresh token + rotación (`TokenSesion` ya existe para esto,
falta la vista), tests E2E (Cypress/Playwright para web, o Appium si hace
falta cubrir nativo), pipeline de build para Android/iOS.

### Fase 8 — Publicación y entregable de portafolio

Build firmado de Android (Play Store) e iOS (App Store) vía Capacitor,
íconos/splash, políticas de privacidad que piden las stores, y documentación
de arquitectura + capturas/video corto para mostrar en el portafolio.

## Abierto / a decidir con el usuario antes de cada fase

No asumir alcance de una fase sin confirmar primero — la Fase 1 ya se ajustó
una vez en esta misma migración (se preguntó explícitamente qué seguía en
vez de adivinar). En particular, para Fase 2 falta decidir: ¿el endpoint de
catálogo requiere autenticación o es público de verdad (como hoy en
`/servicios/`)?, ¿se pagina igual que el template (`PUBLICACIONES_POR_PAGINA
= 20`) o se ajusta para scroll infinito, más natural en mobile?
