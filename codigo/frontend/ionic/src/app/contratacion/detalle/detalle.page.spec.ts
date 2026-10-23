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

  it('cargar una plantilla llena la hoja de presupuesto y se envía al confirmar', () => {
    component.contratacionId = 7;
    component.plantillaElegida = 3;
    component.cargarPlantillaEnPresupuesto();
    httpMock.expectOne(`${environment.apiUrl}/calculadora/plantillas/3/items/`).flush({
      items: [{ descripcion: 'Mano de obra', categoria: 'MANO_DE_OBRA', monto: 24000 }], total: 24000,
    });
    expect(component.itemsPresupuesto.length).toBe(1);
    expect(component.totalItemsPresupuesto).toBe(24000);

    component.formularioReauth.patchValue({ password: 'clave' });
    component.confirmar();
    const req = httpMock.expectOne((r) => r.method === 'POST' && r.url.endsWith('/contrataciones/7/confirmar/'));
    expect(req.request.body.items).toEqual([{ descripcion: 'Mano de obra', categoria: 'MANO_DE_OBRA', monto: 24000 }]);
  });

  it('quitar la plantilla vuelve a pedir el monto acordado a mano', () => {
    component.itemsPresupuesto = [{ descripcion: 'x', categoria: 'OTRO', monto: 1 }];
    component.totalItemsPresupuesto = 1;
    component.quitarPlantillaDelPresupuesto();
    expect(component.itemsPresupuesto).toEqual([]);
    expect(component.plantillaElegida).toBeNull();
  });

  it('rechazar/cancelar: cada rol ve solo su botón, y una contratación ya pagada remite a soporte', () => {
    const base = { cliente: 10, proveedor: 20 } as never;
    component.contratacion = { ...(base as object), estado: 'SOLICITADA' } as never;

    component.usuarioActualId = 20; // proveedor
    expect(component.puedeRechazar).toBeTrue();
    expect(component.puedeCancelar).toBeFalse();

    component.usuarioActualId = 10; // cliente
    expect(component.puedeRechazar).toBeFalse();
    expect(component.puedeCancelar).toBeTrue();

    component.contratacion = { ...(base as object), estado: 'CONFIRMADA' } as never;
    expect(component.puedeCancelar).toBeTrue();

    component.contratacion = { ...(base as object), estado: 'EN_CURSO' } as never;
    expect(component.puedeCancelar).toBeFalse();
    expect(component.requiereSoporteParaCancelar).toBeTrue();
  });

  it('enviarCierre("cancelar") llama a la API y actualiza la contratación', () => {
    component.contratacionId = 1;
    component.enviarCierre('cancelar');

    const req = httpMock.expectOne(`${environment.apiUrl}/contrataciones/1/cancelar/`);
    expect(req.request.method).toBe('POST');
    req.flush({ id_contratacion: 1, estado: 'CANCELADA' });

    expect(component.contratacion?.estado).toBe('CANCELADA');
    expect(component.procesandoAccion).toBeFalse();
    httpMock.match(`${environment.apiUrl}/contrataciones/1/mensajes/`).forEach((r) => r.flush([]));
  });

  it('pedirReembolso() manda el motivo y deja el reembolso pendiente en la contratación', () => {
    component.contratacionId = 1;
    component.contratacion = { cliente: 10, proveedor: 20, estado: 'EN_CURSO', reembolso: null } as never;
    component.motivoReembolso = '  El proveedor no llegó  ';

    component.pedirReembolso();

    const req = httpMock.expectOne(`${environment.apiUrl}/contrataciones/1/reembolso/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ motivo: 'El proveedor no llegó' });
    req.flush({ estado: 'PENDIENTE', monto: 20000, motivo: 'CANCELACION' });

    expect((component.contratacion as unknown as { reembolso: { estado: string } }).reembolso.estado).toBe('PENDIENTE');
    expect(component.procesandoAccion).toBeFalse();
    httpMock.match(`${environment.apiUrl}/contrataciones/1/mensajes/`).forEach((r) => r.flush([]));
  });

  it('enviarCierre muestra el detalle del 409 cuando ya está pagada', () => {
    component.contratacionId = 1;
    component.enviarCierre('cancelar');

    httpMock
      .expectOne(`${environment.apiUrl}/contrataciones/1/cancelar/`)
      .flush({ detail: 'Esta contratación ya está pagada', code: 'requiere_soporte' }, { status: 409, statusText: 'Conflict' });

    expect(component.errorAccion).toContain('ya está pagada');
    expect(component.procesandoAccion).toBeFalse();
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

  it('exportarChat() pide el .txt y dispara la descarga', () => {
    component.contratacionId = 1;
    const clickSpy = spyOn(HTMLAnchorElement.prototype, 'click');

    component.exportarChat();

    expect(component.exportandoChat).toBeTrue();
    const req = httpMock.expectOne(`${environment.apiUrl}/contrataciones/1/mensajes/exportar/`);
    expect(req.request.method).toBe('GET');

    req.flush(new Blob(['Chat: prueba'], { type: 'text/plain' }));

    expect(clickSpy).toHaveBeenCalled();
    expect(component.exportandoChat).toBeFalse();
    expect(component.errorExportarChat).toBeNull();
  });

  it('exportarChat() marca un error si la descarga falla', () => {
    component.contratacionId = 1;

    component.exportarChat();

    const req = httpMock.expectOne(`${environment.apiUrl}/contrataciones/1/mensajes/exportar/`);
    req.flush(new Blob(['no autorizado'], { type: 'text/plain' }), { status: 404, statusText: 'Not Found' });

    expect(component.exportandoChat).toBeFalse();
    expect(component.errorExportarChat).toBe('No se pudo exportar el chat.');
  });

  it('exportarChat() no dispara una segunda descarga mientras la primera está en curso', () => {
    component.contratacionId = 1;

    component.exportarChat();
    component.exportarChat();

    const solicitudes = httpMock.match(`${environment.apiUrl}/contrataciones/1/mensajes/exportar/`);
    expect(solicitudes.length).toBe(1);
  });
});
