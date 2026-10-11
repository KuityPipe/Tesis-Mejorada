# EIPD (borrador) — Verificación de identidad con biometría en KeyServ

> **Estado: borrador técnico para la postulación Corfo. No es asesoría legal ni un
> documento firmado.** Redactado por el equipo técnico a partir del código real
> (`docs/fase-0-reconocimiento.md`). Las secciones marcadas **[DECISIÓN PENDIENTE]**
> requieren resolución del responsable del producto y revisión de un abogado antes de
> presentarse como respaldo de cumplimiento de la Ley 21.719. El producto hoy es una demo.

## 1. Descripción del tratamiento

KeyServ es un marketplace de servicios en Chile. Para dar confianza entre clientes y
proveedores, se quiere verificar la identidad de quien contrata o publica. Hay dos vías:

| Vía | Qué ocurre | Qué recibe el servidor |
|---|---|---|
| **Biometría nativa** (app móvil) | Face ID / huella del propio teléfono | Nada biométrico: solo un indicador `verificado_biometricamente = true` |
| **Reconocimiento facial en servidor** (web, o móvil sin biometría nativa) | El navegador captura ~2 s de fotogramas; se exige un parpadeo como prueba de vida | Los fotogramas, que se procesan y **se descartan**; se guarda un vector de 128 números (`encoding_facial`) |

Es un dato personal **sensible** (biometría con fines de identificación).

## 2. Necesidad y proporcionalidad **[DECISIÓN PENDIENTE]**

- **Finalidad:** reducir suplantación y fraude entre desconocidos que contratan servicios.
- **Minimización — recomendación técnica:** la biometría nativa es la vía principal, porque
  el dato nunca sale del dispositivo. El reconocimiento facial en servidor debería ser solo
  alternativa para quien no pueda usar la nativa, y no obligatorio si existe otra forma de
  verificación (p. ej. un documento de identidad).
- **A decidir:** ¿es indispensable verificar a todos, o solo a quien publica o supera un
  monto? ¿Se ofrece una vía sin biometría? Hoy **no hay enforcement**: nada bloquea
  contratar o publicar sin verificarse, lo que también debe reflejarse en el texto público.
- Se guarda un vector, no la foto. Un vector no es reversible a una imagen reconocible de
  forma sencilla, pero **sigue siendo dato biométrico** y se trata como tal.

## 3. Riesgos para las personas

| # | Riesgo | Estado actual | Gravedad |
|---|---|---|---|
| 1 | Filtración de `encoding_facial` (no es revocable como una contraseña) | Sin cifrar en la BD | Alta |
| 2 | Edición o lectura indebida desde el panel `/admin/` | Corregido: solo lectura (Fase 1) | Media (residual) |
| 3 | Tratamiento sin consentimiento válido | Sin consentimiento registrado ni checkbox | Alta |
| 4 | Falsos rechazos o aceptaciones (sesgo del modelo, poca luz) | Umbral 0.5 y filtro de calidad; sin pruebas de mismatch real | Media |
| 5 | Suplantación con foto o video | Prueba de vida por parpadeo; sin auditoría independiente | Media |
| 6 | Retención indefinida | Sin plazo ni purga | Media |
| 7 | Imposibilidad de ejercer derechos (acceso, supresión) | Solo por contacto manual | Alta |
| 8 | Exposición de fotos de reseñas no moderadas | Corregido: almacenamiento privado (Fase 1) | Baja (residual) |
| 9 | Fotogramas huérfanos si falla la escritura temporal | Raro; se borran en `finally` | Baja |

## 4. Medidas

**Implementadas:** fotogramas a disco temporal y borrado en `finally`; no se registra
ningún dato biométrico en logs; `encoding_facial` excluido de la API y de solo lectura
en el admin; biometría nativa sin transferencia al servidor; documentos y fotos de
reseñas/chat en almacenamiento privado con control de acceso; logs sin email en claro.

**Previstas (Fases 2-3):**
1. Consentimiento explícito, específico y revocable, con fecha y versión del texto, antes
   de capturar el rostro.
2. Cifrado de `encoding_facial` en reposo.
3. Endpoints de acceso, portabilidad y supresión; al revocar se borra el vector.
4. Plazo de retención y purga automática (vector, intentos sospechosos, tokens vencidos).
5. Pruebas de rechazo con rostros distintos y de iluminación, registradas.
6. Vía alternativa sin biometría **[DECISIÓN PENDIENTE]**.

## 5. Riesgo residual y aprobación **[DECISIÓN PENDIENTE]**

Mientras no existan consentimiento y cifrado, el riesgo residual de los puntos 1, 3 y 7 es
**alto** y no debería activarse la verificación obligatoria con usuarios reales. Con las
medidas previstas implementadas, el residual esperado pasa a medio-bajo. Esa valoración, y
su aceptación, corresponde a la persona responsable del producto y debe validarla un
abogado especialista.

| Rol | Nombre | Fecha | Firma |
|---|---|---|---|
| Responsable del producto | | | |
| Revisión legal | | | |
