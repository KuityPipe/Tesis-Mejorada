# Roadmap de Desarrollo — KeyServ

Basado en `docs/PDF_ANALYSIS_FINDINGS.md`, `docs/CODE_ANALYSIS_FINDINGS.md` y `docs/RECOMMENDED_ARCHITECTURE.md`. El código actual cubre ~15-20% de los requisitos funcionales documentados en la tesis y **ningún flujo de negocio funciona de punta a punta hoy**. Este roadmap prioriza destrabar un flujo mínimo funcional antes de sumar features nuevas.

Esfuerzo estimado en talla de camiseta: **S** (< 1 día), **M** (2-5 días), **L** (1-2 semanas), **XL** (> 2 semanas) — para un desarrollador part-time, sin equipo dedicado.

## FASE MVP — Desbloquear un flujo de negocio real

Objetivo: que un usuario se pueda registrar, verificar por huella, hacer login, publicar y contratar un servicio, de punta a punta, sin errores 500.

| # | Item | Esfuerzo | Por qué es bloqueante |
|---|---|---|---|
| 1 | Arreglar desalineamiento de nombres de campo `views.py` ↔ `models.py` (portar modelo de `codigo/viejo/ProyectoDjango`, con `db_column`/`ForeignKey` reales) | M | Sin esto, **ningún** registro de usuario funciona — es el bug #1 encontrado en el análisis de código |
| 2 | Migrar autenticación a `django.contrib.auth` (modelo de usuario custom + hashers PBKDF2/Argon2) | M | Elimina el bug de password re-hasheado en cada `save()` y el hashing SHA256 sin salt; habilita login/logout real (RF003/RF005/RF006) |
| 3 | Sacar `SECRET_KEY` y credenciales (DB, SMTP) a variables de entorno (`.env` + `django-environ`) y **rotar la contraseña SMTP expuesta** (`Wesdxc32`) | S | Riesgo de seguridad crítico ya en el repo; rotar la contraseña real de esa cuenta de correo es urgente e independiente del código |
| 4 | Completar `urls.py`/`views.py` para las 19 páginas sin ruta, portando el wiring de `codigo/viejo/ProyectoDjango` (16 vistas `mostrarXXX` ya resueltas ahí) | L | Hoy solo 2 de 21 páginas son alcanzables por URL — sin esto no hay sitio navegable |
| 5 | Unificar el backend de biometría de huella: eliminar la dependencia rota de `CONEXION_BD.cur`, integrar `IMAGEN_HUELLA.py` como módulo invocado desde una vista Django (no un script Flask aparte) | M | RF001 exige verificación biométrica en el registro; hoy no hay ningún punto de conexión entre biometría y la app |
| 6 | Reescribir `probando_face_recognition.py` como Python válido e integrarlo igual que la huella | M | Es uno de los dos métodos de verificación obligatorios según RF001; hoy no es ni siquiera código ejecutable |
| 7 | Corregir `STATICFILES_DIRS` y reubicar CSS/imágenes fuera de `templates/` a una carpeta `static/` real | S | Los `{% static %}` de los 2 templates que ya los usan no resuelven a nada hoy |
| 8 | Registrar los 24 modelos en `admin.py` | S | Sin esto no hay forma de inspeccionar datos durante el desarrollo/QA |
| 9 | Agregar campo de estado de moderación a `Publicaciones` + vista de aprobación (BPMN "Crear publicación", PAGE 135-136 del PDF) | M | Requisito de negocio explícito en el diseño BPMN de la tesis, no solo deuda técnica |
| 10 | Suite de tests mínima: `Usuario.save()`/hashing, `register_view` POST, `load_comunas`, import de los módulos de biometría, `manage.py check` en CI | M | 0% de cobertura hoy; estos 4 tests habrían atrapado los 4 bugs más graves encontrados |

**Esfuerzo total Fase MVP: ~4-6 semanas** (talla L-XL agregada), asumiendo un desarrollador.

## FASE 2 — Funcionalidad secundaria (valor de negocio, no bloqueante para un demo interno)

| # | Item | Esfuerzo |
|---|---|---|
| 11 | Vista de búsqueda/listado de `Publicaciones` (RF004) | M |
| 12 | Flujo de contratación cliente-proveedor con re-autenticación (BPMN "Proceso de contratación", PAGE 136-137) | L |
| 13 | Integración de pagos Transbank Webpay Plus (RF012) | L |
| 14 | Mensajería entre `Usuario`s sobre los modelos `Mensaje`/`Conversacion` ya existentes | L |
| 15 | Sistema de valoración/calificación por estrellas post-servicio (`Valoracion`/`Ranking`) | M |
| 16 | Auditoría CSRF completa: agregar `{% csrf_token %}` a los 19 templates restantes | S |
| 17 | Rate-limiting en el código de verificación SMTP de 5 dígitos (`AUTENTIFICACION.py`) | S |
| 18 | Guía de estilos consistente (paleta Powder Blue/Cornflower Blue del PDF, PAGE 171-172) aplicada uniformemente en el CSS | M |

## FASE 3 — Futuro / dependiente de terceros

| # | Item | Esfuerzo | Dependencia |
|---|---|---|---|
| 19 | Integración ClaveÚnica (OIDC) + firma electrónica e-certchile | XL | **Bloqueado por convenio institucional con el Estado**, no es solo trabajo de ingeniería |
| 20 | Eliminar el API Flask redundante de `CONEXION_BD.py` (`/regiones`, `/comunas`) — ya cubierto por `/ajax/load-comunas/` de Django | S | — |
| 21 | Pipeline CI/CD (GitHub Actions: lint + tests + `manage.py check`) | M | — |
| 22 | Dockerizar el proyecto (hay artefactos `.pyc` de Python 3.9/3.10/3.11 mezclados — entornos inconsistentes entre desarrolladores) | M | — |
| 23 | Cola async (Celery/Redis o django-rq) para procesamiento biométrico pesado, ver `RECOMMENDED_ARCHITECTURE.md` §4 | L | — |
| 24 | Pruebas de carga/concurrencia — el PDF no define un número objetivo, hay que consensuarlo con el negocio primero | M | Requiere definición de negocio |
| 25 | HTTPS/SSL en el entorno de despliegue (restricción explícita del PDF, PAGE 134) | S | Depende de la infraestructura AWS elegida |

## Deuda técnica transversal (aplicar durante las fases de arriba, no como fase separada)

- Generar `requirements.txt` con versiones fijadas (Django 4.2.1, Pillow, face_recognition, opencv-python, fpdf2, django-environ, etc.) y fijar la versión de Python objetivo (recomendado: 3.11, es la más usada entre los `.pyc` encontrados).
- Eliminar código muerto: `register_view` duplicada, imports duplicados, bloques comentados grandes en `views.py`/`urls.py`.
- Estandarizar convención de nombres (hoy mezcla `snake_case`/`UPPERCASE`/`camelCase` según archivo).
- Sanear nombres de archivo en `GUARDAR_DOCUMENTO.py` antes de exponerlo como endpoint de subida (riesgo de path traversal si se reactiva tal cual).

## Priorización resumida

1. **Fase MVP (#1-10)** — sin esto no hay producto, es requisito para cualquier demo o venta.
2. **Fase 2 (#11-18)** — features de valor diferencial (pagos, contratación, mensajería) que convierten el MVP en un producto usable por usuarios reales.
3. **Fase 3 (#19-25)** — expansión y robustez operativa; #19 (ClaveÚnica) es la única con dependencia externa fuerte y debería gestionarse en paralelo desde ya (el convenio institucional toma tiempo) aunque el desarrollo técnico se haga al final.
