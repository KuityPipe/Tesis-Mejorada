# KeyServ — Plan de mejoras 2026/2027 (Ley 21.719 + postulación Corfo)

> Resumen del plan maestro **original** (7 fases, pegado por el usuario el 2026-10-12; texto completo solo en local,
> `docs/privado/PLAN_MAESTRO_ORIGINAL.md`, gitignorado). Reemplaza la reconstrucción anterior, que había mezclado
> las fases (ver `docs/plan-ajustes.md`, entrada 2026-10-12). Estado actual y retoma: `docs/ESTADO_Y_PROXIMOS_PASOS.md`.

## Principios

- Objetivo principal: cumplir la **Ley 21.719** (vigente desde **2026-12-01**; la biometría es dato sensible) y poder
  postular a **Corfo**. Si hay conflicto entre cumplimiento y una mejora visual/funcional, gana el cumplimiento.
- Prioridad: Fases 1–4 (cumplimiento) antes que 5–6 (bot y diseño). Debe quedar **evidencia documental**.
- Commits pequeños **en español y directo a `master`** (el plan original pedía inglés y una rama por fase; el dueño decidió
  no hacerlo, ver `plan-ajustes.md`), tests en verde antes de cerrar, ADRs en `docs/adr/`, strangler fig. Nunca borrar biometría ni migrar datos reales sin respaldo y confirmación explícita.
- Ningún dato personal o biométrico a servicios externos de IA.

## Fases y estado (2026-10-12)

| Fase | Tema | Estado |
|---|---|---|
| 0 | Reconocimiento → `fase-0-reconocimiento.md` | Hecha |
| 1 | Auditoría de datos sensibles → `fase-1-auditoria-datos.md` | **Hecha** (hallazgos corregidos; abiertos: revisión legal, contratos con encargados, `Pago.respuesta_bruta`) |
| 2 | Reforzar la verificación existente (ADR + diagrama) | **Hecha**: `adr/0001` con diagrama Mermaid; WebAuthn evaluado y diferido |
| 3 | Refuerzo (cifrado, bloqueo, auditoría, rotación, tests) | **Hecha**: cifrado Fernet, enforcement con vigencia de 180 días, `EventoVerificacion`, `rotar_llaves_biometricas` + guía, tests de fallos (E2E de navegador no: el demo tiene el enforcement apagado) |
| 4 | Cumplimiento visible | **Hecha**: consentimiento, "Mis datos" completo (descargar, corregir, oponerse, bloquear, eliminar), retención visible en la política, protocolo de brechas, EIPD/registro/encargados en borrador (falta revisión legal) |
| 5 | Bot asistente con IA (NVIDIA NIM) | **Implementado** (ADR 0005): preguntas frecuentes + búsqueda en el catálogo, enmascarado de datos personales, flujo guiado sin IA, botón flotante en todas las pantallas. Falta probarlo con una clave real y cargarla en Render |
| 6 | Rediseño visual 2026/27 | Pendiente; **requiere propuesta visual aprobada antes de implementar** |
| 7 | Calidad y cierre (README, `resumen-mejoras.md`, índice y matriz en `docs/cumplimiento/`) | **Hecha** (2026-10-12): `cumplimiento/README.md` con matriz, `resumen-mejoras.md`, READMEs renovados, E2E del asistente y de "Mis datos" |

Pospuesto por presupuesto/entorno: revisión legal por abogado, entorno de producción real
(`BIOMETRIC_ENCRYPTION_KEYS`, `EXIGIR_IDENTIDAD_VERIFICADA`), respaldo del keystore Android (PC de torre).

## Hecho que no estaba en el plan

Demo en Render + Neon (la Postgres de Render expiró), tests del backend de ~13 min a ~25 s (`settings_test.py`), reorden de
la documentación, Moderador revisa la vía alternativa, retención agendada con GitHub Actions. Detalle en `plan-ajustes.md`.
