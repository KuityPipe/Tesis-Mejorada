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

**Tiempo activo estimado hasta el checkpoint #10** (sumando solo los intervalos cortos dentro del mismo día, sin las pausas entre días): ~9 h 45 min. **Hasta el checkpoint #13**: ~13 h 30 min. **Hasta el checkpoint #17**: ~15 h 41 min. **Hasta el checkpoint #19**: ~16 h 33 min. **Hasta el checkpoint #21**: ~17 h 04 min. **Hasta el checkpoint #22**: ~17 h 47 min. **Hasta el checkpoint #27**: ~25 h 35 min. **Hasta el checkpoint #33**: ~27 h 05 min.

---

*Este archivo lo mantiene Claude Code junto con cada checkpoint — no es un timesheet exacto, es una referencia para no perder la cuenta de cuánto se ha avanzado.*
