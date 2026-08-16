# Bitácora de desarrollo — KeyServ

Registro de checkpoints de trabajo (commit + push), para llevar cuenta de
cuánto tiempo se le fue dedicando al proyecto. Cada fila corresponde a un
commit real del repo. La columna "desde el anterior" es una aproximación
del tiempo transcurrido entre commits consecutivos — no descuenta pausas,
comidas o sueño dentro de una misma sesión, y se corta a "—" cuando el
salto claramente cruza a otro día (no cuenta como tiempo de trabajo).

A partir del checkpoint #11, la cadencia es un commit+push cada ~1.5 horas
de trabajo activo — **siempre con aprobación explícita antes de commitear**,
nunca automático.

| # | Fecha/hora | Commit | Resumen | Desde el anterior |
|---|---|---|---|---|
| 1 | 2026-07-22 20:31 | `fd23205` | Fase 1: reorganizar estructura del repo y limpiar git | — |
| 2 | 2026-07-22 20:46 | `4db69ff` | Fase 2: análisis de PDF/código, arquitectura y roadmap | 15 min |
| 3 | 2026-07-22 21:36 | `bac7322` | Fase 3: refactoring, features nuevas, calidad, infraestructura y docs | 50 min |
| 4 | 2026-07-22 22:16 | `a972dae` | Fase 4 (parcial): PostgreSQL instalado, migrado y validado end-to-end | 40 min |
| 5 | 2026-07-22 22:28 | `008e5f4` | Fase 4: cargar catálogos reales (regiones/comunas/tipos de cuenta) | 12 min |
| 6 | 2026-07-22 22:52 | `85e83a7` | Fase 4: crear publicación, contratación completa, mensajería y tests | 24 min |
| 7 | 2026-07-23 16:01 | `ab7a1ec` | Documentar comandos para correr un solo test en CLAUDE.md | — (otro día) |
| 8 | 2026-07-23 19:58 | `8c3a6dd` | Fase 5: rediseño completo, chat por trabajo, roles de admin y moderación | 3 h 57 min |
| 9 | 2026-07-24 09:48 | `169cb66` | Agregar toggle de tema claro/oscuro y poner CLAUDE.md al día con Fase 5 | — (otro día) |
| 10 | 2026-07-24 12:55 | `c184930` | Fase 6: carrusel y calificaciones moderadas, admin reorganizado, endurecimiento de seguridad | 3 h 7 min |
| 11 | 2026-07-24 14:10 | `fcd4b90` | Previsualización en vivo al crear publicación + selector de fotos/documentos acumulativo | 1 h 15 min |
| 12 | 2026-07-24 15:27 | `4ceb7af` | Rediseño de reservas con filtros + perfil editable, recuperación de contraseña y paginación del catálogo | 1 h 15 min |
| 13 | 2026-07-24 16:43 | `371dea6` | Rediseño de bandeja de entrada del chat + pagos reales con Webpay Plus y Khipu (monto acordado ajustable) | 1 h 15 min |
| 14 | 2026-07-24 17:31 | `4c73182` | Hoja de presupuesto opcional en la contratación (ItemPresupuesto) + CLAUDE.md al día con Fase 6 | 47 min |
| 15 | 2026-07-24 18:08 | `f0dc2f5` | Rediseño de Acerca de nosotros y Contacto, más cercanos e intuitivos | 37 min |
| 16 | 2026-07-24 18:33 | `426ac49` | Terminar perfil de proveedor, preferencias de cuenta e historial de pagos | 25 min |
| 17 | 2026-07-24 18:55 | `2ff061a` | Buscador + área libre en perfil de proveedor, certificados/documentos + fix de bug real en Documento | 22 min |
| 18 | 2026-07-26 17:43 | `b60e26c` | Corregir CLAUDE.md: contador de tests, estado de ItemPresupuesto y paso de venv | — (otro día) |
| 19 | 2026-07-26 18:35 | `fb88d9a` | Aplicar migración pendiente 0023 (path de storage de Documento) tras pruebas E2E | 52 min |
| 20 | 2026-07-30 17:36 | `5154f29` | Poner CLAUDE.md al día (conteo de modelos, nota migración 0023) y completar checkpoints 18-19 en la bitácora | — (otro día) |
| 21 | 2026-07-30 18:07 | `501caf9` | Conectar reconocimiento facial: encoding de referencia real, vistas /rostro/ y tests | 31 min |
| 22 | 2026-07-30 18:50 | `6a6304c` | Agregar captura de cámara en vivo a /rostro/ y documentar intento fallido de instalar face_recognition | 43 min |
| 23 | 2026-08-03 13:32 | `c385a5e` | Instalar opencv-python/face_recognition/dlib de verdad (reintento con red estable) y corregir manejo de errores en biometria.py | — (otro día) |
| 24 | 2026-08-03 14:33 | `45d014b` | Agregar prueba de vida de 3 pasos (centro/derecha/izquierda) al reconocimiento facial | 1 h 01 min |
| 25 | 2026-08-03 15:24 | `b7ca678` | Validar cada paso de la prueba de vida por AJAX antes de avanzar | 51 min |
| 26 | 2026-08-03 20:55 | `11099bd` | Reemplazar la prueba de vida de 3 fotos por parpadeo (EAR) en una sola captura | 5 h 31 min |
| 27 | 2026-08-03 21:20 | `23bb819` | Agregar tests automatizados para el grupo Moderador, el agrupamiento de admin y el dashboard de moderación | 25 min |
| 28 | 2026-08-13 19:49 | `c18a711` | Fase 1 (API/Ionic): API REST (DRF + JWT propio) + TokenSesion + scaffold Ionic/Angular, y CLAUDE.md al día | — (otro día) |
| 29 | 2026-08-13 20:09 | `ef5f775` | Fase 1 (API/Ionic): login funcional en Ionic contra la API JWT, verificado en vivo por curl, y fix del puerto de npm start | 20 min |
| 30 | 2026-08-13 20:26 | `a8d05ce` | Documentar el plan de migración a Ionic (docs/PLAN_MIGRACION_IONIC.md) y comentar el código Angular/Ionic ya escrito | 16 min |
| 31 | 2026-08-13 20:49 | `bbf1ff7` | Fase 2 (API/Ionic): catálogo público — API (listado+detalle de publicaciones) y pantallas Ionic con scroll infinito | 24 min |
| 32 | 2026-08-13 21:07 | `39a5c11` | Fase 3 (API/Ionic, parcial): registro de cuenta — API (reusa RegistroForm), catálogos de referencia, pantalla Ionic con cascada región→comuna | 18 min |
| 33 | 2026-08-13 21:19 | `83c8143` | Fase 3 (API/Ionic, parcial): editar perfil — API (reusa EditarPerfilForm, sube foto), pantalla Ionic; se agregó la Fase 6 de diseño visual al plan (deferida a después de toda la funcionalidad) | 12 min |
| 34 | 2026-08-13 21:30 | `fac4e38` | Fase 3 (API/Ionic, parcial): recuperación de contraseña — API (reusa RecuperarForm/NuevaPasswordForm, link apunta al frontend Ionic), pantallas Ionic de los 2 pasos | 11 min |
| 35 | 2026-08-13 22:33 | `f68e139` | Fase 3 (API/Ionic, completa): perfil de proveedor y preferencias de cuenta | 1 h 03 min |
| 36 | 2026-08-13 23:03 | `b0d961d` | Fase 4 (API/Ionic, parcial): contrataciones, mensajería y valoraciones | 30 min |
| 37 | 2026-08-13 23:39 | `6c0105c` | Fase 4 (API/Ionic, completa): pagos Webpay y Khipu | 36 min |
| 38 | 2026-08-14 01:07 | `fcf317b` | Fase 5 (API/Ionic, parcial): verificación biométrica nativa | 1 h 28 min |
| 39 | 2026-08-14 02:32 | `b0e253d` | Fase 5 (API/Ionic, completa): reconocimiento facial por cámara | 1 h 25 min |
| 40 | 2026-08-14 03:22 | `626a236` | Fase 6 (API/Ionic, parcial): identidad visual del sitio Django portada a Ionic | 50 min |
| 41 | 2026-08-14 23:42 | `96c0ef9` | Fase 6 (API/Ionic, completa): páginas públicas, publicar servicio y fix de login real | — (pausa larga, mismo día calendario) |
| 42 | 2026-08-15 00:01 | `e748ef6` | Alternar proveedor + historial de pagos en Ionic | 19 min |
| 43 | 2026-08-15 00:20 | `9514df8` | Bandeja de mensajes en Ionic | 19 min |
| 44 | 2026-08-15 00:46 | `49e1ec0` | Verificación en viewport móvil real (375–390px) y 3 bugs corregidos | 26 min |
| 45 | 2026-08-15 01:08 | `aac6801` | Reseñas recibidas en el perfil | 22 min |
| 46 | 2026-08-15 01:26 | `ae9e851` | Toggle de tema claro/oscuro manual en Ionic | 18 min |
| 47 | 2026-08-15 01:45 | `481d0dd` | Badge y polling de mensajes no leídos (15s + beep) en Ionic | 19 min |
| 48 | 2026-08-15 01:51 | `af07f2d` | Footer compartido (marca + links + copyright) en las pantallas raíz | 6 min |
| 49 | 2026-08-15 02:22 | `e19a58b` | Fase 7 (hardening): almacenamiento seguro de tokens JWT | 31 min |
| 50 | 2026-08-15 03:01 | `1b20387` | Plan de portafolio en 3 niveles, investigado y documentado | 39 min |
| 51 | 2026-08-15 15:10 | `fca4e26` | Nivel 1.2: limpieza de estructura para portafolio | — (otro bloque de sesión) |
| 52 | 2026-08-15 15:22 | `c263f76` | Nivel 1.1: README.md real (bilingüe) para el portafolio | 12 min |
| 53 | 2026-08-15 15:40 | `94fb4bc` | Nivel 2.1: CI con GitHub Actions (backend + frontend) | 18 min |
| 54 | 2026-08-15 15:46 | `d7f79f4` | Nivel 2.3: diagrama de arquitectura (Mermaid) en el README | 6 min |
| 55 | 2026-08-15 16:20 | `fda0467` | Nivel 3: licencia MIT, badges de stack, link a la carta Gantt | 34 min |
| 56 | 2026-08-15 17:13 | `c9ad073` | Pulido: unificar tuteo (no voseo) en toda la app + contador en catálogo | 53 min |
| 57 | 2026-08-15 17:26 | `57ebaaf` | Pulido: más voseo residual (esta vez en el propio Django) + encabezados faltantes en login/recuperar de Ionic | 13 min |
| 58 | 2026-08-15 17:45 | `832bc09` | Pulido: barrida final de voseo (formas sin tilde/irregulares) | 19 min |
| 59 | 2026-08-15 18:25 | `d30c13d` | Paridad reservas: filtros + grid con fotos + badges descriptivos | 40 min |
| 60 | 2026-08-15 18:35 | `2833d59` | Paridad contratación/detalle: avance visual + descripción/imágenes | 10 min |
| 61 | 2026-08-15 18:36 | `20f2854` | Actualiza BACKLOG.md con los hallazgos de la comparación Ionic vs Django | 1 min |
| 62 | 2026-08-15 18:41 | `b0aed2b` | Paridad preferencias: sección "Términos y condiciones" faltante | 5 min |
| 63 | 2026-08-15 18:52 | `3bcc434` | Paridad rostro/biometría: avatar-ícono + último voseo residual ("Probá") | 11 min |
| 64 | 2026-08-15 20:21 | `5dd8d62` | Retema el panel de /admin/ con identidad KeyServ, inspirado en ServiceNow | 1 h 29 min |
| 65 | 2026-08-15 20:54 | `e67e4e1` | Dashboard de /admin/ usa el ancho completo (fix de `.dashboard #content`) + acota el alcance del Moderador (17→13 permisos, sin contrataciones ni chats) | 31 min |
| 66 | 2026-08-15 22:23 | `0c97c4d` | Microinteracciones (reveal/skeleton/empty-state/toast) en ~20 pantallas + rediseño del header (TopNavComponent + AccountMenuComponent, layout de 3 columnas) tras varias vueltas de feedback en vivo | 1 h 29 min |
| 67 | 2026-08-15 23:56 | `0213c65` | Registro pulido (logo clickeable a Inicio, header más grande, fix de visibilidad de los campos de formulario `!important` en `--border-width`, fix de orden en el header, fix de crowding en móvil) + prueba E2E real de registro en Android nativo (dark mode, vía adb) + `tipo_cuenta` eliminado del registro (redundante con "¿ofreces servicios?", 264 tests backend en verde) | 1 h 33 min |
| 68 | 2026-08-16 14:15 | (pendiente) | Búsqueda por geolocalización (radio en km, solo Ionic) + mini-mapa/link a Google Maps en `catalogo/detalle` — `Comuna.latitud`/`longitud` (migraciones 0026/0027, 9 comunas RM geocodificadas), `_anotar_distancia_km` (Haversine vía ORM) en `PublicacionListView`, `core/ubicacion.ts` (`@capacitor/geolocation`) + selector de radio en `catalogo.page`, `latitud`/`longitud` en `ProveedorSerializer` + embed de Google Maps sin API key en `catalogo/detalle`. 3 bugs reales encontrados y corregidos en el camino (`LEAST()` de Postgres ignorando NULL, `requestPermissions()` no implementado en la versión web de `@capacitor/geolocation`, timeout de `enableHighAccuracy: false` en el emulador Android). Verificado en vivo en `:8100`, y en el emulador Android real (`KeyServ_Test2`) con `adb emu geo fix` simulando el GPS. 269 tests backend + 59 frontend en verde. | — (pausa larga, mismo día calendario) |

**Tiempo activo estimado hasta el checkpoint #10** (sumando solo los intervalos cortos dentro del mismo día, sin las pausas entre días): ~9 h 45 min. **Hasta el checkpoint #13**: ~13 h 30 min. **Hasta el checkpoint #17**: ~15 h 41 min. **Hasta el checkpoint #19**: ~16 h 33 min. **Hasta el checkpoint #21**: ~17 h 04 min. **Hasta el checkpoint #22**: ~17 h 47 min. **Hasta el checkpoint #27**: ~25 h 35 min. **Hasta el checkpoint #34**: ~27 h 16 min. **Hasta el checkpoint #40** (cierre de Fases 3-6 de la migración API/Ionic): ~33 h 08 min. **Hasta el checkpoint #50** (cierre de la sesión nocturna + plan de portafolio): ~36 h 27 min. **Hasta el checkpoint #63** (cierre de la sesión de portafolio + pulido visual, 15 ago): ~40 h 09 min. **Hasta el checkpoint #64** (retema del panel de /admin/): ~41 h 38 min. **Hasta el checkpoint #65** (ancho del dashboard + alcance del Moderador acotado): ~42 h 09 min. **Hasta el checkpoint #66** (microinteracciones + rediseño del header): ~43 h 38 min. **Hasta el checkpoint #67** (registro pulido + prueba E2E Android + quitar tipo_cuenta): ~45 h 11 min.

---

*Este archivo lo mantiene Claude Code junto con cada checkpoint — no es un timesheet exacto, es una referencia para no perder la cuenta de cuánto se ha avanzado.*
