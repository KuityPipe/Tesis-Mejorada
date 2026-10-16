# Borrador de postulación (Semilla Inicia)

> Borrador para completar y pulir, con el contenido que pide el formulario según las bases (§8). Todo lo que dice
> **[COMPLETAR]** es un dato que solo tú tienes; **[VERIFICAR]** es una cifra de la tesis de 2023 que hay que
> reconfirmar con una fuente actual. No inventes números: Corfo cruza lo que declaras con el video y con lo que verifica
> después. Los textos están en español neutro y se pueden copiar al formulario en línea.

## a) Solución (producto o servicio)

**Problema.** En Chile, buena parte de los servicios del hogar y personales se contratan de manera informal
(boca a boca, grupos de redes sociales, marketplaces generalistas), sin forma de saber si quien llega es quien dice ser
ni si el servicio se pagará de forma segura. Esto produce estafas, contrataciones que nunca se realizan y cobros
excesivos, y deja fuera del mercado a buenos proveedores que no tienen cómo demostrar confianza.
*Evidencia de la tesis (2023) a actualizar:* denuncias por estafas y defraudaciones contra particulares (7.256 en los
primeros cinco meses de 2022, de las cuales 4.207 por canales digitales, según la PDI) **[VERIFICAR con el balance más
reciente]**; peso de la informalidad **[VERIFICAR: la tesis atribuye el 27 % a la CEP; usar la tasa de ocupación informal del
INE con su fecha]**.

**Solución.** KeyServ es una plataforma (web y app móvil) que conecta a clientes con proveedores de servicios y reduce
el fraude con **identidad verificada**: el proveedor demuestra quién es con la biometría de su propio teléfono, con
reconocimiento facial o, si prefiere no usar biometría, con su cédula y un video corto revisados por una persona. El pago
se hace dentro de la plataforma, que retiene la comisión y deja trazabilidad para reportar abusos.

**Valor agregado frente a las alternativas.**
- Identidad verificada y vigente (se renueva cada 180 días), no solo "perfil con reseñas".
- Pago seguro integrado (Webpay, y Flow y Mercado Pago como alternativas) y comisión transparente que ve el cliente
  antes de pagar.
- Diseñada para cumplir la nueva ley de protección de datos (Ley 21.719) desde el origen: el dato biométrico
  sensible se minimiza (solo un vector cifrado, nunca la imagen) y hay vías alternativas sin biometría.
- Moderación humana y registro de incidentes.

**Estado de desarrollo (verificable en el repositorio y en el demo).**
- Plataforma funcional desplegada en demo (keyserv.netlify.app): catálogo, contratación completa (solicitud, confirmación,
  pago, ejecución, cierre y valoración), chat por trabajo, panel de moderación y app Android firmada.
- Verificación de identidad con tres vías (biometría nativa, rostro con detección de vida, cédula + video con revisión humana).
- Más de 500 pruebas automáticas en el backend y más de 130 en el frontend; integración continua.
- Cumplimiento de datos: consentimiento, derechos del titular, retención automática, evaluación de impacto en borrador.
- **Lo que falta para operar de verdad:** pasarela de pago en producción, correo transaccional, revisión legal, términos y
  condiciones, constitución de la sociedad y proveedores reales.

**ODS (Anexo 2) [COMPLETAR tras leer el anexo].** Candidatos naturales: ODS 8 (trabajo decente y crecimiento económico:
formalizar el trabajo independiente), ODS 16 (instituciones sólidas: reducir fraude y suplantación) y ODS 9.

**Operación sostenible (Anexo 3) [COMPLETAR].** Ideas con base en el proyecto: acceso a proveedores sin historial
formal, minimización de datos, hosting con plan eficiente, política de moderación y reportes, accesibilidad de la app.

## b) Escalabilidad

**Modelo de negocios.**
- *Clientes:* personas que contratan servicios del hogar y personales; empresas pequeñas con mantenciones.
- *Proveedores:* independientes y microempresas de oficios, que ganan visibilidad y pagos seguros.
- *Ingresos:* comisión por servicio pagado, que paga el cliente encima del precio, en tramos (6 % hasta $50.000, 5 % hasta
  $200.000, 4,5 % hasta $500.000, 4 % sobre eso, mínimo $1.000). Ver [`../ANALISIS_COMISION.md`](../ANALISIS_COMISION.md): con 3 % o
  menos en montos altos y pago con tarjeta la plataforma pierde plata. *Ideas futuras:* publicaciones destacadas por categoría y zona.
- *Canal:* app y web, referidos por proveedores, alianzas con comunidades de oficios **[COMPLETAR]**.
- *Recursos y alianzas clave:* pasarelas de pago, entidad patrocinadora, red de mentores, abogado y contador.

**Mercado.**
- *Tamaño:* **[COMPLETAR con fuentes]** (hogares en la Región Metropolitana, gasto en servicios del hogar, empleo
  independiente informal del INE).
- *Competencia:* la tesis compara con TaskRabbit, Thumbtack, Fiverr, Upwork y Handy, que **no operan en Chile**. Falta lo que
  Corfo preguntará: competidores **chilenos** (marketplaces generalistas con servicios, plataformas de oficios, grupos de
  redes sociales) y qué hace cada uno con identidad y pagos **[COMPLETAR: estudio de competencia local]**.
- *Barreras de entrada:* confianza y masa crítica de proveedores; el costo de la verificación humana.
- *Condiciones de inicio:* Región Metropolitana (demo con proveedores en comunas como Maipú, Providencia y Santiago).
  Escala a otras regiones sin cambiar el producto: la verificación y el pago son iguales en todo el país.

## c) Plan de validación (10 meses)

**Resultados esperados (bases §3):** validación técnica, primeras ventas, mentoría iniciada en los primeros 4 meses y una
estrategia de operación sostenible.

| Mes | Actividad | Resultado / hito |
|---|---|---|
| 1 a 2 | Constituir la sociedad e iniciar actividades en el SII; contrato con la entidad patrocinadora | Sociedad y contrato firmados |
| 1 a 2 | Definir el modelo de negocios con la mentoría | Modelo validado con el mentor |
| 1 a 4 | Producción técnica: pasarela real, correo transaccional, T&C, cumplimiento de la Ley 21.719 | Plataforma lista para cobrar |
| 2 a 10 | Mentoría (inicio antes del mes 4) | Informe de mentoría |
| 3 a 6 | Estrategia de operación sostenible (Anexo 3) | Diagnóstico, indicadores y plan de acción |
| 3 a 9 | Piloto con proveedores y clientes reales; prospección y validación comercial | N proveedores verificados y N servicios completados **[COMPLETAR metas]** |
| 5 a 8 | **Primera venta** (servicio pagado en la plataforma) | Ingresos por comisión acreditados |
| 8 a 10 | Medición, ajustes y plan de escalamiento a otras regiones | Informe de validación |
| 10 | Informe final y rendición | Cierre del proyecto |

La misma carta Gantt está en la hoja `Gantt` del Excel de seguimiento.

## d) Capacidades (equipo)

Equipo: los tres autores del proyecto de tesis (hasta 3 cofundadores permitidos). **[COMPLETAR con datos reales]**

| Persona | Rol propuesto | Experiencia relevante | Dedicación semanal (máx. 40 a 44 h) |
|---|---|---|---|
| Felipe Salinas Sandoval | Producto, backend y cumplimiento | Desarrolló la plataforma completa (backend, app, pagos, verificación) | [COMPLETAR] |
| Omar Chingay Albertis | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] |
| Luis Peña Abarca | [COMPLETAR] | [COMPLETAR] | [COMPLETAR] |

Corfo evalúa la **complementariedad** (20 %) y el **compromiso de horas** (10 %): conviene mostrar a alguien con perfil
comercial o de operaciones, no solo técnico, y asegurar que las horas comprometidas sean reales (se verifican).

## e) Video (máximo 40 segundos)

Debe describir el producto y su innovación frente a las soluciones actuales. Si pasa de 40 segundos se evalúa solo hasta el
segundo 40. Hay que subirlo a una plataforma que muestre la fecha de carga (no se puede cambiar después) y entregar la
clave si es privado. Si no abre, la postulación no se evalúa.

**Guion sugerido (≈ 40 s):**

| Seg. | Imagen | Texto |
|---|---|---|
| 0-6 | Persona dudando antes de contratar a un gasfíter por un grupo de redes | "Contratar un servicio en Chile hoy es una apuesta: no sabes si quien llega es quien dice ser." |
| 6-16 | Pantalla de KeyServ: perfil con insignia de identidad verificada | "KeyServ conecta clientes con proveedores cuya identidad está verificada, con la biometría de su propio teléfono o con su cédula revisada por una persona." |
| 16-26 | Flujo: contratar, ver el total con comisión, pagar | "El pago es seguro y queda registrado dentro de la plataforma: el cliente ve cuánto paga antes de confirmar." |
| 26-34 | Comparación breve con grupos de redes y marketplaces | "A diferencia de los grupos y los marketplaces, aquí la confianza no es una reseña: es una identidad comprobada y vigente." |
| 34-40 | Logo y llamado | "KeyServ: servicios en los que puedes confiar." |

## Lista para revisar antes de enviar
- [ ] Todos los datos [COMPLETAR] y [VERIFICAR] resueltos con fuentes citables.
- [ ] Nada de lo escrito promete lo que el sistema no hace (por ejemplo, "identidad verificada" = lo que prueba cada vía; ver ADR 0006).
- [ ] El video coincide con lo que dice el formulario (si hay inconsistencias, Corfo puede dar por desistida la postulación).
- [ ] Presupuesto consistente con las actividades y con el 25 % de aporte propio.
- [ ] Entidad patrocinadora y mentoría identificadas.
- [ ] Nadie del equipo está en el Registro de Deudores de Pensiones de Alimentos ni tiene otro proyecto Corfo vigente.
