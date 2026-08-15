import { TestBed } from '@angular/core/testing';

import { Tema } from './tema';

describe('Tema', () => {
  let servicio: Tema;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    servicio = TestBed.inject(Tema);
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem('ks-theme');
  });

  afterEach(() => {
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem('ks-theme');
  });

  it('obtenerElegido() devuelve null sin data-theme puesto', () => {
    expect(servicio.obtenerElegido()).toBeNull();
  });

  it('alternar() pasa de claro a oscuro y persiste en localStorage', () => {
    document.documentElement.setAttribute('data-theme', 'light');
    servicio.alternar();
    expect(servicio.obtenerElegido()).toBe('dark');
    expect(localStorage.getItem('ks-theme')).toBe('dark');
  });

  it('alternar() pasa de oscuro a claro', () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    servicio.alternar();
    expect(servicio.obtenerElegido()).toBe('light');
    expect(localStorage.getItem('ks-theme')).toBe('light');
  });

  it('obtenerActual() respeta la elección explícita por sobre la preferencia del SO', () => {
    document.documentElement.setAttribute('data-theme', 'dark');
    expect(servicio.obtenerActual()).toBe('dark');
  });
});
