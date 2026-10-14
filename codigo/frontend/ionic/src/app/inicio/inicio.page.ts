import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { Auth } from '../core/auth';
import { Publicaciones, PublicacionResumen } from '../catalogo/publicaciones';

/**
 * Home marketing público — equivalente Ionic de `/` (`paginicio_view`,
 * `paginicio.html`). Antes la ruta raíz (`''`) redirigía directo a
 * `/catalogo`; ahora `/catalogo` sigue siendo el listado completo
 * (equivalente de `/servicios/`) y esta página es la landing con
 * presentación de marca + búsqueda rápida, igual que el sitio Django
 * distingue `/` de `/servicios/`.
 *
 * "Destacadas" reusa `Publicaciones.listar()` (mismo cliente que usa
 * `catalogo.page`) en vez de un endpoint nuevo — el backend ya devuelve
 * las publicaciones aprobadas ordenadas por más recientes por defecto
 * (`orden=recientes`, ver `PublicacionListView`), así que alcanza con
 * quedarse con las primeras 4 de la página 1, mismo criterio que
 * `paginicio_view` (`[:4]`).
 */
@Component({
  selector: 'app-inicio',
  templateUrl: './inicio.page.html',
  styleUrls: ['./inicio.page.scss'],
  standalone: false,
})
export class InicioPage implements OnInit, AfterViewInit, OnDestroy {
  destacadas: PublicacionResumen[] = [];
  cargandoDestacadas = true;
  q = '';

  /** Categorías de la portada: nombre visible, término de búsqueda (sin tildes) e ícono de fondo. */
  readonly categorias = [
    { nombre: 'Gasfitería', q: 'gasfiteria', icono: 'water-outline', foto: 'reparaciones' },
    { nombre: 'Electricidad', q: 'electricidad', icono: 'flash-outline', foto: 'electricidad' },
    { nombre: 'Jardinería', q: 'jardineria', icono: 'leaf-outline', foto: 'jardineria' },
    { nombre: 'Limpieza y aseo', q: 'limpieza', icono: 'sparkles-outline', foto: 'limpieza' },
    { nombre: 'Pintura', q: 'pintura', icono: 'color-palette-outline', foto: 'pintura' },
    { nombre: 'Carpintería', q: 'carpinteria', icono: 'hammer-outline', foto: 'carpinteria' },
    { nombre: 'Mudanzas', q: 'mudanzas', icono: 'cube-outline', foto: 'mudanzas' },
    { nombre: 'Cerrajería', q: 'cerrajeria', icono: 'key-outline', foto: 'cerrajeria' },
    { nombre: 'Clases particulares', q: 'clases', icono: 'school-outline', foto: 'clases' },
    { nombre: 'Programación', q: 'programacion', icono: 'code-slash-outline', foto: 'programacion' },
    { nombre: 'Cuidado de personas', q: 'cuidado', icono: 'heart-outline', foto: 'cuidado' },
    { nombre: 'Cocina y catering', q: 'cocina', icono: 'restaurant-outline', foto: 'cocina' },
  ];

  /** "Acerca de nosotros": un carrusel con una diapositiva por tema. */
  readonly acercaSlides = [
    {
      id: 'acerca',
      icono: 'key-outline',
      etiqueta: 'Acerca de nosotros',
      titulo: 'Acerca de nosotros',
      subtitulo: '«Contratar un servicio para tu casa no debería sentirse como una apuesta.» Esa es la idea que le dio partida a KeyServ: una plataforma chilena que conecta a quien necesita un servicio con proveedores verificados de verdad, para que sepas con quién estás tratando antes de dejarlo entrar a tu casa.',
      tarjetas: [
        { icono: 'finger-print-outline', titulo: 'Identidad verificada', texto: 'Biometría del teléfono, reconocimiento facial o revisión de documento.' },
        { icono: 'card-outline', titulo: 'Pagos seguros', texto: 'Con Webpay o transferencia; nunca vemos los datos de tu tarjeta.' },
        { icono: 'key-outline', titulo: 'Tus datos, tu control', texto: 'Descarga, corrige, bloquea o elimina lo que quieras cuando quieras.' },
      ],
    },
    {
      id: 'quienes',
      icono: 'people-outline',
      etiqueta: 'Quiénes somos',
      titulo: 'Quiénes somos',
      subtitulo: 'Un equipo pequeño con una pregunta simple, y lo que queremos lograr con ella.',
      tarjetas: [
        { icono: 'locate-outline', titulo: 'Nuestra misión', texto: 'Hacer que contratar servicios del hogar sea simple y seguro, con la tranquilidad de una identidad verificada en ambos extremos de la conexión.' },
        { icono: 'telescope-outline', titulo: 'Nuestra visión', texto: 'Ser la plataforma de referencia en Chile para contratar con confianza, reconocida por su seguridad, su transparencia y lo cercana que se siente.' },
        { icono: 'people-outline', titulo: 'Nuestro equipo', texto: '¿Por qué es tan difícil confiar en quién entra a tu casa a hacer un trabajo? De ahí salió KeyServ. Seguimos siendo un equipo chico y preferimos resolverlo bien antes que rápido.' },
      ],
    },
    {
      id: 'pilares',
      icono: 'shield-checkmark-outline',
      etiqueta: 'Nuestros pilares',
      titulo: 'Nuestros pilares',
      subtitulo: 'Los cuatro principios con los que se diseña cada parte de la plataforma.',
      tarjetas: [
        { icono: 'shield-checkmark-outline', titulo: 'Confianza real', texto: 'Cada persona verifica su identidad con la biometría de su teléfono, con reconocimiento facial o, si prefiere no usar biometría, con un código por correo y la revisión de su documento.' },
        { icono: 'heart-outline', titulo: 'Cercanía', texto: 'Cada consulta que llega a soporte la revisa una persona, no un bot. Y detrás de cada calificación hay un trabajo que realmente se completó.' },
        { icono: 'eye-outline', titulo: 'Transparencia', texto: 'Ves el precio antes de contratar, el historial completo de cada trabajo y calificaciones moderadas antes de publicarse.' },
        { icono: 'hardware-chip-outline', titulo: 'Tecnología accesible', texto: 'Verificar tu identidad no debería sentirse como un trámite bancario: tecnología biométrica en serio, sin filas ni papeleo.' },
      ],
    },
    {
      id: 'tolerancia',
      icono: 'hand-left-outline',
      etiqueta: 'Lo que no toleramos',
      titulo: 'Lo que no estamos dispuestos a tolerar',
      subtitulo: 'Cuatro cosas que la plataforma está hecha para evitar.',
      tarjetas: [
        { icono: 'thumbs-down-outline', titulo: 'Aprovechamiento', texto: 'Ni de un lado ni del otro: cliente y proveedor parten en igualdad de condiciones.' },
        { icono: 'lock-closed-outline', titulo: 'Fraude y robos', texto: 'Identidad verificada en ambos lados: nadie entra a ciegas.' },
        { icono: 'flag-outline', titulo: 'Reseñas falsas', texto: 'Toda calificación pasa por moderación antes de publicarse: nadie compra una buena reputación.' },
        { icono: 'ban-outline', titulo: 'Malos tratos', texto: 'Cero tolerancia al abuso: cualquier intento sospechoso queda registrado y se revisa.' },
      ],
    },
  ];

  slideActivo = 0;

  constructor(
    private readonly api: Publicaciones,
    private readonly router: Router,
    private readonly auth: Auth,
    private readonly ruta: ActivatedRoute,
  ) {}

  @ViewChild('pista') private readonly pistaRef?: ElementRef<HTMLElement>;
  private observador?: ResizeObserver;

  /** `true` mientras se arrastra con el mouse: apaga el imán del scroll para que el carrusel siga el puntero. */
  arrastrando = false;
  private arrastre: { x: number; scroll: number; indice: number; movido: boolean } | null = null;

  /** Lleva el carrusel de "Acerca de nosotros" a una diapositiva. */
  irASlide(carrusel: HTMLElement, indice: number): void {
    const reducido = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    carrusel.scrollTo({ left: indice * carrusel.clientWidth, behavior: reducido ? 'auto' : 'smooth' });
  }

  moverSlide(carrusel: HTMLElement, sentido: 1 | -1): void {
    const total = this.acercaSlides.length;
    this.irASlide(carrusel, (this.slideActivo + sentido + total) % total);
  }

  /** Mantiene resaltada la pestaña de la diapositiva que se está viendo. */
  alScrollearCarrusel(carrusel: HTMLElement): void {
    const indice = Math.round(carrusel.scrollLeft / carrusel.clientWidth);
    if (indice !== this.slideActivo) {
      this.slideActivo = indice;
      this.ajustarAltura(carrusel);
    }
  }

  /** El carrusel mide lo que mide el tema que se ve, no el más largo: así no queda un hueco bajo los temas cortos. */
  private ajustarAltura(carrusel: HTMLElement): void {
    const slide = carrusel.children[this.slideActivo] as HTMLElement | undefined;
    if (slide) carrusel.style.height = `${slide.offsetHeight + 18}px`;
  }

  ngAfterViewInit(): void {
    const carrusel = this.pistaRef?.nativeElement;
    if (!carrusel || typeof ResizeObserver === 'undefined') return;
    this.observador = new ResizeObserver(() => this.ajustarAltura(carrusel));
    Array.from(carrusel.children).forEach((slide) => this.observador?.observe(slide));
  }

  ngOnDestroy(): void {
    this.observador?.disconnect();
  }

  /** Con el dedo el scroll horizontal ya es nativo; el mouse necesita arrastre propio. */
  iniciarArrastre(evento: PointerEvent, carrusel: HTMLElement): void {
    if (evento.pointerType !== 'mouse' || evento.button !== 0) return;
    this.arrastre = { x: evento.clientX, scroll: carrusel.scrollLeft, indice: this.slideActivo, movido: false };
  }

  moverArrastre(evento: PointerEvent, carrusel: HTMLElement): void {
    const a = this.arrastre;
    if (!a) return;
    const dx = evento.clientX - a.x;
    if (!a.movido) {
      if (Math.abs(dx) < 6) return;
      a.movido = true;
      this.arrastrando = true;
      carrusel.setPointerCapture(evento.pointerId);
    }
    carrusel.scrollLeft = a.scroll - dx;
  }

  terminarArrastre(evento: PointerEvent, carrusel: HTMLElement): void {
    const a = this.arrastre;
    this.arrastre = null;
    if (!a || !a.movido) return;
    const dx = evento.clientX - a.x;
    let indice = Math.round(carrusel.scrollLeft / carrusel.clientWidth);
    // Un arrastre corto pero decidido también cambia de tema, como al deslizar con el dedo.
    if (Math.abs(dx) > 50) indice = a.indice + (dx < 0 ? 1 : -1);
    indice = Math.max(0, Math.min(this.acercaSlides.length - 1, indice));
    this.irASlide(carrusel, indice);
    // El imán se reactiva cuando termina la animación, para que no pegue un salto.
    setTimeout(() => (this.arrastrando = false), 450);
  }

  /** El aviso "¿Ofreces servicios?" invita a registrarse: solo tiene sentido sin sesión. */
  get conSesion(): boolean {
    return this.auth.estaAutenticado();
  }

  ngOnInit(): void {
    // `/#acerca` (los links "Acerca de nosotros") baja directo a esa sección.
    this.ruta.fragment.subscribe((fragmento) => {
      if (fragmento) setTimeout(() => document.getElementById(fragmento)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 450);
    });
    this.api.listar(1).subscribe({
      next: (respuesta) => {
        this.destacadas = respuesta.results.slice(0, 4);
        this.cargandoDestacadas = false;
      },
      error: () => {
        this.cargandoDestacadas = false;
      },
    });
  }

  /** Mismo destino que el `<form method="get" action="{% url 'catalogo' %}">` de paginicio.html — navega al catálogo completo con `q` como query param. */
  buscar(): void {
    this.router.navigate(['/catalogo'], { queryParams: this.q ? { q: this.q } : {} });
  }

  /** Lleva la vista a la sección de servicios (el botón "Desliza" del hero). */
  irAServicios(): void {
    document.getElementById('servicios')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  buscarTag(termino: string): void {
    this.router.navigate(['/catalogo'], { queryParams: { q: termino } });
  }
}
