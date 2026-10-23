# Resumen para planificar la postulación (traspaso a Claude desktop)

> Preparado el 2026-10-23 tras revisar `README.md`, `BORRADOR_POSTULACION.md` y `DE_LA_TESIS_A_LA_POSTULACION.md`. Es un
> documento de trabajo: resume el diagnóstico y lo que falta decidir, no reemplaza al borrador.

## Contexto

**Proyecto.** KeyServ es un marketplace chileno de servicios y oficios con verificación de identidad. Empezó como tesis
(entregada) y hoy es producto y portafolio. Backend Django/DRF en Render con Postgres en Neon, app Ionic/Angular en Netlify
y Android, demo en keyserv.netlify.app. Tiene pagos (Webpay, Khipu, Flow, Mercado Pago), comisión por tramos de
6/5/4,5/4 % que paga el cliente encima del precio y un borrador de cumplimiento de la Ley 21.719.

**Objetivo.** Ganar Semilla Inicia: hasta $15M (75 % del costo, con aporte propio del 25 %) y hasta 10 meses de ejecución.
Postula una persona natural, sin sociedad constituida y sin ventas previas. Hoy no hay convocatoria abierta; la siguiente
se espera en el primer semestre de 2027 (inferencia, no dato).

**Necesidad que cubrimos.** Desempleo e informalidad: convertir oficios en ingreso formal y trazable, con una idea de
economía circular.

## Diagnóstico

1. **El relato está mal enfocado.** El borrador plantea el problema como fraude y confianza. Debería centrarse en inclusión
   laboral: la identidad verificada es el medio y el trabajo formal es el fin. Encuadre sugerido: *"Muchas personas con un
   oficio no tienen cómo demostrar confianza, y por eso trabajan sin contrato, sin boleta o no logran trabajar. KeyServ les
   da identidad verificada, pago seguro y boleta."* ODS candidatos: 8, 10, 12 y 16.
2. **"Economía circular" hay que definirla.** En sentido estricto es reparar y reutilizar; en sentido económico, que el
   ingreso quede en la comunidad. No se debe afirmar más de lo que se mide. **Decisión pendiente del dueño: cuál de las dos.**
3. **Pesos de evaluación:** Innovación 40 % (relevancia del problema 15, propuesta de valor 25), Escalabilidad 30 %,
   Equipo 30 %.

## Indicadores propuestos

| Eje | Indicador | Fuente |
|---|---|---|
| Empleo | Primer pago de cada proveedor | `Contratacion`, `Pago` (ya existe) |
| Empleo | Ingreso mensual por proveedor | `monto_servicio` (ya existe) |
| Empleo | Situación laboral previa | Pregunta voluntaria al registrarse (nueva) |
| Formalidad | Servicios con boleta o factura | Flujo SII (nuevo, hoy solo es idea) |
| Formalidad | Paso de "sin documento" a identidad verificada | `EventoVerificacion` (ya existe) |
| Circularidad | Reparación o mantención frente a instalación nueva | Etiqueta de categoría (nueva) |
| Circularidad | Reparaciones que evitan un reemplazo | Pregunta opcional al valorar, autodeclarada (nueva) |
| Territorio | Parte del ingreso que queda en la misma comuna | Comunas de proveedor y cliente (ya existen) |

La situación laboral previa es un dato personal bajo la Ley 21.719: voluntaria, con finalidad declarada y reportada solo
de forma agregada.

## Cambios al producto (por prioridad)

1. Medición de impacto: pregunta voluntaria, etiqueta de reparación/reuso y un comando de reporte agregado.
2. Boleta o factura al SII: es el diferenciador declarado de formalización y hoy no existe.
3. Destacar la vía de cédula y video, que permite empezar a un proveedor sin historial.

## Lo que más decide ganar (pendiente, mayormente fuera del código)

- **Entidad Patrocinadora y mentoría:** obligatorias, hoy faltan.
- **Competencia chilena y tamaño de mercado:** la tesis solo compara con plataformas extranjeras.
- **Encuesta de Google Forms:** debe medir desempleo, informalidad y disposición a pagar.
- **Equipo:** falta un perfil comercial y las horas comprometidas por escrito.
- **Completar el borrador:** metas del piloto, presupuesto con cotizaciones, anexos de ODS y sostenibilidad, video de 40 s.
- **No cobrar ni constituir sociedad** antes del resultado.
- **Cifras vigentes del INE:** las de la tesis son de 2022-2023 (por ejemplo el 27 % atribuido a la CEP) y hay que
  verificarlas con fecha. No citar nada sin fuente.

## Otros cambios de la sesión del 2026-10-23

- `docker-compose.yml` en la raíz, solo con Postgres 16 para desarrollo. Más adelante se le puede sumar un `Dockerfile`
  del backend para producción.
- Limpieza del `CLAUDE.md` (se quitó el log de sesión viejo y se acortó "Project").

## Tareas sugeridas para la planificación

1. Reescribir el relato de la postulación con el encuadre de inclusión laboral.
2. Decidir la definición de economía circular y sus indicadores, con metas realistas para el piloto de 10 meses.
3. Ordenar las tareas pendientes con fechas tentativas.
4. Redactar los anexos de ODS y sostenibilidad.

Cuando eso esté definido, se vuelve a Claude Code para implementar las mediciones y los cambios de producto.
