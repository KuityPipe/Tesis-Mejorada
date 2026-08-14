import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { Auth } from '../../core/auth';
import { Contrataciones, ContratacionDetalle, Mensaje } from '../../contrataciones/contrataciones';

/**
 * Detalle de un trabajo puntual — equivalente Ionic de
 * `contratacion_detalle_view`: línea de tiempo, chat embebido y las
 * acciones disponibles según el rol (confirmar/completar con
 * reautenticación, valorar). Fase 4 del plan de migración — los pagos
 * (Webpay/Khipu) son la última pieza, todavía no migrados, así que hoy no
 * hay forma de pasar de CONFIRMADA a EN_CURSO desde acá.
 */
@Component({
  selector: 'app-contratacion-detalle',
  templateUrl: './detalle.page.html',
  styleUrls: ['./detalle.page.scss'],
  standalone: false,
})
export class DetallePage implements OnInit {
  contratacionId!: number;
  contratacion: ContratacionDetalle | null = null;
  mensajes: Mensaje[] = [];
  usuarioActualId: number | null = null;
  cargando = true;

  formularioMensaje = this.fb.nonNullable.group({ contenido: ['', Validators.required] });
  formularioReauth = this.fb.nonNullable.group({
    password: ['', Validators.required],
    monto: [null as number | null],
  });
  formularioValoracion = this.fb.nonNullable.group({
    puntuacion: [5, [Validators.required, Validators.min(1), Validators.max(5)]],
    comentario: [''],
  });

  enviandoMensaje = false;
  procesandoAccion = false;
  errorAccion: string | null = null;
  fotosValoracion: File[] = [];
  enviandoValoracion = false;
  errorValoracion: string | null = null;
  valoracionOk = false;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly contratacionesApi: Contrataciones,
  ) {}

  ngOnInit(): void {
    this.contratacionId = Number(this.route.snapshot.paramMap.get('id'));
    this.auth.me().subscribe((usuario) => (this.usuarioActualId = usuario.id_usuario));
    this.cargarDetalle();
    this.cargarMensajes();
  }

  private cargarDetalle(): void {
    this.contratacionesApi.detalle(this.contratacionId).subscribe({
      next: (contratacion) => {
        this.contratacion = contratacion;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  private cargarMensajes(): void {
    this.contratacionesApi.mensajes(this.contratacionId).subscribe((mensajes) => (this.mensajes = mensajes));
  }

  get esCliente(): boolean {
    return !!this.contratacion && this.usuarioActualId === this.contratacion.cliente;
  }

  get esProveedor(): boolean {
    return !!this.contratacion && this.usuarioActualId === this.contratacion.proveedor;
  }

  get puedeConfirmar(): boolean {
    return this.esProveedor && this.contratacion?.estado === 'SOLICITADA';
  }

  get puedeCompletar(): boolean {
    return this.esCliente && this.contratacion?.estado === 'EN_CURSO';
  }

  get puedeValorar(): boolean {
    return this.esCliente && this.contratacion?.estado === 'COMPLETADA' && !this.contratacion.valoracion;
  }

  enviarMensaje(): void {
    if (this.formularioMensaje.invalid || this.enviandoMensaje) {
      return;
    }
    this.enviandoMensaje = true;
    const { contenido } = this.formularioMensaje.getRawValue();
    this.contratacionesApi.enviarMensaje(this.contratacionId, contenido).subscribe({
      next: (mensaje) => {
        this.mensajes = [...this.mensajes, mensaje];
        this.formularioMensaje.reset({ contenido: '' });
        this.enviandoMensaje = false;
      },
      error: () => {
        this.enviandoMensaje = false;
      },
    });
  }

  confirmar(): void {
    if (this.formularioReauth.invalid || this.procesandoAccion) {
      return;
    }
    this.procesandoAccion = true;
    this.errorAccion = null;
    const { password, monto } = this.formularioReauth.getRawValue();
    this.contratacionesApi.confirmar(this.contratacionId, password, monto ?? undefined).subscribe({
      next: (contratacion) => {
        this.contratacion = contratacion;
        this.formularioReauth.reset({ password: '', monto: null });
        this.procesandoAccion = false;
      },
      error: (error: HttpErrorResponse) => {
        this.procesandoAccion = false;
        this.errorAccion = error.error?.detail ?? 'No se pudo confirmar.';
      },
    });
  }

  completar(): void {
    if (this.formularioReauth.invalid || this.procesandoAccion) {
      return;
    }
    this.procesandoAccion = true;
    this.errorAccion = null;
    const { password } = this.formularioReauth.getRawValue();
    this.contratacionesApi.completar(this.contratacionId, password).subscribe({
      next: (contratacion) => {
        this.contratacion = contratacion;
        this.formularioReauth.reset({ password: '', monto: null });
        this.procesandoAccion = false;
      },
      error: (error: HttpErrorResponse) => {
        this.procesandoAccion = false;
        this.errorAccion = error.error?.detail ?? 'No se pudo completar.';
      },
    });
  }

  alElegirFotos(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.fotosValoracion = input.files ? Array.from(input.files) : [];
  }

  valorar(): void {
    if (this.formularioValoracion.invalid || this.enviandoValoracion) {
      return;
    }
    this.enviandoValoracion = true;
    this.errorValoracion = null;

    const { puntuacion, comentario } = this.formularioValoracion.getRawValue();
    const formData = new FormData();
    formData.set('puntuacion', String(puntuacion));
    formData.set('comentario', comentario);
    for (const foto of this.fotosValoracion) {
      formData.append('imagenes', foto);
    }

    this.contratacionesApi.valorar(this.contratacionId, formData).subscribe({
      next: () => {
        this.enviandoValoracion = false;
        this.valoracionOk = true;
        this.cargarDetalle();
      },
      error: () => {
        this.enviandoValoracion = false;
        this.errorValoracion = 'No se pudo registrar la calificación — elegí una puntuación de 1 a 5 estrellas.';
      },
    });
  }
}
