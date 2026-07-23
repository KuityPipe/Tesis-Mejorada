# Código Nuevo Creado — Fase 3 (+ actualizaciones de Fase 4)

Funcionalidades que no existían antes de esta fase, en el orden pedido en
`docs/DEVELOPMENT_ROADMAP.md`. Cada una indica si quedó **real** (funciona
de punta a punta) o **esqueleto** (estructura + TODOs explícitos, pendiente
de completar).

> **Actualización Fase 4**: con Postgres ya corriendo se pudo probar todo
> contra una base de datos real (no solo `manage.py check`). Varios ítems
> que en Fase 3 quedaron ESQUELETO ahora son REALES — ver el marcador
> "✅ Fase 4" en cada sección. También se agregó una suite de tests
> automatizados (`KeyServApp/tests.py`, 21 tests, 0% → cobertura real de
> todo lo listado acá) y se subió Django de 4.2.1 a 5.2 LTS (la versión
> original no es compatible con Python 3.14 — ver `requirements.txt`).

## Autenticación — REAL

- `KeyServApp/decorators.py`: `login_requerido` (decorador) + `obtener_usuario_actual`.
- `views.register_view`/`sesion_view`/`logout_view`: registro, login y logout
  reales usando `Usuario.set_password()`/`check_password()` (PBKDF2 vía
  `django.contrib.auth.hashers`) y `request.session`.
- `KeyServApp/forms.py`: `RegistroForm` (valida mayoría de edad, contraseñas
  coincidentes, email no duplicado — RNF010/RNF011 del PDF) y `LoginForm`.

## Modelo de usuario — REAL

- Campo `Usuario.es_proveedor` (`BooleanField`) — distingue los dos actores
  del PDF (Cliente/Proveedor, PAGE 137-141), no existía ningún campo para esto.
- Campo `Usuario.verificado_biometricamente` — lo marca `verificacion_huella_view`
  tras un procesamiento de huella exitoso.

## Listado/búsqueda de servicios — REAL (✅ Fase 4: completado)

- `views.paginicio_view`: REAL — lista `Publicaciones` con `estado_moderacion=APROBADA`.
  `paginicio.html` ahora las muestra de verdad (antes tenía un `<!-- comentario -->` vacío).
- `views.publicacion_detalle_view`: REAL — `detalleserv.html` muestra proveedor,
  ranking y reseñas (`Valoracion`) reales, con botón "Contratar" real.
- `views.publicacion_crear_view`: **REAL** (Fase 4) — se creó
  `crear_publicacion.html`, un template dedicado (reutiliza el
  `stylecrearperfil.css` que estaba huérfano desde la tesis original), con
  `PublicacionForm` completo. Ya no usa `crearperfil.html` como placeholder.
- `perfil.html`: ahora muestra los datos reales del `Usuario`, sus
  publicaciones (si es proveedor), su verificación biométrica y las reseñas
  que recibió — antes era 100% contenido hardcodeado ("John Doe", "Servicio 1").

## Gestión de contratación — REAL (✅ Fase 4: completado)

- Modelo `Contratacion` (`models.py`): cliente, proveedor, publicación,
  estado (`SOLICITADA`/`CONFIRMADA`/`EN_CURSO`/`COMPLETADA`/`CANCELADA`).
- `views.contratacion_crear_view`: crea el registro en `SOLICITADA` **y
  notifica al proveedor** abriendo/reusando una `Conversacion` con un
  mensaje automático (en vez de email — reutiliza el sistema de mensajería).
- `views.contratacion_confirmar_view` (NUEVO): el **proveedor** confirma
  `SOLICITADA` → `CONFIRMADA`, exige re-autenticación (reingresar password).
- `views.contratacion_completar_view` (NUEVO): el **cliente** confirma
  `CONFIRMADA` → `COMPLETADA`, también con re-autenticación. Esto cumple el
  requisito del BPMN del PDF ("ambos se re-autentican") — cada parte lo hace
  en su propio paso del proceso.
- `views.reservas_view`: REAL — lista las `Contratacion` del usuario, con
  los botones de confirmar/completar/valorar según estado y rol.
- Probado de punta a punta vía HTTP real contra Postgres: solicitar →
  confirmar (rechaza password incorrecta, acepta la correcta) → completar →
  valorar → `Ranking` recalculado — ver `docs/FASE4_LOG.md`.
- **Sigue pendiente**: disparar el flujo de pago antes de pasar a `EN_CURSO`
  (bloqueado por credenciales de Transbank, igual que en Fase 3).

## Integración biométrica — PARCIAL

- `codigo/biometria/huella/IMAGEN_HUELLA.py` → `procesar_huella()`: REAL,
  reutilizable, sin cambios en el algoritmo original (solo se sacó del
  contexto de "script que se ejecuta solo al importarlo").
- `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` →
  `cargar_rostro_conocido()`/`verificar_rostro()`: **ESQUELETO**, no probado
  contra una cámara real (no hay webcam en este entorno). Además falta
  decidir dónde se guarda el encoding facial de referencia de cada usuario
  (no existe ese campo en el diccionario de datos de la tesis).
- `KeyServApp/biometria.py`: puente real entre Django y los dos scripts de
  arriba (`procesar_huella_dactilar()`, `verificar_rostro_usuario()`), con
  manejo de errores si las dependencias pesadas (opencv/face_recognition)
  no están instaladas.
- `views.verificacion_huella_view`: REAL en el sentido de que corre el
  pipeline y marca `verificado_biometricamente`, pero **TODO**: no compara
  contra una huella de referencia guardada previamente (no hay campo para
  eso todavía) — hoy cualquier imagen procesada exitosamente "verifica".

## Pagos — ESQUELETO COMPLETO

- `KeyServApp/pagos.py`: clase `TransbankService` con `iniciar_transaccion()`/
  `confirmar_transaccion()`. Ambos métodos lanzan `NotImplementedError`
  explícito — no hay credenciales de comercio Transbank, así que no hay nada
  real que llamar todavía. Lee `TRANSBANK_COMMERCE_CODE`/`TRANSBANK_API_KEY`
  desde `.env` (ver `.env.example`).
- `views.pago_view`/`pago_exitoso_view`: solo renderizan los templates
  existentes, no llaman a `pagos.py` todavía (documentado con TODO en el
  docstring de `pago_view`).

## Sistema de valoraciones — REAL

- `views.valoracion_crear_view`: crea una `Valoracion` sobre la contraparte
  de una `Contratacion` ya `COMPLETADA`, usando `ValoracionForm` (valida
  puntuación 1-5 estrellas).
- `_recalcular_ranking()`: recalcula promedio y total de `Ranking` tras cada
  nueva valoración (usa `Avg`/`Count` de Django, no un cálculo manual).
  Verificado contra Postgres real: 1 valoración de 5 estrellas → ranking
  promedio 5.00, total 1.

## Mensajería — REAL (✅ Fase 4: completado)

- `views._obtener_o_crear_conversacion()`: busca (o crea) la `Conversacion`
  entre dos `Usuario`, junto con sus dos filas de `UsuarioConversacion`.
  La usa `contratacion_crear_view` para notificar al proveedor.
- `views.chat_view`: REAL — lista las `Conversacion` del usuario logueado.
- `views.conversacion_detalle_view` (NUEVO): muestra los `Mensaje` de una
  conversación y procesa el envío de uno nuevo (`MensajeForm`). Verifica que
  el usuario realmente participe en esa conversación (si no, redirige a
  `/chat/` — probado con un tercer usuario "intruso" en los tests).
- `chat.html` reescrito: antes tenía 2 mensajes hardcodeados ("Usuario A"/
  "Usuario B") y un `sendMessage()` en JS puro que solo manipulaba el DOM sin
  persistir nada. Ahora es un template Django real con el formulario posteando de verdad.

## Pagos — ESQUELETO COMPLETO (sin cambios en Fase 4, sigue bloqueado)

- `KeyServApp/pagos.py`: clase `TransbankService` con `iniciar_transaccion()`/
  `confirmar_transaccion()`. Ambos métodos lanzan `NotImplementedError`
  explícito — no hay credenciales de comercio Transbank, así que no hay nada
  real que llamar todavía. Lee `TRANSBANK_COMMERCE_CODE`/`TRANSBANK_API_KEY`
  desde `.env` (ver `.env.example`).
- `views.pago_view`/`pago_exitoso_view`: solo renderizan los templates
  existentes, no llaman a `pagos.py` todavía.

## Tests automatizados — NUEVO en Fase 4

`KeyServApp/tests.py`: 21 tests, 0% → cobertura real de todo lo listado en
este documento (password hashing, registro, login, `load_comunas`, import de
biometría, moderación de publicaciones, flujo completo de contratación con
re-autenticación correcta/incorrecta, mensajería con control de acceso).
Corren contra una base de datos de prueba real en Postgres (`manage.py test`,
no mocks). Ver `docs/FASE4_LOG.md` para el detalle de por qué hizo falta
subir Django a 5.2 para que corrieran sin errores de infraestructura.

## Resumen de TODOs pendientes (buscar el texto "TODO" en el código para ubicarlos exactos)

1. Persistencia del encoding facial de referencia por usuario.
2. Comparación de huella contra una referencia guardada (hoy solo valida que el pipeline corra).
3. Integración real con el SDK de Transbank (requiere credenciales de comercio).
4. Conectar `pago_view` a `pagos.TransbankService`, y disparar el pago antes de `EN_CURSO` en el flujo de contratación.
5. Reconocimiento facial sin probar contra webcam real (no hay cámara en este entorno de desarrollo).

## Prioridad siguiente sugerida

Con auth, publicaciones, contratación, valoraciones y mensajería ya
funcionando de punta a punta, lo que más desbloquea valor de negocio ahora
es: 1) conseguir credenciales de prueba de Transbank (ambiente "integración")
para poder implementar `pagos.py` de verdad, 2) decidir cómo se persiste el
encoding facial de referencia para que la verificación biométrica compare
contra algo real y no solo "el pipeline corrió sin error".
