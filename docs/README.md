# Índice de documentación

El repo es público (portafolio). Esta tabla dice qué hay, para qué sirve y si es presentable.
**Estado vivo del proyecto: `ESTADO_Y_PROXIMOS_PASOS.md`** (único historial/punto de retoma; se sobrescribe en cada cierre de sesión, no se acumulan versiones).

## Vigentes

| Documento | Para qué | Mostrable |
|---|---|---|
| `ESTADO_Y_PROXIMOS_PASOS.md` | Dónde quedamos y qué sigue | Sí (interno por naturaleza, pero sin secretos) |
| `PLAN_MAESTRO_2026-27.md` | Las 7 fases del plan y su estado (resumen del original) | Sí |
| `plan-ajustes.md` | Registro fechado de cambios de alcance | Sí |
| `fase-0-reconocimiento.md` | Auditoría inicial y riesgos | Con reserva: lista riesgos de seguridad (ya mitigados la mayoría) |
| `fase-1-auditoria-datos.md` | Inventario de datos, hallazgos y brechas frente a la ley | Sí |
| `adr/` | Decisiones de arquitectura (verificación, cifrado, vigencia/auditoría, derechos del titular, asistente con IA) | Sí |
| `legal/protocolo-de-brechas.md` | Protocolo ante brechas de seguridad, **borrador** | Con reserva: marcar como borrador |
| `cumplimiento/rotacion-de-llaves.md` | Cómo rotar la clave de cifrado biométrico | Sí |
| `legal/eipd-reconocimiento-facial.md` | EIPD, **borrador sin revisión legal** | Con reserva: marcar como borrador |
| `cumplimiento/*.md` | Registro de tratamiento y encargados, **borradores** | Con reserva: ídem |
| `BACKLOG.md` | Pendientes funcionales de producto | Sí |
| `PLAN_MIGRACION_IONIC.md` | Migración Django → Ionic/API | Sí |
| `PLAN_PORTAFOLIO.md` | Despliegue demo (Render/Netlify) y portafolio | Sí |
| `API_DOCUMENTATION.md`, `DATABASE_DOCUMENTATION.md`, `RECOMMENDED_ARCHITECTURE.md` | Referencia técnica (base; pueden estar algo desactualizadas) | Sí |
| `INFORME_PROYECTO_KEYSERV.md` / `.docx` | Informe de proyecto, continuación de la tesis | Sí |

## Archivo (`archivo/`)

Histórico, superado o de trabajo; se conserva pero no se mantiene y no se presenta como estado actual:
bitácora de commits, logs de Fase 4/refactor, análisis de código y PDF de la tesis, roadmap viejo, auditoría 8000 vs 8100, instrucciones de setup de julio, y `CLAUDE_HISTORIAL.md` (el CLAUDE.md largo anterior al reordenamiento del 2026-10-12).

## Fuera del repo (solo en local, gitignorado)

`academico/` (texto de la tesis, plantilla PDF) y el PDF suelto de `codigo/biometria/huella/`. Siguen en tu disco.
