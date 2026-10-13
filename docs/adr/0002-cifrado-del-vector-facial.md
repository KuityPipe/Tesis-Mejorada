# ADR 0002 — Cifrado en reposo del vector facial

- **Estado:** aceptada (2026-10-11), implementada en `KeyServApp/campos.py` + migración `0031`.
- **Contexto:** `Usuario.encoding_facial` (128 números derivados del rostro) era un dato biométrico guardado en claro y
  editable desde `/admin/`. Un volcado de la BD o un respaldo filtrado lo habría expuesto.

## Opciones

1. **Fernet (cryptography), con `MultiFernet`** — AES-128-CBC + HMAC-SHA256, autenticado, con rotación nativa
   (la primera clave cifra, todas descifran). **Elegida.**
2. AES-256-GCM con envelope encryption y KMS — más fuerte en teoría, pero exige un KMS (costo/infra) que el prototipo no
   tiene; con la clave en una variable de entorno el beneficio práctico sobre Fernet es marginal.
3. Cifrado homomórfico (CKKS) para comparar sin descifrar — interesante como módulo experimental de tesis; fuera de
   alcance (complejidad y rendimiento) para un vector de 128 floats comparado una vez por verificación.

## Decisión

Campo `CampoJSONCifrado`: en Python es una lista normal; en la BD, un token Fernet. Claves en
`BIOMETRIC_ENCRYPTION_KEYS` (distintas de `SECRET_KEY`; si falta, se deriva de `SECRET_KEY`, aceptable solo en
desarrollo/demo). Un valor que no es token se interpreta como JSON antiguo y se cifra al guardarse (migración de filas).
El panel de admin ni siquiera muestra el campo.

## Consecuencias

- Perder la clave equivale a perder los vectores (las personas deben registrar su rostro de nuevo); descifrar con una
  clave incorrecta devuelve `None` y deja un error en el log, nunca un valor falso.
- **Rotación documentada** en `docs/cumplimiento/rotacion-de-llaves.md`, con el comando `rotar_llaves_biometricas`.
- En producción real hay que definir una clave propia y respaldarla **fuera** de la base de datos.
