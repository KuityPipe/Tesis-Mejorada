import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router } from '@angular/router';
import { IonicModule } from '@ionic/angular';

import { NoEncontradoPage } from './no-encontrado.page';
import { SharedModule } from '../shared/shared.module';

describe('NoEncontradoPage', () => {
  let component: NoEncontradoPage;
  let fixture: ComponentFixture<NoEncontradoPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [NoEncontradoPage],
      imports: [IonicModule.forRoot(), FormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(NoEncontradoPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('muestra un único h1 que explica el error', () => {
    const titulos = fixture.nativeElement.querySelectorAll('h1');
    expect(titulos.length).toBe(1);
    expect(titulos[0].textContent).toContain('No encontramos');
  });

  it('buscar lleva al catálogo con el texto escrito', () => {
    const navegar = spyOn(TestBed.inject(Router), 'navigate');
    component.q = '  gasfitería ';
    component.buscar();
    expect(navegar).toHaveBeenCalledWith(['/catalogo'], { queryParams: { q: 'gasfitería' } });
  });
});
