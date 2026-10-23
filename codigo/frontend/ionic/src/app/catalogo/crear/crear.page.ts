import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { Auth, Usuario } from '../../core/auth';
import { TIPOS_SERVICIO } from '../../core/impacto';
import { Catalogos } from '../../registro/catalogos';
import { Publicaciones, PublicacionResumen } from '../publicaciones';

const OTRA_CATEGORIA = 'Otra';
const MAX_FOTOS = 8;
const MAX_DOCUMENTOS = 5;

export const LIMITES = { titulo: 80, subtitulo: 120, descripcion: 800 };

interface PuntoCalidad {
  texto: string;
  cumplido: boolean;
}

/**
 * Publicar un servicio — equivalente Ionic de `/servicios/crear/`
 * (`publicacion_crear_view`, `crear_publicacion.html`). Solo proveedores
 * (`auth.me()` + el mismo chequeo del lado servidor en `PublicacionCrearView`).
 *
 * Campos "inteligentes": contadores de caracteres, precio con prefijo `$`,
 * una barra de calidad que dice qué le falta a la publicación, y fotos con
 * zona de arrastre (se pueden sumar de a varias, quitar y elegir la portada).
 * A la derecha, una vista previa en vivo con tres modos que usan los mismos
 * componentes que el sitio real: la tarjeta del catálogo, la fila de la lista
 * y la página de detalle completa.
 */
@Component({
  selector: 'app-crear',
  templateUrl: './crear.page.html',
  styleUrls: ['./crear.page.scss'],
  standalone: false,
})
export class CrearPage implements OnInit, OnDestroy {
  readonly limites = LIMITES;
  readonly maxFotos = MAX_FOTOS;
  readonly maxDocumentos = MAX_DOCUMENTOS;

  formulario = this.fb.nonNullable.group({
    titulo: ['', [Validators.required, Validators.maxLength(LIMITES.titulo)]],
    sub_titulo: ['', Validators.maxLength(LIMITES.subtitulo)],
    descripcion_publicacion: ['', Validators.maxLength(LIMITES.descripcion)],
    categoria: ['', Validators.required],
    categoria_otra: [''],
    tipo_servicio: ['OTRO'],
    precio: [null as number | null, [Validators.required, Validators.min(1)]],
  });

  categorias: string[] = [];
  readonly tiposServicio = TIPOS_SERVICIO;
  readonly otraCategoria = OTRA_CATEGORIA;

  cargando = true;
  puedePublicar = false;
  usuario: Usuario | null = null;

  imagenesSeleccionadas: File[] = [];
  documentosSeleccionados: File[] = [];
  previewsImagenes: string[] = [];
  arrastrando = false;

  /** Cómo se ve la vista previa: tarjeta del catálogo, fila de la lista o página completa. */
  modoPreview: 'tarjeta' | 'fila' | 'pagina' = 'tarjeta';
  previewPub!: PublicacionResumen;

  enviando = false;
  enviadoOk = false;
  errorGeneral: string | null = null;
  imagenesRechazadas: string[] = [];
  documentosRechazados: string[] = [];

  private readonly suscripcion = new Subscription();

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly catalogos: Catalogos,
    private readonly api: Publicaciones,
    private readonly router: Router,
  ) {
    this.actualizarPreview();
  }

  ngOnInit(): void {
    this.catalogos.categorias().subscribe((categorias) => (this.categorias = categorias));
    this.suscripcion.add(this.formulario.valueChanges.subscribe(() => this.actualizarPreview()));
    this.auth.me().subscribe({
      next: (usuario) => {
        this.usuario = usuario;
        this.puedePublicar = usuario.es_proveedor;
        this.cargando = false;
        this.actualizarPreview();
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  ngOnDestroy(): void {
    this.suscripcion.unsubscribe();
    this.previewsImagenes.forEach((url) => URL.revokeObjectURL(url));
  }

  get categoriaPreview(): string {
    const { categoria, categoria_otra } = this.formulario.getRawValue();
    return categoria === OTRA_CATEGORIA ? (categoria_otra || '').trim() : categoria;
  }

  /** Reconstruye la publicación de ejemplo a partir de lo que la persona va escribiendo. */
  private actualizarPreview(): void {
    const valores = this.formulario.getRawValue();
    const resumen = (valores.descripcion_publicacion || '').trim();
    this.previewPub = {
      id_publicacion: 0,
      titulo: valores.titulo.trim() || 'Título de tu servicio',
      sub_titulo: valores.sub_titulo.trim() || 'Subtítulo breve del servicio',
      categoria: this.categoriaPreview || null,
      precio: valores.precio ? Number(valores.precio) : null,
      fecha_publicacion: new Date().toISOString(),
      imagen_portada: this.previewsImagenes[0] ?? null,
      resumen: resumen.length > 150 ? resumen.slice(0, 150).replace(/\s+\S*$/, '') + '…' : resumen || 'Aquí aparecerá un resumen de tu descripción.',
      distancia_km: null,
      proveedor: {
        id_usuario: this.usuario?.id_usuario ?? 0,
        nombre_usuario: this.usuario?.nombre_usuario ?? 'Tu nombre',
        apellido_usuario: this.usuario?.apellido_usuario ?? '',
        foto_perfil: this.usuario?.foto_perfil ?? null,
        comuna: null,
        region: null,
        puntuacion_promedio: null,
        total_valoraciones: 0,
        latitud: null,
        longitud: null,
      },
    };
  }

  /** Qué le falta a la publicación para quedar completa (alimenta la barra de calidad). */
  get calidad(): { porcentaje: number; puntos: PuntoCalidad[] } {
    const v = this.formulario.getRawValue();
    const puntos: PuntoCalidad[] = [
      { texto: 'Un título claro (15 letras o más)', cumplido: v.titulo.trim().length >= 15 },
      { texto: 'Una categoría', cumplido: !!this.categoriaPreview },
      { texto: 'Un precio de referencia', cumplido: !!v.precio && Number(v.precio) > 0 },
      { texto: 'Una descripción detallada (80 letras o más)', cumplido: (v.descripcion_publicacion || '').trim().length >= 80 },
      { texto: 'Al menos una foto de portada', cumplido: this.imagenesSeleccionadas.length > 0 },
    ];
    return { porcentaje: Math.round((puntos.filter((p) => p.cumplido).length / puntos.length) * 100), puntos };
  }

  get precioFormateado(): string {
    const precio = this.formulario.controls.precio.value;
    return precio ? `$${Number(precio).toLocaleString('es-CL')}` : '';
  }

  longitud(campo: 'titulo' | 'sub_titulo' | 'descripcion_publicacion'): number {
    return (this.formulario.controls[campo].value || '').length;
  }

  // ---- Fotos: se suman de a varias (también arrastrando), se quitan y se elige la portada ----
  alElegirImagenes(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.agregarImagenes(input.files ? Array.from(input.files) : []);
    input.value = '';
  }

  alSoltarImagenes(evento: DragEvent): void {
    evento.preventDefault();
    this.arrastrando = false;
    this.agregarImagenes(Array.from(evento.dataTransfer?.files ?? []).filter((f) => f.type.startsWith('image/')));
  }

  private agregarImagenes(archivos: File[]): void {
    const libres = MAX_FOTOS - this.imagenesSeleccionadas.length;
    archivos.slice(0, Math.max(libres, 0)).forEach((archivo) => {
      this.imagenesSeleccionadas.push(archivo);
      this.previewsImagenes.push(URL.createObjectURL(archivo));
    });
    this.actualizarPreview();
  }

  quitarImagen(indice: number): void {
    URL.revokeObjectURL(this.previewsImagenes[indice]);
    this.imagenesSeleccionadas.splice(indice, 1);
    this.previewsImagenes.splice(indice, 1);
    this.actualizarPreview();
  }

  hacerPortada(indice: number): void {
    if (indice === 0) return;
    const [archivo] = this.imagenesSeleccionadas.splice(indice, 1);
    const [url] = this.previewsImagenes.splice(indice, 1);
    this.imagenesSeleccionadas.unshift(archivo);
    this.previewsImagenes.unshift(url);
    this.actualizarPreview();
  }

  alElegirDocumentos(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const nuevos = input.files ? Array.from(input.files) : [];
    this.documentosSeleccionados = [...this.documentosSeleccionados, ...nuevos].slice(0, MAX_DOCUMENTOS);
    input.value = '';
  }

  quitarDocumento(indice: number): void {
    this.documentosSeleccionados.splice(indice, 1);
  }

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.errorGeneral = null;
    this.imagenesRechazadas = [];
    this.documentosRechazados = [];

    const valores = this.formulario.getRawValue();
    const datos = new FormData();
    datos.append('titulo', valores.titulo);
    datos.append('sub_titulo', valores.sub_titulo);
    datos.append('descripcion_publicacion', valores.descripcion_publicacion);
    datos.append('categoria', valores.categoria);
    datos.append('categoria_otra', valores.categoria_otra);
    datos.append('tipo_servicio', valores.tipo_servicio);
    datos.append('precio', String(valores.precio));
    this.imagenesSeleccionadas.forEach((archivo) => datos.append('imagenes', archivo));
    this.documentosSeleccionados.forEach((archivo) => datos.append('documentos', archivo));

    this.api.crear(datos).subscribe({
      next: (respuesta) => {
        this.enviando = false;
        this.imagenesRechazadas = respuesta.imagenes_rechazadas;
        this.documentosRechazados = respuesta.documentos_rechazados;
        this.enviadoOk = true;
        // Mismo destino que publicacion_crear_view tras crear: el detalle de la publicación recién creada.
        setTimeout(() => this.router.navigate(['/catalogo', respuesta.publicacion.id_publicacion]), 1500);
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        this.errorGeneral = typeof error.error === 'object' && error.error !== null
          ? Object.entries(error.error).filter(([clave]) => clave !== 'code').map(([, valor]) => valor).map((valor) => (Array.isArray(valor) ? valor.join(' ') : String(valor))).join(' ')
          : 'No se pudo crear la publicación. Prueba de nuevo en unos minutos.';
      },
    });
  }

  mensajeError(campo: string): string | null {
    const control = this.formulario.get(campo);
    if (!control || !control.touched || !control.errors) {
      return null;
    }
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['min']) return `Mínimo ${control.errors['min'].min}.`;
    if (control.errors['maxlength']) return `Máximo ${control.errors['maxlength'].requiredLength} caracteres.`;
    return 'Dato inválido.';
  }
}
