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
    correo_verificado: false, documento_enviado: false, motivo_rechazo: '',
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
});
