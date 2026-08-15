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

### Fase 3 — Cuenta de usuario ✅

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
- **Recuperación de contraseña ✅** — `POST /api/auth/recuperar/` +
  `GET`/`POST /api/auth/recuperar/confirmar/<token>/` reusan
  `RecuperarForm`/`NuevaPasswordForm` y los helpers de token firmado
  (`_generar_token_recuperacion`/`_usuario_desde_token_recuperacion`,
  `django.core.signing`) tal cual del lado template, mismo rate-limit y
  mismo mensaje genérico "exista o no la cuenta". Diferencia real con el
  template: el link del correo apunta a `settings.IONIC_FRONTEND_URL`
  (nueva env var), no a una URL de Django — quien pide la recuperación es
  el cliente Ionic, así que el paso 2 también se resuelve ahí
  (`recuperar/confirmar/confirmar.page`, con un `GET` previo que valida el
  token antes de mostrar el formulario, para no hacer perder tiempo
  llenando una contraseña nueva con un link ya vencido). Verificado en vivo
  por `curl` contra la cuenta demo real: pedido → link real en el log del
  `runserver` (backend de email de consola en `DEBUG=True`) → token
  validado. No se probó el cambio de contraseña real de punta a punta
  contra la cuenta demo (para no alterar la contraseña documentada en
  CLAUDE.md) — ese paso específico solo tiene cobertura de tests
  automatizados (`test_post_confirmar_con_token_valido_cambia_la_contrasena`).
- **Perfil de proveedor ✅** — `PUT /api/auth/perfil-proveedor/` reusa
  `CrearPerfilForm` tal cual (misma fusión de `areas_servicio` + texto
  libre en un solo string que el template), y agrega
  `GET /api/auth/perfil-proveedor/documentos/` /
  `DELETE /api/auth/perfil-proveedor/documentos/<id>/` (equivalentes de
  la lista y el borrado de certificados de `crearperfil.html`). Los
  certificados rechazados por `validators.py` (formato/tamaño/contenido
  inválido) no tiran un 400 — se listan en `documentos_rechazados` y el
  resto del perfil se guarda igual, mismo criterio que
  `crear_perfil_view`. Nuevo catálogo público
  `GET /api/catalogos/categorias/` (`CATEGORIAS_PUBLICACION`, forms.py)
  alimenta el checkbox multi-select de `perfil/proveedor/proveedor.page`.
  Verificado en vivo por `curl` contra la cuenta demo real (guardado de
  áreas/experiencia, listado de documentos), restaurado después para no
  dejar los datos demo mutados — la subida de un certificado válido por
  `curl` no se pudo verificar en vivo (el PDF armado a mano en la shell
  no pasó el chequeo de bytes de `validators.py`), pero sí tiene
  cobertura de tests automatizados (`PerfilProveedorApiTests`, que reusa
  el mismo `SimpleUploadedFile` que ya pasaba en `CrearPerfilTests` del
  lado template).
- **Preferencias de cuenta ✅** — `PUT /api/auth/preferencias/` (reusa
  `PreferenciasCuentaForm`) y `POST /api/auth/cambiar-password/` (reusa
  `CambiarPasswordForm`, exige la contraseña actual) — dos endpoints
  independientes en vez de un solo formulario con campo oculto `form`
  como en el template, porque acá cada uno ya es su propia request.
  Verificado en vivo por `curl` contra la cuenta demo real: toggle de
  notificaciones, cambio de contraseña exitoso (confirmado con un login
  posterior usando la contraseña nueva) y rechazo con la contraseña
  actual incorrecta — todo restaurado después al valor original.

### Fase 4 — Núcleo transaccional ✅

Contrataciones (crear → confirmar → pagar → completar → valorar),
mensajería por trabajo (`Conversacion`/`Mensaje`), pagos (Webpay/Khipu). Es
la parte de mayor riesgo (dinero real, estado con muchas transiciones) por
eso se deja para después de validar el patrón en fases más simples.
Dividida en piezas, orden confirmado con el usuario (2026-08-14):

1. **Contrataciones (listar/solicitar/detalle) ✅** —
   `GET`/`POST /api/contrataciones/` (equivalentes de `reservas_view` +
   `contratacion_crear_view`) y `GET /api/contrataciones/<id>/`
   (equivalente de la mitad "detalle" de `contratacion_detalle_view`, sin
   el chat). 404 — no 403 — para una contratación ajena, mismo criterio
   que `documento_descargar_view` (no confirmarle a quien pregunta que el
   recurso existe), con el intento registrado en `IntentoAccesoSospechoso`
   igual que el template. Ionic: `reservas.page` (listado) + botón
   "Contratar" en `catalogo/detalle.page` (llama a
   `Contrataciones.solicitar` y redirige al detalle de la contratación
   recién creada; sin sesión, manda a `/login`).
2. **Mensajería por contratación ✅** — `GET`/`POST
   /api/contrataciones/<id>/mensajes/`, equivalente de la parte de chat
   embebida en `contratacion_detalle_view` (`GET` también marca
   `ultimo_leido`, igual que el template). Ionic: embebido en
   `contratacion/detalle/detalle.page`.
3. **Confirmar/completar con reautenticación ✅** — `POST
   /api/contrataciones/<id>/confirmar/` y `/completar/` reusan
   `ReautenticacionForm`/`MontoAcordadoForm` tal cual, y el mismo
   rate-limit por (usuario, contratación)
   (`_reautenticacion_bloqueada`/`_registrar_intento_reautenticacion`,
   importados de `views.py`, no reimplementados). La hoja de presupuesto
   opcional (`ItemPresupuesto`) tiene su propio parser API
   (`_parsear_items_presupuesto_api`, sobre una lista de objetos JSON en
   vez de `request.POST.getlist(...)` — la única pieza de esta fase que no
   pudo reusar el helper del template tal cual, por la forma en que llega
   el body) pero no está en la pantalla de Ionic todavía — solo el monto
   único. Ionic: formulario de reautenticación embebido en
   `contratacion/detalle/detalle.page`, mismo componente para confirmar y
   completar.
4. **Valoraciones ✅** — `POST /api/contrataciones/<id>/valoracion/`
   reusa `ValoracionForm`, sube fotos con el mismo `validators.py` que el
   resto del sitio (las rechazadas se listan en `imagenes_rechazadas` sin
   tirar un 400 — la reseña ya se guardó, mismo criterio que
   `documentos_rechazados` en `PerfilProveedorView`) y recalcula el
   `Ranking` del proveedor. Ionic: formulario embebido en
   `contratacion/detalle/detalle.page`, visible solo cuando
   `estado === 'COMPLETADA'` y todavía no hay `valoracion`.
   Verificado en vivo por `curl` contra cuentas demo reales: flujo
   completo solicitar → mensaje del cliente → el proveedor lee (marca
   leído) y confirma con un monto acordado → (`EN_CURSO` fijado a mano
   vía `manage.py shell`, ya que los pagos son la pieza 5, todavía sin
   migrar) → el cliente completa (password incorrecta rechazada primero)
   → valora → detalle final muestra el historial de 4 estados y la
   reseña `PENDIENTE`. También verificado: un tercer usuario no puede ver
   el detalle ni los mensajes ajenos (404 + `IntentoAccesoSospechoso`), no
   se puede volver a confirmar una contratación que ya no está
   `SOLICITADA`, y completar sin haber pasado por `EN_CURSO` da 404. La
   contratación de prueba se borró después para no dejar datos demo
   mutados.
5. **Pagos (Webpay/Khipu) ✅** — decisión de diseño tomada con el
   usuario: el retorno del pago se movió de una URL de Django a la app
   Ionic (`IONIC_FRONTEND_URL`), igual que ya se hacía con la
   recuperación de contraseña — no una página de este sitio. `POST
   /api/contrataciones/<id>/pagos/webpay/iniciar/` devuelve `{token,
   url_pago}` en vez de renderizar la página de auto-submit del template
   — el `<form>` que hace el POST real a Transbank (su protocolo lo
   exige, no alcanza una navegación GET) se arma del lado de Ionic
   (`contratacion/detalle/detalle.page.pagarConWebpay()`). `POST
   /api/pagos/webpay/confirmar/` (sin autenticación, mismo motivo que la
   vista de template: Transbank redirige de vuelta al navegador del
   usuario, no manda ningún JWT nuestro) es adonde la nueva pantalla
   `pago/webpay/retorno` manda el `token_ws`/`TBK_TOKEN` que haya
   recibido por query string. Khipu es más simple del lado del cliente
   (`POST /api/contrataciones/<id>/pagos/khipu/iniciar/` devuelve
   `{payment_url}`, Ionic solo navega ahí con `window.location.href` —
   sin el truco del `<form>`) — `GET
   /api/contrataciones/<id>/pagos/khipu/estado/` (equivalente de
   `pago_khipu_retorno_view`, reconsulta si sigue `PENDIENTE`) es adonde
   apunta `pago/khipu/retorno/:id`. El webhook servidor-a-servidor
   (`pago_khipu_notificacion_view`) se queda tal cual en Django — nunca
   lo llama el navegador, así que no había ninguna razón para moverlo.

   **Verificado en vivo de punta a punta, incluido un click-through real
   en el navegador** (la extensión de Chrome por fin conectó esta sesión,
   primera vez en toda la migración): `POST
   /api/contrataciones/<id>/pagos/webpay/iniciar/` contra el sandbox
   público real de Transbank devolvió un token/URL reales; y desde la
   propia app Ionic corriendo en Chrome se completó el pago con una
   tarjeta de prueba de Transbank en el simulador de banco real,
   volviendo a `/pago/webpay/retorno`, confirmando el pago
   ("Pago aprobado — código de autorización..."), avanzando la
   Contratacion a EN_CURSO, completando el trabajo (reautenticación) y
   dejando una calificación — el primer recorrido de clic real de punta
   a punta de toda la migración (Fases 1-4), no solo `curl`/tests
   automatizados. Khipu no se pudo probar en vivo (sigue sin cuenta real,
   ver Known Issues de CLAUDE.md) pero `pago_khipu_iniciar` devuelve el
   mismo error claro (503, "KHIPU_API_KEY no configurado") que ya daba el
   template, verificado en vivo igual.

Los pagos necesitan atención especial en nativo: el flujo de redirect a
Transbank/Khipu no puede ser una navegación de página completa como en web
— en Capacitor se resuelve con el plugin `@capacitor/browser` (ventana
in-app) en vez de `window.location`.

### Fase 5 — Biometría nativa ✅ (núcleo + fallback de cámara hechos)

Reemplaza el reconocimiento facial pesado que hoy corre en el servidor
(`opencv-python`/`dlib-bin`/`face_recognition`, ver CLAUDE.md Known Issues)
por biometría nativa del dispositivo (Face ID / huella del teléfono) vía un
plugin Capacitor. Esto es lo que permite retirar todo ese stack de
dependencias del backend, como ya estaba anotado en `requirements.txt`. La
huella dactilar actual (`codigo/biometria/huella/`) es un pipeline propio
distinto a la huella del sistema operativo — decidir en su momento si
también se reemplaza por la biometría nativa del teléfono o se mantiene
aparte.

**Hecho**: plugin elegido `@capgo/capacitor-native-biometric` (gratis,
mantenido, `peerDependency @capacitor/core >=8.0.0` — coincide con lo ya
instalado; implementación dummy para web así `ng serve` no se rompe).
`POST /api/auth/verificar-biometria-nativa/` (`VerificarBiometriaNativaView`)
marca `verificado_biometricamente=True` confiando en la sesión JWT ya
autenticada — decisión de diseño tomada con el usuario: a diferencia de
`/rostro/`/`/huella/`, acá el servidor nunca ve ni puede ver el dato
biométrico (se valida enteramente en el enclave seguro del teléfono), así
que la única garantía real que puede pedir es una sesión ya válida, sin
reautenticación adicional. Pantalla `biometria/biometria.page` (Ionic).

**Se instaló el entorno de desarrollo Android local en esta sesión**
(Android Studio + SDK + emulador, ver CLAUDE.md Known Issues para el
detalle completo de la instalación no interactiva y los problemas
encontrados — versión de JDK, aceptación de licencias, `cleartextTraffic`,
etc.) y se armó el proyecto nativo Android (`npx cap add android`,
`codigo/frontend/ionic/android/`). **Verificado en vivo de punta a punta
con un build real**: instalado y corrido en un AVD (`KeyServ_Test`, Pixel
6, Android 16/API 36), con un PIN configurado y una huella real enrolada
(simulada con `adb emu finger touch`) — login contra el backend real,
navegación a "Verificación biométrica", `BiometricPrompt` real del sistema
aprobado con el sensor simulado, y confirmación de que
`verificado_biometricamente` quedó en `True` en Postgres (revertido
después para no dejar datos demo mutados). Sin build de iOS — no hay Mac
disponible en este entorno; ver la nota de "Xcode Cloud/Capgo Cloud
Build/rentar un Mac" más arriba si hace falta iOS antes de la Fase 8.

**Reconocimiento facial por cámara portado a Ionic (web + nativo)**: a
pedido explícito del usuario — "es alternativa en caso de que no se pueda
usar la huella o viceversa" — se agregó el flujo de cámara con prueba de
vida por parpadeo (el mismo pipeline que ya usa `/rostro/` del lado
template) también en Ionic, para cubrir el caso de un dispositivo sin
sensor biométrico nativo disponible. Nuevos endpoints
`GET /api/auth/rostro/estado/` + `POST /api/auth/rostro/registrar/` +
`POST /api/auth/rostro/verificar/` (`RostroEstadoView`/`RostroRegistrarView`/
`RostroVerificarView`, reusan `biometria.calcular_encoding_facial`/
`verificar_rostro_usuario` sin reimplementar nada) + pantalla
`rostro/rostro.page` (Ionic) — puerto directo a TypeScript de la captura
`getUserMedia`/`<canvas>` de `_captura_camara.html`, con
`@capacitor/camera` cebando el permiso nativo de cámara al entrar a la
pantalla. Enlazada desde `home.page` y desde el fallback de
`biometria.page` cuando el dispositivo no tiene Face ID/huella nativa.
**Verificado en vivo con webcam real en las tres superficies**: template
Django (`:8000/rostro/`), Ionic web (`:8100/rostro`) y la app Android
nativa (ver CLAUDE.md Known Issues para el detalle del segundo AVD
`KeyServ_Test2` que hizo falta crear — el `KeyServ_Test` original, API 36,
resultó tener un bug real del sistema que impedía lanzar cualquier APK
recién instalado tras este cambio). `manage.py test KeyServApp` pasó de
219 a 228 tests (9 nuevos en `tests_api.py`, `RostroApiTests`); `ng test`
sigue en 29/29.

**Pendiente, sin decidir todavía**: retirar el stack de reconocimiento
facial del servidor (`codigo/biometria/reconocimiento_facial/`,
`opencv-python`/`dlib-bin`/`face_recognition`) — el plan original lo
condicionaba a que existiera un biométrico nativo verificado, que ya
existe, pero en vez de retirarlo el usuario pidió extenderlo a Ionic (ver
arriba), así que ahora depende de él tanto el template como Ionic
(web + nativo) — retirarlo sigue siendo una decisión aparte que el usuario
todavía no tomó, y ahora tiene más superficies que dejarían de funcionar
si se hace. Tampoco se decidió si la huella dactilar propia
(`codigo/biometria/huella/`) se reemplaza o se mantiene aparte. WebAuthn se
evaluó como alternativa futura (recomendado por Claude cuando se preguntó
por biometría "profesional e intuitiva" en web+app) pero se descartó por
ahora por ser redundante con el port de cámara recién hecho — no
implementado.

### Fase 6 — Identidad visual ✅

La app Ionic corría con el tema por defecto de `ionic start` (grises/
azules genéricos), no con la paleta navy/teal/coral + tipografía Quicksand/
Nunito que ya tiene el sitio Django (`base.css`) — decisión explícita del
usuario (2026-08-13): terminar de portar toda la funcionalidad primero
(Fases 1-5) y recién ahí hacer una pasada de diseño completa, en vez de
ir maquillando pantalla por pantalla a medida que se construyen.

**Hecho (2026-08-14)**: paleta navy/teal/coral (clara + oscura, igual que
`base.css`) portada a `src/theme/variables.scss`, mapeada directamente a
los `--ion-color-primary/secondary/tertiary/...` nativos de Ionic — todos
los componentes (`ion-button`, `ion-badge`, `ion-card`, `ion-toolbar`) heredan
la marca automáticamente en las 16 pantallas sin tocarlas una por una.
Tipografía Quicksand/Nunito vía Google Fonts, botones tipo píldora
(`--border-radius: 999px`), cards redondeadas con sombra, franja-gradiente
de marca en los toolbars, logo (`assets/logo.png`, recomprimido de 2.6MB a
~80KB) en los headers de las pantallas raíz (login/catálogo/home — las
pantallas con botón atrás no lo llevan, siguen convención de app móvil, no
de sitio web). Los badges de estado de contratación (`reservas.page`,
`contratacion/detalle`) ahora comparten un único `Contrataciones.colorEstado()`
(antes duplicado y con mapeo distinto en cada pantalla) que replica
exactamente la semántica de `.ks-badge-*` en `base.css`: coral = pendiente
de acción, teal = confirmada/en curso, navy = completada, gris =
cancelada/rechazada.

**Bug real encontrado y corregido en el camino**: el propio `dark.system.css`
de Ionic define `--ion-background-color`/`--ion-toolbar-background`/etc.
bajo selectores `:root.md`/`:root.ios` (más específicos que un `:root`
simple), así que esas propiedades puntuales le ganaban a mis overrides pese
a cargar después en el bundle — mientras que `--ion-color-primary` (definido
por Ionic solo a nivel `:root` liso) sí se pisaba bien. Fix: usar
`:root, :root.ios, :root.md { ... }` en el bloque de modo oscuro de
`variables.scss` para igualar la especificidad. Verificado corrigiendo el
`getComputedStyle` real del navegador antes/después, no solo revisando el
SCSS fuente.

**Verificado en vivo** (Chrome, modo oscuro real del SO — no emulado):
login, catálogo, home, reservas, detalle de contratación (chat, historial,
botones de pago) y registro, todos con la paleta nueva aplicada
correctamente. Modo claro solo verificado por análisis de CSS (no hubo
captura real en esa variante). 29/29 tests de Angular siguen pasando.

**Segunda pasada, misma sesión (2026-08-14): estructura/dimensiones.** El
usuario marcó, viendo las capturas de la primera pasada, que las pantallas
se veían "alargadas y sin estructura" — cierto: Ionic es mobile-first y
asume que el viewport es el ancho del dispositivo, así que en `:8100` sobre
navegador de escritorio el contenido se estiraba de punta a punta sin
ninguna columna ni agrupación visual. Dos arreglos, ambos globales (no
pantalla por pantalla):
- `ion-content::part(scroll) { max-width: 720px; margin-inline: auto }` en
  `global.scss` — centra el contenido con un ancho de lectura razonable en
  pantallas anchas, sin achicar nada en un viewport angosto real (`::part`
  es la forma soportada de estilar el interior de un `ion-content` desde
  fuera de su shadow DOM).
- `.ks-section`/`.ks-section-title` (también en `global.scss`) — el patrón
  reusado en cada pantalla para agrupar contenido relacionado bajo un
  título Quicksand y una `ion-card`, en vez de listas sueltas corriendo
  una tras otra sin separación. Aplicado a las 12 pantallas con contenido
  (login, registro — 3 secciones: datos personales/ubicación/cuenta —,
  editar perfil, perfil de proveedor — 2 secciones —, preferencias — 2
  secciones —, recuperar y su confirmación, home — 2 secciones: datos del
  usuario + menú —, catálogo, reservas, catálogo/detalle — info +
  reseñas —, contratación/detalle — la más densa: encabezado, presupuesto,
  historial, pago, confirmar/completar, valorar, mensajes, cada una su
  propia card —, biometria, rostro). Las pantallas de resultado de pago
  (`pago/webpay|khipu/retorno`) se dejaron sin card por ser solo un
  mensaje + un botón — envolverlas no aportaba nada.

**Tercera pasada, misma sesión: fidelidad real al diseño de Django, en progreso, cortada por límite de sesión.**
El usuario, viendo las capturas de la segunda pasada, marcó que igual se
sentía "simple y sosa" comparada con el sitio Django — comparando en vivo
`/servicios/`, `/sesion/`(→`/inicio/`) y `/perfil/` del lado Django contra
lo hecho hasta ahí, la brecha real no era solo agrupar contenido en cards
genéricas: Django usa un patrón `.ks-page-header` (banda con gradiente,
ícono+título+subtítulo) en cada pantalla interna, `.ks-panel` (borde sutil,
sin sombra permanente — más "definido" que un card-con-sombra-siempre-
encendida), `.ks-avatar` (círculo con iniciales sobre el gradiente de
marca), y `/inicio/` (el dashboard autenticado) es mucho más rico que
un simple menú: saludo + 3 accesos rápidos (Buscar servicios/Mensajes/Mi
perfil) + panel "Trabajos actuales" con las contrataciones activas.

**Hecho en esta tercera pasada** (`global.scss`): `.ks-page-header`
(banda con gradiente, se sale del padding de `ion-content` con margen
negativo para llegar borde a borde de la columna de 720px en vez de quedar
metida adentro — ver comentario en el SCSS), `ion-card`/`ion-card-content`
rediseñados para parecerse a `.ks-panel` (borde en vez de sombra
permanente, padding 24px), `.ks-card-tile`/`.ks-card-grid` (grid de cards
con imagen, listo para usarse pero **todavía no aplicado al catálogo**),
`.ks-avatar-brand` (círculo con inicial), `.ks-quick-actions` (grid de 3
accesos rápidos). **`home.page` fue rediseñada de punta a punta** para
parecerse a `/inicio/`: banda "Hola, {{nombre}}", 3 accesos rápidos
(Buscar servicios/Mis contrataciones/Mi perfil — "Mensajes" se cambió por
"Mis contrataciones" porque Ionic no tiene una pantalla de mensajería
standalone, el chat vive embebido en `contratacion/detalle`), panel
"Trabajos actuales" (nueva llamada a `Contrataciones.listar()` filtrada a
estados no cerrados, primeras 3, con el mismo `colorEstado()` que
`reservas`/`contratacion/detalle`) con botón "Ver todas mis
contrataciones", y la tarjeta de identidad/menú de siempre debajo. Build
(`ng build`) y tests (`ng test`, 29/29) verificados en verde después de
este cambio — **pero no se alcanzó a verificar visualmente en vivo en
browser** (el login automatizado para probarlo falló por las mismas
limitaciones de coordenadas de siempre, y se cortó la sesión antes de
reintentar) — auditar visualmente al retomar antes de asumir que se ve
bien.

**Cuarta pasada (2026-08-14, sesión siguiente): cierre del punch list.**
1. **`home.page` verificado en vivo** contra `/inicio/` (Chrome real, sesión ya logueada): banda de saludo, 3 accesos rápidos, panel "Trabajos actuales" con badges de estado y "Tu cuenta" con avatar — coincide con el diseño de Django.
2. **`.ks-page-header` aplicado**, pero con alcance ajustado tras revisar el propio Django plantilla por plantilla en vez de asumir la lista de candidatas sugerida arriba: **sí** lleva header catálogo (`grid-outline`), reservas (`calendar-outline`, ícono real de `reservas.html`), perfil de proveedor (`briefcase-outline`), preferencias (`settings-outline`), contratación/detalle (`document-text-outline`, título+badge+contraparte+monto, dinámico) y catálogo/detalle (`storefront-outline`, título+badge de categoría+precio, dinámico) — mismo copy que sus plantillas Django (`catalogo.html`, `reservas.html`, `crearperfil.html`, `preferencias_cuenta.html`, `contratacion_detalle.html`, `detalleserv.html`). **No** lleva header login/registro/editar perfil/recuperar/recuperar-confirmar/biometría/rostro — se verificó que sus equivalentes Django (`sesion.html`, `registroinicio.html`, `editarperfil.html`, `recuperar.html`, `recuperar_confirmar.html`, `huella.html`, `rostro.html`) tampoco usan `.ks-page-header`, son formularios angostos centrados en un solo `.ks-panel`, no pantallas de sección con banner.
3. **Catálogo (`/catalogo`) convertido al grid de cards con imagen** (`.ks-card-grid`/`.ks-card-tile`), mismo layout que `/servicios/` (imagen de portada o placeholder, título, categoría/sub_título, precio, proveedor + rating en el footer). Se agregó `.ks-card-tile-img-placeholder` a `global.scss` (no existía) para el caso sin imagen.
4. **Avatar (`.ks-avatar-brand`) agregado en `catalogo/detalle`** para el proveedor sin foto de perfil (fallback junto al `ion-avatar` con foto real que ya existía).

Verificado en vivo (Chrome, modo oscuro): home, catálogo (grid), catálogo/detalle, reservas, contratación/detalle, perfil de proveedor, preferencias — todos con el header/grid nuevo aplicado correctamente. `ng test` (29/29) sigue en verde.

**Modo claro verificado en la misma sesión** (cambiando el tema real de Windows, no emulado, y volviendo a dejarlo en oscuro después): catálogo y home revisados en vivo, sin bugs — a diferencia del bug real que sí apareció en la primera pasada de modo oscuro, acá no hubo ningún problema de cascada/especificidad que corregir.

**Quinta pasada (misma sesión, 2026-08-14): páginas públicas que no tenían ningún equivalente Ionic todavía.** El usuario pidió explícitamente construir `home`/`servicios`/`catalogo`/`contacto` "con la calidad de las demás páginas Ionic/Angular" porque el objetivo del proyecto pasó a ser un entregable de portafolio vendible, no solo la paridad funcional ya lograda en Fases 1-5. Comparando contra el sitio Django surgió que faltaban por completo tres pantallas (no solo estilo, funcionalidad real):
1. **Landing pública** (`inicio.page`, ruta `''`) — equivalente de `/` (`paginicio.html`): hero con gradiente + búsqueda rápida + tags populares + 3 paneles de feature + "Servicios destacados" (reusa `Publicaciones.listar()`, sin endpoint nuevo) + footer con links a Acerca de nosotros/Contacto. `/catalogo` dejó de ser la landing (antes `''` redirigía ahí) y pasó a ser el listado completo puro, igual que Django separa `/` de `/servicios/`.
2. **Catálogo con filtros reales** (`catalogo.page`) — antes solo tenía scroll infinito sin forma de buscar/filtrar; se agregó una `.ks-filter-bar` (ion-searchbar + selects de región/calificación mínima/orden) que pega contra los mismos query params que ya aceptaba `PublicacionListView` (`q`/`region`/`calificacion`/`orden`) pero que ningún cliente usaba todavía. Reusa `Catalogos.regiones()` (ya existía para el registro).
3. **Acerca de nosotros** (`acerca.page`, `/acerca-de-nosotros`) — página estática nueva, mismo contenido que `Acercadeenosotros.html` (misión/visión/pilares/valores/equipo/CTA), con los 4 "pilares" en un grid estático en vez del carrusel Bootstrap del template (no valía la pena traer una librería de carrusel solo para esto).
4. **Contacto** (`contacto.page`, `/contacto`) — **esta sí necesitó backend nuevo**: no existía ningún endpoint API, solo la vista de template (`contacto_view`). Se agregó `ContactoView` (`POST /api/contacto/`, `api/views.py`) reusando `ContactoForm` sin cambios, mismo criterio que `RegistroView` reusando `RegistroForm` — `AllowAny`, usa los datos del `request.user` si hay JWT válido, pide nombre/correo si no. 3 tests nuevos en `tests_api.py` (`ContactoApiTests`).

**Bug real encontrado y corregido en el camino, no cosmético — un bloqueo de login real:** probando el flujo de contacto a mano con una sesión ya vencida en el navegador, `POST /api/contacto/` devolvía 401 pese a ser `AllowAny`. Causa: `authInterceptor` (Ionic) adjunta el access token guardado a *toda* request hacia la API sin excepción — incluido `POST /api/auth/login/` — y `JWTAuthentication.authenticate()` (backend) levantaba `AuthenticationFailed` ante cualquier token vencido/inválido, lo que DRF convierte en un 401 duro *antes* de que la vista (y su `permission_classes`) llegue a correr. En la práctica: una vez que el access token vence (20 min, sin refresh automático todavía — ver nota de Fase 7), la persona queda sin forma de volver a loguearse desde la UI salvo borrando `localStorage` a mano, porque el propio intento de login se rechazaba antes de mirar el email/contraseña del body. Arreglado en `KeyServApp/api/authentication.py`: un token vencido/inválido ahora se trata igual que "sin credenciales" (`return None`, no una excepción) — los endpoints `AllowAny` (login, registro, catálogo, contacto) funcionan igual que si nunca se hubiera mandado el header, y los protegidos (`IsAuthenticated`) siguen devolviendo 401 igual, solo que vía el mensaje genérico de DRF en vez del texto específico "el token expiró". 3 tests de regresión nuevos (`JWTAuthenticationTokenVencidoTests`) cubren los tres casos: login no bloqueado, endpoint público no bloqueado, endpoint protegido sigue en 401. Verificado también en vivo en el navegador (token corrupto inyectado a mano en `localStorage`, reintentado el login, funcionó).

**Otro bug menor encontrado y corregido**: el manejo de errores 400/401 en `contacto.page.ts` asumía que todo `error.error` tenía la forma `{campo: ["mensaje"]}` (la que arma `ContactoForm`) y explotaba (`mensajes.join is not a function`) contra la forma `{detail: "mensaje"}` que usa DRF para sus propios errores genéricos — se descubrió recién al reproducir el bug de arriba. Corregido para manejar ambas formas.

Verificado en vivo, todo contra el backend real (no mocks): landing pública con destacados, búsqueda por texto en el catálogo filtrando resultados correctamente, Acerca de nosotros, y el flujo completo de Contacto enviando una consulta real que quedó guardada en `Consulta` (visible por un moderador en `/admin/`). `ng test` (32/32) y `manage.py test KeyServApp` (234/234, incluye los 6 tests nuevos) en verde.

Con esto, la landing/catálogo/Acerca de nosotros/Contacto quedan al mismo nivel de terminación que el resto de la app — no queda ninguna pantalla pública del sitio Django sin su equivalente Ionic. Pendiente real para más adelante (no bloqueante): registro/login no tienen `.ks-page-header` a propósito (mismo criterio que Django), pero tampoco tienen el footer de Acerca de nosotros/Contacto — agregarlo ahí es solo cuestión de repetir el mismo bloque, no se hizo por no haber sido pedido explícitamente.

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
