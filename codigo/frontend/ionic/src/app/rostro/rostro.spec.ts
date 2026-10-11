import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { Rostro } from './rostro';
import { environment } from '../../environments/environment';

describe('Rostro', () => {
  let service: Rostro;
  let http: HttpTestingController;
  const url = `${environment.apiUrl}/auth/rostro/consentimiento/`;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Rostro);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('consulta el consentimiento con GET', () => {
    service.consentimiento().subscribe();
    http.expectOne({ url, method: 'GET' }).flush({ vigente: false, version: 'v', texto: 't' });
  });

  it('otorga el consentimiento con POST', () => {
    service.otorgarConsentimiento().subscribe();
    http.expectOne({ url, method: 'POST' }).flush({ vigente: true, version: 'v', texto: 't' });
  });

  it('revoca el consentimiento con DELETE', () => {
    service.revocarConsentimiento().subscribe();
    http.expectOne({ url, method: 'DELETE' }).flush({ vigente: false, version: 'v', texto: 't' });
  });
});
