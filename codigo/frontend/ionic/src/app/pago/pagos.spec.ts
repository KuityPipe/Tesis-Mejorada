import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { Pagos } from './pagos';
import { environment } from '../../environments/environment';

describe('Pagos', () => {
  let service: Pagos;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Pagos);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('metodosDisponibles() pide /pagos/metodos/', () => {
    const http = TestBed.inject(HttpTestingController);
    let resultado: unknown;
    service.metodosDisponibles().subscribe((r) => (resultado = r));
    const req = http.expectOne(`${environment.apiUrl}/pagos/metodos/`);
    expect(req.request.method).toBe('GET');
    req.flush({ webpay: true, khipu: false, flow: true, mercadopago: true });
    expect(resultado).toEqual({ webpay: true, khipu: false, flow: true, mercadopago: true });
  });

  it('iniciarExterno() y estadoExterno() usan la ruta genérica del método', () => {
    const http = TestBed.inject(HttpTestingController);
    service.iniciarExterno('mercadopago', 7).subscribe();
    const iniciar = http.expectOne(`${environment.apiUrl}/contrataciones/7/pagos/mercadopago/iniciar/`);
    expect(iniciar.request.method).toBe('POST');
    iniciar.flush({ payment_url: 'https://pago.test' });

    service.estadoExterno('flow', 7).subscribe();
    const estado = http.expectOne(`${environment.apiUrl}/contrataciones/7/pagos/flow/estado/`);
    expect(estado.request.method).toBe('GET');
    estado.flush({ aprobado: false, mensaje: '' });
  });
});
