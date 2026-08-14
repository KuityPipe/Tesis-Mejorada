import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { Rostro } from './rostro';

describe('Rostro', () => {
  let service: Rostro;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(Rostro);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
