import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { Contrataciones } from './contrataciones';

describe('Contrataciones', () => {
  let service: Contrataciones;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Contrataciones);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
