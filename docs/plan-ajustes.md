# Ajustes al plan de fases — KeyServ / Ley 21.719 / Corfo

> Registro vivo de cambios al plan maestro ("KeyServ — Plan de mejoras 2026/2027"),
> según lo pedido ahí mismo: "Si algo de aquí no calza con lo que encuentres... propón
> el cambio, justifícalo y ajusta el plan. Registra cada cambio en
> `docs/plan-ajustes.md`." Cada entrada: fecha, fase afectada, qué cambia, por qué.

## 2026-10-10 — Fase 0 (reconocimiento)

El plan maestro queda vigente en su estructura y orden de prioridad (cumplimiento antes
que bot/diseño). Los siguientes son ajustes de **alcance dentro de cada fase**, no de
orden, derivados de `docs/fase-0-reconocimiento.md`:

- **Fase 0**: se agregó como entregable adicional la remediación de entorno local
  (reinstalar el venv con `pip install -r requirements.txt`) — era un bloqueante real
  para ejecutar cualquier fase siguiente (el backend no levantaba), no solo un tema de
  documentación. Hecho. Queda pendiente instalar Node.js en esta máquina — bloquea
  cualquier trabajo sobre `codigo/frontend/ionic/` (necesario antes de la Fase 6, y
  antes de cualquier ajuste de Fases 2-3 que se quiera probar end-to-end desde Ionic).

- **Fase 2**: el plan maestro pedía "reforzar la verificación de identidad existente"
  asumiendo que el gating al contratar/publicar ya existe. **No es así** — se confirmó
  leyendo `contratacion_crear_view` y `publicacion_crear_view` completas: ninguna
  comprueba `verificado_biometricamente`. El encuadre correcto de la Fase 2/3 es
  **construir el enforcement que hoy no existe, reusando la verificación de rostro y
  biometría nativa que ya funciona** — no es un refuerzo incremental de algo que ya
  corre. La comparación de plataformas (PC/notebook, celular, respaldo sin biometría)
  del plan maestro sigue vigente tal cual está planteada.

- **Fase 2/3**: se acota explícitamente que el trabajo de reforzar/cifrar aplica solo
  al flujo de **rostro** (servidor) + **biometría nativa** (dispositivo) — la huella no
  tiene nada en producción que reforzar, porque no está conectada a Django en ningún
  punto (fue retirada en una fase anterior). El único ítem pendiente sobre huella es de
  higiene de repo (los artefactos de ejemplo committeados en
  `codigo/biometria/huella/`), que corresponde a la Fase 1 (auditoría), no a una
  fase de refuerzo de un flujo que no existe en producción.

- **Fase 1**: se agrega como hallazgo explícito a documentar y resolver pronto (fix
  barato, bajo riesgo de regresión): la exposición de `encoding_facial` y el hash de
  `password` en el formulario de edición de `/admin/` (`UsuarioAdmin` no declara
  `fields`/`exclude`/`readonly_fields`). Candidato a resolverse ya en la Fase 1 o al
  inicio de la Fase 3, no esperar hasta el cierre del proyecto. También se agrega la
  condición real de `media/` (público y con URL adivinable) como hallazgo a evaluar —
  decidir en Fase 1 si se mueve a almacenamiento privado (como ya ocurre con
  `Documento`) o se acepta como riesgo residual documentado (fotos de perfil/catálogo
  son contenido pensado para ser público; las de valoraciones no moderadas, no).

- **Fase 6**: se deja constancia de que modernizar a standalone components/signals no
  es obligatorio para el rediseño visual en sí mismo, pero sí es un prerrequisito técnico
  para usar `@defer`, `withViewTransitions()` en el router y el nuevo control flow
  (`@if`/`@for`) que pide el plan maestro — hoy el bootstrap es `bootstrapModule`, no
  `bootstrapApplication`, y las 32 páginas son `standalone: false`. Se abordará ruta por
  ruta con el patrón strangler fig que ya usa el repo, no como una migración masiva
  previa a todo lo demás.
