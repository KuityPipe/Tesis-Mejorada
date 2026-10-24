import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { InicioPage } from './inicio.page';
import { SharedModule } from '../shared/shared.module';

describe('InicioPage', () => {
  let component: InicioPage;
  let fixture: ComponentFixture<InicioPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [InicioPage],
      // FormsModule: la búsqueda rápida usa [(ngModel)] en ion-searchbar (ver inicio.page.html).
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, FormsModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(InicioPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
  });

  afterEach(() => fixture.destroy());

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('explica la vía sin historial sin prometer más de lo que hace (ADR 0006)', () => {
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Empieza aunque nunca hayas trabajado con boleta');
    expect(texto).toContain('revisa una persona del equipo');
    expect(texto).toContain('no una consulta al Registro Civil');
    // El aviso de privacidad ya no afirma "0 fotos de tu rostro guardadas" (la vía de cédula y video sí guarda un documento).
    expect(texto).not.toContain('de tu rostro guardadas');
  });
});
