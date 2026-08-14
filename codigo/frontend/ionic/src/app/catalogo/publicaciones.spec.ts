import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { Publicaciones } from './publicaciones';

describe('Publicaciones', () => {
  let service: Publicaciones;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Publicaciones);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
