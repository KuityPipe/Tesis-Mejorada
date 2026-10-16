import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';
import { FormsModule } from '@angular/forms';

import { VerificacionAlternativaPage } from './verificacion-alternativa.page';
import { SharedModule } from '../shared/shared.module';
import { EstadoVerificacionAlternativa } from './verificacion-alternativa';

describe('VerificacionAlternativaPage', () => {
  let component: VerificacionAlternativaPage;
  let fixture: ComponentFixture<VerificacionAlternativaPage>;

  const base: EstadoVerificacionAlternativa = {
    identidad_verificada: false, estado: null, advertencia: 'a', advertencia_aceptada: false,
    correo_verificado: false, documento_enviado: false, requiere_video: false, consentimiento_video: 'v',
    consentimiento_video_aceptado: false, video_enviado: false, codigo_video: '', motivo_rechazo: '',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [VerificacionAlternativaPage],
      imports: [IonicModule.forRoot(), FormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();
    fixture = TestBed.createComponent(VerificacionAlternativaPage);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('calcula el paso según el estado del servidor', () => {
    component.estado = base;
    expect(component.paso).toBe('advertencia');
    component.estado = { ...base, advertencia_aceptada: true };
    expect(component.paso).toBe('codigo');
    component.estado = { ...base, advertencia_aceptada: true, correo_verificado: true };
    expect(component.paso).toBe('documento');
    component.estado = { ...base, estado: 'PENDIENTE_REVISION', advertencia_aceptada: true, correo_verificado: true };
    expect(component.paso).toBe('revision');
    component.estado = { ...base, identidad_verificada: true };
    expect(component.paso).toBe('verificada');
  });

  it('con video exigido, después del documento pide el video y recién con ambos pasa a revisión', () => {
    const conVideo = { ...base, requiere_video: true, advertencia_aceptada: true, correo_verificado: true, codigo_video: '4821' };
    component.estado = conVideo;
    expect(component.paso).toBe('documento');
    component.estado = { ...conVideo, documento_enviado: true };
    expect(component.paso).toBe('video');
    // una solicitud antigua que quedó "en revisión" sin video debe poder completarlo
    component.estado = { ...conVideo, documento_enviado: true, estado: 'PENDIENTE_REVISION' };
    expect(component.paso).toBe('video');
    component.estado = { ...conVideo, documento_enviado: true, video_enviado: true, estado: 'PENDIENTE_REVISION' };
    expect(component.paso).toBe('revision');
  });

  it('el primer paso exige aceptar también la grabación solo cuando el servidor pide video', () => {
    component.aceptoAdvertencia = true;
    component.estado = { ...base, requiere_video: true };
    expect(component.puedeIniciar).toBeFalse();
    component.aceptoVideo = true;
    expect(component.puedeIniciar).toBeTrue();
    component.estado = { ...base, requiere_video: false };
    component.aceptoVideo = false;
    expect(component.puedeIniciar).toBeTrue();
  });
});
