# De la tesis a la nueva documentación

> Guía para reutilizar el informe de tesis (INACAP, "Informe Proyecto Seminario de Grado", abril de 2023, autores
> Chingay Albertis, Peña Abarca y Salinas Sandoval) en la postulación a Corfo y en el informe actualizado. El texto
> completo de la tesis está extraído en `.sistema/cache/plantilla_tesis_extracted.txt` (local, no se versiona) y su
> resumen en [`../archivo/PDF_ANALYSIS_FINDINGS.md`](../archivo/PDF_ANALYSIS_FINDINGS.md). Las referencias "p. N" son el número
> de página que le asignó el extractor (no coincide 1:1 con la numeración impresa).

## Qué se puede aprovechar casi tal cual

| Contenido de la tesis | Dónde está | Úsalo en | Ojo |
|---|---|---|---|
| Problema: estafas digitales e informalidad en la contratación de servicios | p. 19-21 y 32-33 | Formulario, sección "Problema" | Actualizar las cifras (PDI 2022, 27 %): citar la fuente primaria con fecha |
| Misión y visión | p. 22 | Formulario y video | Sigue vigente |
| Análisis FODA | p. 30-31 | Escalabilidad / mercado | Quitar las "debilidades" que ya se resolvieron (la app es multiplataforma, hay pruebas automáticas) |
| Requisitos funcionales (IEEE 830) | p. 124-127 | Anexo técnico | Actualizar: ya no hay huella dactilar |
| Marco teórico y referencias | capítulos II y V | Informe actualizado | Reutilizable casi completo |

## Lo que cambió y hay que reescribir

| En la tesis (2023) | Hoy (2026) | Dónde está lo nuevo |
|---|---|---|
| Verificación obligatoria con **huella dactilar y rostro** en el servidor | Biometría **nativa del teléfono** (principal), rostro con detección de vida y vía sin biometría con **cédula y video revisados por una persona**; la huella se retiró | ADR 0001, 0006; `INFORME_PROYECTO_KEYSERV.md` |
| Base de datos MySQL y AWS | PostgreSQL (Neon); backend en Render y frontend en Netlify | `RECOMMENDED_ARCHITECTURE.md` |
| Sitio web con plantillas Django | App Ionic/Angular (web y Android) sobre una API REST | `PLAN_MIGRACION_IONIC.md` |
| Pagos: "Transbank y PayPal" como proveedores posibles | Webpay Plus, Khipu, Flow y Mercado Pago; comisión por tramos | `ANALISIS_COMISION.md`, `PLAN_FLUJO_DE_DINERO.md` |
| Sin marco de protección de datos | Cumplimiento de la Ley 21.719: consentimiento, derechos, retención, EIPD | `cumplimiento/` |
| Sin cobertura de seguridad operativa | Sesiones revocables, códigos por correo, reembolsos, auditoría | ADR 0003, 0007; `ESTADO_Y_PROXIMOS_PASOS.md` |
| Plan de trabajo académico | Metodología por fases, pruebas y CI | `INFORME_PROYECTO_KEYSERV.md` cap. II §10 |

## Lo que la tesis no tiene y Corfo pide

1. **Competencia chilena.** La tesis compara con TaskRabbit, Thumbtack, Fiverr, Upwork y Handy (p. 21-22), que no operan en
   Chile. Hay que levantar competidores locales y qué hacen con identidad y pago.
2. **Tamaño de mercado** con fuentes (INE, estudios del sector, hogares de la Región Metropolitana).
3. **Evidencia de demanda** (la encuesta de Google Forms) y **disposición a pagar**.
4. **Plan de validación** de 10 meses y **presupuesto** con aporte propio del 25 % (ver `BORRADOR_POSTULACION.md`).
5. **Sostenibilidad** y **ODS** (Anexos 2 y 3 de las bases).
6. **Compromiso de horas** del equipo, perfil comercial y roles.

## Cómo construir los documentos nuevos (propuesta para mañana)

| Documento | Base | Qué agregar |
|---|---|---|
| **Postulación a Corfo** (formulario + video) | [`BORRADOR_POSTULACION.md`](BORRADOR_POSTULACION.md) | Mercado, competencia, equipo, presupuesto |
| **Informe de proyecto actualizado** (continuación de la tesis) | `docs/INFORME_PROYECTO_KEYSERV.docx` (ya existe, con contenido real de la tesis) | Capítulos de pagos y comisión, verificación con video, cumplimiento de la Ley 21.719 |
| **Plan de trabajo y carta Gantt** | Hoja `Gantt` del Excel y Planner | Fechas reales cuando se conozca la apertura |
| **Cumplimiento Ley 21.719** | [`../cumplimiento/PLAN_ADECUACION_LEY_21719.md`](../cumplimiento/PLAN_ADECUACION_LEY_21719.md) | Revisión legal |
| **Presupuesto** | Hoja `Presupuesto` del Excel | Cotizaciones |

Si me dejas el PDF o el Word original de la tesis en `docs/academico/` (carpeta local que no se sube), puedo trabajar
directamente sobre su estructura y formato en vez de sobre el texto extraído.
