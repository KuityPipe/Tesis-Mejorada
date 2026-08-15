import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { Auth } from '../../core/auth';
import { Catalogos } from '../../registro/catalogos';
import { Publicaciones } from '../publicaciones';

const OTRA_CATEGORIA = 'Otra';

/**
 * Publicar un servicio — equivalente Ionic de `/servicios/crear/`
 * (`publicacion_crear_view`, `crear_publicacion.html`). Solo proveedores:
 * a diferencia de otras pantallas protegidas solo por `authGuard` (JWT
 * presente), acá además hay que confirmar `es_proveedor` con un
 * `auth.me()` — mismo chequeo que hace la vista Django, del lado
 * servidor (`PublicacionCrearView` también lo valida, esto es solo para
 * no dejar completar un formulario que el backend va a rechazar igual).
 *
 * Sin el carrusel/selector-acumulativo de archivos que tiene
 * `crear_publicacion.html` (JS a medida solo para esa pantalla) — se
 * sigue el mismo patrón simple que ya usan `perfil/proveedor` y
 * `contratacion/detalle` para archivos múltiples (un `<input multiple>`
 * nativo, se reemplaza si se vuelve a abrir el picker). La previsualización
 * en vivo de texto sí se mantiene (más barata acá: `valueChanges` de un
 * Reactive Form) y las fotos elegidas se muestran en una grilla simple de
 * miniaturas, sin carrusel.
 */
@Component({
  selector: 'app-crear',
  templateUrl: './crear.page.html',
  styleUrls: ['./crear.page.scss'],
  standalone: false,
})
export class CrearPage implements OnInit {
  formulario = this.fb.nonNullable.group({
    titulo: ['', Validators.required],
    sub_titulo: [''],
    descripcion_publicacion: [''],
    categoria: ['', Validators.required],
    categoria_otra: [''],
    precio: [null as number | null, [Validators.required, Validators.min(1)]],
  });

  categorias: string[] = [];
  readonly otraCategoria = OTRA_CATEGORIA;

  cargando = true;
  puedePublicar = false;

  imagenesSeleccionadas: File[] = [];
  documentosSeleccionados: File[] = [];
  previewsImagenes: string[] = [];

  enviando = false;
  enviadoOk = false;
  errorGeneral: string | null = null;
  imagenesRechazadas: string[] = [];
  documentosRechazados: string[] = [];

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly catalogos: Catalogos,
    private readonly api: Publicaciones,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.catalogos.categorias().subscribe((categorias) => (this.categorias = categorias));
    this.auth.me().subscribe({
      next: (usuario) => {
        this.puedePublicar = usuario.es_proveedor;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  // "Así se ve tu publicación" — la parte de texto de la previsualización de crear_publicacion.html, portada 1:1 con valueChanges en vez de listeners de input a mano.
  get preview() {
    return this.formulario.getRawValue();
  }

  get categoriaPreview(): string {
    const { categoria, categoria_otra } = this.formulario.getRawValue();
    return categoria === OTRA_CATEGORIA ? (categoria_otra || '').trim() : categoria;
  }

  alElegirImagenes(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.imagenesSeleccionadas = input.files ? Array.from(input.files) : [];
    this.previewsImagenes.forEach((url) => URL.revokeObjectURL(url));
    this.previewsImagenes = this.imagenesSeleccionadas.map((archivo) => URL.createObjectURL(archivo));
  }

  alElegirDocumentos(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.documentosSeleccionados = input.files ? Array.from(input.files) : [];
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
          ? Object.values(error.error).map((valor) => (Array.isArray(valor) ? valor.join(' ') : String(valor))).join(' ')
          : 'No se pudo crear la publicación. Probá de nuevo en unos minutos.';
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
    return 'Dato inválido.';
  }
}
