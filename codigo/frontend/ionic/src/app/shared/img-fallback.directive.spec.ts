import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { ImgFallbackDirective } from './img-fallback.directive';

@Component({ template: '<img src="assets/no-existe.png" alt="x" />', standalone: false })
class PruebaComponent {}

describe('ImgFallbackDirective', () => {
  it('marca como rota una imagen que no carga, para ocultarla sin romper el diseño', () => {
    TestBed.configureTestingModule({ declarations: [PruebaComponent, ImgFallbackDirective] });
    const fixture = TestBed.createComponent(PruebaComponent);
    fixture.detectChanges();
    const img: HTMLImageElement = fixture.nativeElement.querySelector('img');
    img.dispatchEvent(new Event('error'));
    expect(img.classList.contains('ks-img-rota')).toBeTrue();
  });
});
