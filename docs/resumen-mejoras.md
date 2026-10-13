# Resumen de mejoras 2026/2027

> Resumen ejecutivo del plan de mejoras de KeyServ: de demo de tesis a producto que cumple la Ley 21.719 de protección
> de datos personales (vigente desde el 1 de diciembre de 2026). Para la tesis, el portafolio y la postulación a Corfo.
> Detalle técnico en [`cumplimiento/README.md`](cumplimiento/README.md) (con la matriz requisito → evidencia).

## Punto de partida (Fase 0, 2026-10-10)

- El vector facial se guardaba **sin cifrar** y era editable desde el panel de administración.
- **No existía verificación de identidad obligatoria** al contratar ni al publicar.
- No había consentimiento biométrico, ni derechos del titular, ni EIPD, ni registro de tratamiento, ni retención automática.
- La demo en Render estaba caída (la base gratuita había expirado).

## Qué se hizo

| Fase | Resultado |
|---|---|
| 0 Reconocimiento | Estado real, deuda y riesgos priorizados (`fase-0-reconocimiento.md`) |
| 1 Auditoría | Inventario de datos y brechas: **no se guardan imágenes ni huellas**, solo un vector (`fase-1-auditoria-datos.md`) |
| 2 Verificación de identidad | Biometría del teléfono como vía principal, rostro en servidor como secundaria y una vía sin biometría; ADR y diagrama |
| 3 Refuerzo | Vector cifrado con claves rotables, verificación **vigente 180 días**, registro de eventos sin datos biométricos, exigencia de identidad al contratar/publicar |
| 4 Cumplimiento visible | Consentimiento versionado y revocable, panel "Mis datos" (descargar, corregir, oponerse, bloquear, eliminar), política de privacidad con plazos reales, retención semanal automatizada, protocolo de brechas, EIPD/registro/encargados |
| 5 Asistente con IA | Asistente flotante (preguntas frecuentes + búsqueda en el catálogo) con **enmascarado de datos personales** antes de salir y flujo de respaldo sin IA |
| 7 Cierre | Matriz de cumplimiento, README renovado, CI ampliado con E2E del asistente y de "Mis datos" |

Pendiente por decisión del dueño: **Fase 6 (rediseño visual)**, revisión legal por abogado, entorno de producción real y
respaldo de la llave de firma de Android.

## Por qué importa

- **Para el usuario:** su rostro nunca se guarda como imagen; puede usar su teléfono, o ni siquiera usar biometría; y puede
  descargar, corregir, bloquear o borrar sus datos desde la app.
- **Para el negocio:** KeyServ llega a la fecha de vigencia de la ley con las medidas técnicas hechas y documentadas.
- **Para una postulación:** hay evidencia verificable (código, tests y documentos) de cada requisito, no solo declaraciones.

## Cifras (2026-10-12)

- **407 tests de backend** (suite local en ~35 s) y **93 de frontend**; E2E con Playwright contra la app real en CI.
- **5 ADR** y más de 15 documentos de cumplimiento, auditoría y legales.
- Migraciones nuevas: `0029` a `0033`; nuevos modelos de consentimiento, verificación alternativa, eventos de verificación
  y solicitudes de titulares.

## Otras mejoras del camino

- Demo reactivado con base de datos externa (Neon) y despliegue desde `master`.
- Suite de tests del backend de ~13 minutos a ~30 segundos (hash de contraseñas liviano solo en tests, con protección que
  impide usarlo fuera de ellos).
- Retención de datos agendada con GitHub Actions en lugar del cron de pago de Render.
- Documentación reordenada: índice en `docs/README.md`, histórico en `docs/archivo/`, un único documento de estado vivo.
