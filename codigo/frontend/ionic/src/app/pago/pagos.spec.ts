import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { Pagos } from './pagos';

describe('Pagos', () => {
  let service: Pagos;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Pagos);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
