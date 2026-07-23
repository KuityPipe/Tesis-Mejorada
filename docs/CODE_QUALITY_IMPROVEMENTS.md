# Mejoras de Calidad de Código — Fase 3

## Logging

`KeyServProject/settings.py` tiene ahora un `LOGGING` real (antes no existía
ninguna configuración — los errores quedaban silenciados o como excepción
cruda sin registro). Las vistas nuevas/refactorizadas usan
`logger.info()`/`logger.exception()` en vez de `print()` o fallar en
silencio (ej. `register_view` loguea cada alta de usuario, `biometria.py`
loguea cuando no puede importar un módulo de biometría en vez de reventar
la vista que lo llama).

## Validación de input

Antes, `views.py` hacía `int(request.POST.get('edad'))` sin manejo de
errores — cualquier input no numérico tiraba un 500 sin control. Ahora
`forms.py` centraliza toda la validación:
- `RegistroForm.clean_edad()`: RNF011 del PDF, mayoría de edad.
- `RegistroForm.clean_email()`: evita cuentas duplicadas.
- `RegistroForm.clean()`: contraseñas coincidentes.
- `ValoracionForm.clean_puntuacion()`: rango válido de estrellas (1-5).

Un `IntegerField`/`EmailField` de Django ya rechaza inputs no numéricos o
mal formados antes de llegar a la vista, sin que el desarrollador tenga que
acordarse de envolver cada conversión en un `try/except`.

## Código muerto eliminado

- `views.py`: la función `register_view` duplicada (una definición muerta,
  sobrescrita por la otra) y los 3 imports repetidos de `JsonResponse`/`render`
  desaparecieron en la reescritura completa.
- `urls.py`: los 3 `path()` comentados (`registroinicio`, `comunas_por_region`,
  `sesion`) se reemplazaron por rutas reales, ya no quedan como comentarios.
- `views.py`/`urls.py` de la versión anterior: los bloques grandes de código
  comentado (`comunas_por_region`, `RegistroInicioView`) no se portaron —
  quedan solo en el backup de `codigo/viejo/backup_fase3/` si hace falta
  consultarlos.

## Convención de nombres

Python: todo el código nuevo/refactorizado usa `snake_case` consistente
(antes se mezclaban `UPPERCASE` en `models.py`, `snake_case` parcial en
`views.py`, y `camelCase` en algunas variables JS de los templates). La
única mayúscula que se preserva a propósito es `db_column='NOMBRE_MAYUSCULA'`
en `models.py`, porque documenta el diccionario de datos original de la
tesis — es intencional, no inconsistencia.

## Templates (18 archivos)

Se corrigieron, con un script de reemplazo mecánico (ver `docs/REFACTORING_LOG.md`):
- **CSS/imágenes rotos**: `paginicio.html` apuntaba a `Pag/css/styleinicio.css`
  (carpeta que ya no existe desde la Fase 1); varios templates referenciaban
  `css/X.css` con rutas relativas que solo funcionaban si Django servía los
  archivos exactamente desde `templates/`, lo cual nunca fue cierto. Todos
  pasaron a `{% static 'KeyServApp/css/X.css' %}`/`{% static 'KeyServApp/imagenes/X' %}`,
  apuntando a los assets ya reubicados en `KeyServApp/static/KeyServApp/`.
  Se verificó (script + grep) que cada `{% static %}` resultante apunta a un
  archivo real.
- **Enlaces de navegación rotos**: los `<a href="pagina.html">` (navegación
  por nombre de archivo plano, no por URL de Django) se reemplazaron por
  `{% url 'KeyServApp:nombre' %}` — esto ataca directamente RF007 del PDF
  ("Correcto funcionamiento... sin errores de enlace entre botones"). Se
  verificó que cada `{% url %}` usado existe en `urls.py` (si no, Django
  tira `NoReverseMatch` al renderizar — se comprobó que ninguno lo hace).
- **`registroinicio.html`**: el `<select name="region">` activo no tenía
  `id="id_region"`, que es justo lo que el script jQuery de la misma página
  necesita para enganchar el AJAX de comunas — el selector de región nunca
  disparaba la carga de comunas. Se corrigió, y se sacó el bloque de región
  duplicado (uno activo con bug, uno comentado sin el bug) dejando solo el
  correcto. También se agregó el checkbox de `es_proveedor` (campo nuevo del
  modelo) y se corrigió el `<a href="editarperfil.html"s>` con una `s`
  sobrante en `perfil.html`.
- **No se tocaron** (fuera de alcance, son placeholders de diseño, no bugs
  de la Fase 1): `src="ruta_de_la_imagen.jpg"` en `perfil.html`,
  `src="ruta_del_logo.png"` en "preferencias de la cuenta.html", y
  `href="perfil-proveedor.html"` en `detalleserv.html` (no existe una vista
  de perfil público de proveedor todavía).

## Consistencia general

Con `models.py`/`views.py`/`urls.py` ya alineados entre sí (mismos nombres
de campo, mismas URLs referenciadas desde los templates), el código dejó de
tener las 3 fuentes de verdad desincronizadas que tenía antes (el modelo
decía una cosa, la vista esperaba otra, y el template navegaba a páginas
sin ruta).
