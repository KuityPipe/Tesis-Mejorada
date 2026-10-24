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
  }

  /** Trabajo que el proveedor va a confirmar: solo si es suyo y sigue en "Solicitada". */
  private cargarTrabajo(id: number): void {
    this.trabajoId = id;
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
