# Backlog — migración Ionic + producto KeyServ

Documento vivo (se actualiza cada sesión, a diferencia de `docs/AUDITORIA_8000_vs_8100.md`, que es
una foto fija del 2026-08-14). Acá se anota qué falta, en qué orden, y por qué — para no perder el
hilo entre sesiones y para tener un registro real del trabajo (útil también para portafolio: es la
prueba de que esto se llevó con metodología, no a los saltos).

Ver también: `docs/PLAN_MIGRACION_IONIC.md` (fases 1-8 de la migración, más técnico) y
`docs/AUDITORIA_8000_vs_8100.md` (comparación sección por sección Django vs Ionic).

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
- [ ] **Badge + polling de mensajes no leídos** (cada 15s, con beep) en el header — no existe en
      Ionic todavía, existe en Django desde Fase 5.
- [ ] **Footer** (marca + links + copyright) en el resto de pantallas raíz — hoy solo está en
      `inicio`/`catalogo`.

## Pendiente — prioridad baja / decisión de negocio

- [ ] **Espacios reservados para publicidad** (`.ks-ad-slot`) en landing/catálogo/detalle — ver
      recomendación en `docs/AUDITORIA_8000_vs_8100.md` sección 5. Bloqueado en: qué red de ads,
      políticas de consentimiento — decisión del usuario, no técnica.
- [ ] Retirar `huella.html` (demo legacy) del propio sitio Django, ya superado por biometría nativa
      + reconocimiento facial. No migrar a Ionic.

## Fase 7 — Hardening de producción (después de cerrar los gaps de arriba)

- [ ] Almacenamiento seguro de tokens (Keychain/Keystore vía plugin nativo, no `localStorage`).
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
