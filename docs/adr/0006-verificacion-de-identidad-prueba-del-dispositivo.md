# ADR 0006 — Qué prueba una "identidad verificada" y cómo proteger la vía nativa

- **Estado:** **propuesta, sin decidir** (2026-10-15). Nada de lo que sigue está implementado; espera la decisión del dueño.
- **Contexto:** la revisión del 2026-10-15 encontró que la verificación "nativa" se puede saltar y que la palabra
  "verificado" promete más de lo que el sistema comprueba. Complementa el [ADR 0001](0001-estrategia-de-verificacion-de-identidad.md).

## 1. El hallazgo

`POST /api/auth/verificar-biometria-nativa/` (`VerificarBiometriaNativaView`) solo exige un JWT válido y marca
`verificado_biometricamente = True` (con vigencia de 180 días). Cualquier persona registrada puede llamarlo con `curl`, sin
abrir la app, y con `EXIGIR_IDENTIDAD_VERIFICADA=True` queda "verificada". El README decía que la API confiaba además en una
"atestación de hardware del dispositivo": **no existe** (ni Play Integrity, ni App Attest, ni firma de un desafío, ni en el
backend ni en Ionic). El README ya se corrigió; este ADR decide qué hacer al respecto.

Lo que sí hace hoy el plugin (`@capgo/capacitor-native-biometric` 8.6.5): `verifyIdentity()` devuelve "ok" o error a la propia app
(un booleano en JavaScript, que nada ata a la llamada al servidor), y ofrece almacenamiento de credenciales protegido por
biometría (`setCredentials` / `getSecureCredentials`). **No ofrece firma de desafíos ni atestación.**

## 2. Qué significa hoy "verificado" (B2)

| Vía | Qué prueba realmente | Qué NO prueba |
|---|---|---|
| Biometría nativa | Que quien desbloqueó el teléfono está enrolado en **ese teléfono** (y, hoy, ni siquiera eso: ver el hallazgo) | Que sea la persona del RUT; que la persona enrolada sea el dueño legítimo del teléfono |
| Rostro en servidor (`/rostro/registrar` + `/verificar`) | Que hay un rostro vivo (parpadeo) y que es **el mismo** que se registró antes | Que ese rostro sea el de la persona del RUT: se registra *cualquier* cara y luego se compara consigo misma |
| Vía sin biometría | Que quien tiene la cuenta controla el correo, aceptó la advertencia y un humano revisó un documento | Depende del cuidado de la revisión (no hay comparación automática documento–persona) |

**Ninguna vía vincula la cuenta con una cédula.** La más cercana es la vía sin biometría (un humano ve el documento). Por eso la
promesa "proveedores con identidad verificada" es más fuerte que lo implementado: hoy equivale a "tiene un dispositivo
desbloqueado por alguien / tiene un rostro consistente / un humano revisó un documento", según la vía.

### Definición propuesta de "identidad verificada" (a decidir)

Dos niveles distintos, con nombres distintos en la app:

1. **Cuenta de confianza** (lo que existe hoy): la persona demostró control continuo de un dispositivo / rostro / correo.
   Texto sugerido: "Cuenta verificada" o "Verificación de dispositivo".
2. **Identidad verificada** (solo cuando exista vínculo con la cédula): un humano o un proveedor validó que el documento
   corresponde a la persona, **y** la biometría (nativa o rostro) se enroló después de esa validación o se comparó con la foto
   del documento.

Opciones para llegar al nivel 2, de menor a mayor esfuerzo:

- **Comparar el rostro del registro con la foto de la cédula** (que el humano ya revisa en la vía sin biometría): costo bajo,
  reutiliza `face_recognition`; exige guardar o procesar la foto del documento (dato personal) y tiene error de comparación
  entre una foto impresa y una selfie.
- **Hacer de la revisión de documento el paso obligatorio** y tratar la biometría nativa solo como "reconfirmación" de que
  sigue siendo la misma persona (ver opción (c) abajo).
- **Proveedor externo de validación de identidad chileno** (comparación contra el Registro Civil / cédula con prueba de vida).
  Es lo que de verdad prueba identidad legal; tiene costo por verificación y un contrato de encargado de tratamiento. **Lo
  tiene que evaluar y pagar el dueño**; no investigué proveedores concretos aquí.

**Estado (2026-10-16): implementada la primera mitad del nivel 2.** La vía sin biometría ahora pide, además del documento, un
**video corto** de la persona mostrando su cédula junto a la cara y diciendo su nombre y un número de 4 dígitos que la app
le muestra (el número evita reutilizar un video viejo). Una persona del staff lo compara con la foto de la cédula y con el
nombre y el RUT de la cuenta (que `/admin/` muestra junto al video), y aprueba o rechaza. Es la única vía que hoy ata una
cuenta con una cédula, con un humano como juez. **El video es un dato sensible:** exige consentimiento expreso, vive en
almacenamiento privado, solo lo ve el staff, se borra al aprobar o rechazar (o a los 30 días si nadie lo resuelve, o al
eliminar la cuenta) y no se procesa ni se compara automáticamente. Falta: la revisión de un abogado sobre este tratamiento
(consentimiento, plazo y base legal), y decidir si la biometría nativa y el rostro en servidor deben exigir también este paso
antes de contar como "identidad verificada" (hoy cada vía vale por separado).

### Dónde la promesa es más fuerte que lo implementado (revisar el copy)

Para que decidas si cambiar el texto o el sistema, estos son los lugares que prometen identidad (hay que revisarlos uno a uno):

- README (`README.md`/`README.es.md`): "biometric identity verification", "Identity verification that expires".
- Política de privacidad (`privacidad.html` y `privacidad.page.ts`) y el aviso/consentimiento biométrico (`consentimiento.py`).
- El asistente de IA (`asistente.py`: FAQ sobre verificación) y los textos de las pantallas de verificación
  (`app-verificacion-lateral`, `app-verif-exito`).
- Cualquier insignia de "verificado" en el catálogo/perfil de proveedor (`verificado_biometricamente` se expone en la API).

## 3. Opciones para la vía nativa (B1)

| | Qué protege | Qué NO protege | Esfuerzo | ¿Probable en el emulador `KeyServ_Test2`? |
|---|---|---|---|---|
| **(a) Llave asimétrica en Keystore/Secure Enclave, atada a la biometría, que firma un desafío (nonce) del servidor.** El servidor guarda la llave pública por dispositivo y verifica la firma | Que la llamada la produjo **un dispositivo enrolado** y que la biometría se pidió en esa operación; el `curl` con solo el JWT deja de servir. Es el estándar (equivalente a FIDO/passkeys) | Que sea la persona del RUT (ver B2); un dispositivo con rooting y hooking puede mentir al nivel de la app, aunque no extraer la llave | **Alto**: el plugin instalado no firma. Hay que cambiar de plugin (ver abajo) o escribir uno propio; backend de enrolamiento de llaves (`DispositivoBiometrico`), endpoint de desafío y de verificación, rotación y revocación | **Sí en Android**: el emulador soporta huella simulada (`adb emu finger touch`) y Keystore. iOS no se puede probar sin Mac |
| **(a-lite) Secreto de dispositivo guardado con el almacenamiento protegido por biometría que el plugin actual sí tiene** (`setCredentials`/`getSecureCredentials`): el servidor emite un secreto aleatorio al enrolar el dispositivo (con autenticación fuerte), la app lo lee con la biometría y lo manda; el servidor compara su hash | Que el que llama tiene el secreto del dispositivo y la app pidió biometría para leerlo; elimina el `curl` con solo JWT sin cambiar de plugin | El secreto pasa por memoria JavaScript (se puede robar en un dispositivo comprometido, a diferencia de una firma); se pierde con reinstalaciones; sin protección frente a repetición salvo rotarlo | **Medio-bajo**: sin plugin nuevo; un modelo y dos endpoints | **Sí** (mismo método que se usó en la verificación nativa original) |
| **(b) Play Integrity (Android) / App Attest (iOS)** | Que la llamada viene de **la app real, sin modificar, en un dispositivo certificado** (no de un script ni de una app clonada). Se verifica en el servidor con Google/Apple | No prueba biometría ni persona; es complemento de (a) o (a-lite), no reemplazo. Requiere proyecto de Google Cloud y cuenta de Apple Developer | **Medio**: existen plugins de Capacitor (`@capgo/capacitor-app-attest`, Capawesome App Integrity, `@capacitor-community/play-integrity`); el trabajo está en la verificación en el servidor (decodificar el veredicto, comprobar el nonce, el paquete y el certificado de firma) | **Parcial**: Play Integrity necesita Google Play Services y un APK firmado/instalado desde Play (el emulador "google_apis" puede dar veredictos básicos, no `STRONG`); App Attest solo funciona en iPhone físico |
| **(c) Mínimo inmediato: la vía nativa solo cuenta si la persona ya tiene una verificación por documento aprobada** (la nativa pasa a ser "reconfirmación") | Elimina de golpe el salto: sin documento aprobado por una persona, llamar al endpoint no verifica nada. Alinea el copy con lo que se puede probar | Quien tenga documento aprobado puede seguir "reconfirmando" con un `curl` (pero ya pasó la revisión humana); frena la vía principal (la nativa deja de ser autoservicio) | **Bajo**: un `if` en `identidad.identidad_verificada` / en el endpoint, más ajustes de copy | **Sí** |

### Plugins de Capacitor para (a) — lo que encontré

Búsqueda web del 2026-10-15; no probé ninguno ni revisé su mantenimiento, **hay que evaluarlos antes de adoptar uno**:

- [capacitor-pq-secure-storage](https://forum.ionicframework.com/t/post-quantum-crypto-plugin-for-capacitor-ml-dsa-ml-kem-secure-enclave-keystore/251695): firma con llaves en
  Secure Enclave/Keystore con chequeo biométrico por operación; su autor indica que Android solo se probó en emulador. Usa
  criptografía poscuántica (ML-DSA), distinta de la que verificaría el backend sin librerías extra.
- [Secure Biometric Key Auth](https://www.outsystems.com/forge/component-overview/25249/secure-biometric-key-auth-o11) (OutSystems Forge): llaves P-256 no exportables firmando desafíos del
  servidor. Es Cordova, no Capacitor: sirve de **diseño de referencia** (enrolar primero la clave pública), no de dependencia.
- Capawesome [Vault](https://capawesome.io/docs/plugins/vault/): almacenamiento protegido por biometría, **no firma** (equivale a (a-lite)).
- Escribir un plugin propio sobre `BiometricPrompt` + `KeyGenParameterSpec(setUserAuthenticationRequired)` (Android) y
  `SecKeyCreateSignature` con `SecAccessControl` (iOS) es la opción más controlable y la más cara.

Para (b): [@capgo/capacitor-app-attest](https://development.capgo.app/plugins/capacitor-app-attest/), [Capawesome App Integrity](https://capawesome.io/docs/sdks/capacitor/app-integrity/) y
[@capacitor-community/play-integrity](https://ionic.io/docs/tutorials/mobile-security/play-integrity) (Android).

## 4. Qué pasa cuando vence la verificación (B3)

`identidad.falta_verificar` se evalúa al **publicar** y al **contratar**, pero cuando la verificación del proveedor vence (180
días) sus publicaciones siguen en el catálogo y puede seguir **confirmando** trabajos. Con `EXIGIR_IDENTIDAD_VERIFICADA` activo,
propongo las dos, en este orden:

1. **Pedir reverificación al confirmar** (`ContratacionConfirmarView`): barato y es donde el vencimiento importa (el proveedor
   acepta trabajo nuevo). Respuesta 403 con `code=identidad_no_verificada`, igual que contratar y publicar.
2. **Ocultar del catálogo** las publicaciones de proveedores sin verificación vigente: más visible para el cliente (la
   garantía que se vende) pero castiga más (un proveedor con trabajos en curso no debería desaparecer de golpe). Sugiero
   aplicarlo con un aviso previo (correo) unos días antes de que venza, usando `notificaciones_correo.avisar`.

Los trabajos ya confirmados o en curso **no** se cortan por el vencimiento.

**Estado (2026-10-15):** el punto 1 (pedir reverificación al confirmar) está implementado, activo cuando `EXIGIR_IDENTIDAD_VERIFICADA=True`. El punto 2 (ocultar del catálogo) sigue pendiente.

## 5. Recomendación

1. **Ya:** opción (c) (mínimo, bajo costo) y renombrar en el copy "identidad verificada" por lo que realmente se prueba, hasta
   tener vínculo con la cédula.
2. **Siguiente:** (a-lite) o (a) según cuánto valga cerrar el hueco antes del lanzamiento real, más (b) si el abuso desde fuera
   de la app es una preocupación.
3. **Antes de prometer "identidad verificada" a un cliente o a Corfo:** elegir una de las opciones del nivel 2 de la sección 2.

Hasta la decisión, el test `BiometriaNativaSinPruebaTests` queda marcado como `expectedFailure` y apunta a este ADR.
