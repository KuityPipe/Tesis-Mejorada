import { TestBed } from '@angular/core/testing';

import { VerifExitoComponent } from './verif-exito';

describe('VerifExitoComponent', () => {
  it('anuncia el mensaje como estado y dibuja la animación como decorativa', () => {
    TestBed.configureTestingModule({ declarations: [VerifExitoComponent] });
    const fixture = TestBed.createComponent(VerifExitoComponent);
    fixture.componentInstance.mensaje = 'Listo';
    fixture.detectChanges();
    const raiz: HTMLElement = fixture.nativeElement;
    expect(raiz.querySelector('[role="status"]')?.textContent).toContain('Listo');
    expect(raiz.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });
});
