# Instrucciones de Setup — KeyServ (post Fase 3)

## 1. Entorno Python

```powershell
.\venv_tesis\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ya se instalaron y validaron en `venv_tesis` durante esta fase: `Django==4.2.1`,
`django-environ`, `psycopg2-binary`, `Pillow`. `opencv-python`/`face_recognition`
(reconocimiento facial) y `fpdf2` (generación de PDF) quedan en
`requirements.txt` pero no se instalaron en este entorno — son pesados y no
hacen falta para levantar el resto del sitio; instalarlos solo si vas a
probar esa funcionalidad puntual.

## 2. Variables de entorno

```powershell
Copy-Item .env.example codigo\backend\django\.env
```

Editar `codigo/backend/django/.env` con valores reales. Como mínimo para
desarrollo local: `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` de tu
Postgres. `DJANGO_SECRET_KEY` puede quedar con cualquier string largo random
en desarrollo (nunca reusar el mismo valor en producción).

## 3. Base de datos: PostgreSQL

No había ningún servidor Postgres corriendo en el entorno donde se hizo este
refactor (se confirmó que el puerto 5432 estaba cerrado), así que **falta
este paso de tu lado**. Dos caminos:

**Opción A — Postgres local** (Windows):
1. Descargar el instalador desde postgresql.org (incluye pgAdmin).
2. Crear una base de datos `keyserv` (o el nombre que pongas en `.env`).
3. Completar `DB_*` en el `.env` con esas credenciales.

**Opción B — Postgres gestionado gratis** (más simple, cero instalación local):
Supabase, Neon o Railway dan un Postgres gratis en minutos — copiás la
connection string que te dan a las variables `DB_*` del `.env` (`DB_HOST`
va a ser el host que te den, no `localhost`).

Con cualquiera de las dos, una vez que Postgres responda:

```powershell
cd codigo\backend\django
python manage.py migrate
python manage.py createsuperuser   # para entrar a /admin/
python manage.py sqlmigrate KeyServApp 0001 > ..\..\database\schema.sql   # opcional, referencia
python manage.py runserver 8000
```

`manage.py check` y `manage.py makemigrations` ya se corrieron y validaron
en esta fase sin necesitar una conexión viva — `migrate` sí la necesita, por
eso queda pendiente para cuando levantes tu propio Postgres.

## 4. Verificar que el sitio funciona

Con el servidor corriendo (`python manage.py runserver 8000`):
1. `http://localhost:8000/` — página de inicio.
2. `http://localhost:8000/registro/` — registrar un usuario de prueba.
3. `http://localhost:8000/sesion/` — loguearse con ese usuario.
4. `http://localhost:8000/admin/` — con el superusuario creado arriba, deberías ver los ~24 modelos ya registrados.

## 5. Biometría (opcional, requiere hardware)

- Huella dactilar: `python codigo/biometria/huella/IMAGEN_HUELLA.py` corre
  standalone contra la imagen de ejemplo del repo, no necesita hardware.
- Reconocimiento facial: `python codigo/biometria/reconocimiento_facial/probando_face_recognition.py`
  necesita una webcam conectada y `pip install opencv-python face_recognition`
  (face_recognition depende de `dlib`, que se compila nativamente — en
  Windows puede requerir Visual Studio Build Tools instalados).

## 6. Pagos (bloqueado hasta tener credenciales)

`codigo/backend/django/KeyServApp/pagos.py` necesita `TRANSBANK_COMMERCE_CODE`/
`TRANSBANK_API_KEY` en el `.env` y el SDK instalado (`pip install transbank-sdk`,
no está en `requirements.txt` porque no hay nada que llamar sin credenciales
todavía). Transbank da credenciales de ambiente "integración" (pruebas) sin
costo al registrarse como desarrollador — ver su portal de comercio.

## Checklist de lo que falta de tu lado

- [ ] Levantar Postgres (local o gestionado) y correr `migrate`.
- [ ] Rotar la contraseña SMTP que estaba hardcodeada en el código (ver
      `docs/REFACTORING_LOG.md`, sección final) — es independiente de todo
      lo demás, hacerlo cuanto antes.
- [ ] Conseguir credenciales de Transbank ambiente integración si querés
      probar pagos.
- [ ] Decidir/diseñar la pantalla de "crear publicación" (ver `docs/NEW_CODE_CREATED.md`).
