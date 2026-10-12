# Análisis de Código — KeyServ

Fecha: revisión post-Fase 1 (reorg de carpetas). Rutas usadas: `codigo/backend/django` (activo), `codigo/biometria/huella`, `codigo/biometria/reconocimiento_facial`, `codigo/viejo/ProyectoDjango`, `codigo/viejo/ProyectoKeyServ`.

## 1. Resumen ejecutivo

El código es el resultado de un desarrollo académico de ~2 meses (mayo-junio 2023), nunca completado más allá de un prototipo. **Ningún flujo de negocio funciona hoy de punta a punta.** El hallazgo más grave: el proyecto Django "activo" (`codigo/backend/django`) tiene una discordancia sistemática entre los nombres de campo en MAYÚSCULAS de `models.py` y los nombres en minúsculas usados en `views.py` — esto significa que el único formulario "funcional" documentado (registro de usuario) **falla garantizado con `TypeError`** apenas se envía un POST. Curiosamente, la variante legacy `ProyectoDjango` sí tiene los nombres de campo correctos (fue generada con `inspectdb` sobre la base de datos real), por lo que **hay más código correcto en la carpeta "vieja" que en la activa** para ese flujo puntual.

El backend de biometría (`codigo/biometria/huella`) tiene 3 de 4 scripts rotos por una dependencia inexistente (`CONEXION_BD.cur`), y el script de reconocimiento facial no es ni siquiera texto Python válido. No hay tests, no hay `requirements.txt`, hay credenciales y secretos hardcodeados en texto plano en al menos 4 archivos.

## 2. Stack tecnológico

| Capa | Tecnología detectada | Evidencia |
|---|---|---|
| Backend web principal | Django 4.2.1 | `settings.py`, comentarios en migraciones |
| Backend biometría | Flask + `flask_mysqldb` | `codigo/biometria/huella/CONEXION_BD.py` |
| Backend biometría (alternativo, muerto) | `pymysql` | bloque comentado en `CONEXION_BD.py` |
| Base de datos | MySQL | `DATABASES.ENGINE = django.db.backends.mysql` |
| Procesamiento de imágenes | Pillow (`PIL`), `math` puro | `IMAGEN_HUELLA.py` |
| PDF | `fpdf` (FPDF) | `GUARDAR_DOCUMENTO.py` |
| GUI de escritorio | `tkinter` | `GUARDAR_DOCUMENTO.py` (uso indebido en un backend) |
| Reconocimiento facial (intención) | `opencv-python` (`cv2`) + `face_recognition` | inferido del contenido decodificado de `probando_face_recognition.py` |
| Email | `smtplib` + `email.message` (stdlib) | `AUTENTIFICACION.py` |
| Hashing | `hashlib` — SHA256 (passwords), MD5 (código de verificación) | `models.py`, `AUTENTIFICACION.py` |
| Frontend | HTML/CSS puro, sin JS de framework, sin build step | `templates/KeyServApp/` |
| Autenticación | Custom, no usa `django.contrib.auth` pese a tenerlo instalado | `models.py` (`Usuario` no hereda de `AbstractUser`) |

**No declarado en ningún lado:** versión de Python objetivo (se detectan artefactos `.pyc` de Python 3.9, 3.10 y 3.11 en distintas carpetas — entornos inconsistentes entre desarrolladores), ni un `requirements.txt`/`Pipfile`/`pyproject.toml`.

## 3. Inventario por componente

| Componente | Ruta | Estado |
|---|---|---|
| Backend Django activo | `codigo/backend/django/` | Arranca (probablemente), pero sus 2 únicas rutas activas están rotas en runtime |
| Biometría huella | `codigo/biometria/huella/` | 1 de 5 scripts funcional de forma aislada, 3 rotos, 1 es solo datos |
| Reconocimiento facial | `codigo/biometria/reconocimiento_facial/` | 0% funcional — no es código válido |
| Django legacy #1 | `codigo/viejo/ProyectoDjango/` | Más completo en wiring de URLs/vistas que el activo, pero nunca depurado (bloque muerto con errores de sintaxis) |
| Django legacy #2 | `codigo/viejo/ProyectoKeyServ/` | Scaffold vacío (`startproject`/`startapp`), sin lógica |

## 4. Código funcional (qué corre hoy)

- **`codigo/backend/django`**: el servidor Django arranca y sirve páginas vía `GET` (ej. `registro/` renderiza el formulario). El renderizado de templates que no dependen de datos de la DB (la mayoría de las 21 páginas) funcionaría si se las conecta a una URL — hoy 19 de 21 no tienen ruta asignada.
- **`codigo/biometria/huella/IMAGEN_HUELLA.py`**: el pipeline de procesamiento de imagen (carga → binarización → adelgazamiento → poda → hash SHA256) es lógicamente autocontenido y no depende de la base de datos ni de Flask. Es el único script de biometría que podría ejecutarse hoy — **con una salvedad crítica**: usa rutas hardcodeadas `"BackHuella/Huella Imagen/..."` (líneas 13, 16, 30, 32, 78, 114, 160, 172, 185, 187, 190) que **ya no existen** tras la reorganización de Fase 1 (la carpeta se llama ahora `codigo/biometria/huella/`). Este script quedó roto por el propio reorg y hay que actualizar esas 9 rutas.
- Los 24 modelos ORM de `codigo/backend/django` son válidos y migran correctamente (una sola migración inicial, ya aplicada en su momento).

## 5. Código roto (causa raíz de cada falla)

| Archivo | Falla | Causa raíz |
|---|---|---|
| `codigo/backend/django/KeyServApp/views.py:50-72` (`register_view`, rama POST) | `TypeError` garantizado al recibir un POST a `/registro/` | Usa kwargs en minúscula (`rut_usuario`, `contrasena`, etc.) contra un modelo `Usuario` cuyos campos reales están en MAYÚSCULAS (`RUT_USUARIO`, `CONTRASEÑA`) y sin relación `ForeignKey` real — Django no hace match case-insensitive de kwargs |
| `codigo/backend/django/KeyServApp/views.py:50-53` | `FieldError: Cannot resolve keyword 'id'` | `Region.objects.get(id=...)`, `Comuna.objects.get(id=...)`, `TipoCuenta.objects.get(id=...)` — el PK real se llama `ID_REGION`/`ID_COMUNA`/`ID_TIPO_CUENTA`, no `id` |
| `codigo/backend/django/KeyServApp/views.py:85-89` (`load_comunas`) | `FieldError` al llamarse desde el AJAX de comunas | `Comuna.objects.filter(region_id=...)` — `FK_REGION` es un `IntegerField` plano, no un `ForeignKey`, por lo que Django no genera el alias `region_id`; además `.order_by('nombre_comuna')` y `.values('id', 'nombre_comuna')` usan nombres que no existen en el modelo |
| `codigo/biometria/huella/REGISTRO_BD.py:9-10` | `AttributeError: module 'CONEXION_BD' has no attribute 'cur'` al importar | `cur` solo se define dentro de un bloque `"""..."""` (comentado) en `CONEXION_BD.py`; el código activo de `CONEXION_BD.py` usa `flask_mysqldb`, que no expone `cur` a nivel de módulo |
| `codigo/biometria/huella/REGISTRO_BD.py:29` | Flask no arrancaría (`ValueError: ... must start with a leading slash`) | `@app.route('Pag/registroinicio.html', ...)` — falta el `/` inicial y además referencia una ruta de archivo (`Pag/`), no una URL |
| `codigo/biometria/huella/AUTENTIFICACION.py:9-10` | Mismo `AttributeError` que arriba, más: es un script lineal con `input()`, no un endpoint | No está expuesto vía Flask/web; además ejecuta un envío real de correo con credenciales hardcodeadas en cuanto se importa/ejecuta |
| `codigo/biometria/huella/GUARDAR_DOCUMENTO.py:10-11` | Mismo `AttributeError`; además `pdf` (objeto `FPDF`) se pasa directo como parámetro SQL en la línea 49 | Debería guardarse el archivo generado (bytes) o su ruta, no el objeto Python en memoria — fallaría el binding del driver MySQL |
| `codigo/biometria/reconocimiento_facial/probando_face_recognition.py` | `SyntaxError` / no ejecutable | El archivo contiene un volcado de bytes decimales separados por coma, no texto Python (issue ya conocido, confirmado) |

## 6. Scaffolding sin implementar

- **Login / sesión de usuario**: `sesion_view` (views.py:33-35) renderiza `sesion.html` sin ninguna lógica — no valida credenciales, no crea sesión. El login descrito conceptualmente en la documentación del proyecto **no existe en código**.
- **19 de 21 páginas HTML** de `codigo/backend/django` (chat, perfil, reservas, pago, huella, valoraciones, etc.) no tienen `path()` en `urls.py` — son solo archivos de template sin vista que los sirva.
- **Panel de administración Django**: `admin.py` está vacío, 0 de 24 modelos registrados — hoy no hay forma de inspeccionar/editar datos vía `/admin/`.
- **`forms.py`**: no existe; toda la validación de formulario se hace ad-hoc con `request.POST.get(...)` sin `Form`/`ModelForm`, sin validación de tipos ni sanitización.
- **Autenticación biométrica real** (huella + facial) integrada al flujo de login/registro: no existe ningún punto de conexión entre `IMAGEN_HUELLA.py`/`probando_face_recognition.py` y la app Django — son scripts aislados, nunca se llaman desde una vista.
- **Pagos**: existen templates (`pago.html`, `pagoexitoso.html`, `tarjeta credito.html` — este último vacío, 0 bytes) y un modelo `Transaccion`, pero cero lógica de integración con una pasarela de pago real.
- **Notificaciones/mensajería**: modelos `Mensaje`/`Conversacion` existen en la DB, sin ninguna vista ni lógica.

## 7. Hallazgos de seguridad

| # | Hallazgo | Ubicación | Severidad |
|---|---|---|---|
| 1 | `SECRET_KEY` de Django hardcodeada en el repo | `codigo/backend/django/KeyServProject/settings.py:11`, y también en las 2 variantes legacy | Alta |
| 2 | Credencial SMTP en texto plano (`Wesdxc32`) | `codigo/biometria/huella/AUTENTIFICACION.py:57` | Crítica — es una contraseña de cuenta de correo real |
| 3 | Email personal hardcodeado como remitente | `codigo/biometria/huella/AUTENTIFICACION.py:32` (`kuitysalinas@outlook.com`) | Media (privacidad) |
| 4 | Passwords con SHA256 **sin salt** | `codigo/backend/django/KeyServApp/models.py:220` | Alta — vulnerable a tablas rainbow, no usa `django.contrib.auth.hashers` (PBKDF2/Argon2) pese a tener el framework instalado |
| 5 | `Usuario.save()` re-hashea el password en cada `.save()` | `models.py:219-221` | Alta — si se llama `usuario.save()` dos veces (ej. al actualizar cualquier otro campo), el password legítimo se vuelve irrecuperable (hash del hash) |
| 6 | Sin validación de inputs en las vistas | `views.py` en las 3 variantes Django | Media — `int(request.POST.get('edad'))` etc. sin try/except, cualquier input no numérico causa `500` |
| 7 | CSRF: solo 2 de 21 templates incluyen `{% csrf_token %}` | `templates/KeyServApp/*.html` | Media — cualquier formulario de los otros 19, si se conecta a una vista POST, será rechazado por CSRF (correcto por diseño, pero indica que ninguno fue probado end-to-end) |
| 8 | Credenciales de base de datos en texto plano (usuario root sin password) | `settings.py` (Django) y `CONEXION_BD.py` (Flask), en las 3 variantes | Media (mitigado en dev local, crítico si se despliega tal cual) |
| 9 | `GUARDAR_DOCUMENTO.py` no sanea el nombre de archivo | `GUARDAR_DOCUMENTO.py:23` (`NombreArchi = Path(archivo).stem`) | Baja hoy (es CLI local), pero si se expone como endpoint de subida de archivos sería un vector de path traversal |
| 10 | No hay rate-limiting ni bloqueo de intentos en el flujo de autenticación por código de 5 dígitos | `AUTENTIFICACION.py` | Media — un código de 5 dígitos sin límite de intentos es fuerza-bruteable |

## 8. Deuda técnica priorizada (crítico → cosmético)

1. **[Crítico/bloqueante]** Arreglar el desajuste de nombres de campo entre `views.py` y `models.py` en `codigo/backend/django` — sin esto, el registro de usuarios no funciona en absoluto.
2. **[Crítico/seguridad]** Rotar y sacar del código la contraseña SMTP y el `SECRET_KEY` de Django; mover todo a variables de entorno (`.env`, ya excluido en `.gitignore` desde Fase 1).
3. **[Crítico/seguridad]** Reemplazar el hashing de passwords por `django.contrib.auth.hashers.make_password` (o Argon2), y quitar el re-hash en cada `save()`.
4. **[Crítico/funcional]** Arreglar `CONEXION_BD.py` (biometría) para que `cur`/la conexión realmente exista y sea importable por los otros 3 scripts, o reescribir esos scripts para no depender de un cursor global de módulo.
5. **[Alto]** Corregir las rutas hardcodeadas de `IMAGEN_HUELLA.py` tras el reorg de Fase 1 (`BackHuella/` → `codigo/biometria/huella/`).
6. **[Alto]** Unificar el nombre de base de datos entre Django (`notpaper2`) y Flask (`notpaper`) — hoy son esquemas distintos.
7. **[Alto]** Repararar/regenerar `probando_face_recognition.py` como texto Python válido.
8. **[Medio]** Completar `urls.py`/`views.py` para las 19 páginas sin ruta, portando el patrón de `ProyectoDjango` (ver sección 9).
9. **[Medio]** Corregir la configuración de archivos estáticos (`STATICFILES_DIRS` apunta a una carpeta inexistente; los CSS/imágenes reales están mal ubicados dentro de `templates/`).
10. **[Medio]** Registrar modelos en `admin.py` para tener visibilidad operativa de los datos.
11. **[Bajo]** Eliminar código muerto: función `register_view` duplicada, imports duplicados de `JsonResponse`/`render`, bloques comentados grandes en `views.py` y `urls.py`.
12. **[Bajo]** Reemplazar el diálogo `tkinter` de `GUARDAR_DOCUMENTO.py` por un endpoint HTTP de subida de archivos real.
13. **[Cosmético]** Estandarizar convención de nombres (mezcla de `snake_case`, `UPPERCASE`, `camelCase` según el archivo).

## 9. Comparación entre variantes Django y qué rescatar

| Aspecto | `codigo/backend/django` (activo) | `codigo/viejo/ProyectoDjango` | `codigo/viejo/ProyectoKeyServ` |
|---|---|---|---|
| Modelos | 24, nombres UPPERCASE, sin `db_column`, sin `ForeignKey` reales (`managed` implícito `True`) | 24, generados con `inspectdb` (`db_column='UPPERCASE'`, `managed=False`, `ForeignKey` reales) | 1 modelo, **vacío (0 bytes)** |
| URLs activas | 2 (`registro/`, `ajax/load-comunas/`) | 16 (`paginicio`, `registroinicio`, `sesion`, `sesioninicio`, `Acercadeenosotros`, `chat`, `contacto`, `crearperfil`, `editarperfil`, `perfil`, `detalleserv`, `huella`, `pago`, `pagoexitoso`, `preferenciascuenta`, `recuperar`, `reservas` — falta confirmar el archivo `urls.py` de `KeyProject`, pero `views.py` define las 16 funciones `mostrarXXX`) | 1 (solo `admin/`) |
| Registro de usuario | Roto (ver sección 5) | **Coincide en nombres de campo con su propio `models.py`** — más cerca de funcionar, aunque nunca se probó (tiene un bloque comentado con errores de sintaxis obvios: `request.POST{'rut')` en vez de `request.POST['rut']`, evidencia de que fue un borrador abandonado) | No aplica (sin vistas) |
| Vale la pena rescatar | — | El **patrón de wiring de 16 vistas `mostrarXXX` → templates**, y el enfoque `inspectdb` con `db_column`/`ForeignKey` reales para el modelo de datos | Nada — es un scaffold vacío, solo sirve como referencia de que fue el primer intento |

**Recomendación concreta**: la forma más rápida de tener un Django funcional es tomar `codigo/viejo/ProyectoDjango/KeyProject/KeyApp/models.py` (con `db_column`/`ForeignKey` correctos) como base del modelo de datos del proyecto activo, y portar el wiring de vistas/URLs de `ProyectoDjango` — en vez de intentar parchear el desajuste de nombres en `codigo/backend/django` campo por campo.

## 10. Cobertura de tests

**0% en las 3 variantes.** Los tres `tests.py` (`codigo/backend/django/KeyServApp/tests.py`, `codigo/viejo/ProyectoDjango/.../tests.py`, `codigo/viejo/ProyectoKeyServ/KeyServ/tests.py`) contienen únicamente el boilerplate de Django (`from django.test import TestCase` + comentario), sin una sola aserción. No hay tests para los scripts de biometría ni para Flask. No hay configuración de CI.

**Qué testear primero si se agregan tests** (orden sugerido, de mayor a menor retorno):
1. `Usuario.save()` / hashing de password (test unitario de modelo) — habría atrapado el bug de re-hash inmediatamente.
2. `register_view` POST (test de vista/integración) — habría atrapado el desajuste de nombres de campo antes de llegar a producción.
3. `load_comunas` (test de vista) — mismo motivo.
4. Import de los 3 scripts de `codigo/biometria/huella/` que dependen de `CONEXION_BD.cur` — un test de import trivial ya habría detectado el `AttributeError`.
5. Test de humo (`manage.py check` + arranque del servidor) como gate mínimo de CI.
