# Fase 4 — Puesta en marcha y cierre de brechas funcionales

Resumen de lo hecho en esta fase (continuación de Fase 3). A diferencia de
las fases anteriores, esta no vino con un prompt estructurado — se acordó el
alcance conversacionalmente y se fue ejecutando por partes.

## 1. Postgres instalado y en marcha

No había ningún servidor Postgres disponible en el entorno de desarrollo.
El instalador gráfico oficial de PostgreSQL 17 fallaba (`exit code 1` casi
instantáneo, sin log útil) porque este entorno no tiene sesión de escritorio
interactiva. Se resolvió instalando los **binarios portables** (zip, sin
instalador) y registrando el servidor como **servicio de Windows**:

- Servicio: `postgresql-keyserv` (arranque automático).
- Datos: `C:\pgsql\data`, puerto 5432.
- Base: `keyserv`, usuario `postgres` / password `keyserv_local_dev` (dev local).
- `codigo/backend/django/.env` generado con `DJANGO_SECRET_KEY` real
  (aleatorio, vía `get_random_secret_key()`), gitignorado.

`manage.py migrate` corrido con éxito — las ~24 tablas existen de verdad.
`codigo/database/schema.sql` generado desde la migración real aplicada.

## 2. Catálogos reales cargados

Se encontró un dump MySQL viejo del proyecto (`notpaper3`, fuera del repo,
en una carpeta personal del usuario) con datos de desarrollo. Se extrajeron
**solo las tablas de catálogo** — 16 regiones de Chile, 330 comunas reales,
los 4 `TipoCuenta` reales, `TipoFirma`, `EstadoAutentificacion`,
`EstadoDocumento` — a `KeyServApp/fixtures/catalogos_iniciales.json`, cargado
vía `manage.py loaddata`.

**Deliberadamente NO se migraron** las tablas `usuario`/`autentificacion`/
`documento`/`publicaciones`/`transaccion` del dump: datos de prueba
descartables con contraseñas SHA-256 sin salt, incompatibles con el hasher
PBKDF2 de Fase 3. El usuario confirmó que ya rotó las credenciales reales
que aparecían ahí.

## 3. Features completadas (de esqueleto a real)

Ver el detalle completo en `docs/NEW_CODE_CREATED.md` (actualizado). Resumen:

- **Crear publicación**: template dedicado `crear_publicacion.html` (antes
  usaba `crearperfil.html` como placeholder).
- **Contratación completa**: `contratacion_confirmar_view` (proveedor,
  re-autenticación) y `contratacion_completar_view` (cliente,
  re-autenticación) — el flujo BPMN del PDF completo: solicitar → confirmar
  → completar → valorar.
- **Notificación**: al solicitar una contratación, se crea/reusa una
  `Conversacion` con un mensaje automático al proveedor (en vez de email).
- **Mensajería real**: `chat_view` + `conversacion_detalle_view` — listar
  conversaciones, ver mensajes, enviar uno nuevo, con control de acceso
  (solo participantes).
- **Templates conectados a datos reales**: `paginicio.html`, `perfil.html`,
  `detalleserv.html`, `reservas.html`, `chat.html` — antes tenían contenido
  100% hardcodeado ("John Doe", "Servicio 1", "Usuario A").
- **Auditoría CSRF**: los 4 `<form>` sin `{% csrf_token %}` que quedaban
  (`crearperfil.html`, `editarperfil.html`, `pago.html`, `recuperar.html`)
  ahora lo tienen, con `method="post"`.

Todo probado de punta a punta vía HTTP real contra Postgres (no solo
`manage.py check`): registro → login → crear publicación → aprobar
(moderación) → ver en el listado público → contratar → confirmar (rechaza
password incorrecta, acepta la correcta) → completar → valorar → ranking
recalculado (5.00, 1 valoración) → mensajería visible para ambas partes,
rechazada para un tercero.

## 4. Tests automatizados

`KeyServApp/tests.py`: 21 tests cubriendo todo lo de Fase 3 y Fase 4
(0% de cobertura antes de esta fase). Corren contra una base de datos de
prueba real en Postgres, no mocks.

### El hallazgo más importante de esta fase: Django 4.2.1 no es compatible con Python 3.14

Al correr `manage.py test`, **todas** las vistas que renderizan un template
tiraban un error de infraestructura:

```
AttributeError: 'super' object has no attribute 'dicts' and no __dict__ for setting new attributes
```

Causa: el test client de Django captura el contexto de cada template
renderizado (para `assertTemplateUsed`/`response.context`) haciendo
`copy(context)` — y `Context.__copy__` en Django 4.2 choca con un cambio de
comportamiento de `copy.copy()` en Python 3.14. No es un bug de KeyServ.

Se probó primero actualizar solo el parche (`Django==4.2.30`, el último de
la rama LTS 4.2) — seguía roto. Se subió a **Django 5.2.16 LTS**, que sí
soporta Python 3.14 limpio. El usuario confirmó explícitamente que está bien
cambiar versiones de Django/Python si mejora la compatibilidad — no hace
falta quedarse en 4.2.1 solo porque era lo que decía la documentación
original de la tesis. Ningún código de la app tuvo que cambiar por este
upgrade (la API que usa KeyServ — ORM, forms, urls, views, admin — es
estable entre 4.2 y 5.2).

De paso se encontró y arregló un segundo problema de infraestructura: el
`LOGGING` de `settings.py` no sobreescribía el logger `django.request` de
Django, así que los errores 500 se enrutaban al `AdminEmailHandler` por
defecto (activo porque `manage.py test` fuerza `DEBUG=False`), que a su vez
intentaba generar un traceback HTML y chocaba con el mismo problema de
`copy()` — un segundo error tapando al primero. Se agregó un override
explícito en `LOGGING['loggers']['django.request']` para que los 500 solo
vayan a consola.

## 5. Archivos nuevos/modificados en esta fase

- `KeyServApp/fixtures/catalogos_iniciales.json` (nuevo)
- `KeyServApp/templates/KeyServApp/crear_publicacion.html` (nuevo)
- `KeyServApp/tests.py` (reescrito, era el stub vacío)
- `codigo/database/schema.sql` (nuevo, generado desde la migración real)
- `views.py`, `urls.py`, `forms.py`: nuevas vistas de contratación/mensajería
- `paginicio.html`, `perfil.html`, `detalleserv.html`, `reservas.html`, `chat.html`: conectados a datos reales
- `crearperfil.html`, `editarperfil.html`, `pago.html`, `recuperar.html`: `{% csrf_token %}` agregado
- `settings.py`: `DATABASES` apuntando a Postgres real, `LOGGING` con el fix de `django.request`
- `requirements.txt`: `Django==5.2.16` (antes `4.2.1`)

## 6. Qué queda pendiente

Ver `docs/NEW_CODE_CREATED.md` §"Resumen de TODOs pendientes" — en orden de
prioridad: credenciales de Transbank (pagos), persistencia del encoding
facial de referencia (biometría facial), y probar el reconocimiento facial
contra una webcam real (no disponible en este entorno).
