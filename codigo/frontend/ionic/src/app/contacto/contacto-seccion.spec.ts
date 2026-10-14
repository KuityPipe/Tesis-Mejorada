import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { IonicModule } from '@ionic/angular';

import { ContactoSeccionComponent } from './contacto-seccion';
import { Contacto } from './contacto';
import { SharedModule } from '../shared/shared.module';

describe('ContactoSeccionComponent', () => {
  let component: ContactoSeccionComponent;
  let fixture: ComponentFixture<ContactoSeccionComponent>;
  let enviar: jasmine.Spy;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(ContactoSeccionComponent);
    component = fixture.componentInstance;
    enviar = spyOn(TestBed.inject(Contacto), 'enviar').and.returnValue(of({ detalle: 'ok' }));
    fixture.detectChanges();
  });

  const llenar = () => {
    component.formulario.patchValue({ asunto_consulta: 'Quiero ofrecer mis servicios', nombre_contacto: 'Ana', email_contacto: 'ana@correo.cl', descripcion: 'Soy gasfiter en Maipú.' });
  };

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('sin asunto no se envía y el mensaje lo explica', () => {
    component.formulario.patchValue({ nombre_contacto: 'Ana', email_contacto: 'ana@correo.cl', descripcion: 'Hola' });
    component.formulario.controls.asunto_consulta.markAsTouched();
    component.enviar();
    expect(enviar).not.toHaveBeenCalled();
    expect(component.mensajeError('asunto_consulta')).toBe('Escribe un asunto.');
  });

  it('el teléfono opcional se agrega al final del mensaje y no se manda como campo aparte', () => {
    llenar();
    component.formulario.patchValue({ telefono_contacto: '+56 9 1234 5678' });
    component.enviar();
    const datos = enviar.calls.mostRecent().args[0] as Record<string, string>;
    expect(datos['descripcion']).toBe('Soy gasfiter en Maipú.\n\nTeléfono de contacto: +56 9 1234 5678');
    expect(datos['telefono_contacto']).toBeUndefined();
    expect(datos['asunto_consulta']).toBe('Quiero ofrecer mis servicios');
  });

  it('sin teléfono el mensaje se envía tal cual', () => {
    llenar();
    component.enviar();
    expect((enviar.calls.mostRecent().args[0] as Record<string, string>)['descripcion']).toBe('Soy gasfiter en Maipú.');
  });

  it('tras enviar muestra la confirmación y deja volver al formulario', () => {
    llenar();
    component.enviar();
    expect(component.enviadoOk).toBeTrue();
    component.enviarOtro();
    expect(component.enviadoOk).toBeFalse();
  });

  it('rechaza un teléfono que no parece un teléfono', () => {
    component.formulario.controls.telefono_contacto.setValue('hola');
    component.formulario.controls.telefono_contacto.markAsTouched();
    expect(component.mensajeError('telefono_contacto')).toContain('número válido');
  });
});
