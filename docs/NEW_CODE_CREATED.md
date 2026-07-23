# Código Nuevo Creado — Fase 3

Funcionalidades que no existían antes de esta fase, en el orden pedido en
`docs/DEVELOPMENT_ROADMAP.md`. Cada una indica si quedó **real** (funciona
de punta a punta, dentro de lo que se puede probar sin Postgres/hardware) o
**esqueleto** (estructura + TODOs explícitos, pendiente de completar).

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

## Listado/búsqueda de servicios — PARCIAL

- `views.paginicio_view`: REAL — lista `Publicaciones` con `estado_moderacion=APROBADA`.
- `views.publicacion_detalle_view`: REAL — usa `detalleserv.html` existente.
- `views.publicacion_crear_view`: **ESQUELETO** — la lógica de guardado con
  `PublicacionForm` está completa y funciona, pero renderiza sobre
  `crearperfil.html` como placeholder porque **no existe ningún template de
  "crear publicación" entre las páginas heredadas de la tesis** (fuera de
  alcance diseñar una pantalla nueva en esta fase). TODO: diseñar
  `crear_publicacion.html` dedicado.

## Gestión de contratación — ESQUELETO

- Modelo `Contratacion` nuevo (`models.py`): cliente, proveedor, publicación,
  estado (`SOLICITADA`/`CONFIRMADA`/`EN_CURSO`/`COMPLETADA`/`CANCELADA`).
- `views.contratacion_crear_view`: crea el registro en `SOLICITADA`. **TODO
  pendiente** (documentado en el docstring de la vista):
  - Notificar al proveedor.
  - Forzar re-autenticación de ambas partes antes de pasar a `CONFIRMADA`
    (lo exige el BPMN "Proceso de contratación" del PDF, PAGE 136-137).
  - Disparar el flujo de pago antes de `EN_CURSO`.
- `views.reservas_view`: REAL — lista las `Contratacion` del usuario logueado.

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

## Resumen de TODOs pendientes (buscar el texto "TODO" en el código para ubicarlos exactos)

1. Template de "crear publicación" (no existe, `publicacion_crear_view` usa un placeholder).
2. Notificación + re-autenticación + disparo de pago en el flujo de contratación.
3. Persistencia del encoding facial de referencia por usuario.
4. Comparación de huella contra una referencia guardada (hoy solo valida que el pipeline corra).
5. Integración real con el SDK de Transbank (requiere credenciales de comercio).
6. Conectar `pago_view` a `pagos.TransbankService`.
7. Vistas reales de mensajería (`chat_view` es un placeholder — modelos `Mensaje`/`Conversacion` ya existen).

## Prioridad siguiente sugerida

Con la autenticación y el modelo de datos ya arreglados, lo que más
desbloquea valor de negocio es (en orden): 1) diseñar la pantalla de "crear
publicación" para que `publicacion_crear_view` deje de usar un placeholder,
2) completar el flujo de contratación (notificación + confirmación), 3)
conseguir credenciales de prueba de Transbank (ambiente "integración") para
poder implementar `pagos.py` de verdad.
