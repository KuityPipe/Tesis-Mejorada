import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormGroup } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, debounceTime } from 'rxjs';

import { Auth } from '../core/auth';
import { ContratacionDetalle, Contrataciones } from '../contrataciones/contrataciones';
import { Retroalimentacion } from '../core/retroalimentacion';
import {
  Calculadora,
  ConfigCalculadora,
  describirTramos,
  DatosValorizacion,
  Documento,
  PlantillaValorizacion,
  ResultadoValorizacion,
  valorHora,
} from '../core/calculadora';

/** Tiempo sin actividad tras el cual la calculadora ofrece ayuda. */
export const ESPERA_AYUDA_MS = 20000;

export type PasoId = 'modo' | 'precio' | 'materiales' | 'traslado' | 'trabajo' | 'herramientas' | 'extras' | 'documento' | 'resultado';
export type Termino = 'retencion' | 'iva' | 'imprevistos' | 'ganancia' | 'comision';

/** Guion fijo del guía: lo que dice en cada paso. Sin IA: lo que se escribe aquí no sale a ningún modelo (ADR 0005). */
export const GUION_PASOS: Record<PasoId, { titulo: string; texto: string; ejemplo: string; terminos: Termino[] }> = {
  modo: { titulo: '¡Hola! Vamos a ponerle precio a tu trabajo', texto: '¿Ya sabes cuánto quieres que te quede, o prefieres que lo calculemos juntos desde tus costos?', ejemplo: 'si siempre cobras lo mismo (por ejemplo, destapar un lavaplatos), elige la primera opción. Si cada trabajo cambia, la segunda.', terminos: [] },
  precio: { titulo: 'Lo que quieres que te quede', texto: 'Escribe lo que quieres recibir por el servicio, sin contar materiales ni gastos. Después vemos cuánto cobrar.', ejemplo: 'quieres recibir $30.000 por destapar un lavaplatos: escribe 30000, sin puntos.', terminos: [] },
  materiales: { titulo: 'Materiales', texto: 'Anota lo que compras o usas para el trabajo. Si no usas nada, déjalo vacío y sigue.', ejemplo: 'una llave de paso: descripción «llave de paso», cantidad 1 y precio unitario 8500.', terminos: [] },
  traslado: { titulo: 'Traslado', texto: '¿Tienes que ir a otro lugar? Cuenta los kilómetros, peajes y estacionamiento. Si no aplica, salta este paso.', ejemplo: 'si vas 12 km ida y vuelta y calculas $300 por km, son $3.600. Si no sales de tu taller, salta el paso.', terminos: [] },
  trabajo: { titulo: 'Tu trabajo', texto: 'Tu tiempo vale. Indica cuántas horas tomará y cuánto cobras por hora. ¿No lo sabes? Te ayudo a calcularlo.', ejemplo: 'si el trabajo toma 3 horas y cobras $8.000 por hora, son $24.000.', terminos: [] },
  herramientas: { titulo: 'Herramientas', texto: 'Las herramientas se gastan o se arriendan. Suma ese desgaste, o salta el paso si no aplica.', ejemplo: 'si en este trabajo gastas unos $2.000 en herramientas, escribe 2000. Si no, salta el paso.', terminos: [] },
  extras: { titulo: 'Imprevistos y ganancia', texto: 'Dos colchones opcionales: uno para lo que no se ve al cotizar y otro para crecer. Puedes apagarlos.', ejemplo: 'con 10 % de imprevistos y 15 % de ganancia, unos costos de $24.000 suben a $30.360.', terminos: ['imprevistos', 'ganancia'] },
  documento: { titulo: 'Documento que entregas', texto: 'Según el documento cambia cuánto debes cobrar para que te quede lo que necesitas.', ejemplo: 'si das boleta de honorarios, elige esa; si no entregas ningún documento, «Sin documento».', terminos: ['retencion', 'iva'] },
  resultado: { titulo: '¡Listo! Esto es lo que sale', texto: 'Estas son tus tres cifras. Abre el detalle si quieres ver cómo se reparte el cobro.', ejemplo: '«Te quedan» es lo que recibes de verdad; «El cliente paga» incluye la comisión de KeyServ.', terminos: ['comision', 'retencion'] },
};

export const GLOSARIO: Record<Termino, string> = {
  retencion: 'La retención ({retencion} % estimado) es un adelanto de tu impuesto a la renta que se descuenta cuando emites boleta de honorarios. No es un costo: lo recuperas en tu declaración de abril. Confírmalo con un contador.',
  iva: 'El IVA ({iva} %) no es tuyo: lo cobras y lo traspasas al SII. Solo corresponde si tienes inicio de actividades de primera categoría.',
  imprevistos: 'Un colchón para lo que no se ve al cotizar: un material que sube de precio o un arreglo que se complica.',
  ganancia: 'Lo que queda para ti por encima de tus costos: para renovar herramientas, cubrir meses con poco trabajo y crecer. No es tu pago por hora.',
  comision: 'La comisión de KeyServ la paga quien contrata, además de tu precio: tú recibes el precio completo.',
};

/**
 * Calculadora gratuita de valorización (bloque 2). Pública: cualquiera puede ponerle precio a un trabajo sin crear una
 * cuenta. El cálculo vive en el servidor (`KeyServApp/calculadora.py`) para que la comisión y la retención sean siempre
 * las que de verdad se aplican; con cuenta se pueden guardar plantillas y cargarlas al confirmar una contratación.
 */
@Component({
  selector: 'app-calculadora',
  templateUrl: './calculadora.page.html',
  styleUrls: ['./calculadora.page.scss'],
  standalone: false,
})
export class CalculadoraPage implements OnInit, OnDestroy {
  readonly materiales = new FormArray<FormGroup>([]);

  formulario = this.fb.nonNullable.group({
    modo: ['simple' as 'simple' | 'costos'],
    precio_simple: [0],
    materiales: this.materiales,
    traslado_modo: ['km' as 'km' | 'fijo'],
    km_ida_vuelta: [0],
    costo_km: [0],
    monto_fijo: [0],
    peajes_estacionamiento: [0],
    horas: [0],
    valor_hora: [0],
    personas: [1],
    herramientas_modo: ['monto' as 'monto' | 'porcentaje'],
    herramientas_monto: [0],
    herramientas_porcentaje: [0],
    // Imprevistos y ganancia son opcionales: se pueden apagar si el trabajo es simple.
    usar_imprevistos: [true],
    imprevistos_pct: [10],
    usar_ganancia: [true],
    ganancia_pct: [15],
    documento: ['SIN_DOCUMENTO' as Documento],
  });

  /** Ayudante del valor por hora (no forma parte de la valorización). */
  ayudante = this.fb.nonNullable.group({ ingreso_mensual: [0], horas_cobrables: [80] });

  config: ConfigCalculadora | null = null;
  resultado: ResultadoValorizacion | null = null;
  error: string | null = null;
  calculando = false;
  exportando: 'pdf' | 'xlsx' | null = null;
  mostrarAyudante = false;

  // Con cuenta
  autenticado = false;
  plantillas: PlantillaValorizacion[] = [];
  nombrePlantilla = '';
  guardandoPlantilla = false;
  mensajePlantilla: string | null = null;

  // Trabajo que se está confirmando (llegada desde "Confirmar contratación"): `/calculadora?contratacion=<id>`.
  trabajo: ContratacionDetalle | null = null;
  trabajoId: number | null = null;
  errorTrabajo: string | null = null;
  passwordConfirmar = '';
  confirmando = false;
  errorConfirmar: string | null = null;

  // Asistente por pasos (por defecto) o todo a la vista. Al confirmar un trabajo se muestra todo junto.
  vista: 'pasos' | 'todo' = 'pasos';
  indicePaso = 0;
  terminoAbierto: Termino | null = null;
  /** «¿Te confunde algo?»: se abre sola si la persona se queda un rato sin hacer nada. */
  ayudaAbierta = false;
  ayudaAutomatica = false;
  /** En «todo junto»: resalta la invitación a ir paso a paso cuando la persona parece perdida. */
  sugerirGuia = false;
  private temporizadorEspera?: ReturnType<typeof setTimeout>;

  readonly guion = GUION_PASOS;
  readonly glosario = GLOSARIO;
  readonly etiquetas: Record<Termino, string> = { retencion: 'la retención', iva: 'el IVA', imprevistos: 'los imprevistos', ganancia: 'la ganancia', comision: 'la comisión' };

  private suscripcion?: Subscription;

  constructor(
    private readonly fb: FormBuilder,
    private readonly api: Calculadora,
    private readonly auth: Auth,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly contratacionesApi: Contrataciones,
    private readonly retroalimentacion: Retroalimentacion,
  ) {}

  nuevoMaterial() {
    return this.fb.nonNullable.group({
      descripcion: [''],
      cantidad: [1],
      unidad: [''],
      precio_unitario: [0],
      reutilizado: [false],
    });
  }

  ngOnInit(): void {
    this.materiales.push(this.nuevoMaterial());
    this.autenticado = this.auth.estaAutenticado();
    this.api.config().subscribe({
      next: (config) => {
        this.config = config;
        this.formulario.patchValue({ imprevistos_pct: config.imprevistos_porcentaje, ganancia_pct: config.ganancia_porcentaje }, { emitEvent: false });
        this.calcular();
      },
      error: () => this.calcular(),
    });
    // Recalcula mientras la persona escribe, sin disparar una consulta por cada tecla.
    this.suscripcion = this.formulario.valueChanges.pipe(debounceTime(400)).subscribe(() => this.calcular());
    this.suscripcion.add(this.formulario.valueChanges.subscribe(() => this.reiniciarEspera()));
    this.reiniciarEspera();
    if (this.autenticado) {
      this.cargarPlantillas();
    }
    const id = Number(this.route.snapshot.queryParamMap.get('contratacion'));
    if (id > 0) {
      this.cargarTrabajo(id);
    }
  }

  ngOnDestroy(): void {
    this.suscripcion?.unsubscribe();
    clearTimeout(this.temporizadorEspera);
  }

  /** Trabajo que el proveedor va a confirmar: solo si es suyo y sigue en "Solicitada". */
  private cargarTrabajo(id: number): void {
    this.trabajoId = id;
    this.vista = 'todo';
    if (!this.autenticado) {
      this.errorTrabajo = 'Inicia sesión como proveedor para confirmar este trabajo.';
      return;
    }
    this.auth.me().subscribe({
      next: (usuario) => {
        this.contratacionesApi.detalle(id).subscribe({
          next: (trabajo) => {
            if (trabajo.proveedor !== usuario.id_usuario || trabajo.estado !== 'SOLICITADA') {
              this.errorTrabajo = 'Este trabajo ya no está pendiente de tu confirmación.';
              return;
            }
            this.trabajo = trabajo;
            // Parte del precio de la publicación: el proveedor puede mantenerlo o ajustarlo.
            if (trabajo.publicacion_precio) {
              this.formulario.patchValue({ modo: 'simple', precio_simple: trabajo.publicacion_precio });
            }
          },
          error: () => (this.errorTrabajo = 'No pudimos cargar este trabajo.'),
        });
      },
      error: () => (this.errorTrabajo = 'No pudimos verificar tu sesión.'),
    });
  }

  /** Precio de la publicación, el monto sugerido (grande y a la vista porque el proveedor puede o no cambiarlo). */
  get precioSugerido(): number {
    return this.trabajo?.publicacion_precio ?? 0;
  }

  /** ¿El precio calculado es distinto al de la publicación? Solo entonces tiene sentido ofrecer las dos opciones. */
  get precioCalculadoDistinto(): boolean {
    const calculado = this.resultado?.precio_boleta ?? 0;
    return calculado > 0 && calculado !== this.precioSugerido;
  }

  /** Confirma el trabajo. Sin `usarCalculado` se mantiene el precio de la publicación; con él, el monto que sale de la calculadora. */
  confirmarTrabajo(usarCalculado: boolean): void {
    if (!this.trabajoId || this.confirmando) {
      return;
    }
    if (!this.passwordConfirmar) {
      this.errorConfirmar = 'Escribe tu contraseña para confirmar.';
      return;
    }
    if (usarCalculado && !(this.resultado && this.resultado.precio_boleta > 0)) {
      this.errorConfirmar = 'Primero calcula un precio mayor a cero.';
      return;
    }
    this.confirmando = true;
    this.errorConfirmar = null;
    const monto = usarCalculado ? this.resultado!.precio_boleta : undefined;
    // En el modo de costos el desglose viaja como hoja de presupuesto; la suma de sus filas es el monto acordado.
    const items = usarCalculado && this.modo === 'costos' ? this.resultado!.items : undefined;
    this.contratacionesApi.confirmar(this.trabajoId, this.passwordConfirmar, monto, items).subscribe({
      next: () => {
        this.confirmando = false;
        this.retroalimentacion.exito('Contratación confirmada.');
        this.router.navigate(['/contratacion', this.trabajoId]);
      },
      error: (e: HttpErrorResponse) => {
        this.confirmando = false;
        this.errorConfirmar = e.error?.detail ?? 'No pudimos confirmar el trabajo. Intenta de nuevo.';
      },
    });
  }

  agregarMaterial(): void {
    this.materiales.push(this.nuevoMaterial());
  }

  quitarMaterial(indice: number): void {
    this.materiales.removeAt(indice);
    if (this.materiales.length === 0) {
      this.agregarMaterial();
    }
  }

  /** El cuerpo que entiende el servidor, a partir de lo escrito en el formulario. */
  datos(): DatosValorizacion {
    const v = this.formulario.getRawValue();
    const numero = (x: unknown) => (Number(x) > 0 ? Number(x) : 0);
    return {
      modo: v.modo,
      precio_simple: numero(v.precio_simple),
      materiales: (v.materiales as { descripcion: string; cantidad: number; unidad: string; precio_unitario: number; reutilizado: boolean }[]).map((m) => ({
        descripcion: (m.descripcion || '').trim(),
        cantidad: numero(m.cantidad),
        unidad: (m.unidad || '').trim(),
        precio_unitario: numero(m.precio_unitario),
        reutilizado: !!m.reutilizado,
      })),
      traslado: {
        modo: v.traslado_modo,
        km_ida_vuelta: numero(v.km_ida_vuelta),
        costo_km: numero(v.costo_km),
        monto_fijo: numero(v.monto_fijo),
        peajes_estacionamiento: numero(v.peajes_estacionamiento),
      },
      mano_obra: { horas: numero(v.horas), valor_hora: numero(v.valor_hora), personas: Math.max(1, numero(v.personas)) },
      herramientas: { modo: v.herramientas_modo, monto: numero(v.herramientas_monto), porcentaje: numero(v.herramientas_porcentaje) },
      imprevistos_pct: v.usar_imprevistos ? numero(v.imprevistos_pct) : 0,
      ganancia_pct: v.usar_ganancia ? numero(v.ganancia_pct) : 0,
      documento: v.documento,
    };
  }

  calcular(): void {
    this.calculando = true;
    this.api.calcular(this.datos()).subscribe({
      next: (resultado) => {
        this.resultado = resultado;
        this.error = null;
        this.calculando = false;
      },
      error: (e: HttpErrorResponse) => {
        this.calculando = false;
        this.error = e.error?.detail ?? 'No pudimos calcular. Revisa los números e intenta de nuevo.';
      },
    });
  }

  /** Los tramos de la comisión en palabras, tal como los aplica el servidor. */
  get tramosTexto(): string {
    return this.config ? describirTramos(this.config.comision_tramos) : '';
  }

  /** Lo que queda por tu trabajo tras pagar materiales, traslado y herramientas (solo tiene sentido en el modo de costos). */
  paraTi(r: ResultadoValorizacion): number {
    return Math.max(0, r.liquido - r.materiales_total - r.traslado_total - r.herramientas_total);
  }

  get modo(): 'simple' | 'costos' {
    return this.formulario.controls.modo.value;
  }

  // ---- Asistente por pasos ----
  /** Los pasos según el modo: el normal es corto, el de costos recorre cada tema. */
  get pasos(): PasoId[] {
    return this.modo === 'simple'
      ? ['modo', 'precio', 'documento', 'resultado']
      : ['modo', 'materiales', 'traslado', 'trabajo', 'herramientas', 'extras', 'documento', 'resultado'];
  }

  get pasoActual(): PasoId {
    return this.pasos[Math.min(this.indicePaso, this.pasos.length - 1)];
  }

  get progreso(): number {
    return (this.indicePaso + 1) / this.pasos.length;
  }

  get esPasoOpcional(): boolean {
    return ['traslado', 'herramientas', 'extras'].includes(this.pasoActual);
  }

  /** ¿Se muestra este tema? En «todo junto» van todos los del modo; en pasos, solo el actual. */
  ver(id: PasoId): boolean {
    return this.vista === 'todo' ? this.pasos.includes(id) : this.pasoActual === id;
  }

  elegirModo(modo: 'simple' | 'costos'): void {
    this.formulario.controls.modo.setValue(modo);
    this.indicePaso = 1;
    this.cambioDeContexto();
  }

  siguiente(): void {
    this.indicePaso = Math.min(this.indicePaso + 1, this.pasos.length - 1);
    this.cambioDeContexto();
  }

  atras(): void {
    this.indicePaso = Math.max(this.indicePaso - 1, 0);
    this.cambioDeContexto();
  }

  cambiarVista(vista: 'pasos' | 'todo'): void {
    this.vista = vista;
    this.cambioDeContexto();
  }

  /** Vuelve al primer paso sin borrar lo escrito. */
  reiniciar(): void {
    this.indicePaso = 0;
    this.cambioDeContexto();
  }

  alternarAyuda(): void {
    this.ayudaAbierta = !this.ayudaAbierta;
    this.ayudaAutomatica = false;
  }

  private cambioDeContexto(): void {
    this.terminoAbierto = null;
    this.reiniciarEspera();
  }

  /** Si pasan ~20 s sin escribir ni navegar, ofrece ayuda: el ejemplo del paso, o ir paso a paso. Cualquier acción lo reinicia. */
  private reiniciarEspera(): void {
    clearTimeout(this.temporizadorEspera);
    this.ayudaAbierta = false;
    this.ayudaAutomatica = false;
    this.sugerirGuia = false;
    this.temporizadorEspera = setTimeout(() => {
      if (this.vista === 'pasos') {
        this.ayudaAbierta = true;
        this.ayudaAutomatica = true;
      } else {
        this.sugerirGuia = true;
      }
    }, ESPERA_AYUDA_MS);
  }

  alternarTermino(termino: Termino): void {
    this.terminoAbierto = this.terminoAbierto === termino ? null : termino;
  }

  /** Texto del glosario con los porcentajes vigentes del servidor. */
  textoTermino(termino: Termino): string {
    return this.glosario[termino]
      .replace('{retencion}', String(this.config?.retencion_porcentaje ?? 16))
      .replace('{iva}', String(this.config?.iva_porcentaje ?? 19));
  }

  get valorHoraSugerido(): number {
    const { ingreso_mensual, horas_cobrables } = this.ayudante.getRawValue();
    return valorHora(Number(ingreso_mensual), Number(horas_cobrables));
  }

  usarValorHora(): void {
    if (this.valorHoraSugerido > 0) {
      this.formulario.controls.valor_hora.setValue(this.valorHoraSugerido);
    }
  }

  exportar(tipo: 'pdf' | 'xlsx'): void {
    if (this.exportando) {
      return;
    }
    this.exportando = tipo;
    this.api.exportar(tipo, this.datos()).subscribe({
      next: (archivo) => {
        const url = URL.createObjectURL(archivo);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `valorizacion-keyserv.${tipo}`;
        enlace.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        this.exportando = null;
      },
      error: () => {
        this.exportando = null;
        this.error = 'No pudimos generar el archivo. Revisa los números e intenta de nuevo.';
      },
    });
  }

  // ---- Plantillas (con cuenta) ----
  cargarPlantillas(): void {
    this.api.plantillas().subscribe({ next: (p) => (this.plantillas = p), error: () => (this.plantillas = []) });
  }

  guardarPlantilla(): void {
    const nombre = this.nombrePlantilla.trim();
    if (!nombre || this.guardandoPlantilla) {
      return;
    }
    this.guardandoPlantilla = true;
    this.mensajePlantilla = null;
    this.api.guardarPlantilla(nombre, '', this.datos()).subscribe({
      next: () => {
        this.guardandoPlantilla = false;
        this.mensajePlantilla = 'Plantilla guardada.';
        this.nombrePlantilla = '';
        this.cargarPlantillas();
      },
      error: (e: HttpErrorResponse) => {
        this.guardandoPlantilla = false;
        this.mensajePlantilla = e.error?.detail ?? 'No pudimos guardar la plantilla.';
      },
    });
  }

  cargarPlantilla(plantilla: PlantillaValorizacion): void {
    const d = plantilla.datos;
    this.formulario.controls.modo.setValue('costos');
    this.materiales.clear();
    for (const m of d.materiales ?? []) {
      const fila = this.nuevoMaterial();
      fila.patchValue({ ...m });
      this.materiales.push(fila);
    }
    if (this.materiales.length === 0) {
      this.agregarMaterial();
    }
    this.formulario.patchValue({
      traslado_modo: d.traslado?.modo ?? 'km',
      km_ida_vuelta: d.traslado?.km_ida_vuelta ?? 0,
      costo_km: d.traslado?.costo_km ?? 0,
      monto_fijo: d.traslado?.monto_fijo ?? 0,
      peajes_estacionamiento: d.traslado?.peajes_estacionamiento ?? 0,
      horas: d.mano_obra?.horas ?? 0,
      valor_hora: d.mano_obra?.valor_hora ?? 0,
      personas: d.mano_obra?.personas ?? 1,
      herramientas_modo: d.herramientas?.modo ?? 'monto',
      herramientas_monto: d.herramientas?.monto ?? 0,
      herramientas_porcentaje: d.herramientas?.porcentaje ?? 0,
      usar_imprevistos: (d.imprevistos_pct ?? 10) > 0,
      imprevistos_pct: d.imprevistos_pct ? d.imprevistos_pct : 10,
      usar_ganancia: (d.ganancia_pct ?? 15) > 0,
      ganancia_pct: d.ganancia_pct ? d.ganancia_pct : 15,
      documento: d.documento ?? 'SIN_DOCUMENTO',
    });
    this.nombrePlantilla = plantilla.nombre;
  }

  borrarPlantilla(plantilla: PlantillaValorizacion): void {
    this.api.eliminarPlantilla(plantilla.id_plantilla).subscribe({ next: () => this.cargarPlantillas() });
  }
}
