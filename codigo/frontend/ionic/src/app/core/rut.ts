import { AbstractControl, ValidationErrors } from '@angular/forms';

/** `12.345.678-5`, `12345678-5` o `123456785` → `12345678-5`. Mismo criterio que `KeyServApp/rut.py`. */
export function normalizarRut(valor: string): string {
  let limpio = (valor ?? '').replace(/[.\s]/g, '').toUpperCase();
  if (!limpio.includes('-') && limpio.length >= 2) {
    limpio = `${limpio.slice(0, -1)}-${limpio.slice(-1)}`;
  }
  return limpio;
}

function digitoVerificador(cuerpo: string): string {
  let suma = 0;
  let factor = 2;
  for (const digito of cuerpo.split('').reverse()) {
    suma += Number(digito) * factor;
    factor = factor === 7 ? 2 : factor + 1;
  }
  const resto = 11 - (suma % 11);
  return resto === 10 ? 'K' : resto === 11 ? '0' : String(resto);
}

/** `true` si el RUT tiene formato correcto y su dígito verificador coincide. */
export function rutValido(valor: string): boolean {
  const rut = normalizarRut(valor);
  if (!/^\d{7,8}-[\dK]$/.test(rut)) return false;
  const [cuerpo, dv] = rut.split('-');
  return digitoVerificador(cuerpo) === dv;
}

/** Validador de formulario: vacío lo deja pasar (para eso está `required`); un RUT mal escrito da `{ rut: true }`. */
export function validadorRut(control: AbstractControl): ValidationErrors | null {
  const valor = control.value as string;
  return !valor || rutValido(valor) ? null : { rut: true };
}
