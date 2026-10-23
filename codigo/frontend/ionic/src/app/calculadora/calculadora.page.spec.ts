import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { CalculadoraPage } from './calculadora.page';
import { SharedModule } from '../shared/shared.module';
import { Calculadora, valorHora } from '../core/calculadora';
import { environment } from '../../environments/environment';

describe('valorHora', () => {
  it('divide el ingreso deseado por las horas cobrables y redondea hacia arriba', () => {
    expect(valorHora(800000, 80)).toBe(10000);
    expect(valorHora(1000000, 90)).toBe(11112);
  });

  it('devuelve 0 si falta un dato', () => {
    expect(valorHora(0, 80)).toBe(0);
    expect(valorHora(800000, 0)).toBe(0);
    expect(valorHora(NaN, 10)).toBe(0);
  });
});

describe('CalculadoraPage', () => {
  let component: CalculadoraPage;
  let fixture: ComponentFixture<CalculadoraPage>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    localStorage.removeItem('ks_visitante_calculadora');
    await TestBed.configureTestingModule({
      declarations: [CalculadoraPage],
      imports: [IonicModule.forRoot(), FormsModule, ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(CalculadoraPage);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  it('should create y pide la configuración sin necesitar sesión', () => {
    expect(component).toBeTruthy();
    const req = httpMock.expectOne(`${environment.apiUrl}/calculadora/config/`);
    req.flush({ retencion_porcentaje: 16, imprevistos_porcentaje: 10, ganancia_porcentaje: 15, comision_tramos: [], comision_minima: 1000 });
    httpMock.expectOne(`${environment.apiUrl}/calculadora/calcular/`).flush({});
    expect(component.autenticado).toBeFalse();
    httpMock.expectNone(`${environment.apiUrl}/calculadora/plantillas/`);
  });

  it('arma el cuerpo con números no negativos, al menos una persona y los valores por defecto', () => {
    component.materiales.at(0).patchValue({ descripcion: ' Cañería ', cantidad: 3, precio_unitario: 2500, reutilizado: true });
    component.formulario.patchValue({ horas: 3, valor_hora: 8000, personas: 0, km_ida_vuelta: -5, documento: 'BOLETA_HONORARIOS' });
    const d = component.datos();
    expect(d.materiales[0]).toEqual({ descripcion: 'Cañería', cantidad: 3, unidad: '', precio_unitario: 2500, reutilizado: true });
    expect(d.mano_obra).toEqual({ horas: 3, valor_hora: 8000, personas: 1 });
    expect(d.traslado.km_ida_vuelta).toBe(0);
    expect(d.imprevistos_pct).toBe(10);
    expect(d.ganancia_pct).toBe(15);
    expect(d.documento).toBe('BOLETA_HONORARIOS');
  });

  it('el ayudante del valor por hora lo copia a la mano de obra', () => {
    component.ayudante.patchValue({ ingreso_mensual: 900000, horas_cobrables: 90 });
    expect(component.valorHoraSugerido).toBe(10000);
    component.usarValorHora();
    expect(component.formulario.controls.valor_hora.value).toBe(10000);
  });

  it('nunca deja la lista de materiales vacía', () => {
    component.quitarMaterial(0);
    expect(component.materiales.length).toBe(1);
    component.agregarMaterial();
    expect(component.materiales.length).toBe(2);
  });

  it('muestra el mensaje del servidor si los datos no son válidos', () => {
    component.calcular();
    const reqs = httpMock.match(`${environment.apiUrl}/calculadora/calcular/`);
    reqs[reqs.length - 1].flush({ detail: 'Mano de obra, horas: debe ser un número positivo.' }, { status: 400, statusText: 'Bad Request' });
    expect(component.error).toContain('Mano de obra');
  });

  it('el identificador de visitante es estable y no se parece a un dato personal', () => {
    const api = TestBed.inject(Calculadora);
    const primero = api.visitante();
    expect(api.visitante()).toBe(primero);
    expect(primero.length).toBeGreaterThanOrEqual(8);
    expect(primero).not.toContain('@');
  });

  it('exportar pide el archivo con el identificador anónimo en el cuerpo', () => {
    spyOn(URL, 'createObjectURL').and.returnValue('blob:x');
    component.exportar('xlsx');
    const req = httpMock.expectOne(`${environment.apiUrl}/calculadora/exportar/xlsx/`);
    expect(req.request.body.visitante).toBeTruthy();
    expect(req.request.responseType).toBe('blob');
    req.flush(new Blob(['x']));
    expect(component.exportando).toBeNull();
  });
});
