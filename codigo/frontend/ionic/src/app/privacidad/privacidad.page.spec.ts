import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { PrivacidadPage } from './privacidad.page';
import { SharedModule } from '../shared/shared.module';

describe('PrivacidadPage', () => {
  let component: PrivacidadPage;
  let fixture: ComponentFixture<PrivacidadPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PrivacidadPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(PrivacidadPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('el índice apunta a una sección que existe en la página', () => {
    const ids = Array.from(fixture.nativeElement.querySelectorAll('section.ks-priv-seccion')).map((s) => (s as HTMLElement).id);
    for (const item of component.indice) {
      expect(ids).toContain(item.id);
    }
  });

  it('conserva los plazos de retención de la política', () => {
    const valores = component.plazos.map((p) => `${p.valor} ${p.unidad}`);
    expect(valores).toContain('180 días');
    expect(valores).toContain('90 días');
  });
});
