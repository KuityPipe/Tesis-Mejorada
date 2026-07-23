# Arquitectura Recomendada — KeyServ

Basado en `docs/PDF_ANALYSIS_FINDINGS.md` (requisitos de la tesis) y `docs/CODE_ANALYSIS_FINDINGS.md` (estado real del código). Principio rector: **la tesis ya fijó el stack como restricción del proyecto** (Django, MySQL, AWS) y el modelo de datos del diccionario de datos coincide con lo ya implementado — no hay motivo técnico para reescribir desde cero. La recomendación es **consolidar sobre lo que existe**, no reemplazarlo.

## 1. Stack recomendado

| Capa | Recomendación | Justificación |
|---|---|---|
| Backend | **Django 4.2.x** (monolito, mismo framework ya usado) | Restricción explícita del PDF (PAGE 133-134); modelo de datos de 24 tablas ya migrado y validado contra el diccionario de datos de la tesis |
| Base de datos | **MySQL, un solo schema (`notpaper2`)** | Ya usado por Django; se elimina el schema `notpaper` duplicado que solo usaba el Flask muerto (ver §3) |
| Frontend | **Django templates server-rendered** (HTML/CSS/JS vanilla, sin framework SPA) | Coincide con la restricción del PDF ("HTML, CSS3, JavaScript", sin mención de SPA); los 21 templates ya existen, reescribir a React/Vue sería tirar trabajo ya hecho sin que el PDF lo pida |
| Autenticación | **`django.contrib.auth`** con modelo de usuario personalizado (`AbstractUser` o perfil 1-a-1 sobre `Usuario`) + hashers nativos (PBKDF2/Argon2) | El diccionario de datos del PDF ya incluye `django_session` (PAGE 129) — los autores ya contemplaban el sistema de sesiones nativo de Django, nunca se usó. Elimina el bug de SHA256 sin salt y el re-hash en cada `save()` |
| Biometría | Módulo interno de Django (`KeyServApp/biometria/` o app separada `Biometria`), **no un proceso Flask aparte** | Hoy la huella y el reconocimiento facial corren aislados sin conexión HTTP a Django — no tiene sentido mantenerlos como microservicio Flask separado cuando pueden ser funciones Python invocadas directamente desde la vista de registro/login, evitando la duplicación de conexión a BD que ya causó el desalineamiento `notpaper`/`notpaper2` |
| Pagos | **Transbank Webpay Plus** (SDK oficial `transbank-sdk-python`) como proveedor primario | Es el estándar de facto en Chile y el único de los dos proveedores mencionados en el PDF (Transbank/PayPal, PAGE 11) con encaje natural para un marketplace 100% chileno; PayPal queda como opción secundaria si se necesita cobro internacional |
| Identidad gubernamental | **ClaveÚnica vía OpenID Connect (OIDC)**, condicionado a convenio institucional | El PDF (PAGE 11, 51) exige un "convenio con ChileGob" — esto es una dependencia de negocio/legal antes que técnica; no se puede integrar sin que el convenio exista. Se documenta como integración diferida (ver roadmap Fase 3) |
| Hosting | **AWS** (EC2 o Elastic Beanstalk + RDS MySQL) | Restricción explícita del PDF |
| Tests / CI | **pytest-django** + GitHub Actions | El repo ya usa GitHub (confirmado por `TesisAntigua/`); no hay CI hoy |

## 2. Por qué NO cambiar de stack

- El modelo de datos (24 tablas) fue diseñado en el diccionario de datos de la tesis y coincide con `models.py` — cambiar de ORM/framework obligaría a rediseñar esa parte, que es la única que el análisis de código confirma como completa y correcta.
- Las restricciones del PDF (sección 1.8.3.2, PAGE 133-134) son literalmente un contrato con el cliente/evaluador académico: Django + MySQL + AWS + SSL/TLS + tiempo de respuesta ≤3s. Ignorarlas no es "modernizar", es desviarse de lo entregado.
- El código roto no está roto por el stack — está roto por errores de implementación puntuales (nombres de campo desalineados, credenciales hardcodeadas, script corrupto). Esos se arreglan sin migrar de framework.

## 3. Componentes clave y su rol

```
codigo/backend/django/          Monolito Django — único punto de entrada HTTP
  KeyServApp/
    models.py                   24 modelos — MIGRAR a ForeignKey reales (portar de codigo/viejo/ProyectoDjango, que ya usa inspectdb con db_column correcto)
    views.py                    Vistas de negocio — reescribir register_view/sesion_view usando forms.py + auth nativo
    forms.py                    NUEVO — ModelForm por cada flujo (registro, publicación, contratación)
    biometria/                  NUEVO módulo — envuelve la lógica de IMAGEN_HUELLA.py y el reconocimiento facial (reescrito) como funciones invocadas desde las vistas, no procesos aparte
    urls.py                     Completar con las 19 rutas faltantes, portando el patrón de codigo/viejo/ProyectoDjango (16 vistas mostrarXXX ya wireadas ahí)
    admin.py                    Registrar los 24 modelos
  KeyServProject/
    settings.py                 SECRET_KEY y credenciales DB a variables de entorno (django-environ), STATICFILES_DIRS corregido

codigo/biometria/huella/        Se retiene SOLO como librería de procesamiento de imagen (IMAGEN_HUELLA.py ya no depende de Flask/DB) — CONEXION_BD.py, REGISTRO_BD.py, AUTENTIFICACION.py, GUARDAR_DOCUMENTO.py se DEPRECAN como servidores Flask independientes; su lógica útil (envío de código SMTP, guardado de documento) se porta a vistas Django

codigo/biometria/reconocimiento_facial/   Reescribir probando_face_recognition.py como módulo Python válido, expuesto igual que la huella: función invocada desde Django, no proceso aislado
```

**Eliminación recomendada (no ahora, en Fase 3 de limpieza):** el API Flask de `CONEXION_BD.py` (`/regiones`, `/comunas/<id>`) es **funcionalmente redundante** — Django ya sirve exactamente lo mismo vía `/ajax/load-comunas/` (`load_comunas` en `views.py`). Mantener dos implementaciones de la misma consulta contra dos bases de datos distintas (`notpaper` vs `notpaper2`) es la causa raíz del desalineamiento de esquemas encontrado en el análisis de código.

## 4. Flujo de autenticación biométrica recomendado

1. Registro estándar (RUT, email, password) vía `forms.py` + `django.contrib.auth.hashers`.
2. Paso adicional obligatorio (RF001): captura de huella o rostro desde el navegador → POST a un endpoint Django → invoca el módulo `biometria/` internamente (sin salir del proceso Django) → guarda hash/resultado en el modelo correspondiente.
3. Procesamiento pesado de imagen (especialmente reconocimiento facial con `dlib`/`face_recognition`) se ejecuta de forma **asíncrona** (Celery + Redis, o `django-rq`) para no violar la restricción de tiempo de respuesta ≤3s del PDF — la vista responde de inmediato con "procesando" y notifica el resultado vía polling o WebSocket.
4. Login: credenciales estándar vía `django.contrib.auth`; la biometría queda como verificación de registro (según RF001), no como factor de cada login, salvo que el negocio decida lo contrario.

## 5. Riesgos de arquitectura a vigilar

- El PDF no especifica requisitos de carga/concurrencia (§11 de `PDF_ANALYSIS_FINDINGS.md`) — antes de comprometerse a RNF014 ("escalabilidad") hay que definir un número objetivo de usuarios concurrentes con el negocio.
- `face_recognition`/`dlib` son pesados de instalar y correr (requieren compilación nativa) — validar que el entorno de AWS elegido pueda soportarlo, o evaluar un servicio gestionado de reconocimiento facial como alternativa si el deployment se complica.
- La integración con ClaveÚnica depende de un convenio institucional que aún no existe — no bloquear el resto del roadmap esperando esa integración.
