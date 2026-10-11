# EIPD (borrador) — Verificación de identidad con biometría en KeyServ

> **Estado: borrador técnico para la postulación Corfo. No es asesoría legal ni un
> documento firmado.** Redactado por el equipo técnico a partir del código real
> (`docs/fase-0-reconocimiento.md`). Las decisiones de producto de §2 ya están tomadas;
> falta la revisión de un abogado antes de
> presentarse como respaldo de cumplimiento de la Ley 21.719. El producto hoy es una demo.

## 1. Descripción del tratamiento

KeyServ es un marketplace de servicios en Chile. Para dar confianza entre clientes y
proveedores, se quiere verificar la identidad de quien contrata o publica. Hay dos vías:

| Vía | Qué ocurre | Qué recibe el servidor |
|---|---|---|
| **Biometría nativa** (app móvil) | Face ID / huella del propio teléfono | Nada biométrico: solo un indicador `verificado_biometricamente = true` |
| **Reconocimiento facial en servidor** (web, o móvil sin biometría nativa) | El navegador captura ~2 s de fotogramas; se exige un parpadeo como prueba de vida | Los fotogramas, que se procesan y **se descartan**; se guarda un vector de 128 números (`encoding_facial`) |

Es un dato personal **sensible** (biometría con fines de identificación).

## 2. Necesidad y proporcionalidad

**Decisión del responsable del producto (2026-10-11):**

1. **La biometría nativa del dispositivo es la vía principal y el pilar de seguridad de
   KeyServ.** Es la más segura para la persona porque el dato biométrico nunca sale del
   teléfono, y la que da confianza entre desconocidos que se contratan.
2. **Se ofrece una vía alternativa sin biometría**, más lenta, que **exige verificación
   multifactor** (ver §4). No es obligatorio dar datos biométricos para usar la
   plataforma.
3. El reconocimiento facial en servidor queda como opción para quien no puede usar la
   biometría nativa (p. ej. en web); no es la vía por defecto.

- **Finalidad:** reducir suplantación y fraude entre desconocidos que contratan servicios.
- Se guarda un vector, no la foto. Un vector no es reversible a una imagen reconocible de
  forma sencilla, pero **sigue siendo dato biométrico** y se trata como tal.
- **Pendiente de definir:** si la verificación se exige a todos o solo a quien publica o
  supera cierto monto. Hoy **no hay enforcement**: nada bloquea contratar o publicar sin
  verificarse, y el texto público no debe afirmar lo contrario.

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
6. **Vía alternativa sin biometría, con multifactor** (decidida; diseño por definir). Propuesta
   técnica: contraseña + segundo factor (código por correo o app autenticadora) + revisión
   manual de un documento de identidad. Es más lenta a propósito. El segundo factor y el
   flujo de revisión no existen hoy y se construyen en la Fase 2.
7. **Advertencia explícita** al elegir esa vía (ver §5).

## 5. Riesgo residual y advertencia al usuario

Mientras no existan consentimiento y cifrado, el riesgo residual de los puntos 1, 3 y 7 es
**alto** y no debería activarse la verificación obligatoria con usuarios reales. Con las
medidas previstas implementadas, el residual esperado pasa a medio-bajo.

**Vía sin biometría:** la persona que la elige recibe una advertencia clara, que debe
aceptar activamente, indicando que la verificación es menos robusta y que **asume el riesgo
asociado** (p. ej. mayor exposición a suplantación de cuenta). Texto a redactar en la
Fase 2 y a revisar por un abogado.

> **Alcance de esa advertencia (revisar con abogado):** la aceptación del usuario sirve
> para informar y dejar constancia, pero **no traslada la responsabilidad de KeyServ como
> responsable del tratamiento**: seguridad, minimización y derechos del titular siguen
> siendo obligaciones de la empresa, y una cláusula de "bajo su propio riesgo" no las
> elimina. Por eso el multifactor de la vía alternativa es obligatorio y no solo
> una advertencia.

La aceptación del riesgo residual global y la firma corresponden a la persona responsable
del producto, con revisión de un abogado especialista.

| Rol | Nombre | Fecha | Firma |
|---|---|---|---|
| Responsable del producto | | | |
| Revisión legal | | | |
