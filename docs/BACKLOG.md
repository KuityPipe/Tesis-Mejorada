# Backlog — migración Ionic + producto KeyServ

## PRÓXIMA SESIÓN — empezar por acá

**Búsqueda por geolocalización — terminar lo que quedó pendiente de la sesión 2026-08-16.** El filtro
de radio ya funciona de punta a punta (ver "Hecho" más abajo), pero quedaron dos cosas explícitamente
fuera de alcance de esa sesión:
- **Fallback a la comuna guardada del usuario** cuando no da el permiso de geolocalización real —
  hoy, sin geolocalización real, el filtro de radio simplemente no aparece (`catalogo.page.ts`,
  `usarMiUbicacion()`). Implica: exponer `latitud`/`longitud` en `ComunaSerializer`
  (api/serializers.py), y en `Ubicacion`/`catalogo.page.ts` resolver la comuna del usuario logueado
  (`Auth.me()` → `comuna`/`region`) y buscar sus coordenadas si `posicionActual()` devuelve `null`.
- **Geocodificar más comunas.** Migración `0027_comuna_coordenadas_demo.py` solo cargó las 9 comunas
  RM que usa la data demo (coordenadas de la plaza principal, de memoria general — no verificadas con
  un geocoder real, ver el comentario en esa migración). El resto de las ~330 queda con
  `latitud`/`longitud` en `NULL` — no se completan todas de una, se van agregando según haga falta.
  Cualquier corrección a las 9 ya cargadas va en una migración nueva, no editando la `0027`.

## Otros ítems pendientes

Documento vivo (se actualiza cada sesión, a diferencia de `docs/AUDITORIA_8000_vs_8100.md`, que es
una foto fija del 2026-08-14). Acá se anota qué falta, en qué orden, y por qué — para no perder el
hilo entre sesiones y para tener un registro real del trabajo (útil también para portafolio: es la
prueba de que esto se llevó con metodología, no a los saltos).

Ver también: `docs/PLAN_MIGRACION_IONIC.md` (fases 1-8 de la migración, más técnico),
`docs/AUDITORIA_8000_vs_8100.md` (comparación sección por sección Django vs Ionic) y
`docs/PLAN_PORTAFOLIO.md` (plan en 3 niveles para presentar este proyecto como portafolio —
decidido 2026-08-15, arranca en la próxima sesión).

## Cómo se usa este documento

- Cada ítem tiene un estado: `[ ]` pendiente, `[~]` en progreso, `[x]` hecho.
- Al cerrar un ítem, se anota la fecha y qué se verificó (no alcanza con "se escribió el código" —
  tiene que estar probado, ver `CLAUDE.md` sobre el estándar de verificación de este proyecto).
- Prioridad = impacto real en el negocio (¿esto bloquea que alguien use la app de verdad?), no
  dificultad técnica.

## Hecho

- [x] Fases 1-5 de la migración (auth JWT, catálogo, cuenta de usuario, contrataciones/pagos,
      biometría nativa+facial) — 2026-08-13/14, ver `docs/PLAN_MIGRACION_IONIC.md`.
- [x] Fase 6, identidad visual (paleta, tipografía, `.ks-page-header`, grid de cards, modo claro
      verificado) — 2026-08-14.
- [x] Landing pública (`/`), catálogo con filtros reales (búsqueda/región/calificación/orden),
      Acerca de nosotros, Contacto (+ endpoint API nuevo `POST /api/contacto/`) — 2026-08-14.
- [x] **Bug de login real corregido**: un JWT vencido bloqueaba el login mismo (401 antes de mirar
      el body) — `authentication.py` ahora trata un token vencido/inválido como anónimo. 3 tests de
      regresión. — 2026-08-14.
- [x] Publicar un servicio (`/catalogo/crear` + `POST /api/publicaciones/crear/`) y Mis
      publicaciones (`/perfil/publicaciones` + `GET /api/publicaciones/mias/`) — 2026-08-14,
      verificado en vivo creando una publicación real con un proveedor demo.
- [x] **Alternar proveedor** — `POST /api/auth/alternar-proveedor/` (`AlternarProveedorView`) +
      botón en `home.page` ("Tu cuenta"), con confirmación solo al desactivar (mismo criterio que
      Django). — 2026-08-14, verificado en vivo: activar/desactivar actualiza el badge y hace
      aparecer/desaparecer "Mis publicaciones" del menú al instante. 3 tests.
- [x] **Historial de pagos** — `GET /api/pagos/historial/` (`PagoHistorialView` +
      `PagoHistorialSerializer`) + `/perfil/pagos`. — 2026-08-14, verificado en vivo (estado vacío
      y con un pago real creado a propósito para probar el listado, revertido después). 4 tests.
- [x] **Bandeja de entrada de mensajes** — `GET /api/conversaciones/` (`ConversacionListView` +
      `ConversacionResumenSerializer`, arma la lista igual que `chat_view`) + `/mensajes`, con badge
      de no leídos también en el tile "Mensajes" de `home.page`. Cada fila navega directo a
      `/contratacion/:id` (el chat ya vive embebido ahí, no se duplicó una pantalla de conversación
      aparte). — 2026-08-15, verificado en vivo con 6 conversaciones reales de datos demo (avatares,
      badges de estado, preview del último mensaje, navegación a la contratación correcta). 5 tests.

Con esto se cierra el punch list de gaps funcionales de prioridad alta — no queda ningún ítem `[ ]`
en esa categoría.

## Pendiente — prioridad media (completar lo empezado)

- [x] **Prueba real en viewport de teléfono** (375px y 390px, vía un iframe de ese ancho exacto
      dentro de una pestaña — el Chrome remoto de esta sesión no soporta redimensionar la ventana
      de verdad) — 2026-08-15. Las 21 pantallas revisadas no tienen overflow horizontal, pero
      aparecieron **3 bugs reales de recorte de texto**, todos corregidos:
      1. El badge de estado ("COMPLETADA", etc.) en `.ks-page-header` se recortaba contra el borde
         de la pantalla en títulos largos — `.ks-page-header h1` ahora tiene `flex-wrap: wrap` y el
         badge nunca se achica (`global.scss`).
      2. El label largo de un `ion-checkbox` ("¿Ofrecés servicios como proveedor?" en `registro`)
         se truncaba con "…" en vez de bajar de línea — `ion-checkbox::part(label) { white-space:
         normal }` (`global.scss`).
      3. El label de un `<input type="file">` nativo junto a su `ion-label` en el mismo `ion-item`
         se apretaba en una columna angosta (bajaba palabra por palabra) en 4 pantallas
         (`catalogo/crear`, `contratacion/detalle`, `perfil/editar`, `perfil/proveedor`) — se
         envolvieron en un `.ks-file-field` propio (flex-column) en vez de depender del layout
         interno de `ion-item`. De paso, el label flotante de "otra área de servicio" en
         `perfil/proveedor` (mismo problema, `ion-textarea`) se acortó en vez de parcharse con CSS.
- [x] **Reseñas recibidas** en el perfil — `GET /api/perfil/resenas-recibidas/`
      (`ResenasRecibidasView` + `ResenaRecibidaSerializer`, sin filtrar por `estado_moderacion` a
      propósito, igual que `perfil_view`) + sección nueva en `home.page` entre "Tu cuenta" y el
      menú. — 2026-08-15, verificado en vivo con una reseña real de datos demo (Camila ← Javiera,
      ★5). 4 tests.
- [x] **Toggle de tema claro/oscuro manual** — `core/tema.ts` (`Tema`, tres estados: sin elección
      sigue al SO, `data-theme="light"`/`"dark"` puestos a mano lo pisan en cualquier dirección) +
      switch nuevo en `/preferencias` ("Apariencia") + bootstrap en `index.html` (aplica el
      `localStorage['ks-theme']` guardado antes del primer pintado, evita el flash). Detectado y
      corregido en el camino un bug real de especificidad CSS: la paleta clara de `variables.scss`
      vivía en un `:root { ... }` a secas, así que con el SO en oscuro `dark.system.css` de Ionic
      (que usa `:root.ios`/`:root.md`, más específico) le seguía ganando la cascada a la elección
      explícita "claro" del usuario para `--ion-background-color`/`--ion-card-background`/etc. —
      mismo patrón que el bug de la paleta oscura ya documentado en `CLAUDE.md`, esta vez del lado
      claro. Se resolvió con el mismo mecanismo: paleta clara en un `@mixin ks-light-palette`,
      reaplicada bajo `:root[data-theme="light"], :root.ios[data-theme="light"],
      :root.md[data-theme="light"]`. — 2026-08-15, verificado en vivo con el SO en modo oscuro:
      alternar el switch cambia el tema al instante (paleta completa, no solo el header), persiste
      al navegar a otra página (`/home`) y al recargar. 4 tests nuevos (`tema.spec.ts`).
- [x] **Badge + polling de mensajes no leídos** (cada 15s, con beep) en el header — equivalente
      Ionic de `mensajes_no_leidos_ajax`/el script de `base.html`: nuevo endpoint liviano
      `GET /api/mensajes/no-leidos/` (`MensajesNoLeidosView`, solo el total, no la lista completa de
      conversaciones) + `core/notificaciones.ts` (`Notificaciones`, servicio singleton arrancado una
      sola vez desde `AppComponent` — sobrevive la navegación entre páginas de Angular a diferencia
      de un `<script>` por página en Django). Mismo criterio exacto que el original: intervalo de
      15s, beep sintetizado con Web Audio (880Hz, sin archivo externo) solo si el conteo subió
      respecto de la última consulta y `Usuario.notificaciones_sonido` está activo. Badge nuevo en
      el ícono de chat del header de `home`/`catalogo`/`inicio` (antes solo existía como resumen en
      el tile "Mensajes" de `home`, ahora ambos comparten el mismo observable en vivo). —
      2026-08-15, verificado en vivo con un mensaje sin leer real de datos demo: el badge aparece
      con "1" tanto en el ícono del header como en el tile, en `/home` y en `/catalogo`, y el ícono
      navega a `/mensajes`. 4 tests backend (`MensajesNoLeidosApiTests`) + 4 tests frontend
      (`notificaciones.spec.ts`).
- [x] **Footer** (marca + links + copyright) en el resto de pantallas raíz — nuevo `FooterComponent`
      compartido (`app/shared/footer/`, declarado/exportado desde `SharedModule`) para no duplicar
      el mismo bloque de HTML en cada página; reemplaza el footer ad-hoc que `inicio`/`catalogo` ya
      tenían (inconsistentes entre sí — `catalogo` no tenía la línea de copyright) y se agrega nuevo
      a `login`/`home`, que no tenían ninguno. Mismo `.ks-footer` de `base.css` del sitio Django
      (marca+bajada, nav de links, copyright con año dinámico) portado a `global.scss`. — 2026-08-15,
      verificado en vivo en las 4 pantallas (`/login`, `/`, `/catalogo`, `/home`, esta última y
      `/catalogo` autenticadas con una cuenta demo). 2 tests nuevos (`footer.spec.ts`).

Con esto se cierra también la prioridad media — no queda ningún ítem `[ ]` en esa categoría. Lo que
resta es prioridad baja/decisión de negocio y las Fases 7-8 (hardening y publicación).

- [x] **Comparación pantalla por pantalla Ionic vs Django (pedida explícitamente por el usuario,
      "pulamos la página")** — 2026-08-15. Encontró y cerró varios gaps reales que `AUDITORIA_8000_vs_8100.md`
      (foto fija del 14) no había capturado: voseo mezclado con tuteo en ~60 strings entre ambos
      frontends (incluido el propio Django, no solo deuda de la migración — `views.py`, `api/views.py`,
      8 templates); catálogo sin el encabezado "Todos los servicios/N publicaciones"; login/recuperar
      sin el título+subtítulo del panel ni "Volver al inicio"; **reservas sin filtros/grid con foto/
      badges descriptivos** (ahora con paridad completa, ver `reservas.page.ts`); **contratación/detalle
      sin el indicador visual de 4 pasos ni la descripción/imágenes de la publicación** (agregado,
      `ContratacionDetailSerializer` suma `publicacion_descripcion`/`publicacion_imagenes`). 263 tests
      backend + 54 frontend en verde en cada commit, verificado en vivo contra datos demo reales.
- [x] **Búsqueda por geolocalización (radio en km) — solo Ionic, decisión explícita del usuario** (el
      filtro de radio no se portó a `catalogo_view`/Django). Backend: `Comuna.latitud`/`longitud`
      (migración `0026`) + 9 comunas RM geocodificadas con la plaza principal como referencia
      (migración `0027`, solo las que usa la data demo — el resto queda `NULL`, se completa después);
      `_anotar_distancia_km` (api/views.py, fórmula de Haversine vía funciones trigonométricas del
      ORM, sin PostGIS) anota `distancia_km` en `PublicacionListView` cuando la request trae
      `lat`/`lng`, y `radio_km` además filtra — igual que `region`/`calificación`, se puede sacar y
      volver a ver todo el catálogo (no es un límite duro). Encontrado y corregido en el camino: un
      bug real donde `LEAST(a, 1.0)` en Postgres ignora los `NULL` en vez de propagarlos, convirtiendo
      una comuna sin geocodificar en ~20015 km en vez de excluirla (atrapado por
      `PublicacionGeolocalizacionApiTests`, no en producción). Frontend: `core/ubicacion.ts`
      (`@capacitor/geolocation`, cubre web y nativo) + botón "Buscar cerca de mí"/selector de radio
      (múltiplos de 3 km) en `catalogo.page`. Sin fallback a la comuna guardada del usuario todavía —
      ver "PRÓXIMA SESIÓN" arriba. — 2026-08-16, verificado en vivo contra `:8100` real con los 9
      proveedores demo geocodificados: activar ubicación anota las distancias correctas en cada card,
      el radio de 12 km filtra de 8 a 4 publicaciones (todas dentro del radio real), y "Quitar
      ubicación" vuelve a mostrar las 8. Esa misma prueba en vivo encontró un segundo bug real: la
      implementación web de `@capacitor/geolocation` no tiene `requestPermissions()` implementado
      (tira excepción siempre), así que el botón no hacía nada en el navegador — corregido
      distinguiendo con `Capacitor.isNativePlatform()`. 4 tests backend
      (`PublicacionGeolocalizacionApiTests`) + 3 tests frontend (`catalogo.page.spec.ts`); sin test
      unitario directo de `Ubicacion`/Capacitor (mismo motivo que `rostro`/`biometria`: el Proxy que
      arma `@capacitor/core` para cada plugin ignora las reasignaciones de `spyOn`, así que un test así
      no probaría nada real — la verificación es en vivo). 268 tests backend + 57 frontend en verde.
      **Verificado también en el emulador Android real** (`KeyServ_Test2`, API 35, ver Known Issues en
      CLAUDE.md) — `adb emu geo fix` simula la posición GPS. Encontró un tercer bug real (además de
      los dos de arriba, específico de nativo): con `enableHighAccuracy: false`, `getCurrentPosition()`
      siempre daba timeout ahí porque `adb emu geo fix` solo alimenta al proveedor GPS, no al de red
      (`IONGeolocationController: Location request timed out`, visto en logcat) — cambiado a
      `enableHighAccuracy: true, timeout: 15000` en `core/ubicacion.ts` (razonable de todos modos para
      un botón que el usuario toca activamente esperando su ubicación). Con eso: el diálogo real de
      permiso de Android apareció, se concedió, y el catálogo mostró "3.8 km" para la publicación de
      Ñuñoa desde una posición mock en Providencia — igual que en web. El mini-mapa de
      `catalogo/detalle` también se probó ahí: tardó unos segundos en cargar dentro del WebView nativo
      pero terminó mostrando el mapa real con el pin junto a Plaza Ñuñoa, igual que en Chrome.
- [x] **Mini-mapa + "Abrir en Google Maps" en `catalogo/detalle`** — pedido explícito del usuario tras
      probar el filtro de radio ("lo más importante"). `ProveedorSerializer` suma
      `latitud`/`longitud` (mismo dato que ya carga `Comuna`, ver arriba, expuesto como `float` en vez
      de string a diferencia de `puntuacion_promedio`). `detalle.page` arma un embed de Google Maps
      sin API key (`output=embed`, sanitizado con `DomSanitizer.bypassSecurityTrustResourceUrl` porque
      la URL sale solo de números del backend) + un link `https://www.google.com/maps?q=lat,lng`; nada
      de esto aparece si la comuna del proveedor todavía no está geocodificada. — 2026-08-16,
      verificado en vivo en `/catalogo/3` (Ñuñoa): el pin cae justo al lado de Plaza Ñuñoa (la
      referencia que se cargó), y el link "Abrir en Google Maps" trae las coordenadas correctas.
      2 tests backend + 3 tests frontend nuevos.
- [ ] **"Exportar chat" sin endpoint API** — `conversacion_exportar_view` (Django) no tiene
      equivalente en `api/urls.py`; encontrado al comparar contratación/detalle. Es trabajo de backend
      nuevo (endpoint + descarga de archivo), no solo de frontend — quedó fuera de la pasada de
      2026-08-15 por alcance, no por dificultad.
- [x] **Retema del panel `/admin/` con identidad KeyServ (inspirado en ServiceNow)** — 2026-08-15,
      pedido explícito del usuario tras comparar contra paneles tipo ServiceNow. Franja de tarjetas KPI
      arriba del dashboard, badges de color en los `<select>` de moderación (sin perder la edición
      inline) y en `Contratacion.estado`/`Pago.estado`, borde de severidad en "Intentos de acceso
      sospechoso", login/sidebar/formularios con la paleta navy/teal/coral + Quicksand/Nunito — todo
      sobre la misma base de Django admin (permisos, validación, auditoría intactos, nada reescrito
      desde cero). De paso se corrigió un bug real: 3 de los paneles del dashboard se mostraban (sin
      datos) a cualquier usuario staff aunque no tuviera el permiso real, porque el template no
      chequeaba si la clave existía en el contexto — ahora si un usuario no tiene permiso, el panel ni
      aparece. Verificado en vivo como superuser y como cuenta Moderador, modo claro y oscuro
      explícitos. 263 tests backend en verde.
- [x] **Ancho del dashboard de `/admin/` + alcance del Moderador acotado** — 2026-08-15, pedido
      explícito del usuario tras usar el retema: "usa el espacio de página de manera inteligente" y
      "el moderador solo debe ver casos que deriven... no trabajos pendientes, solo las alertas".
      El dashboard quedaba limitado a ~600px por una regla de fábrica de Django
      (`.dashboard #content { width: 600px }`, pensada para el app-list plano sin contenido propio) —
      se sacó y los paneles se reacomodaron en una grilla responsive (`.ks-panel-grid`,
      `ks_admin_theme.css`): KPIs y paneles pareados en 2 columnas, "Intentos sospechosos" a ancho
      completo. `PERMISOS_MODERADOR` (`configurar_grupo_moderador.py`) bajó de 17 a 13 permisos —
      se sacó `Contratacion`/`HistorialEstadoContratacion` (pipeline de contrataciones) y
      `Conversacion`/`Mensaje` (chats privados); se mantuvo `Consulta` (casos derivados),
      moderación de contenido (`Publicaciones`/`Documento`/`Valoracion`/`ValoracionImagen`/
      `Imagenes`), `Ranking` (resultado de las valoraciones que sí modera) e
      `IntentoAccesoSospechoso` (las alertas). La categoría "Mensajería" del sidebar desaparece sola
      para Moderador (Django omite categorías sin modelos visibles). Bug real encontrado de paso: el
      panel "Auditoría" (sin filas `<tr>`, solo `<caption>`) colapsaba a un ancho absurdo con el
      texto envuelto palabra por palabra dentro de la grilla — corregido agregándole una fila
      descriptiva, igual que ya tenía su panel vecino. Verificado en vivo como superuser y como
      cuenta Moderador (sidebar sin "Mensajería" ni "Contratación" en ningún lado de la página).
      264 tests backend en verde (+1 test de regresión).
- [x] **Microinteracciones/animaciones + rediseño del header con menú de cuenta** — 2026-08-15,
      pedido explícito del usuario ("busca páginas bonitas y corporativas... Canva, Hostinger...
      que mejoras podemos hacer en diseño") tras investigar patrones de sitios corporativos 2026
      (fuentes en el resumen de la sesión al usuario). Base compartida nueva (`shared/
      reveal.directive.ts`, `shared/empty-state/`, `shared/skeleton/`, `core/retroalimentacion.ts`)
      aplicada de forma sistemática en ~20 pantallas: reveal al hacer scroll (fade+slide
      escalonado), skeleton screens en vez de `ion-spinner` en catálogo/reservas/mensajes/mis
      publicaciones/historial de pagos, estados vacíos con ícono+CTA en vez de un `<ion-text>`
      suelto, toast de éxito donde antes se navegaba en silencio (editar perfil, publicar servicio,
      confirmar/completar contratación, alternar proveedor, registro), y feedback táctil/hover
      global (cards, botones, zoom de imagen) — todo respetando `prefers-reduced-motion`.
      Por pedido explícito del usuario, el header de las 4 pantallas raíz (login/catálogo/home/
      inicio) pasó por varias vueltas de rediseño en vivo hasta terminar en un layout de 3 columnas
      (logo / título de la página / accesos): `TopNavComponent` (Inicio/Servicios/Acerca de
      nosotros/Contacto en un solo botón que abre un `ion-popover` — probado primero como fila
      horizontal siempre visible, cambiado a "siempre popover" cuando el título quedaba truncado
      compitiendo por espacio) + `AccountMenuComponent` (ícono de bandeja de entrada con badge +
      nombre de usuario que abre un menú con Mi cuenta/Bandeja de entrada/Mis contrataciones/
      Preferencias/Cerrar sesión, reemplazando el botón de texto "Ingresar" por un ícono). Tres
      bugs reales de Ionic encontrados y corregidos en el camino (ver detalle en el mensaje del
      commit `0c97c4d`): `slot="start"/"end"` no funciona en un elemento anidado dentro de OTRO
      componente Angular (solo en hijos directos del shadow host); Ionic le pone `order:3` al área
      del `ion-title` rompiendo el orden visual cuando hay contenido en `slot="end"`; y
      `ion-content::part(scroll)` con `max-width`+`margin-inline:auto` (la regla que centra el
      contenido de cada página) colapsa a "shrink-to-fit" dentro de un `ion-popover` angosto en vez
      de llenar el ancho disponible, causando que "Acerca de nosotros"/"Bandeja de entrada"
      envolvieran a dos líneas. Verificado en vivo con datos demo reales, con sesión y sin ella,
      en cada vuelta de feedback. 54 tests frontend en verde.

## Pendiente — prioridad baja / decisión de negocio

- [ ] **Espacios reservados para publicidad** (`.ks-ad-slot`) en landing/catálogo/detalle — ver
      recomendación en `docs/AUDITORIA_8000_vs_8100.md` sección 5. Bloqueado en: qué red de ads,
      políticas de consentimiento — decisión del usuario, no técnica.
- [ ] Retirar `huella.html` (demo legacy) del propio sitio Django, ya superado por biometría nativa
      + reconocimiento facial. No migrar a Ionic.

## Fase 7 — Hardening de producción (después de cerrar los gaps de arriba)

- [x] **Almacenamiento seguro de tokens** (Keychain en iOS / Android Keystore, no `localStorage`) —
      `capacitor-secure-storage-plugin` (`EncryptedSharedPreferences` en Android nativo; en web el
      propio plugin cae a su fallback de `localStorage` con prefijo+base64, no hay equivalente real
      de Keychain/Keystore en un navegador). `core/almacenamiento-seguro.ts` (`AlmacenamientoSeguro`)
      es el wrapper fino; `Auth` (core/auth.ts) mantiene una copia en memoria de los tokens (para el
      acceso síncrono que necesitan `authGuard`/`authInterceptor`) poblada una sola vez al arrancar
      vía `Auth.inicializar()`, enganchado como `APP_INITIALIZER` en `app.module.ts` — Angular no
      termina de bootstrapear (ni corre ningún guard) hasta que esa carga async desde
      `AlmacenamientoSeguro` termina. `login()`/`logout()` mantienen memoria + almacenamiento seguro
      sincronizados en cada escritura. — 2026-08-15, **verificado en vivo con una build nativa Android
      real** (no solo web): `gradlew assembleDebug` + instalado en el emulador `KeyServ_Test2` (API
      35) → login real contra el backend (`adb reverse tcp:8000`) → `force-stop` del proceso
      (simula un cierre real de la app, no solo recargar una pestaña) → relanzar → la sesión seguía
      iniciada (`/` mostró "Mi perfil", no "Ingresar", y `/home` cargó los datos reales) — confirma
      que el token sobrevivió en el Keystore real, no solo en memoria del proceso. Logout después
      también verificado (vuelve a `/login`, el Keystore quedó vacío). 8 tests nuevos
      (`auth.spec.ts` +4, `almacenamiento-seguro.spec.ts` +4).
- [ ] Endpoint de refresh token + rotación (`TokenSesion` ya existe, falta la vista).
- [ ] Tests E2E (Cypress/Playwright para web, Appium si hace falta cubrir nativo).
- [ ] Pipeline de build para Android/iOS.

## Fase 8 — Publicación / portafolio

- [ ] Build firmado Android (Play Store) / iOS (App Store).
- [ ] Íconos, splash screens, políticas de privacidad que piden las stores.
- [ ] Documentación de arquitectura + capturas/video corto para portafolio.

## Ver también

Carta Gantt (línea de tiempo visual de todo esto, hecho con fechas reales de commits + estimado
para lo pendiente): https://claude.ai/code/artifact/aea584bb-cc91-4a5a-8bf0-238cd886903b — privado
por defecto, compartir desde el menú de la página si se quiere mostrar en el portafolio.
