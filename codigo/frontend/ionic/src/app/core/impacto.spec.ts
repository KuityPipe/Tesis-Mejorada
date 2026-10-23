import { esReparacionOMantencion, SITUACIONES_LABORALES, TIPOS_SERVICIO } from './impacto';

describe('impacto', () => {
  it('solo reparación y mantención activan la pregunta de reemplazo', () => {
    expect(esReparacionOMantencion('REPARACION')).toBeTrue();
    expect(esReparacionOMantencion('MANTENCION')).toBeTrue();
    expect(esReparacionOMantencion('INSTALACION_NUEVA')).toBeFalse();
    expect(esReparacionOMantencion(undefined)).toBeFalse();
  });

  it('ofrece "prefiero no decir" y los tipos de servicio del backend', () => {
    expect(SITUACIONES_LABORALES.some((s) => s.valor === 'NO_DICE')).toBeTrue();
    expect(TIPOS_SERVICIO.map((t) => t.valor)).toEqual(['REPARACION', 'MANTENCION', 'INSTALACION_NUEVA', 'OTRO']);
  });
});
