# Seguimiento del proyecto

Para no perder nada de lo que se agrega o se modifica. Tres piezas que se complementan:

| Pieza | Para qué | Dónde |
|---|---|---|
| **Tablero en Excel** | Tareas, cambios, decisiones, pendientes tuyos, riesgos, presupuesto, calculadora de comisión y guion de pruebas | [`KeyServ_Seguimiento.xlsx`](KeyServ_Seguimiento.xlsx) |
| **Changelog** | Historia legible de qué cambió y por qué, por fecha | [`CHANGELOG.md`](CHANGELOG.md) |
| **Documentos de fondo** | El detalle: decisiones (ADR), planes, análisis | [`../README.md`](../README.md) (índice) |

La fuente de verdad del código es **git**; el tablero es para decidir y organizar, no para guardar versiones.

## El libro de Excel (`KeyServ_Seguimiento.xlsx`)

| Hoja | Qué hay | Cómo se mantiene |
|---|---|---|
| `Leeme` | Cómo usar el libro y los colores | Fija |
| `Tareas` | Todo lo que falta o se hizo (ID, área, prioridad, estado, responsable, dependencias, fecha) | **A mano**: cambia el estado con el desplegable |
| `Planner` | Las mismas tareas con las columnas de Microsoft Planner | Se llena sola desde `Tareas` |
| `Cambios` | Un commit por fila (de `git log`) | Se regenera desde git (ver más abajo) |
| `Decisiones` | Qué se decidió, quién, cuándo y dónde está el detalle | A mano |
| `Pendientes_dueño` | Lo que solo puedes hacer tú (cuentas, claves, abogado, Corfo) | A mano, columna "Listo" |
| `Riesgos` | Probabilidad x impacto con colores | A mano |
| `Comision` | Calculadora con fórmulas: tramos, tarifas de las pasarelas y margen por transacción | Cambia los valores azules |
| `Presupuesto` | Costos con supuestos escritos (para Corfo) | Completa las celdas amarillas |
| `Pruebas` | Guion de recorrido manual con resultado OK/Falla | A mano mientras pruebas |
| `Corfo` | Requisitos de las bases de Semilla Inicia con su estado (cumple, falta, por verificar) | A mano; detalle en `docs/corfo/` |
| `Gantt` | Carta Gantt de los 10 meses de ejecución; las barras se mueven al cambiar inicio y fin | Cambia los meses (azul) |

Convención de colores: **azul** = dato que puedes cambiar · **amarillo** = falta completarlo · negro = fórmula o texto fijo.

### Usarlo con Planner, Teams o Google Sheets
- **Planner:** abre la hoja `Planner`, copia las filas y pégalas en tu plan (o, si usas el Planner con Excel/Power Automate, conéctalo a esa hoja). Los buckets son las áreas; las prioridades se traducen solas (Alta → Importante).
- **Teams / OneDrive:** el archivo vive en el repo; si lo quieres compartido y editable por más gente, súbelo a OneDrive o Teams (el repo queda con la copia de referencia).
- **Google Sheets:** *Archivo → Importar → Subir*. Los desplegables y las fórmulas se conservan.

### Regenerar la hoja `Cambios`
Cada commit ya queda en git. Para ver los últimos en la terminal:

```
git log --since=2026-10-10 --date=short --format="%ad  %h  %s"
```

Pega ese resultado en la hoja `Cambios` (fecha, commit, resumen), o pídeselo a Claude, que la regenera completa.

## Qué hacer cada vez que se agrega o se cambia algo

1. **Commit en español** que diga qué y por qué (queda solo en `git log` y en `Cambios`).
2. **`Tareas`:** marca la tarea como *Hecho* (o agrégala si no existía) y anota la fecha.
3. **`CHANGELOG.md`:** una línea bajo la fecha de hoy, en lenguaje simple.
4. **Si fue una decisión** (se eligió una opción, se descartó otra): una fila en `Decisiones` y, si es de arquitectura o de riesgo legal, un ADR en `docs/adr/`.
5. **Si dependes de otra persona o cuenta:** una fila en `Pendientes_dueño`.
6. **Si cambia un número de negocio** (comisión, plazos, costos): actualiza `Comision` o `Presupuesto`.
7. **Al cerrar la sesión:** sobrescribe [`../ESTADO_Y_PROXIMOS_PASOS.md`](../ESTADO_Y_PROXIMOS_PASOS.md) (único documento de estado; no se crean copias con fecha).

## Dónde vive cada cosa (mapa del proyecto)

```
codigo/backend/django/   Backend (Django + API REST). Cambios de código y migraciones.
codigo/frontend/ionic/   App (Ionic/Angular + Capacitor Android). Tests: npm test; e2e: npm run test:e2e
codigo/biometria/        Scripts de reconocimiento facial (se usan desde Django) y un ejemplo de huella
docs/                    Documentación de ingeniería (índice en docs/README.md)
  adr/                   Decisiones de arquitectura y riesgo (una por archivo, numeradas)
  cumplimiento/          Evidencia para la Ley 21.719 (matriz, encargados, rotación de llaves)
  legal/                 Borradores legales (EIPD, protocolo de brechas), sin revisión de abogado
  seguimiento/           Este tablero: Excel, changelog y cómo llevarlo
  archivo/               Historia superada; no es el estado actual
  academico/             Tesis (solo local, no se sube)
render.yaml, .env.example, .github/workflows/   Despliegue y CI
```

Reglas para no desordenar:
- **Un solo documento de estado** (`ESTADO_Y_PROXIMOS_PASOS.md`), que se sobrescribe. Lo superado va a `docs/archivo/`.
- **Nombres:** ADR como `NNNN-tema-en-minusculas.md`; planes en mayúsculas (`PLAN_...`, `ANALISIS_...`).
- **Los secretos nunca van al repo ni al chat:** claves y contraseñas solo en `.env` local y en Render.
- Los archivos de datos de prueba y los videos o documentos subidos (`media/`, `media_privado/`) están ignorados por git.
