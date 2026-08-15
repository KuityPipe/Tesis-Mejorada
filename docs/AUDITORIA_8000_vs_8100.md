# Auditoría 8000 (Django) vs 8100 (Ionic) — 2026-08-14

Comparación sección por sección de todo lo que existe en el sitio Django (`:8000`) contra lo que ya
tiene la app Ionic (`:8100`), para cerrar la brecha hacia un producto completo y vendible. Ver
`docs/PLAN_MIGRACION_IONIC.md` para el historial de fases — este documento es el corte de estado
puntual que pidió el usuario el 2026-08-14, no reemplaza al plan de fases.

## 1. Header / navegación global

| Elemento (Django `base.html`) | Estado en Ionic |
|---|---|
| Logo enlazando a home | ✅ en pantallas raíz (inicio/catálogo/home) |
| Nav Inicio/Servicios/Acerca de nosotros/Contacto | ⚠️ parcial — agregado como footer en inicio/catálogo/home esta sesión, no como nav persistente (decisión: convención de app móvil, no de sitio web, ver `PLAN_MIGRACION_IONIC.md` Fase 6) |
| Toggle tema claro/oscuro manual | ❌ no existe — Ionic sigue solo la preferencia del SO |
| Ícono + badge de mensajes no leídos con polling (15s) + beep | ❌ no existe — ningún indicador de mensajes nuevos fuera de entrar al chat de una contratación puntual |
| Avatar + nombre → perfil | ✅ (`.ks-avatar-brand` en home) |
| Botón "Salir" | ✅ en las pantallas que corresponde |
| Botones Ingresar/Registrarse (anónimo) | ✅ |

## 2. Footer global

| Elemento | Estado en Ionic |
|---|---|
| Marca + tagline | ❌ no existe |
| Links Inicio/Servicios/Acerca de/Contacto | ✅ solo en inicio/catálogo (agregado esta sesión) — falta en el resto de pantallas raíz y en las de back-button |
| Copyright | ✅ solo en inicio |

## 3. Páginas que existen en Django y NO tienen ningún equivalente en Ionic (gap funcional, no solo visual)

Ordenadas por impacto real en el negocio:

1. ✅ **Publicar un servicio** (`crear_publicacion.html`, `/servicios/crear/`) — **hecho el 2026-08-14**: `catalogo/crear/crear.page` + `POST /api/publicaciones/crear/` (`PublicacionCrearView`, reusa `PublicacionForm`), con imágenes/documentos múltiples y previsualización en vivo (texto + miniaturas, sin el carrusel Bootstrap del template Django). Verificado en vivo con una publicación real creada por un proveedor demo.
2. ✅ **Mis publicaciones** (dentro de `perfil.html`) — **hecho el 2026-08-14**: pantalla propia `perfil/publicaciones/publicaciones.page` + `GET /api/publicaciones/mias/` (`MisPublicacionesView`), grid con badge de estado (pendiente/aprobada/rechazada). Verificado en vivo.
3. **Alternar proveedor** (`alternar_proveedor_view`, botón en `perfil.html`) — sigue sin endpoint API ni UI en Ionic para "convertirme en proveedor" / "dejar de ofrecer servicios" después del registro inicial. Hoy `es_proveedor` solo se define en `/registro/` y no se puede cambiar después desde Ionic (si querés probar "Publicar un servicio" con un usuario no-proveedor, hay que activarlo desde `/perfil/` en el sitio Django).
4. **Historial de pagos** (`historial_pagos.html`, `/historial-pagos/`) — el cliente no puede ver sus pagos pasados agrupados en un solo lugar en Ionic (solo ve el pago de una contratación puntual dentro de esa contratación).
5. **Bandeja de entrada / lista de conversaciones** (`chat.html`, `/chat/`) — en Django podés ver todos tus chats en un solo lugar; en Ionic el chat solo es accesible entrando a la contratación puntual, no hay un "inbox".
6. **Perfil propio como página dedicada** (`perfil.html`, `/perfil/`) — hoy vive parcialmente disuelto dentro de `home.page` ("Tu cuenta"); le falta reseñas recibidas y lo de arriba (alternar proveedor).
7. **Huella dactilar vía imagen** (`huella.html`) — prioridad baja: es el demo/legacy que la biometría nativa (`biometria.page`) y facial (`rostro.page`) ya superan en la práctica; no se recomienda migrarlo, es más bien candidato a retirarse eventualmente del propio Django (fuera del alcance de hoy).

Ver `docs/BACKLOG.md` para el estado vivo de todo esto (esta sección queda como foto fija del 2026-08-14, no se sigue actualizando acá).

## 4. Disposición / márgenes / layout

- El centrado a 720px (`ion-content::part(scroll)`) y las `.ks-section`/`.ks-page-header` ya dan estructura en escritorio — verificado visualmente esta sesión en varias pantallas.
- **No verificado todavía**: comportamiento real a anchos de viewport de teléfono (375–430px) — todo lo probado hasta ahora fue a ~1568px de ancho de ventana de escritorio. Antes de dar esto por completo hay que probar en viewports angostos reales (Chrome DevTools device toolbar o el emulador Android ya configurado, ver Known Issues de CLAUDE.md) los puntos más densos: la barra de filtros del catálogo (3 selects en fila pueden apretarse), `contratacion/detalle` (la pantalla más densa, muchas secciones), y el formulario de registro (3 secciones largas).
- Los formularios largos (registro, perfil de proveedor) no tienen indicador de progreso ni sticky-submit — en una pantalla de teléfono real, con teclado abierto, el botón de submit puede quedar lejos de la vista. No es un bug, es una mejora de UX a evaluar.

## 5. Espacios para publicidad futura

Recomendación: **reservar contenedores explícitos y predecibles ahora, no dejar huecos improvisados** —
un slot de ads reservado desde ya es mucho más fácil de rellenar después que retro-adaptar el layout
cuando ya haya usuarios viendo la app. Propuesta concreta:
- Un componente `<ks-ad-slot>` (o simplemente una `ion-card` vacía con una clase `.ks-ad-slot`, altura fija, placeholder "Espacio publicitario" en dev) insertable entre secciones de contenido.
- Ubicaciones naturales, sin interrumpir flujos transaccionales (nunca en medio de pago/confirmar/re-auth — ahí un ad sería no solo mala UX sino un riesgo de que alguien toque el ad por error en un flujo con plata de por medio):
  - Landing pública (`inicio.page`): entre "Servicios destacados" y el footer.
  - Catálogo: cada N tarjetas dentro del grid (patrón feed estándar), nunca dentro de la barra de filtros.
  - `catalogo/detalle`: debajo de las reseñas.
- Dejar el componente listo y con el hueco reservado ahora, pero **sin contratar/integrar ningún proveedor de ads todavía** — eso es una decisión de negocio (qué red, políticas, consentimiento/cookies) que no corresponde tomar en código sin que el usuario la defina primero.

## 6. Sobre usar templates externos / buscar referencias en la web

No se recomienda adoptar un template genérico de internet: KeyServ ya tiene una identidad visual propia
completa (paleta navy/teal/coral, tipografía, componentes) portada 1:1 de Django a Ionic durante la Fase 6 —
meter un template ajeno significaría empezar de nuevo esa identidad y perder la coherencia que ya se logró
entre ambos frontends. Tiene más sentido seguir extendiendo el mismo sistema. Sí vale la pena buscar
referencias puntuales (no templates completos) para patrones específicos que hoy no existen en el proyecto,
por ejemplo: cómo estructuran otras apps un flujo de "publicar un anuncio con imágenes" en mobile, o
patrones de ad-slot no intrusivos en apps de marketplace — investigación acotada, no una base de diseño nueva.
