# Cumplimiento de la Ley 21.719 — carpeta de evidencia

> KeyServ trata un dato sensible (el vector derivado del rostro) y por eso el cumplimiento fue prioridad antes que
> el bot y el diseño. Esta carpeta reúne la evidencia: qué datos se tratan, por qué, cómo se protegen y cómo se
> respetan los derechos de las personas. **Es orientación técnica, no asesoría jurídica**: la revisión de un abogado
> sigue pendiente (ver [Riesgos residuales](#riesgos-residuales-y-lo-pendiente)). La ley entra en vigencia el
> **1 de diciembre de 2026**.

## Índice

| Qué | Dónde |
|---|---|
| Inventario de datos, hallazgos y brechas | [`../fase-1-auditoria-datos.md`](../fase-1-auditoria-datos.md) |
| Registro de actividades de tratamiento | [`registro-actividades-tratamiento.md`](registro-actividades-tratamiento.md) |
| Encargados y transferencia internacional | [`encargados-de-tratamiento.md`](encargados-de-tratamiento.md) |
| Evaluación de impacto (EIPD) del reconocimiento facial | [`../legal/eipd-reconocimiento-facial.md`](../legal/eipd-reconocimiento-facial.md) |
| Protocolo de brechas de seguridad | [`../legal/protocolo-de-brechas.md`](../legal/protocolo-de-brechas.md) |
| Rotación de la clave de cifrado biométrico | [`rotacion-de-llaves.md`](rotacion-de-llaves.md) |
| Decisiones de arquitectura (ADR 0001–0005) | [`../adr/`](../adr/) |
| Política de privacidad que ve el usuario | `/privacidad/` (`KeyServApp/templates/KeyServApp/privacidad.html`) |
| Historial de cambios de alcance | [`../plan-ajustes.md`](../plan-ajustes.md) |

## Medidas técnicas implementadas

- **Minimización:** del rostro solo se guarda un vector de 128 números; las imágenes se procesan en un archivo temporal que
  se borra en la misma petición. La biometría nativa (Face ID/huella del teléfono) nunca llega al servidor.
- **Cifrado en reposo** del vector con claves rotables (ADR 0002). Documentos de identidad y fotos de chat/reseñas en
  almacenamiento privado, servidos solo por vistas autenticadas.
- **Consentimiento** explícito, versionado y revocable antes de capturar el rostro (revocar borra el vector).
- **Alternativas a la biometría:** una vía sin biometría (código por correo + documento revisado por una persona).
- **Verificación reciente y auditada:** vale 180 días y cada intento deja un evento sin datos biométricos (ADR 0003).
- **Derechos del titular** autoservicio en la app (ADR 0004) y con plazo de 30 días para los que requieren revisión.
- **Retención automatizada** con purga semanal (GitHub Actions) y plazos publicados en la política de privacidad.
- **Seguridad de acceso:** contraseñas con PBKDF2, límite de intentos, registro de accesos sospechosos con geolocalización
  local (sin consultar terceros), validación real de archivos subidos, panel de administración con permisos acotados.
- **IA externa con enmascarado:** el asistente solo recibe texto sin RUT/correo/teléfono/números largos y datos del
  catálogo público (ADR 0005).

## Matriz de cumplimiento

| Requisito (Ley 21.719) | Cómo lo cumple KeyServ | Evidencia |
|---|---|---|
| Biometría es dato sensible; tratamiento restringido (art. 2 g) | Solo vector cifrado, nunca imágenes; alternativa sin biometría | `campos.py`, migración `0031`, ADR 0001–0002; `RotacionDeLlavesTests` |
| Consentimiento explícito e informado; informar sistema, finalidad y período (art. 16 ter) | Texto versionado que indica sistema, finalidad y período; evidencia de versión y fecha; revocable | `consentimiento.py` (`VERSION`/`TEXTO`), `ConsentimientoBiometrico`; `ConsentimientoBiometricoApiTests`, `ConsentimientoBiometricoTemplateTests` |
| Licitud, finalidad y proporcionalidad | Biometría solo para verificar identidad al contratar/publicar; la vía principal no deja datos en el servidor | `identidad.py`, ADR 0001 |
| Minimización y calidad | Vector (no imagen); datos del asistente enmascarados; retención con purga | `asistente.py`; `purgar_datos_vencidos`; `RetencionDatosTests`, `VigenciaYEventosVerificacionTests` |
| Privacidad desde el diseño y por defecto | Enforcement de identidad configurable, biometría opcional, bloqueo reversible, almacenamiento privado por defecto | ADR 0001, 0004; `storage.py` |
| Seguridad (medidas técnicas y organizativas) | Cifrado, control de acceso, límites de intentos, auditoría, validación de archivos, admin acotado | `campos.py`, `validators.py`, `IntentoAccesoSospechoso`, `GrupoModeradorCommandTests` |
| Transparencia | Política de privacidad con datos, terceros, plazos y derechos; aviso de IA externa en el widget | `privacidad.html`; `asistente.spec.ts` |
| Derecho de acceso y portabilidad | `GET /api/auth/mis-datos/` (JSON descargable) | `MisDatosView`; `DerechosTitularApiTests` |
| Rectificación | Edición de perfil + solicitud con plazo de 30 días | `DerechosView`, `SolicitudTitular`; `DerechosDelTitularTests` |
| Supresión | Eliminación de cuenta por anonimización, con reautenticación | `derechos_titular.eliminar_cuenta`; `DerechosTitularApiTests` |
| Oposición | Oposición biométrica inmediata (revoca y borra el vector); otras, revisión manual | `solicitar_oposicion_biometria`; `DerechosDelTitularTests` |
| Bloqueo | Bloqueo reversible: se ocultan servicios y no se puede publicar ni contratar | `fijar_bloqueo`; `test_bloqueo_oculta_publicaciones...` |
| Plazo de respuesta (30 días) | Cada solicitud guarda su vencimiento y el dashboard destaca las vencidas | `SolicitudTitular.vence_en`; `AdminDerechosTitularTests` |
| Retención limitada | Plazos concretos (chats 90 d, accesos 365 d, eventos 365 d, sesiones 30 d, verificación 180 d) | `mantenimiento_retencion`, `.github/workflows/retencion.yml` |
| Responsabilidad proactiva / trazabilidad | Registro de eventos de verificación y de solicitudes; historial del admin | `EventoVerificacion`, `SolicitudTitular`; `AdminDerechosTitularTests` |
| Evaluación de impacto (EIPD) | Borrador completo del reconocimiento facial | `../legal/eipd-reconocimiento-facial.md` |
| Registro de actividades y encargados | Borradores actualizados con cada nuevo tratamiento (incluye NVIDIA, Neon, GitHub) | `registro-actividades-tratamiento.md`, `encargados-de-tratamiento.md` |
| Notificación de brechas "sin dilaciones indebidas" | Protocolo con contención, evaluación, registro y avisos | `../legal/protocolo-de-brechas.md` |
| Transferencia internacional | Identificada por proveedor (EE. UU., Brasil); evaluación jurídica pendiente | `encargados-de-tratamiento.md` |
| No enviar datos personales a IA externa (restricción del plan) | Enmascarado antes de enviar; el modelo no ve cuentas ni biometría; contenido no se registra | ADR 0005; `EnmascaradoDeDatosPersonalesTests`, `AsistenteApiTests` |

## Riesgos residuales y lo pendiente

1. **Revisión jurídica** de consentimiento, EIPD, registro, plazos de retención y alcance de lo que se conserva al eliminar
   una cuenta (pospuesta por presupuesto). Todos los textos legales son **borradores**.
2. **Contratos/DPA con encargados** y evaluación de la transferencia internacional (Render y Neon en el demo, GitHub,
   NVIDIA, Netlify, Google).
3. **Entorno de producción real** inexistente: hoy solo hay un demo. Allí se debe definir `BIOMETRIC_ENCRYPTION_KEYS`
   propia y respaldada fuera de la BD, y encender `EXIGIR_IDENTIDAD_VERIFICADA`.
4. **El enmascarado del asistente es por patrones**: un dato escrito de forma inusual podría pasar; por eso el widget pide
   no compartir datos personales.
5. `Pago.respuesta_bruta` guarda la respuesta cruda del medio de pago y falta filtrarla.
6. Las solicitudes manuales las atiende una sola persona; no hay suplente designado para brechas ni solicitudes.
7. El bloqueo del tratamiento solo aplica en la API/Ionic (las plantillas Django están en retiro).
8. Los tests de detección facial sobre imágenes reales siguen siendo manuales (los automáticos cubren la comparación y el umbral).
