# Refactoring Log — Fase 3

Registro de qué se tocó, por qué, y dónde quedó la versión anterior. Todos
los archivos pre-refactor están respaldados en `codigo/viejo/backup_fase3/`
(pedido explícito del usuario: nunca sobreescribir sin dejar backup).

## Decisiones previas confirmadas con el usuario

1. **Autenticación**: sesión propia ligera sobre `Usuario` (`request.session` +
   `django.contrib.auth.hashers`), no `AUTH_USER_MODEL`. Ver `KeyServApp/decorators.py`.
2. **Base de datos**: PostgreSQL en vez de MySQL (la restricción de la tesis
   era solo para el contexto académico). Ver `docs/RECOMMENDED_ARCHITECTURE.md`.
3. Todo el código nuevo/refactorizado lleva comentarios en español explicando
   qué hace cada función (pedido explícito, para poder tocar el código a
   mano más adelante sin releer todo).

## Interpretación de `codigo/frontend/` y `codigo/database/`

El prompt de esta fase pedía carpetas `codigo/frontend/`, `codigo/backend/`,
`codigo/database/`. Dado que la arquitectura decidida en Fase 2 es Django
server-rendered (sin SPA separada), **no se creó un `codigo/frontend/` vacío**
— el frontend vive dentro de `codigo/backend/django/KeyServApp/templates/` +
el nuevo `static/`. Se creó `codigo/database/` con un `README.md` explicando
que el esquema real lo gestionan las migraciones de Django, no un script SQL
a mano (el `schema.sql` de referencia queda pendiente de generar hasta que
haya un Postgres corriendo — ver `docs/SETUP_INSTRUCTIONS.md`).

## Archivos refactorizados

| Archivo | Backup en `codigo/viejo/backup_fase3/` | Qué cambió |
|---|---|---|
| `KeyServApp/models.py` | `KeyServApp/models.py` | Nombres de atributo a `snake_case` con `db_column` MAYÚSCULA (preserva el diccionario de datos de la tesis), `ForeignKey` reales donde antes había enteros sueltos (esto es lo que rompía `load_comunas`), `AutoField`/`BigAutoField` en las PK que antes eran manuales, `Usuario.password` con `set_password()`/`check_password()` reales (elimina el bug de re-hasheo en cada `save()`), campo nuevo `es_proveedor`. Se agregó el modelo `Contratacion` (no existía). |
| `KeyServApp/views.py` | `KeyServApp/views.py` | Reescrito completo: `register_view` ahora usa `forms.py` y nombres de campo reales (antes tiraba `TypeError` garantizado), `sesion_view` pasó de renderizar sin lógica a loguear de verdad, `logout_view` es nuevo, `load_comunas` corregido. Se eliminaron la función duplicada, los imports repetidos y los bloques comentados muertos de la versión anterior. |
| `KeyServApp/urls.py` | `KeyServApp/urls.py` | De 2 rutas activas a 24 — todas las 18 páginas heredadas de la tesis ahora tienen URL, más las rutas nuevas de publicaciones/contratación/biometría/pagos/valoraciones. |
| `KeyServApp/admin.py` | `KeyServApp/admin.py` | De 0 a ~24 modelos registrados. `Publicaciones` tiene `list_editable` en el estado de moderación para poder aprobar/rechazar directo desde el listado. |
| `KeyServProject/settings.py` | `KeyServProject/settings.py` | `SECRET_KEY`/credenciales de DB movidas a variables de entorno (`django-environ`), motor cambiado a PostgreSQL, `STATICFILES_DIRS` corregido (apuntaba a una carpeta que nunca existió), `LOGGING` agregado, `LANGUAGE_CODE`/`TIME_ZONE` a español/Chile. |
| `KeyServApp/migrations/0001_initial.py` | `KeyServApp/migrations/0001_initial.py` | Se eliminó la migración original (pensada para el `models.py` viejo/MySQL) y se regeneró desde cero contra el modelo corregido — no había datos reales que preservar. |
| `codigo/biometria/huella/IMAGEN_HUELLA.py` | `biometria_huella/IMAGEN_HUELLA.py` | De script top-level (con `img.show()` incluido, inutilizable en servidor) a función `procesar_huella()` reutilizable, importable desde Django vía `KeyServApp/biometria.py`. |
| `codigo/biometria/huella/AUTENTIFICACION.py` | — (edición puntual, no reescritura completa) | Se sacó la contraseña SMTP real hardcodeada (`"Wesdxc32"`) y el email personal a variables de entorno. **El resto del archivo sigue roto/legacy a propósito** (depende de `CONEXION_BD.cur`, que no existe) — la decisión de arquitectura es reemplazar este flujo por una vista Django, no reparar el script CLI. |
| `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` | `reconocimiento_facial/probando_face_recognition.py` | Reescrito desde el volcado de bytes original (que no era Python válido) a un módulo real con `cargar_rostro_conocido()`/`verificar_rostro()`. |
| 18 templates HTML | (no se respaldaron individualmente — el diff completo queda en el historial de git) | Ver `docs/CODE_QUALITY_IMPROVEMENTS.md` §"Templates" para el detalle de qué se corrigió en cada uno (enlaces rotos, rutas de CSS/imágenes). |

## Archivos nuevos (no son refactor, ver `docs/NEW_CODE_CREATED.md` para el detalle completo)

`forms.py`, `decorators.py`, `biometria.py`, `pagos.py`, y el modelo `Contratacion` dentro de `models.py`.

## Verificación realizada

- `python manage.py check` → sin errores.
- `python manage.py makemigrations KeyServApp` → generó `0001_initial.py` limpio, sin warnings de campos faltantes (más allá del aviso esperado de que no hay conexión a Postgres para comparar historial).
- `python -m py_compile` sobre los 12 archivos `.py` tocados → todos compilan.
- Import real de `KeyServApp.biometria`/`KeyServApp.pagos`/`KeyServApp.forms`/`KeyServApp.decorators` con `django.setup()` → sin errores.
- Cada `{% static %}` de los 18 templates verificado contra archivos reales en `KeyServApp/static/` (ninguno apunta a un archivo inexistente).
- Cada `{% url %}` de los 18 templates verificado contra los nombres definidos en `urls.py`.
- **No se pudo correr** `manage.py migrate` ni `sqlmigrate` (requieren una conexión viva a Postgres, no disponible en este entorno) — pendiente para cuando el usuario tenga Postgres corriendo, ver `docs/SETUP_INSTRUCTIONS.md`.

## Importante: rotar la contraseña SMTP expuesta

Se removió la contraseña de `AUTENTIFICACION.py`, pero **esa contraseña ya
quedó en el historial de git** desde antes de esta fase (commits de Fase 1 y
Fase 2). Sacarla del archivo actual no la saca del historial. Se recomienda
**cambiar esa contraseña de la cuenta de correo real cuanto antes** — es
independiente de cualquier limpieza de código que se haga en el repo.
