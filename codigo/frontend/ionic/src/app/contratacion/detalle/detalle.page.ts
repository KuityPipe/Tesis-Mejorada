import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

import { Auth } from '../../core/auth';
import { Retroalimentacion } from '../../core/retroalimentacion';
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
export class DetallePage implements OnInit, OnDestroy {
  contratacionId!: number;
  contratacion: ContratacionDetalle | null = null;
  mensajes: Mensaje[] = [];
  usuarioActualId: number | null = null;
  cargando = true;

  /**
   * `imagen_url` apunta al endpoint privado de descarga (`ContratacionMensajeImagenView`,
   * exige el JWT en el header `Authorization`) — un `<img [src]>` común no puede mandar ese
   * header, así que renderizarla directo daría 401. Se descarga como blob autenticado (mismo
   * `HttpClient` con el interceptor de auth) y se guarda acá como `blob:` URL, por id de
   * mensaje. Revocadas en `ngOnDestroy` para no filtrar memoria.
   */
  private readonly imagenesSeguras = new Map<number, string>();

  /** Referencia al contenedor con scroll propio de la lista de mensajes (ver detalle.page.html) — a diferencia del resto de la página, el chat tiene su propio scroll acotado, no el de `ion-content` entero. */
  @ViewChild('listaMensajes') listaMensajesRef?: ElementRef<HTMLDivElement>;

  formularioMensaje = this.fb.nonNullable.group({ contenido: [''] });
  formularioReauth = this.fb.nonNullable.group({
    password: ['', Validators.required],
    monto: [null as number | null],
  });
  formularioValoracion = this.fb.nonNullable.group({
    puntuacion: [5, [Validators.required, Validators.min(1), Validators.max(5)]],
    comentario: [''],
  });

  enviandoMensaje = false;
  imagenMensaje: File | null = null;
  previsualizacionImagenMensaje: string | null = null;
  mostrarEmojis = false;
  /** Set chico y curado, no un picker completo — alcanza para el uso real del chat (coordinar un trabajo), sin sumar una librería externa de emojis. */
  readonly emojisFrecuentes = [
    '😀', '😂', '👍', '🙏', '❤️', '😢', '😮', '🎉',
    '✅', '❌', '⏰', '📸', '💰', '🏠', '🔧', '🚚',
  ];
  exportandoChat = false;
  errorExportarChat: string | null = null;
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
    private readonly http: HttpClient,
    private readonly auth: Auth,
    private readonly contratacionesApi: Contrataciones,
    private readonly pagosApi: Pagos,
    private readonly retroalimentacion: Retroalimentacion,
  ) {}

  ngOnInit(): void {
    this.contratacionId = Number(this.route.snapshot.paramMap.get('id'));
    this.auth.me().subscribe((usuario) => (this.usuarioActualId = usuario.id_usuario));
    this.cargarDetalle();
    this.cargarMensajes();
  }

  ngOnDestroy(): void {
    for (const url of this.imagenesSeguras.values()) {
      URL.revokeObjectURL(url);
    }
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
    this.contratacionesApi.mensajes(this.contratacionId).subscribe((mensajes) => {
      this.mensajes = mensajes;
      mensajes.forEach((m) => this.cargarImagenSegura(m));
      this.desplazarAlFinal();
    });
  }

  esPropio(mensaje: Mensaje): boolean {
    return mensaje.usuario === this.usuarioActualId;
  }

  /** `undefined` mientras descarga — la burbuja no muestra la imagen hasta tenerla, en vez de un ícono roto. */
  urlSeguraImagen(mensaje: Mensaje): string | undefined {
    return this.imagenesSeguras.get(mensaje.id_mensaje);
  }

  private cargarImagenSegura(mensaje: Mensaje): void {
    if (!mensaje.imagen_url || this.imagenesSeguras.has(mensaje.id_mensaje)) {
      return;
    }
    this.http.get(mensaje.imagen_url, { responseType: 'blob' }).subscribe((blob) => {
      this.imagenesSeguras.set(mensaje.id_mensaje, URL.createObjectURL(blob));
    });
  }

  /** Corre después de que Angular ya pintó los mensajes nuevos en el DOM — sin el `setTimeout`, `scrollHeight` todavía mediría el alto de antes de agregar el mensaje. */
  private desplazarAlFinal(): void {
    setTimeout(() => {
      const contenedor = this.listaMensajesRef?.nativeElement;
      if (contenedor) {
        contenedor.scrollTop = contenedor.scrollHeight;
      }
    });
  }

  alElegirImagenMensaje(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0] ?? null;
    this.quitarImagenMensaje();
    this.imagenMensaje = archivo;
    this.previsualizacionImagenMensaje = archivo ? URL.createObjectURL(archivo) : null;
    input.value = ''; // permite elegir el mismo archivo dos veces seguidas (ej. si se saca y se vuelve a adjuntar) sin que el navegador se lo trague por ser el mismo path.
  }

  quitarImagenMensaje(): void {
    if (this.previsualizacionImagenMensaje) {
      URL.revokeObjectURL(this.previsualizacionImagenMensaje);
    }
    this.imagenMensaje = null;
    this.previsualizacionImagenMensaje = null;
  }

  insertarEmoji(emoji: string): void {
    const actual = this.formularioMensaje.controls.contenido.value;
    this.formularioMensaje.controls.contenido.setValue(actual + emoji);
  }

  get puedeEnviarMensaje(): boolean {
    return !this.enviandoMensaje && (!!this.formularioMensaje.value.contenido?.trim() || !!this.imagenMensaje);
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

  etiquetaEstado(estado: string | undefined): string {
    return this.contratacionesApi.etiquetaEstado(estado);
  }

  /**
   * "Avance del trabajo" — mismo `.ks-progress-steps` de 4 pasos que
   * contratacion_detalle.html (Solicitada/Confirmada/Pagada-en curso/
   * Completada), que el historial en lista de abajo no reemplaza (es un
   * resumen visual rápido, el historial es el detalle completo). Un paso
   * está "done" si el estado actual ya lo pasó (o es CANCELADA — ningún
   * paso más que "Solicitada" queda done ahí, mismo criterio que Django:
   * `estado != 'CANCELADA'` para el primer paso, índice-based para el resto),
   * "current" si es el paso inmediatamente siguiente al estado actual.
   */
  private readonly ORDEN_PASOS = ['SOLICITADA', 'CONFIRMADA', 'EN_CURSO', 'COMPLETADA'];

  clasePaso(paso: string): string {
    if (!this.contratacion) {
      return '';
    }
    const indicePaso = this.ORDEN_PASOS.indexOf(paso);
    const indiceEstado = this.ORDEN_PASOS.indexOf(this.contratacion.estado);
    if (indiceEstado === -1) {
      // CANCELADA: solo "Solicitada" (índice 0) queda marcada, igual que Django.
      return indicePaso === 0 ? 'done' : '';
    }
    if (indiceEstado >= indicePaso) {
      return 'done';
    }
    return indiceEstado === indicePaso - 1 ? 'current' : '';
  }

  fechaPaso(paso: string): string | null {
    return this.contratacion?.historial.find((h) => h.estado === paso)?.fecha ?? null;
  }

  enviarMensaje(): void {
    if (!this.puedeEnviarMensaje) {
      return;
    }
    this.enviandoMensaje = true;
    const { contenido } = this.formularioMensaje.getRawValue();
    const imagen = this.imagenMensaje ?? undefined;
    this.contratacionesApi.enviarMensaje(this.contratacionId, contenido.trim(), imagen).subscribe({
      next: (mensaje) => {
        this.mensajes = [...this.mensajes, mensaje];
        this.cargarImagenSegura(mensaje);
        this.formularioMensaje.reset({ contenido: '' });
        this.quitarImagenMensaje();
        this.mostrarEmojis = false;
        this.enviandoMensaje = false;
        this.desplazarAlFinal();
      },
      error: () => {
        this.enviandoMensaje = false;
      },
    });
  }

  /**
   * "Backup estilo WhatsApp" del chat, equivalente Ionic de
   * `conversacion_exportar_view` — el backend exige el JWT en el header
   * (no un `<a href>` común, mismo motivo que la foto de un mensaje, ver
   * `cargarImagenSegura`), así que se descarga como blob autenticado y se
   * dispara la descarga con un `<a download>` armado a mano. Verificado
   * solo en web (`:8100`) — en un WebView nativo (Android/iOS) el atributo
   * `download` de un `<a>` no está garantizado, queda pendiente probarlo
   * ahí si hace falta de verdad.
   */
  exportarChat(): void {
    if (this.exportandoChat) {
      return;
    }
    this.exportandoChat = true;
    this.errorExportarChat = null;
    this.contratacionesApi.exportarChat(this.contratacionId).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `chat_${this.contratacionId}.txt`;
        document.body.appendChild(enlace);
        enlace.click();
        document.body.removeChild(enlace);
        URL.revokeObjectURL(url);
        this.exportandoChat = false;
      },
      error: () => {
        this.exportandoChat = false;
        this.errorExportarChat = 'No se pudo exportar el chat.';
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
        this.retroalimentacion.exito('Contratación confirmada.');
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
        this.retroalimentacion.exito('Trabajo marcado como completado.');
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
