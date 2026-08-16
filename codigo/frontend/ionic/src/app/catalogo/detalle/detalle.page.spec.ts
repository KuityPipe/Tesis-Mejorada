import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { DetallePage } from './detalle.page';
import { SharedModule } from '../../shared/shared.module';
import { environment } from '../../../environments/environment';

const proveedorBase = {
  id_usuario: 1,
  nombre_usuario: 'Camila',
  apellido_usuario: 'Rojas',
  foto_perfil: null,
  comuna: 'Ñuñoa',
  region: 'Región Metropolitana',
  puntuacion_promedio: null,
  total_valoraciones: 0,
};

const publicacionBase = {
  id_publicacion: 1,
  titulo: 'Jardinería',
  sub_titulo: null,
  descripcion_publicacion: null,
  categoria: null,
  precio: null,
  fecha_publicacion: '2026-08-16T00:00:00Z',
  imagenes: [],
  resenas: [],
};

describe('DetallePage', () => {
  let component: DetallePage;
  let fixture: ComponentFixture<DetallePage>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [DetallePage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
      providers: [{ provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ id: '1' }) } } }],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DetallePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    httpMock.expectOne(`${environment.apiUrl}/publicaciones/1/`).flush({ ...publicacionBase, proveedor: { ...proveedorBase, latitud: null, longitud: null } });
    expect(component).toBeTruthy();
  });

  it('arma el mini-mapa y el link de Google Maps cuando la comuna del proveedor está geocodificada', () => {
    httpMock.expectOne(`${environment.apiUrl}/publicaciones/1/`).flush({
      ...publicacionBase,
      proveedor: { ...proveedorBase, latitud: -33.4558, longitud: -70.598 },
    });

    expect(component.enlaceGoogleMaps).toBe('https://www.google.com/maps?q=-33.4558,-70.598');
    expect(component.mapaUrl).toBeTruthy();
  });

  it('no arma el mini-mapa si la comuna todavía no está geocodificada', () => {
    httpMock.expectOne(`${environment.apiUrl}/publicaciones/1/`).flush({
      ...publicacionBase,
      proveedor: { ...proveedorBase, latitud: null, longitud: null },
    });

    expect(component.enlaceGoogleMaps).toBeNull();
    expect(component.mapaUrl).toBeNull();
  });
});
