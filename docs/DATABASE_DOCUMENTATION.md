# Documentación de Base de Datos — KeyServ

Generado a mano a partir de `codigo/backend/django/KeyServApp/models.py`
(Fase 3). El esquema real lo gestionan las migraciones de Django
(`KeyServApp/migrations/0001_initial.py`) contra **PostgreSQL** — ver
`docs/RECOMMENDED_ARCHITECTURE.md` para la justificación del motor.

Convención: los nombres de columna (`db_column`) se preservan en MAYÚSCULA
del diccionario de datos original de la tesis; los nombres de tabla
(`db_table`) también. Los atributos Python son `snake_case`.

## Catálogos (PK manual, se cargan con datos fijos)

| Tabla | PK | Columnas | Notas |
|---|---|---|---|
| `REGION` | `ID_REGION` | `NOMBRE_REGION` | Las 16 regiones de Chile |
| `COMUNA` | `ID_COMUNA` | `NOMBRE_COMUNA`, `FK_REGION` → `REGION` | |
| `TIPO_CUENTA` | `ID_TIPO_CUENTA` | `NOMBRE_TIPO_CUENTA`, `VALOR_CUENTA` | Tiers: free/individual/pyme/empresa |
| `ESTADO_AUTENTIFICACION` | `ID_ESTADO_AUTENTIFICACION` | `NOMBRE_ESTADO_AUTENTIFICACION` | |
| `ESTADO_CONSULTA` | `ID_ESTADO_CONSULTA` | `NOMBRE_ESTADO_CONSULTA` | |
| `ESTADO_DOCUMENTO` | `ID_ESTADO_DOCUMENTO` | `NOMBRE_ESTADO_DOCUMENTO` | |
| `TIPO_FIRMA` | `ID_TIPO_FIRMA` | `NOMBRE_TIPO_FIRMA` | |
| `ROL_CUENTA_ADMINISTRATIVA` | `ID_ROL_CUENTA_ADMINISTRATIVA` | `NOMBRE_ROL_CUENTA_ADMINISTRATIVA` | |
| `AREA_ADMINISTRATIVA` | `ID_AREA_ADMINISTRATIVA` | `NOMBRE_AREA_ADMINISTRATIVA` | |

## Tablas transaccionales (PK autoincremental)

| Tabla | PK | FK | Columnas propias | Notas |
|---|---|---|---|---|
| `TRANSACCION` | `ID_TRANSACCION` | `FK_VALOR_CUENTA` → `TIPO_CUENTA` | `TIEMPO_TRANSACCION` | Se crea una por cada alta de cuenta |
| `USUARIO` | `ID_USUARIO` | `FK_TRANSACCION` → `TRANSACCION`, `FK_TIPO_CUENTA` → `TIPO_CUENTA`, `FK_COMUNA` → `COMUNA` | `RUT_USUARIO`, nombre/apellido ×2, `TELEFONO`, `EMAIL` (único), `DIRECCION_USUARIO`, `EDAD`, `CONTRASEÑA` (hash, no texto plano), `ES_PROVEEDOR` (nuevo), `VERIFICADO_BIOMETRICAMENTE` (nuevo) | Entidad central del sistema |
| `USUARIO_ADMINISTRATIVO` | `ID_USUARIO_ADMINISTRATIVO` | `FK_ROL_CUENTA_ADMINISTRATIVA`, `FK_AREA_ADMINISTRATIVA` | datos personales + `TELEFONO_USUARIO_ADMINISTRATIVO`, `EMAIL_USUARIO_ADMINISTRATIVO` | Staff interno, separado de `USUARIO` |
| `AUTENTIFICACION` | `ID_AUTENTIFICACION` | `FK_USUARIO_AUTENTIFICACION` → `USUARIO`, `FK_ESTADO_AUTENTIFICACION` → `ESTADO_AUTENTIFICACION` | `CODIGO_AUTENTIFICACION` (binario), `FECHA_AUTENTIFICACION` | Log de cada intento de auth |
| `CONSULTA` | `ID_CONSULTA` | `FK_ESTADO_CONSULTA`, `FK_USUARIO_CONSULTA` → `USUARIO`, `FK_USUARIO_ADMINISTRATIVO` | `ASUNTO_CONSULTA`, fechas | Tickets de soporte |
| `CONVERSACION` | `ID_CONVERSACION` | — | `NOMBRE_CONVERSACION`, `FECHA_CREACION` | Hilo de mensajería |
| `USUARIO_CONVERSACION` | `ID_USUARIO_CONVERSACION` | `FK_USUARIO_C` → `USUARIO`, `FK_CONVERSACION` → `CONVERSACION` | — | Tabla puente (participantes), `unique_together` |
| `MENSAJE` | `ID_MENSAJE` | `FK_CONVERSACION`, `FK_USUARIO` → `USUARIO` | `CONTENIDO`, `FECHA_ENVIO` | |
| `PUBLICACIONES` | `ID_PUBLICACION` | `FK_USUARIO_P` → `USUARIO` (proveedor) | `TITULO`, `SUB_TITULO`, `DESCRIPCION_PUBLICACION`, fechas, `ESTADO_MODERACION` (nuevo: `PENDIENTE`/`APROBADA`/`RECHAZADA`) | El campo de moderación es nuevo — ver `docs/NEW_CODE_CREATED.md` |
| `IMAGENES` | `ID_IMAGEN` | `FK_PUBLICACION` → `PUBLICACIONES` | `URL_IMAGEN`, fechas | |
| `CONTRATACION` | `ID_CONTRATACION` | `FK_PUBLICACION`, `FK_CLIENTE` → `USUARIO`, `FK_PROVEEDOR` → `USUARIO` | `ESTADO`, fechas | **Tabla nueva** (no existía antes de Fase 3) |
| `VALORACION` | `ID_VALORACION` | `FK_USUARIO_EMISOR` → `USUARIO`, `FK_USUARIO_RECEPTOR` → `USUARIO`, `FK_PUBLICACION` | `PUNTUACION` (1-5), `COMENTARIO`, `FECHA_VALORACION` | |
| `RANKING` | `ID_RANKING` | `FK_USUARIO` → `USUARIO` (**OneToOne**) | `TOTAL_VALORACIONES`, `PUNTUACION_PROMEDIO` | Agregado recalculado en cada nueva `Valoracion` (ver `views._recalcular_ranking`) |
| `DOCUMENTO` | `ID_DOCUMENTO` | `FK_USUARIO`, `FK_ESTADO_DOCUMENTO` | `NOMBRE_DOCUMENTO`, `ARCHIVO` (binario), `FECHA_SUBIDA_DOCUMENTO` | |
| `FIRMA` | `ID_FIRMA` | `FK_AUTENTIFICACION`, `FK_FIRMA_USUARIO` → `USUARIO`, `FK_TIPO_FIRMA`, `FK_DOCUMENTO` | `HASH_FIRMA` (binario), fecha | |
| `GASTO` | `ID_GASTO` | `FK_RESPONSABLE_GASTO` → `USUARIO_ADMINISTRATIVO` | `MONTO_GASTO`, `FECHA_GASTO` | Contabilidad interna |

## Diagrama de relaciones (simplificado, entidades de negocio principales)

```
USUARIO ──< PUBLICACIONES ──< IMAGENES
   │              │
   │              └──< CONTRATACION >── USUARIO (cliente/proveedor, 2 FK distintas)
   │                        │
   │                        └── (al completarse) ──> VALORACION >── USUARIO
   │
   ├──< AUTENTIFICACION
   ├──< DOCUMENTO ──< FIRMA
   ├── RANKING (1-a-1)
   └──< USUARIO_CONVERSACION >── CONVERSACION ──< MENSAJE
```

## Qué cambió respecto al diccionario de datos original de la tesis

Comparado con lo documentado en `docs/PDF_ANALYSIS_FINDINGS.md` §6 (que
confirmó que el diccionario de datos coincidía con el `models.py` de
entonces):

1. Se agregaron `ForeignKey` reales donde antes había enteros sueltos sin
   relación declarada — el diccionario de datos ya implicaba estas
   relaciones (los nombres `FK_*` lo dejan claro), solo faltaba
   modelarlas como tal en Django.
2. Se agregaron `USUARIO.ES_PROVEEDOR` y `USUARIO.VERIFICADO_BIOMETRICAMENTE`
   — no estaban en el diccionario de datos original, son necesarios para
   soportar RF001 (verificación biométrica) y distinguir los dos actores
   del PDF (Cliente/Proveedor).
3. Se agregó la tabla `CONTRATACION` completa — el diccionario de datos
   original no tenía una tabla para el proceso de contratación en sí (solo
   `PUBLICACIONES`, `VALORACION`, `TRANSACCION`), a pesar de que el BPMN
   "Proceso de contratación" del PDF (PAGE 136-137) sí lo describe.
4. Se agregó `PUBLICACIONES.ESTADO_MODERACION` — el BPMN "Crear publicación"
   (PDF PAGE 135-136) exige un flujo de aprobación que no tenía dónde
   guardarse.
