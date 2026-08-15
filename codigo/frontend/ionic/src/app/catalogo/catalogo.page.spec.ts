import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { CatalogoPage } from './catalogo.page';
import { SharedModule } from '../shared/shared.module';

describe('CatalogoPage', () => {
  let component: CatalogoPage;
  let fixture: ComponentFixture<CatalogoPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CatalogoPage],
      // FormsModule: la barra de filtros usa [(ngModel)] en ion-searchbar/ion-select (ver catalogo.page.html) — sin importarlo acá, Angular no reconoce el binding y tira NG0303 en consola (el test igual pasa, pero con ruido).
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, FormsModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogoPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
