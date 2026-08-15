import { TestBed } from '@angular/core/testing';

import { AlmacenamientoSeguro } from './almacenamiento-seguro';

describe('AlmacenamientoSeguro', () => {
  let servicio: AlmacenamientoSeguro;
  const clave = 'clave-de-prueba-almacenamiento-seguro';

  beforeEach(async () => {
    TestBed.configureTestingModule({});
    servicio = TestBed.inject(AlmacenamientoSeguro);
    await servicio.eliminar(clave);
  });

  afterEach(async () => {
    await servicio.eliminar(clave);
  });

  it('obtener() devuelve undefined para una clave que nunca se guardó', async () => {
    expect(await servicio.obtener(clave)).toBeUndefined();
  });

  it('guardar() y obtener() redondean el mismo valor', async () => {
    await servicio.guardar(clave, 'un-valor-secreto');
    expect(await servicio.obtener(clave)).toBe('un-valor-secreto');
  });

  it('eliminar() hace que obtener() vuelva a devolver undefined', async () => {
    await servicio.guardar(clave, 'un-valor-secreto');
    await servicio.eliminar(clave);
    expect(await servicio.obtener(clave)).toBeUndefined();
  });

  it('eliminar() sobre una clave inexistente no lanza', async () => {
    await expectAsync(servicio.eliminar('clave-que-nunca-existio')).toBeResolved();
  });
});
