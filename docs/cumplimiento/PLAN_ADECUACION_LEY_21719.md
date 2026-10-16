# Plan de adecuación a la Ley 21.719 (protección de datos personales)

> Escrito el **2026-10-16**. **No es asesoría jurídica.** Resume lo que la ley exige según fuentes secundarias y lo que KeyServ
> ya hizo, y deja claro qué falta y qué debe ver un abogado. No pude leer el texto consolidado de la ley (la página de LeyChile no
> cargó para mi herramienta): lo que depende de artículos concretos está marcado **[CONFIRMAR EN EL TEXTO]**.
> Este documento complementa la [carpeta de evidencia](README.md) (matriz requisito → evidencia).

## 1. Cuenta regresiva

| Dato | Valor | Confianza |
|---|---|---|
| Publicación en el Diario Oficial | 13 de diciembre de 2024 | Alta (varias fuentes, incluida [Carey](https://www.carey.cl/law-no-21719-amending-law-no-19628-on-the-protection-of-private-life-is-published-in-the-chilean-official-gazette)) |
| Entrada en vigencia | **1 de diciembre de 2026** (24 meses después; primer día del mes) | Media: fuentes secundarias coinciden; **confirmar en [LeyChile](https://www.bcn.cl/leychile/navegar?i=1209272)**. Una guía menciona un proyecto de postergación (Boletín 18.623-07) en primer trámite al 23 de septiembre: **no contar con él** |
| Días que quedan desde hoy | **46** | — |
| Multas | Hasta **20.000 UTM** (según Carey); las fuentes difieren en el detalle por tipo de infracción | Media: **[CONFIRMAR EN EL TEXTO]** |
| Régimen transitorio para empresas pequeñas (amonestación en el primer año) | Lo mencionan algunas guías | **Baja**: confirmar con el abogado antes de apoyarse en esto |
| Autoridad | Agencia de Protección de Datos Personales (creada por la ley) | Alta |

## 2. Lo que la ley pide, en simple (resumen no vinculante)

- **Principios:** licitud, finalidad, proporcionalidad, calidad, responsabilidad, seguridad, transparencia y confidencialidad.
- **Bases para tratar datos:** consentimiento (libre, informado y específico) u otra base legal (contrato, obligación legal, interés legítimo).
- **Datos sensibles** (entre ellos los **biométricos**): régimen reforzado; consentimiento explícito y medidas adicionales.
- **Derechos de las personas:** acceso, rectificación, supresión, oposición, **portabilidad** y **bloqueo**, con plazos de respuesta.
- **Deberes del responsable:** informar de forma clara, registrar sus tratamientos, hacer evaluaciones de impacto en los casos de riesgo,
  adoptar medidas de seguridad, **avisar las vulneraciones de seguridad** y regular las relaciones con encargados y las transferencias al extranjero.
- **Modelo de prevención** y delegado de protección de datos: la ley contempla mecanismos voluntarios de cumplimiento **[CONFIRMAR EN EL TEXTO si alguno es obligatorio para KeyServ]**.

## 3. Estado de KeyServ por área

Semáforo: 🟢 implementado y con tests · 🟡 borrador o falta revisión legal · 🔴 falta.

| Área | Estado | Qué hay | Qué falta |
|---|---|---|---|
| Transparencia (política de privacidad) | 🟡 | Página `/privacidad` en la app y en Django, con datos, terceros y plazos; **actualizada hoy** con el video de verificación, Flow y Mercado Pago | Revisión del abogado; fecha de vigencia y versión; enlace en el registro |
| Consentimiento biométrico (rostro) | 🟢 | Versionado, revocable, borra el vector al revocar | Revisión legal del texto |
| **Consentimiento del video de verificación (nuevo)** | 🟡 | Casilla expresa, **fecha y versión del texto aceptado** (migración 0043); el video se borra al resolver (o a los 30 días) | Revisión legal del texto, del plazo y de la base |
| Derechos del titular | 🟢 | Descarga, rectificación, oposición, bloqueo, supresión con 15 días de espera; plazo de 30 días con alertas | Procedimiento escrito para quien no use la app; responder solicitudes con un suplente |
| Seguridad | 🟢 | Cifrado del vector, almacenamiento privado, sesiones revocables, códigos por correo, auditoría, validación de archivos, admin acotado | **Claves de producción** propias (hoy valores por defecto en el demo); avisos `keyserv.W001-W003` |
| Retención | 🟢 | Purga semanal automática (chats 90 d, accesos 365 d, eventos 365 d, sesiones 30 d, videos 30 d, cuentas eliminadas a los 15 d) | **Evidencia para investigaciones** (ADR 0007): decisión con abogado |
| Evaluación de impacto (EIPD) | 🟡 | Borrador del reconocimiento facial | **Actualizar con el video de verificación** y la vía con revisión humana |
| Registro de actividades de tratamiento | 🟡 | Borrador | Sumar: video, avisos por correo, reembolsos, Flow y Mercado Pago |
| Encargados y contratos (DPA) | 🔴 | Lista de encargados (Render, Neon, GitHub, Netlify, NVIDIA, Transbank, Khipu, Flow, Mercado Pago, Google) | **Contratos con cada uno**; revisar términos de los planes gratuitos |
| **Transferencias internacionales** | 🔴 | Identificadas: EE. UU. (Render, GitHub, NVIDIA, Mercado Pago/Google), Brasil (Neon) | **Evaluar el mecanismo legal** de cada una; el texto enviado a NVIDIA se enmascara pero no es infalible |
| Brechas de seguridad | 🟡 | Protocolo en borrador | Responsables y suplente, plantilla de aviso a la Agencia y a las personas, registro de incidentes, **simulacro** |
| Menores de edad | 🟢 | El registro exige edad mínima (validación en `RegistroForm`) | Confirmar que cubre la regla de la ley **[CONFIRMAR EN EL TEXTO]** |
| Agencia (registro, fiscalización) | 🔴 | — | Averiguar si hay inscripción u obligaciones de reporte para KeyServ |
| Delegado / modelo de prevención | 🔴 | — | Decidir con el abogado si corresponde; definir un responsable interno |
| Términos y Condiciones | 🔴 | No existen | Redactar con abogado (incluye datos, pagos, reembolsos, disputas) |

## 4. Tratamientos nuevos desde el 15 de octubre (revisar uno a uno)

| Tratamiento | Datos | Base propuesta | Riesgo | Mitigación hecha |
|---|---|---|---|---|
| Video de verificación con cédula | Rostro y cédula (sensible) | Consentimiento expreso | **Alto** | Almacenamiento privado, solo staff, borrado al resolver o a los 30 días, código anti-reutilización |
| Correo del pagador a Flow y Mercado Pago | Correo electrónico | Ejecución del contrato (pago) | Medio | Informado en la política; solo se envía al elegir ese medio |
| Código de seguridad por correo | Correo | Seguridad / interés legítimo | Bajo | Solo hash, 10 minutos, un uso |
| Avisos por correo (solicitud, pago, cambio de clave) | Correo, nombre del servicio | Ejecución del contrato / seguridad | Bajo | Sin datos sensibles en el cuerpo |
| Reembolsos | Montos, motivo | Ejecución del contrato y obligación legal | Medio | Registro con quién resolvió |
| Comisión y pagos | Montos | Obligación tributaria y contrato | Medio | Se conservan las filas por retención tributaria |

## 5. Plan hasta el 1 de diciembre (6 semanas)

| Semana | Qué | Quién |
|---|---|---|
| 1 (hasta 23-oct) | Contratar o consultar a un abogado de datos; enviarle este documento, el EIPD, los ADR 0006 y 0007 y las preguntas de abajo | Dueño |
| 1 | Actualizar EIPD y registro de tratamientos con el video de verificación (la versión del consentimiento ya se guarda) | Claude |
| 2 | Fijar claves de producción en Render; revisar términos de Render, Neon, Netlify y NVIDIA | Dueño |
| 2 a 3 | Borrador de Términos y Condiciones con el abogado | Dueño + abogado |
| 3 | Procedimiento escrito de derechos (canal, plazos, suplente) y plantilla de aviso de brechas | Claude + dueño |
| 4 | Contratos o DPA con los encargados principales; decisión sobre transferencias internacionales | Dueño + abogado |
| 5 | **Simulacro de brecha** y de solicitud de derechos; ajustes | Dueño + Claude |
| 6 (hasta 30-nov) | Política de privacidad final publicada con fecha y versión; revisión final contra la lista de abajo | Dueño + abogado |

## 6. Preguntas para el abogado (por prioridad)

1. ¿El video de verificación con cédula es dato sensible/biométrico en este uso? ¿Basta el consentimiento actual y el plazo de 30 días?
2. ¿Qué deben contener los contratos con los encargados y cómo se legitiman las transferencias a EE. UU. y Brasil?
3. ¿Cuándo hay que avisar una vulneración, a quién y con qué contenido? ¿Aplica un plazo concreto?
4. ¿Qué se puede conservar como evidencia para la policía y por cuánto tiempo (ADR 0007)? ¿Qué pasa con los datos de cuentas eliminadas (anonimización)?
5. ¿Hay obligaciones para una empresa pequeña o de menor tamaño (régimen transitorio, modelo de prevención, delegado, inscripción)?
6. ¿Qué debe decir la política de privacidad y el aviso al registrarse? ¿Cómo se acredita el consentimiento (versión, fecha)?
7. Custodia de fondos y ley fintech (ver [`../PLAN_FLUJO_DE_DINERO.md`](../PLAN_FLUJO_DE_DINERO.md)).
8. Términos y Condiciones: datos, pagos, reembolsos y disputas.

## 7. Lista de verificación antes del 1 de diciembre

- [ ] Política de privacidad final, con fecha y versión, revisada por un abogado.
- [x] Texto del consentimiento del video **versionado** (se guarda con cada aceptación).
- [ ] Texto del consentimiento del video revisado por el abogado.
- [ ] EIPD actualizada (reconocimiento facial + video) y registro de tratamientos al día.
- [ ] Contratos con encargados y decisión sobre transferencias internacionales.
- [ ] Protocolo de brechas con responsables, plantilla y simulacro hecho.
- [ ] Procedimiento de derechos con suplente.
- [ ] Claves de producción fijadas (sin avisos `keyserv.W00x`).
- [ ] Términos y Condiciones publicados.
- [ ] Decisión sobre evidencia y retención (ADR 0007).
- [ ] Decisión sobre delegado, modelo de prevención e inscripción ante la Agencia.
- [ ] Confirmada la fecha de vigencia y los plazos en el texto oficial de LeyChile.
