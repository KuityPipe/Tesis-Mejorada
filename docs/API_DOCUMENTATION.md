# Documentación de Rutas — KeyServ

Todas las rutas viven bajo `KeyServApp` (namespace `KeyServApp:`), definidas
en `codigo/backend/django/KeyServApp/urls.py`. Esto no es una API REST/JSON
(salvo `ajax/load-comunas/`) — son vistas Django que renderizan HTML server-side,
consistente con la arquitectura decidida en Fase 2 (sin SPA separada).

## Páginas simples

| Ruta | Nombre | Método | Auth | Template |
|---|---|---|---|---|
| `/` | `paginicio` | GET | No | `paginicio.html` |
| `/acerca-de-nosotros/` | `acerca_de_nosotros` | GET | No | `Acercadeenosotros.html` |
| `/contacto/` | `contacto` | GET | No | `contacto.html` |
| `/inicio/` | `sesion_iniciada` | GET | **Sí** | `Sesioniniciadainicio.html` |
| `/preferencias-cuenta/` | `preferencias_cuenta` | GET | **Sí** | `preferencias de la cuenta.html` |
| `/recuperar/` | `recuperar` | GET | No | `recuperar.html` (TODO: flujo real no implementado) |
| `/tarjeta-credito/` | `tarjeta_credito` | GET | **Sí** | `tarjeta credito.html` (template vacío, 0 bytes) |

## Autenticación

| Ruta | Nombre | Método | Body/Params | Respuesta |
|---|---|---|---|---|
| `/registro/` | `registro` | GET | — | Formulario de registro |
| `/registro/` | `registro` | POST | `rut, nombre1, nombre2, apellido1, apellido2, edad, telefono, email, region, comuna, direccion, tipo_cuenta, es_proveedor, password, password_confirm` | Redirect a `sesion` si es válido; re-renderiza el form con errores si no |
| `/sesion/` | `sesion` | GET | — | Formulario de login |
| `/sesion/` | `sesion` | POST | `email, password` | Redirect a `sesion_iniciada` si las credenciales son válidas; mensaje de error si no |
| `/logout/` | `logout` | GET | — | Limpia la sesión, redirect a `paginicio` |
| `/ajax/load-comunas/` | `ajax_load_comunas` | GET | `?region_id=<int>` | JSON: `[{"id": int, "nombre_comuna": str}, ...]` |

## Perfil

| Ruta | Nombre | Método | Auth |
|---|---|---|---|
| `/perfil/` | `perfil` | GET | **Sí** |
| `/perfil/crear/` | `crear_perfil` | GET | **Sí** |
| `/perfil/editar/` | `editar_perfil` | GET | **Sí** (TODO: no persiste cambios todavía) |

## Publicaciones / servicios

| Ruta | Nombre | Método | Auth | Notas |
|---|---|---|---|---|
| `/servicios/<int:pk>/` | `publicacion_detalle` | GET | No | 404 si `pk` no existe |
| `/servicios/crear/` | `publicacion_crear` | GET/POST | **Sí, solo `es_proveedor=True`** | POST body: `titulo, sub_titulo, descripcion_publicacion`. Redirect a `publicacion_detalle` si es válido |
| `/servicios/<int:publicacion_id>/contratar/` | `contratacion_crear` | POST | **Sí** | Crea una `Contratacion` en estado `SOLICITADA` |

## Contrataciones / valoraciones

| Ruta | Nombre | Método | Auth | Notas |
|---|---|---|---|---|
| `/reservas/` | `reservas` | GET | **Sí** | Lista contrataciones donde el usuario es cliente o proveedor |
| `/contrataciones/<int:contratacion_id>/valorar/` | `valoracion_crear` | GET/POST | **Sí** | Solo si la `Contratacion` está `COMPLETADA`. POST body: `puntuacion (1-5), comentario` |

## Biometría

| Ruta | Nombre | Método | Auth | Notas |
|---|---|---|---|---|
| `/huella/` | `huella` | GET | **Sí** | Pantalla de captura |
| `/huella/verificar/` | `verificacion_huella` | POST | **Sí** | Body: `ruta_imagen` (TODO: en la integración real vendría de un `<input type="file">`, no de texto) |

## Mensajería (esqueleto)

| Ruta | Nombre | Método | Auth | Notas |
|---|---|---|---|---|
| `/chat/` | `chat` | GET | **Sí** | TODO: no lista conversaciones/mensajes reales todavía |

## Pagos (esqueleto)

| Ruta | Nombre | Método | Auth | Notas |
|---|---|---|---|---|
| `/pago/` | `pago` | GET | **Sí** | TODO: no invoca `pagos.TransbankService` todavía |
| `/pago/exitoso/` | `pago_exitoso` | GET | **Sí** | Pantalla de confirmación estática |

## Panel de administración

`/admin/` — Django admin estándar, requiere superusuario (`manage.py createsuperuser`).
Todos los ~24 modelos están registrados (ver `KeyServApp/admin.py`).

## Notas sobre autenticación

"Auth: Sí" significa que la vista está decorada con `@login_requerido`
(`KeyServApp/decorators.py`) — redirige a `/sesion/` si no hay
`request.session['usuario_id']`. Esto es una sesión propia sobre el modelo
`Usuario`, **no** el sistema de autenticación estándar de Django
(`django.contrib.auth` sigue existiendo para el panel `/admin/`, que usa su
propio modelo `User` con superusuarios independientes).
