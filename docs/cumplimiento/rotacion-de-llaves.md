# Rotación de llaves de cifrado biométrico

> Procedimiento para cambiar la clave que cifra `Usuario.encoding_facial` sin perder datos. Ver ADR 0002.

**Cuándo rotar:** al sospechar que la clave se filtró, cuando alguien con acceso a ella deja el proyecto, y como
práctica periódica (propuesta: una vez al año).

## Pasos

1. **Generar una clave nueva** (no la subas a ningún repositorio):
   ```
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
2. **Ponerla primera** en `BIOMETRIC_ENCRYPTION_KEYS`, dejando las anteriores detrás, separadas por coma
   (la primera cifra, todas descifran). Reiniciar el servicio.
   Ejemplo: `BIOMETRIC_ENCRYPTION_KEYS=<clave_nueva>,<clave_vieja>`
3. **Simular:** `python manage.py rotar_llaves_biometricas --dry-run` (muestra cuántas filas rotaría).
4. **Rotar:** `python manage.py rotar_llaves_biometricas`. Re-cifra cada vector con la clave nueva. Nunca pisa un vector
   que no pudo descifrar: lo cuenta como "ilegible" y lo deja intacto.
5. Cuando el comando informe **Por rotar: 0** e **Ilegibles: 0**, quitar la clave vieja de la variable y reiniciar.
6. **Respaldar la clave nueva fuera de la base de datos** (gestor de contraseñas). Perder la clave equivale a perder los
   vectores: las personas tendrían que registrar su rostro de nuevo.

## Notas

- Si `BIOMETRIC_ENCRYPTION_KEYS` está vacía, la clave se deriva de `SECRET_KEY`: sirve solo para desarrollo/demo.
  Cambiar `SECRET_KEY` en ese estado volvería ilegibles los vectores.
- El comando está probado (`RotacionDeLlavesTests`): rota, no modifica en `--dry-run` y no sobrescribe ilegibles.
- Quien rota debe dejar constancia (fecha y motivo) en `docs/ESTADO_Y_PROXIMOS_PASOS.md`.
