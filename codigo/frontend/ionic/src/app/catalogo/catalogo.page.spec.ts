import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { CatalogoPage } from './catalogo.page';
import { SharedModule } from '../shared/shared.module';
import { Ubicacion } from '../core/ubicacion';

describe('CatalogoPage', () => {
  let component: CatalogoPage;
  let fixture: ComponentFixture<CatalogoPage>;
  let ubicacion: jasmine.SpyObj<Ubicacion>;

  beforeEach(async () => {
    ubicacion = jasmine.createSpyObj('Ubicacion', ['posicionActual']);

    await TestBed.configureTestingModule({
      declarations: [CatalogoPage],
      // FormsModule: la barra de filtros usa [(ngModel)] en ion-searchbar/ion-select (ver catalogo.page.html) — sin importarlo acá, Angular no reconoce el binding y tira NG0303 en consola (el test igual pasa, pero con ruido).
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, FormsModule, SharedModule],
      providers: [{ provide: Ubicacion, useValue: ubicacion }],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogoPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('usarMiUbicacion carga lat/lng en los filtros cuando hay posición', async () => {
    ubicacion.posicionActual.and.resolveTo({ lat: -33.4237, lng: -70.6112 });
    spyOn(component as any, 'aplicarFiltros');

    await component.usarMiUbicacion();

    expect(component.ubicacionActiva).toBeTrue();
    expect(component.filtros.lat).toBe(-33.4237);
    expect(component.filtros.lng).toBe(-70.6112);
  });

  it('usarMiUbicacion no activa el filtro de radio si el usuario niega el permiso', async () => {
    ubicacion.posicionActual.and.resolveTo(null);

    await component.usarMiUbicacion();

    expect(component.ubicacionActiva).toBeFalse();
    expect(component.filtros.lat).toBeUndefined();
  });

  it('quitarUbicacion saca lat/lng/radio_km — el radio es un filtro, no un límite duro', () => {
    component.ubicacionActiva = true;
    component.filtros = { orden: 'cercania', lat: -33.4, lng: -70.6, radio_km: 6 };
    spyOn(component as any, 'aplicarFiltros');

    component.quitarUbicacion();

    expect(component.ubicacionActiva).toBeFalse();
    expect(component.filtros.lat).toBeUndefined();
    expect(component.filtros.lng).toBeUndefined();
    expect(component.filtros.radio_km).toBeUndefined();
    expect(component.filtros.orden).toBe('recientes');
  });
});
