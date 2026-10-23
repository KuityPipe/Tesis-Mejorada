# ADR 0008 — Medición de impacto (inclusión laboral y formalización)

- **Estado:** implementado (bloque 1, 2026-10-23). Decisión de estrategia del dueño: la postulación a Corfo se plantea como
  inclusión laboral (oficios → ingreso formal y trazable); la identidad verificada es el medio y el trabajo formal el fin.
  Economía circular = reparar y mantener en vez de reemplazar; el ingreso que queda en la comuna se reporta aparte como
  "economía local".
- **Contexto:** la postulación va a declarar cifras de impacto. Corfo cruza lo declarado con lo verificable, así que cada
  indicador debe salir del código, no de una estimación, y sin exponer a personas concretas (Ley 21.719).

## Decisiones

1. **Datos nuevos, todos voluntarios.**
   - `Usuario.situacion_laboral_previa` (sin trabajo / informal / formal / estudiante / prefiero no decir) y `Usuario.genero`:
     `CharField` con `blank=True`; vacío = no respondió. Se preguntan en el registro, con la finalidad escrita en la misma
     pantalla, sin bloquear el registro, y se editan desde Preferencias (`PUT /api/auth/datos-impacto/`, endpoint aparte de
     `preferencias` para que un cliente que solo manda el toggle de sonido no las borre).
   - `Publicaciones.tipo_servicio` (reparación / mantención / instalación nueva / otro, por defecto "otro").
   - `Valoracion.evito_reemplazo` (sí / no / no aplica), pregunta opcional que Ionic solo muestra en reparaciones y mantenciones.
   - Migración `0044` (a mano, como las anteriores). Se incluyen en la exportación `mis-datos` y se vacían al anonimizar.
   - No se exponen en ningún serializer público: solo el propio usuario ve sus respuestas (`/auth/me/`).
2. **Reporte solo agregado** (`impacto.py`, `manage.py reporte_impacto [--json] [--incluir-demo]`):
   - Grupos de menos de `MINIMO_GRUPO` = 5 personas se suprimen (`None`); si en una distribución queda un único grupo
     suprimido, también se suprime el menor de los restantes (supresión complementaria) para que no se despeje restando.
   - Montos y porcentajes basados en pocas personas (menos de 5 proveedores con pago) también se suprimen.
   - El ingreso se mide sobre `Pago.monto_servicio` (sin la comisión); la mediana es entre pares proveedor-mes.
   - "Economía local": parte del ingreso cuyo cliente vive en la misma comuna del proveedor.
   - Las cuentas `@demo.keyserv` se excluyen por defecto: no son personas reales y las cifras para Corfo no deben incluirlas.
   - La vía de verificación se deduce de la verificación vigente (`alternativa`) o del último evento exitoso (`nativa`/`rostro`).
3. **Lo que NO se hace:** no se infiere género ni situación laboral de otros datos; no se cruzan con el reporte individual de
   ninguna persona; no condicionan acceso, ranking ni visibilidad.

## Pendiente (a validar con un abogado, ver `Pendientes_dueño`)

Base de licitud (consentimiento voluntario y revocable es lo implementado), si la situación laboral previa o el género cuentan
como dato sensible bajo la Ley 21.719 y qué tratamiento adicional exigen, plazo de conservación y redacción final de la finalidad
en la política de privacidad (hoy es un borrador técnico).
