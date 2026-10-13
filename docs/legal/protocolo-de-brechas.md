# Protocolo de respuesta a brechas de seguridad (borrador)

> Borrador técnico. **No es asesoría legal**: los plazos y el contenido de las notificaciones deben validarse con un
> abogado. La Ley 21.719 exige reportar a la Agencia de Protección de Datos Personales **sin dilaciones indebidas**
> (no hay un plazo fijo de 72 horas; eso es del RGPD europeo) y avisar a los titulares cuando haya riesgo para sus derechos.

**Responsable:** el dueño del proyecto (único mantenedor hoy). Designar un suplente es una decisión pendiente.

## 1. Qué es una brecha

Acceso, pérdida, alteración o divulgación no autorizados de datos personales. Ejemplos en KeyServ: filtración de la base de
datos (Neon) o de un respaldo; exposición de `media_privado/`; clave de cifrado biométrico comprometida; credenciales de
Render/Netlify/GitHub/Neon robadas; cuenta de administrador comprometida; documentos de identidad accesibles a terceros.

## 2. Cómo se detecta

- Alerta del tablero de `/admin/` y listado de **accesos sospechosos** (`IntentoAccesoSospechoso`).
- **Eventos de verificación** anómalos (`EventoVerificacion`: ráfagas de fallos).
- Avisos de los proveedores (Render, Neon, GitHub, Netlify) y de GitHub (secretos expuestos, dependabot).
- Reporte de una persona usuaria por el formulario de contacto.

## 3. Pasos

| # | Paso | Detalle |
|---|---|---|
| 1 | **Contener** | Revocar credenciales y tokens (`TokenSesion`), rotar `DJANGO_SECRET_KEY`/`JWT_SECRET`/`DATABASE_URL`, rotar la clave biométrica (`docs/cumplimiento/rotacion-de-llaves.md`), cerrar el acceso expuesto |
| 2 | **Evaluar** | Qué datos, de cuántas personas, desde cuándo, si eran sensibles (vector facial, documento de identidad), si el vector estaba cifrado y la clave sigue segura |
| 3 | **Registrar** | Anotar fecha/hora de detección, descripción, datos afectados, decisiones y responsables (registro interno, abajo) |
| 4 | **Notificar a la Agencia** | Sin dilaciones indebidas si hay riesgo para los derechos de las personas: qué ocurrió, categorías y volumen de datos, consecuencias probables, medidas adoptadas, contacto |
| 5 | **Avisar a las personas afectadas** | Si el riesgo es alto (datos sensibles, documentos de identidad): en lenguaje claro, qué pasó, qué datos, qué hacer (cambiar contraseña, estar atento a suplantación) y cómo contactarnos |
| 6 | **Corregir y aprender** | Causa raíz, arreglo, test que lo cubra y actualización de este protocolo y de `docs/fase-1-auditoria-datos.md` |

## 4. Plantilla de registro interno

```
Fecha y hora de detección:
Cómo se detectó:
Descripción de lo ocurrido:
Datos y categorías afectadas (¿sensibles?):
Personas afectadas (número aproximado):
Cifrado al momento de la brecha (sí/no, qué clave):
Medidas de contención y hora:
Notificación a la Agencia (fecha / pendiente / no corresponde, por qué):
Aviso a las personas (fecha / no corresponde, por qué):
Causa raíz y corrección:
```

## 5. Pendiente

- Revisión jurídica y canal oficial de notificación a la Agencia cuando esté operativo.
- Suplente del responsable y datos de contacto de emergencia.
- Simulacro (una vez al año).
