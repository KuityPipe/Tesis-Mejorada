import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { AsistenteComponent } from './asistente';

describe('AsistenteComponent', () => {
  let component: AsistenteComponent;
  let fixture: ComponentFixture<AsistenteComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AsistenteComponent],
      imports: [IonicModule.forRoot(), FormsModule, HttpClientTestingModule, RouterTestingModule],
    }).compileComponents();
    fixture = TestBed.createComponent(AsistenteComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  it('arranca cerrado, con el botón flotante accesible', () => {
    expect(component.abierto).toBeFalse();
    const boton: HTMLButtonElement = fixture.nativeElement.querySelector('.ks-asistente-boton');
    expect(boton.getAttribute('aria-label')).toContain('Abrir');
    expect(fixture.nativeElement.querySelector('.ks-asistente-panel')).toBeNull();
  });

  it('al abrir muestra el aviso de IA externa', () => {
    component.alternar();
    fixture.detectChanges();
    const aviso = fixture.nativeElement.querySelector('.ks-asistente-aviso');
    expect(aviso.textContent).toContain('inteligencia artificial');
  });

  it('Escape cierra el panel', () => {
    component.abierto = true;
    component.cerrarConEscape();
    expect(component.abierto).toBeFalse();
  });

  it('no envía mensajes vacíos', () => {
    component.texto = '   ';
    component.enviar();
    http.expectNone((r) => r.url.endsWith('/asistente/'));
  });

  it('envía solo el texto de la conversación y muestra la respuesta con sus servicios', () => {
    component.texto = 'Busco un gasfíter';
    component.enviar();
    const req = http.expectOne((r) => r.method === 'POST' && r.url.endsWith('/asistente/'));
    expect(req.request.body.mensajes[req.request.body.mensajes.length - 1]).toEqual({ rol: 'user', texto: 'Busco un gasfíter' });
    expect(Object.keys(req.request.body)).toEqual(['mensajes']);
    req.flush({
      respuesta: 'Mira estos servicios.',
      servicios: [{ id: 3, titulo: 'Gasfitería', categoria: 'Gasfitería', precio: 25000, comuna: 'Santiago', puntuacion: 4.5 }],
      origen: 'ia', aviso_ia: 'aviso', sugerencias: [],
    });
    expect(component.enviando).toBeFalse();
    expect(component.burbujas[component.burbujas.length - 1].servicios?.length).toBe(1);
    expect(component.precio(component.burbujas[component.burbujas.length - 1].servicios![0])).toContain('25');
  });

  it('muestra un mensaje claro si el servidor limita el uso (429)', () => {
    component.texto = 'hola';
    component.enviar();
    http.expectOne((r) => r.url.endsWith('/asistente/')).flush({}, { status: 429, statusText: 'Too Many Requests' });
    expect(component.error).toContain('muchas veces');
    expect(component.enviando).toBeFalse();
  });

  it('un error genérico no deja el chat bloqueado', () => {
    component.texto = 'hola';
    component.enviar();
    http.expectOne((r) => r.url.endsWith('/asistente/')).error(new ProgressEvent('error'));
    expect(component.error).toContain('No pudimos responder');
    expect(component.enviando).toBeFalse();
  });
});
