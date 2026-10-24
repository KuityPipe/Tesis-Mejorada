import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
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

  it('"Confirmar contratación" lleva a la calculadora de ese trabajo', () => {
    const router = TestBed.inject(Router);
    const navegar = spyOn(router, 'navigate').and.resolveTo(true);
    component.contratacionId = 29;
    component.irACalculadora();
    expect(navegar).toHaveBeenCalledWith(['/calculadora'], { queryParams: { contratacion: 29 } });
  });

  it('el proveedor ve "Confirmar contratación" como un botón hacia la calculadora, sin pedir la contraseña aquí', () => {
    component.usuarioActualId = 20;
    component.cargando = false;
    component.contratacion = {
      cliente: 10, proveedor: 20, estado: 'SOLICITADA', pago: null, items_presupuesto: [], boleta: null, historial: [],
      publicacion_imagenes: [], desglose_pago: null,
    } as never;
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Confirmar contratación');
    expect(el.textContent).toContain('calculadora de este trabajo');
    expect(el.querySelector('ion-input[label="Confirma tu contraseña"]')).toBeNull();
  });

  it('el proveedor solo registra la boleta de un trabajo pagado', () => {
    component.contratacion = { cliente: 10, proveedor: 20, estado: 'EN_CURSO', pago: { estado: 'PAGADO' } } as never;
    component.usuarioActualId = 20;
    expect(component.puedeRegistrarBoleta).toBeTrue();
    component.usuarioActualId = 10; // el cliente no registra
    expect(component.puedeRegistrarBoleta).toBeFalse();
    component.usuarioActualId = 20;
    component.contratacion = { cliente: 10, proveedor: 20, estado: 'CONFIRMADA', pago: { estado: 'PENDIENTE' } } as never;
    expect(component.puedeRegistrarBoleta).toBeFalse();
  });

  it('guardar la boleta manda el folio y la respuesta sobre la primera boleta', () => {
    component.contratacionId = 7;
    component.formularioBoleta.setValue({ folio: ' 1234 ', fecha_emision: '2026-10-20', es_primera_boleta: 'SI' });
    component.guardarBoleta();
    const req = httpMock.expectOne((r) => r.method === 'PUT' && r.url.endsWith('/contrataciones/7/boleta/'));
    expect(req.request.body).toEqual({ folio: '1234', fecha_emision: '2026-10-20', es_primera_boleta: 'SI' });
  });

  it('no manda un folio con letras ni sin responder si es la primera boleta', () => {
    component.contratacionId = 7;
    component.formularioBoleta.setValue({ folio: '12ab', fecha_emision: '', es_primera_boleta: '' });
    component.guardarBoleta();
    httpMock.expectNone((r) => r.method === 'PUT' && r.url.endsWith('/boleta/'));
    expect(component.formularioBoleta.controls.folio.errors?.['pattern']).toBeTruthy();
  });

  it('muestra los errores que devuelve el servidor por campo', () => {
    component.contratacionId = 7;
    component.formularioBoleta.setValue({ folio: '55', fecha_emision: '', es_primera_boleta: 'SI' });
    component.guardarBoleta();
    httpMock.expectOne((r) => r.method === 'PUT' && r.url.endsWith('/boleta/')).flush(
      { es_primera_boleta: ['Ya marcaste otra boleta como tu primera.'] }, { status: 400, statusText: 'Bad Request' },
    );
    expect(component.erroresBoleta['es_primera_boleta']).toEqual(['Ya marcaste otra boleta como tu primera.']);
    expect(component.guardandoBoleta).toBeFalse();
  });

  it('quien contrata ve cómo se calcula su pago y un agradecimiento', () => {
    component.usuarioActualId = 10;
    component.tramosComision = '6 % hasta $50.000 y 4 % sobre eso';
    component.contratacion = {
      cliente: 10, proveedor: 20, estado: 'CONFIRMADA', pago: null, items_presupuesto: [], boleta: null, historial: [],
      publicacion_imagenes: [], desglose_pago: { monto_servicio: 20000, comision_porcentaje: 6, comision: 1200, total: 21200 },
    } as never;
    component.cargando = false;
    fixture.detectChanges();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Cómo se calcula tu pago');
    expect(texto).toContain('6 % hasta $50.000 y 4 % sobre eso');
    expect(texto).toMatch(/21[.,]200/);
    expect(texto).toContain('Gracias por elegir KeyServ');
    expect(texto).toContain('ambiente sano');
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
