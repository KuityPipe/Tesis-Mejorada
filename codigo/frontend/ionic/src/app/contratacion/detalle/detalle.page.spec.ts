import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { DetallePage } from './detalle.page';
import { SharedModule } from '../../shared/shared.module';
import { Mensaje } from '../../contrataciones/contrataciones';
import { environment } from '../../../environments/environment';

const mensajeBase: Mensaje = {
  id_mensaje: 1,
  contenido: 'Hola',
  fecha_envio: '2026-08-16T12:00:00Z',
  usuario: 10,
  usuario_nombre: 'Camila',
  imagen_url: null,
};

describe('DetallePage', () => {
  let component: DetallePage;
  let fixture: ComponentFixture<DetallePage>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [DetallePage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(DetallePage);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('esPropio() distingue el mensaje del usuario actual del de la contraparte', () => {
    component.usuarioActualId = 10;
    expect(component.esPropio(mensajeBase)).toBeTrue();
    expect(component.esPropio({ ...mensajeBase, usuario: 99 })).toBeFalse();
  });

  it('alElegirImagenMensaje() guarda el archivo y arma una previsualización; quitarImagenMensaje() la limpia', () => {
    const archivo = new File(['contenido'], 'foto.jpg', { type: 'image/jpeg' });
    const evento = { target: { files: [archivo], value: '' } } as unknown as Event;

    component.alElegirImagenMensaje(evento);

    expect(component.imagenMensaje).toBe(archivo);
    expect(component.previsualizacionImagenMensaje).toMatch(/^blob:/);

    component.quitarImagenMensaje();

    expect(component.imagenMensaje).toBeNull();
    expect(component.previsualizacionImagenMensaje).toBeNull();
  });

  it('insertarEmoji() agrega el emoji al final del texto ya escrito', () => {
    component.formularioMensaje.controls.contenido.setValue('Quedó ');

    component.insertarEmoji('👍');

    expect(component.formularioMensaje.controls.contenido.value).toBe('Quedó 👍');
  });

  it('puedeEnviarMensaje: false sin texto ni foto, true con solo texto, true con solo foto', () => {
    expect(component.puedeEnviarMensaje).toBeFalse();

    component.formularioMensaje.controls.contenido.setValue('  ');
    expect(component.puedeEnviarMensaje).toBeFalse(); // solo espacios no cuenta

    component.formularioMensaje.controls.contenido.setValue('Hola');
    expect(component.puedeEnviarMensaje).toBeTrue();

    component.formularioMensaje.controls.contenido.setValue('');
    component.imagenMensaje = new File(['x'], 'foto.jpg', { type: 'image/jpeg' });
    expect(component.puedeEnviarMensaje).toBeTrue();
  });

  it('enviarMensaje() manda un FormData con la foto adjunta y limpia la previsualización al terminar', () => {
    component.contratacionId = 1;
    component.usuarioActualId = 10;
    const archivo = new File(['x'], 'foto.jpg', { type: 'image/jpeg' });
    component.imagenMensaje = archivo;
    component.previsualizacionImagenMensaje = 'blob:algo';
    component.formularioMensaje.controls.contenido.setValue('Mira');

    component.enviarMensaje();

    const req = httpMock.expectOne(`${environment.apiUrl}/contrataciones/1/mensajes/`);
    expect(req.request.body instanceof FormData).toBeTrue();
    const body = req.request.body as FormData;
    expect(body.get('contenido')).toBe('Mira');
    expect(body.get('imagen')).toBe(archivo);

    req.flush({ ...mensajeBase, id_mensaje: 2, contenido: 'Mira', usuario: 10 });

    expect(component.mensajes.length).toBe(1);
    expect(component.imagenMensaje).toBeNull();
    expect(component.previsualizacionImagenMensaje).toBeNull();
    expect(component.formularioMensaje.controls.contenido.value).toBe('');
  });

  it('enviarMensaje() no hace nada si no hay texto ni foto', () => {
    component.contratacionId = 1;
    component.formularioMensaje.controls.contenido.setValue('');
    component.imagenMensaje = null;

    component.enviarMensaje();

    httpMock.expectNone(`${environment.apiUrl}/contrataciones/1/mensajes/`);
    expect(component.mensajes.length).toBe(0);
  });
});
