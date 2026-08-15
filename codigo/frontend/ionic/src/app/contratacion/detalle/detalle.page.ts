import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { Auth } from '../../core/auth';
import { Contrataciones, ContratacionDetalle, Mensaje } from '../../contrataciones/contrataciones';
import { Pagos } from '../../pago/pagos';

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
  procesandoPago = false;
  errorPago: string | null = null;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly contratacionesApi: Contrataciones,
    private readonly pagosApi: Pagos,
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

  get puedePagar(): boolean {
    return this.esCliente && this.contratacion?.estado === 'CONFIRMADA';
  }

  get puedeValorar(): boolean {
    return this.esCliente && this.contratacion?.estado === 'COMPLETADA' && !this.contratacion.valoracion;
  }

  colorEstado(estado: string | undefined): string {
    return this.contratacionesApi.colorEstado(estado);
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

  /**
   * Transbank exige un POST real de `token_ws` a `url_pago` (no una
   * navegación GET) — se arma un `<form>` oculto y se lo manda con
   * `.submit()`, mismo truco que la página de auto-submit del template
   * (`pago_webpay_redirigir.html`), pero armado del lado del cliente.
   * Esto navega fuera de la SPA por completo (no vuelve nunca a este
   * método) hasta que Transbank redirige a `/pago/webpay/retorno`.
   */
  pagarConWebpay(): void {
    if (this.procesandoPago) {
      return;
    }
    this.procesandoPago = true;
    this.errorPago = null;
    this.pagosApi.iniciarWebpay(this.contratacionId).subscribe({
      next: ({ token, url_pago }) => {
        const formulario = document.createElement('form');
        formulario.method = 'POST';
        formulario.action = url_pago;
        const campoToken = document.createElement('input');
        campoToken.type = 'hidden';
        campoToken.name = 'token_ws';
        campoToken.value = token;
        formulario.appendChild(campoToken);
        document.body.appendChild(formulario);
        formulario.submit();
      },
      error: (error: HttpErrorResponse) => {
        this.procesandoPago = false;
        this.errorPago = error.error?.detail ?? 'No se pudo iniciar el pago con Webpay.';
      },
    });
  }

  /** Khipu sí acepta una navegación GET directa a `payment_url` — no hace falta el truco del `<form>` que necesita Webpay. */
  pagarConKhipu(): void {
    if (this.procesandoPago) {
      return;
    }
    this.procesandoPago = true;
    this.errorPago = null;
    this.pagosApi.iniciarKhipu(this.contratacionId).subscribe({
      next: ({ payment_url }) => {
        window.location.href = payment_url;
      },
      error: (error: HttpErrorResponse) => {
        this.procesandoPago = false;
        this.errorPago = error.error?.detail ?? 'No se pudo iniciar el pago con Khipu.';
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
        this.errorValoracion = 'No se pudo registrar la calificación — elige una puntuación de 1 a 5 estrellas.';
      },
    });
  }
}
