import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { Catalogos } from './catalogos';

describe('Catalogos', () => {
  let service: Catalogos;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Catalogos);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
