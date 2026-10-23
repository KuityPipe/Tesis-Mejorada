import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { RegistroPage } from './registro.page';
import { SharedModule } from '../shared/shared.module';

describe('RegistroPage', () => {
  let component: RegistroPage;
  let fixture: ComponentFixture<RegistroPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [RegistroPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(RegistroPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('el select de comuna arranca deshabilitado hasta elegir una región', () => {
    expect(component.formulario.controls.comuna.disabled).toBeTrue();
  });

  it('el avance de los pasos parte en 0 y el primero es el actual', () => {
    expect(component.progreso).toBe(0);
    expect(component.pasoActual).toBe(1);
  });

  it('el paso 1 se completa con los datos personales obligatorios', () => {
    component.formulario.patchValue({ rut: '12.345.678-5', nombre1: 'Ana', apellido1: 'Soto', edad: 30, telefono: '+56911112222', email: 'ana@correo.cl' });
    expect(component.pasoCompleto(1)).toBeTrue();
    expect(component.pasoActual).toBe(2);
  });

  it('mide la seguridad de la contraseña y si coinciden', () => {
    component.formulario.patchValue({ password: 'abc', password_confirm: 'abd' });
    expect(component.fuerzaClave.nivel).toBe(0);
    expect(component.clavesCoinciden).toBeFalse();
    component.formulario.patchValue({ password: 'Clave-Segura-2026', password_confirm: 'Clave-Segura-2026' });
    expect(component.fuerzaClave.nivel).toBe(4);
    expect(component.clavesCoinciden).toBeTrue();
  });

  it('rechaza un RUT con dígito verificador incorrecto y acepta uno correcto, con o sin puntos', () => {
    const rut = component.formulario.controls.rut;
    rut.setValue('12345678-9');
    expect(rut.errors?.['rut']).toBeTruthy();
    rut.setValue('12.345.678-5');
    expect(rut.errors).toBeNull();
  });

  it('el RUT se ordena al salir del campo', () => {
    component.formulario.controls.rut.setValue('12.345.678-5');
    component.ordenarRut();
    expect(component.formulario.controls.rut.value).toBe('12345678-5');
  });

  it('sin aceptar la política el paso 3 no se completa', () => {
    component.formulario.patchValue({ password: 'Clave-Segura-2026', password_confirm: 'Clave-Segura-2026', acepta_politica: false });
    expect(component.pasoCompleto(3)).toBeFalse();
    component.formulario.patchValue({ acepta_politica: true });
    expect(component.pasoCompleto(3)).toBeTrue();
  });

  it('si no se acepta la política, el mensaje lo explica en vez de decir "Campo requerido"', () => {
    component.formulario.controls.acepta_politica.markAsTouched();
    expect(component.mensajeError('acepta_politica')).toContain('política de privacidad');
  });

  it('las preguntas de impacto son opcionales: no impiden completar el registro', () => {
    expect(component.formulario.controls.situacion_laboral_previa.value).toBe('');
    expect(component.formulario.controls.situacion_laboral_previa.valid).toBeTrue();
    expect(component.formulario.controls.genero.valid).toBeTrue();
    expect(component.finalidadImpacto).toContain('medir el impacto de KeyServ en el empleo');
  });

  it('elegir el tipo de cuenta actualiza es_proveedor', () => {
    component.elegirTipo(true);
    expect(component.formulario.controls.es_proveedor.value).toBeTrue();
    component.elegirTipo(false);
    expect(component.formulario.controls.es_proveedor.value).toBeFalse();
  });
});
