import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { PreferenciasPage } from './preferencias.page';
import { SharedModule } from '../shared/shared.module';

describe('PreferenciasPage', () => {
  let component: PreferenciasPage;
  let fixture: ComponentFixture<PreferenciasPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PreferenciasPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(PreferenciasPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('pide el estado de derechos al iniciar', () => {
    const http = TestBed.inject(HttpTestingController);
    const reqs = http.match((r) => r.url.endsWith('/auth/derechos/'));
    expect(reqs.length).toBeGreaterThan(0);
  });

  it('no envía una rectificación vacía', () => {
    const http = TestBed.inject(HttpTestingController);
    component.detalleRectificacion = '   ';
    component.enviarRectificacion();
    http.expectNone((r) => r.method === 'POST' && r.url.endsWith('/auth/derechos/'));
  });

  it('la oposición a la biometría manda finalidad "biometria"', () => {
    const http = TestBed.inject(HttpTestingController);
    component.oponerseABiometria();
    const req = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/auth/derechos/'));
    expect(req.request.body.tipo).toBe('OPOSICION');
    expect(req.request.body.finalidad).toBe('biometria');
  });

  it('cerrar sesiones: pedir el código llama al backend y pasa al paso del código', () => {
    const http = TestBed.inject(HttpTestingController);
    component.pedirCodigoSesiones();
    const req = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/auth/cerrar-sesiones/codigo/'));
    req.flush({ detail: 'Te enviamos un código a tu correo.', vence_en_minutos: 10 });
    expect(component.codigoSesionesEnviado).toBeTrue();
    expect(component.errorSesiones).toBeNull();
  });

  it('cerrar sesiones: no manda un código que no tiene 6 dígitos', () => {
    const http = TestBed.inject(HttpTestingController);
    component.codigoSesiones = '12ab';
    component.cerrarTodasLasSesiones();
    http.expectNone((r) => r.method === 'POST' && r.url.endsWith('/auth/cerrar-sesiones/'));
  });

  it('cerrar sesiones: un código incorrecto muestra el error y no cierra la sesión local', () => {
    const http = TestBed.inject(HttpTestingController);
    component.codigoSesiones = '123456';
    component.cerrarTodasLasSesiones();
    const req = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/auth/cerrar-sesiones/'));
    expect(req.request.body).toEqual({ codigo: '123456' });
    req.flush({ detail: 'Código incorrecto.' }, { status: 400, statusText: 'Bad Request' });
    expect(component.errorSesiones).toBe('Código incorrecto.');
    expect(component.cerrandoSesiones).toBeFalse();
  });

  it('alterna el bloqueo contra el valor actual', () => {
    const http = TestBed.inject(HttpTestingController);
    component.derechos = { tratamiento_bloqueado: false, solicitudes: [] };
    component.alternarBloqueo();
    const req = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/auth/bloqueo-tratamiento/'));
    expect(req.request.body).toEqual({ bloquear: true });
  });
});
