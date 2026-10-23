# Changelog

Historia de lo que cambia en KeyServ, en lenguaje simple y por fecha (lo más reciente arriba). El detalle técnico está en
`git log` y en la hoja `Cambios` del libro de seguimiento. Cómo mantenerlo: [README](README.md).

## 2026-10-23

Encuadre de la postulación a Corfo: inclusión laboral y formalización (oficios → ingreso formal y trazable). Detalle técnico:
[ADR 0008](../adr/0008-medicion-de-impacto.md).

### Agregado
- **Medición de impacto (bloque 1).** Preguntas **voluntarias** de situación laboral previa y género al registrarse (con la finalidad escrita en la misma pantalla; no bloquean el registro) y editables en Preferencias. Cada publicación tiene un **tipo de servicio** (reparación, mantención, instalación nueva, otro) y, al calificar una reparación, el cliente puede decir si evitó comprar uno nuevo.
- **`manage.py reporte_impacto`:** entrega solo cifras agregadas (proveedores verificados por vía, primer pago, ingreso mensual mediano, % de reparación/mantención, % del ingreso en la misma comuna, situación laboral previa, % de mujeres) y **oculta cualquier grupo de menos de 5 personas**. Excluye las cuentas de demostración.
- La política de privacidad y el registro de actividades de tratamiento mencionan la finalidad (borrador: lo debe revisar un abogado).

## 2026-10-16 (tarde)

### Agregado
- **Guía de postulación a Corfo** (`docs/corfo/`) hecha con las bases técnicas oficiales de Semilla Inicia: requisitos, cómo calza KeyServ, qué falta (Entidad Patrocinadora y mentoría son obligatorias), cómo se evalúa, borrador de la postulación con guion del video de 40 segundos y puente de la tesis a los documentos nuevos.
- **Plan de adecuación a la Ley 21.719** (`docs/cumplimiento/`): cuenta regresiva al 1 de diciembre de 2026, estado por área, tratamientos nuevos, plan de 6 semanas y preguntas para el abogado.
- Hojas `Corfo` y `Gantt` en el libro de seguimiento, y 13 tareas nuevas.
- El consentimiento del video de verificación ahora guarda **la versión del texto** que la persona aceptó.

## 2026-10-16

### Agregado
- **Comisión por tramos que paga el cliente encima del precio** (6 % hasta $50.000, 5 % hasta $200.000, 4,5 % hasta $500.000, 4 % sobre eso; mínimo $1.000). Se muestra el desglose antes de pagar y queda congelado en cada pago. Los tramos se cambian por configuración. Análisis de costos en [`../ANALISIS_COMISION.md`](../ANALISIS_COMISION.md): con 3 % o menos en montos altos y pago con tarjeta, la plataforma pierde plata.
- **Verificación sin biometría con video y cédula:** la persona sube su cédula y un video corto con su cara y su cédula, diciendo su nombre y un número que se le muestra. Un moderador lo compara en `/admin/` y aprueba o rechaza; **el video se borra al resolver** (o a los 30 días, o al eliminar la cuenta). Solo lo ve el staff y exige consentimiento explícito.
- **Flow y Mercado Pago** como medios de pago adicionales (con sandbox). Solo aparecen si hay claves configuradas. *Probados con simulaciones; falta probarlos en el sandbox real.*
- **Registro de reembolsos:** se abren solos si un pago llega tarde sobre un trabajo cancelado, o cuando el cliente lo pide; el superusuario los resuelve en `/admin/` (hay un indicador en el panel). La devolución del dinero sigue siendo manual.
- **Cerrar sesión en todos los dispositivos**, confirmado con un código enviado al correo.
- **Más avisos por correo:** solicitud nueva, confirmada, rechazada o cancelada; pago aprobado; cambio de contraseña; pedido de reembolso.
- **Avisos de configuración insegura** al desplegar (`SECRET_KEY`, `JWT_SECRET`, llave biométrica por defecto).
- **Tablero de seguimiento** (este directorio) con Excel, Planner y changelog.

### Cambiado
- Un proveedor con la verificación vencida ya no puede confirmar trabajos nuevos (con la exigencia de identidad activa).
- La política de privacidad y el registro de encargados incluyen el video de verificación, Flow y Mercado Pago.

### Seguridad
- Cambiar o recuperar la contraseña, y pedir eliminar la cuenta, **invalidan al instante** todas las sesiones y los tokens ya emitidos.

## 2026-10-15

### Corregido (revisión externa)
- **Webpay:** recargar la página de retorno ya no marca como rechazado un pago cobrado; el pago aprobado bloquea la fila para evitar duplicados.
- **Sesiones:** cambiar la clave cierra las otras sesiones; la persona que la cambió no queda fuera.
- **Rechazar y cancelar** una contratación (antes no había salida); una ya pagada se resuelve por reembolso.
- **Eliminar la cuenta:** queda bloqueada 15 días antes de anonimizarse, y cancela sus solicitudes sin confirmar.
- **Solicitudes sin respuesta expiran** (7 días) y avisan por correo.
- **Biometría nativa:** ya no se puede verificar con una llamada directa a la API; solo reconfirma a quien ya tiene documento aprobado.
- El asistente de IA oculta también direcciones y nombres declarados, y los textos ya no dicen que no se envían datos personales.

### Documentación
- ADR 0006 (qué prueba una identidad verificada), ADR 0007 (retención, evidencia y avisos) y plan del flujo de dinero.

## Antes del 2026-10-15
Rediseño visual de las pantallas, asistente con IA, cumplimiento de la Ley 21.719 (consentimiento, derechos del titular, retención) y despliegue del demo en Render y Netlify. Ver `docs/ESTADO_Y_PROXIMOS_PASOS.md` y los ADR 0001 a 0005.
