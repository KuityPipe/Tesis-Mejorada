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

`codigo/backend/django/.env` **ya existe y está configurado** (gitignorado,
no está en el repo). Si necesitás recrearlo desde cero:

```powershell
Copy-Item .env.example codigo\backend\django\.env
```

Y completar con valores reales — `DJANGO_SECRET_KEY` puede ser cualquier
string largo random en desarrollo (nunca reusar el mismo valor en producción).

## 3. Base de datos: PostgreSQL — YA INSTALADA Y CORRIENDO

Se instaló PostgreSQL 17 de forma **portable** (sin el instalador gráfico
oficial, que fallaba en este entorno sin sesión de escritorio interactiva —
se usaron los binarios "zip" en su lugar) en `C:\pgsql`, con los datos en
`C:\pgsql\data`. Está registrado como **servicio de Windows** (arranca solo
con el sistema):

```powershell
Get-Service -Name postgresql-keyserv          # ver estado
Start-Service -Name postgresql-keyserv        # si estuviera detenido
Stop-Service -Name postgresql-keyserv         # para detenerlo
```

Credenciales configuradas en `.env` (puerto 5432, host `localhost`):
- Base de datos: `keyserv`
- Usuario: `postgres`, password: `keyserv_local_dev` (**es un password de desarrollo local, cambiarlo si esto se despliega alguna vez**)

Ya se corrió `manage.py migrate` contra esta instancia — las ~24 tablas
existen de verdad en `C:\pgsql\data`, no es solo una migración generada sin
aplicar. `codigo/database/schema.sql` también ya se generó desde la
migración real aplicada. Se creó además un superusuario de Django
(`admin` / `keyserv_admin_dev`) para entrar a `/admin/`.

**Catálogos reales cargados** (Fase 4): se encontró un dump MySQL viejo del
proyecto (`notpaper3 (3).sql`, fuera del repo, en una carpeta personal del
usuario) con datos reales de desarrollo. Se extrajeron **solo las tablas de
catálogo** (16 regiones de Chile, 330 comunas reales, los 4 `TipoCuenta`
reales — `CLIENTE`/`CLIENTE PREMIUM`/`COLABORADOR`/`COLABORADOR PREMIUM` —,
`TipoFirma`, `EstadoAutentificacion`, `EstadoDocumento`) a
`KeyServApp/fixtures/catalogos_iniciales.json` y se cargaron con
`manage.py loaddata catalogos_iniciales`. **Deliberadamente NO se migraron**
las tablas `usuario`/`autentificacion`/`documento`/`publicaciones`/
`transaccion` del dump — son datos de prueba descartables (usuarios ficticios
tipo "Usuario1"-"Usuario12" más un puñado de cuentas de prueba de los
desarrolladores) con contraseñas hasheadas en SHA-256 sin salt (el hasher
viejo, incompatible con el `check_password()` de PBKDF2 de Fase 3) —
importarlas habría dejado cuentas con contraseñas efectivamente
irrecuperables. El usuario ya rotó sus credenciales reales que aparecían ahí
por separado. Para recargar los catálogos en otra base nueva:

```powershell
cd codigo\backend\django
python manage.py loaddata catalogos_iniciales
```

Si en algún momento preferís migrar a un Postgres gestionado en la nube
(Supabase, Neon, Railway, AWS RDS), simplemente cambiá `DB_HOST`/`DB_USER`/
`DB_PASSWORD`/`DB_PORT` en `.env` a los que te den — el resto no cambia.

```powershell
cd codigo\backend\django
python manage.py runserver 8000
```

## 4. Verificar que el sitio funciona

**Ya verificado end-to-end en esta fase** (no es solo teoría): se registró un
usuario de prueba real vía POST a `/registro/`, se confirmó que el password
quedó hasheado (no en texto plano) y que `check_password()` funciona, se hizo
login real por `/sesion/`, y se probó `/ajax/load-comunas/` — los 3 flujos
que antes estaban rotos o sin probar ahora funcionan contra una base de
datos real. El usuario de prueba se borró después de verificar.

Para probarlo vos mismo, con el servidor corriendo (`python manage.py runserver 8000`):
1. `http://localhost:8000/` — página de inicio.
2. `http://localhost:8000/registro/` — registrar un usuario (las 16 regiones y 330 comunas reales de Chile ya están cargadas).
3. `http://localhost:8000/sesion/` — loguearse con ese usuario.
4. `http://localhost:8000/admin/` — con `admin`/`keyserv_admin_dev`, deberías ver los ~24 modelos ya registrados.

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

- [x] ~~Levantar Postgres y correr `migrate`~~ — hecho en esta fase (servicio `postgresql-keyserv`, ver §3).
- [x] ~~Rotar la contraseña SMTP~~ — confirmado por el usuario.
- [x] ~~Cargar regiones/comunas de Chile~~ — hecho en esta fase, 16 regiones + 330 comunas reales vía `KeyServApp/fixtures/catalogos_iniciales.json` (ver §3).
- [ ] Conseguir credenciales de Transbank ambiente integración si querés
      probar pagos.
- [ ] Decidir/diseñar la pantalla de "crear publicación" (ver `docs/NEW_CODE_CREATED.md`).
- [ ] Si esto se despliega alguna vez: cambiar `DB_PASSWORD`/`DJANGO_SECRET_KEY` de los valores de desarrollo local a algo generado para ese entorno, y considerar migrar de la instancia portable local a un Postgres gestionado (ver §3).
