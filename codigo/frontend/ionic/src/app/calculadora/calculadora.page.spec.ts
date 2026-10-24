import { ComponentFixture, TestBed, discardPeriodicTasks, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router } from '@angular/router';
import { IonicModule } from '@ionic/angular';

import { CalculadoraPage, ESPERA_AYUDA_MS } from './calculadora.page';
import { SharedModule } from '../shared/shared.module';
import { Calculadora, describirTramos, valorHora } from '../core/calculadora';
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

describe('describirTramos', () => {
  it('escribe los tramos como los aplica el servidor', () => {
    expect(describirTramos([[50000, 6], [200000, 5], [500000, 4.5], [null, 4]])).toBe('6 % hasta $50.000, 5 % hasta $200.000, 4,5 % hasta $500.000 y 4 % sobre eso');
    expect(describirTramos([[null, 5]])).toBe('5 % sobre eso');
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

  it('arranca en modo normal y manda el precio simple; el modo de costos es la otra opción', () => {
    expect(component.modo).toBe('simple');
    component.formulario.patchValue({ precio_simple: 30000, documento: 'BOLETA_HONORARIOS' });
    expect(component.datos().modo).toBe('simple');
    expect(component.datos().precio_simple).toBe(30000);
    component.formulario.controls.modo.setValue('costos');
    expect(component.modo).toBe('costos');
    expect(component.datos().modo).toBe('costos');
  });

  it('cargar una plantilla cambia al modo de costos', () => {
    component.cargarPlantilla({ id_plantilla: 1, nombre: 'x', tipo_trabajo: '', actualizada_en: '', datos: component.datos() });
    expect(component.modo).toBe('costos');
  });

  it('imprevistos y ganancia son opcionales: apagados se mandan en 0', () => {
    expect(component.datos().imprevistos_pct).toBe(10);
    expect(component.datos().ganancia_pct).toBe(15);
    component.formulario.patchValue({ usar_imprevistos: false, usar_ganancia: false });
    expect(component.datos().imprevistos_pct).toBe(0);
    expect(component.datos().ganancia_pct).toBe(0);
  });

  it('en el modo de costos cada opción se explica en la pantalla', () => {
    component.vista = 'todo';
    component.formulario.controls.modo.setValue('costos');
    fixture.detectChanges();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Sumar imprevistos');
    expect(texto).toContain('Un colchón para lo que no se ve al cotizar');
    expect(texto).toContain('Sumar ganancia');
    expect(texto).toContain('Lo que queda para ti por encima de tus costos');
  });

  it('explica la retención como un adelanto de impuesto y el IVA como plata que no es tuya', () => {
    const texto = () => (fixture.nativeElement as HTMLElement).textContent ?? '';
    component.vista = 'todo';
    component.formulario.patchValue({ documento: 'BOLETA_HONORARIOS' });
    fixture.detectChanges();
    expect(texto()).toContain('Las boletas de honorarios no llevan IVA');
    expect(texto()).toContain('adelanto de tu impuesto a la renta, no un costo');
    component.formulario.patchValue({ documento: 'DOCUMENTO_IVA' });
    fixture.detectChanges();
    expect(texto()).toContain('El IVA no es tuyo');
    expect(texto()).toContain('inicio de actividades de primera categoría');
    component.formulario.patchValue({ documento: 'SIN_DOCUMENTO' });
    fixture.detectChanges();
    expect(texto()).toContain('Sin documento no queda constancia tributaria');
  });

  it('cargar una plantilla respeta si tenía imprevistos o ganancia apagados', () => {
    const base = component.datos();
    component.cargarPlantilla({ id_plantilla: 1, nombre: 'x', tipo_trabajo: '', actualizada_en: '', datos: { ...base, imprevistos_pct: 0, ganancia_pct: 20 } });
    expect(component.formulario.controls.usar_imprevistos.value).toBeFalse();
    expect(component.formulario.controls.usar_ganancia.value).toBeTrue();
    expect(component.formulario.controls.ganancia_pct.value).toBe(20);
  });

  it('el ayudante del valor por hora lo copia a la mano de obra', () => {
    component.ayudante.patchValue({ ingreso_mensual: 900000, horas_cobrables: 90 });
    expect(component.valorHoraSugerido).toBe(10000);
    component.usarValorHora();
    expect(component.formulario.controls.valor_hora.value).toBe(10000);
  });

  it('"para ti" descuenta materiales, traslado y herramientas de lo que recibes', () => {
    const r = { liquido: 59077, materiales_total: 15500, traslado_total: 6000, herramientas_total: 1200 } as never;
    expect(component.paraTi(r)).toBe(36377);
    expect(component.paraTi({ liquido: 100, materiales_total: 500, traslado_total: 0, herramientas_total: 0 } as never)).toBe(0);
  });

  describe('al confirmar un trabajo desde la calculadora', () => {
    const trabajo = { id_contratacion: 29, proveedor: 4, estado: 'SOLICITADA', publicacion_precio: 25000, publicacion_titulo: 'Gasfitería' } as never;

    beforeEach(() => {
      component.trabajo = trabajo;
      component.trabajoId = 29;
    });

    it('muestra el precio sugerido de la publicación, grande y a la vista', () => {
      fixture.detectChanges();
      const el = fixture.nativeElement as HTMLElement;
      expect(component.precioSugerido).toBe(25000);
      expect(el.querySelector('.ks-calc-sugerido-grande strong')?.textContent).toContain('25');
      expect(el.textContent).toContain('Precio sugerido en tu publicación');
    });

    it('confirmar con el precio de la publicación no manda monto: el servidor usa el de la publicación', () => {
      const router = TestBed.inject(Router);
      spyOn(router, 'navigate').and.resolveTo(true);
      component.passwordConfirmar = 'clave';
      component.confirmarTrabajo(false);
      const req = httpMock.expectOne((r) => r.method === 'POST' && r.url.endsWith('/contrataciones/29/confirmar/'));
      expect(req.request.body.monto).toBeUndefined();
      expect(req.request.body.items).toBeUndefined();
      expect(req.request.body.password).toBe('clave');
    });

    it('confirmar con el precio calculado en el modo de costos manda el monto y el desglose', () => {
      component.formulario.controls.modo.setValue('costos');
      component.resultado = { precio_boleta: 70329, items: [{ descripcion: 'Mano de obra', categoria: 'MANO_DE_OBRA', monto: 70329 }] } as never;
      component.passwordConfirmar = 'clave';
      component.confirmarTrabajo(true);
      const req = httpMock.expectOne((r) => r.method === 'POST' && r.url.endsWith('/contrataciones/29/confirmar/'));
      expect(req.request.body.monto).toBe(70329);
      expect(req.request.body.items.length).toBe(1);
    });

    it('confirmar con el precio calculado en el modo normal manda solo el monto', () => {
      component.resultado = { precio_boleta: 30000, items: [{ descripcion: 'Servicio', categoria: 'OTRO', monto: 30000 }] } as never;
      component.passwordConfirmar = 'clave';
      component.confirmarTrabajo(true);
      const req = httpMock.expectOne((r) => r.method === 'POST' && r.url.endsWith('/contrataciones/29/confirmar/'));
      expect(req.request.body.monto).toBe(30000);
      expect(req.request.body.items).toBeUndefined();
    });

    it('sin contraseña no confirma', () => {
      component.confirmarTrabajo(false);
      httpMock.expectNone((r) => r.url.endsWith('/confirmar/'));
      expect(component.errorConfirmar).toContain('contraseña');
    });

    it('un error del servidor se muestra y no navega', () => {
      component.passwordConfirmar = 'mala';
      component.confirmarTrabajo(false);
      httpMock.expectOne((r) => r.url.endsWith('/confirmar/')).flush({ detail: 'Contraseña incorrecta — no se pudo confirmar.' }, { status: 400, statusText: 'Bad Request' });
      expect(component.errorConfirmar).toContain('Contraseña incorrecta');
      expect(component.confirmando).toBeFalse();
    });

    it('ofrece el precio calculado solo si es distinto al de la publicación', () => {
      component.resultado = { precio_boleta: 25000 } as never;
      expect(component.precioCalculadoDistinto).toBeFalse();
      component.resultado = { precio_boleta: 29762 } as never;
      expect(component.precioCalculadoDistinto).toBeTrue();
    });
  });

  describe('asistente por pasos', () => {
    it('arranca en pasos, en el primer paso, y el modo normal es corto', () => {
      expect(component.vista).toBe('pasos');
      expect(component.pasoActual).toBe('modo');
      component.elegirModo('simple');
      expect(component.pasos).toEqual(['modo', 'precio', 'documento', 'resultado']);
      expect(component.pasoActual).toBe('precio');
    });

    it('el modo de costos recorre cada tema y se puede volver atrás', () => {
      component.elegirModo('costos');
      expect(component.pasoActual).toBe('materiales');
      component.siguiente();
      expect(component.pasoActual).toBe('traslado');
      expect(component.esPasoOpcional).toBeTrue();
      component.atras();
      component.atras();
      expect(component.pasoActual).toBe('modo');
      component.atras();
      expect(component.indicePaso).toBe(0);
    });

    it('no pasa del último paso y solo muestra el tema actual', () => {
      component.elegirModo('simple');
      for (let i = 0; i < 10; i++) {
        component.siguiente();
      }
      expect(component.pasoActual).toBe('resultado');
      expect(component.ver('resultado')).toBeTrue();
      expect(component.ver('precio')).toBeFalse();
      expect(component.progreso).toBe(1);
    });

    it('en «todo junto» se ven todos los temas del modo', () => {
      component.cambiarVista('todo');
      expect(component.ver('precio')).toBeTrue();
      expect(component.ver('materiales')).toBeFalse();
      component.formulario.controls.modo.setValue('costos');
      expect(component.ver('materiales')).toBeTrue();
      expect(component.ver('precio')).toBeFalse();
    });

    it('el guía tiene guion para cada paso y el glosario usa los porcentajes del servidor', () => {
      for (const paso of component.pasos) {
        expect(component.guion[paso].texto.length).toBeGreaterThan(10);
      }
      component.config = { retencion_porcentaje: 14.5, iva_porcentaje: 19 } as never;
      expect(component.textoTermino('retencion')).toContain('14.5 %');
      component.alternarTermino('iva');
      expect(component.terminoAbierto).toBe('iva');
      component.alternarTermino('iva');
      expect(component.terminoAbierto).toBeNull();
    });

    it('cada paso tiene ejemplo y la ayuda se abre y se cierra a mano', () => {
      for (const paso of component.pasos) {
        expect(component.guion[paso].ejemplo.length).toBeGreaterThan(10);
      }
      component.alternarAyuda();
      expect(component.ayudaAbierta).toBeTrue();
      expect(component.ayudaAutomatica).toBeFalse();
      component.siguiente();
      expect(component.ayudaAbierta).toBeFalse();
    });

    it('si la persona se queda quieta, ofrece ayuda sola (pasos) o resalta ir paso a paso (todo junto)', fakeAsync(() => {
      component.ngOnInit();
      tick(ESPERA_AYUDA_MS);
      expect(component.ayudaAbierta).toBeTrue();
      expect(component.ayudaAutomatica).toBeTrue();
      component.cambiarVista('todo');
      expect(component.sugerirGuia).toBeFalse();
      tick(ESPERA_AYUDA_MS);
      expect(component.sugerirGuia).toBeTrue();
      component.ngOnDestroy();
      discardPeriodicTasks();
    }));

    it('en «todo junto» el botón de ir paso a paso está a la vista', () => {
      component.cambiarVista('todo');
      fixture.detectChanges();
      const boton = (fixture.nativeElement as HTMLElement).querySelector('.ks-calc-guiame-boton');
      expect(boton?.textContent).toContain('Ir paso a paso');
    });

    it('al final muestra tres cifras y el detalle plegado', () => {
      component.elegirModo('simple');
      for (let i = 0; i < 3; i++) {
        component.siguiente();
      }
      component.resultado = { simple: true, documento: 'BOLETA_HONORARIOS', precio_boleta: 35715, total_cliente: 37858, liquido: 30000, precio_neto: 30000, retencion_pct: 16, retencion_monto: 5715, comision_porcentaje: 6, comision_monto: 2143 } as never;
      fixture.detectChanges();
      const el = fixture.nativeElement as HTMLElement;
      expect(el.querySelectorAll('.ks-calc-cifra').length).toBe(3);
      expect(el.querySelector('details.ks-calc-detalle summary')?.textContent).toContain('Ver el detalle');
    });
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
