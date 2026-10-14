import { normalizarRut, rutValido } from './rut';

describe('RUT', () => {
  it('normaliza puntos, espacios y guion faltante', () => {
    expect(normalizarRut('12.345.678-5')).toBe('12345678-5');
    expect(normalizarRut('123456785')).toBe('12345678-5');
    expect(normalizarRut(' 12345678-k ')).toBe('12345678-K');
  });

  it('acepta RUT con dígito verificador correcto', () => {
    expect(rutValido('12345678-5')).toBeTrue();
    expect(rutValido('11.111.111-1')).toBeTrue();
    expect(rutValido('76086428-5')).toBeTrue();
  });

  it('rechaza dígito verificador incorrecto, formato raro y texto', () => {
    expect(rutValido('12345678-9')).toBeFalse();
    expect(rutValido('1234-5')).toBeFalse();
    expect(rutValido('abcdefgh-1')).toBeFalse();
    expect(rutValido('')).toBeFalse();
  });
});
