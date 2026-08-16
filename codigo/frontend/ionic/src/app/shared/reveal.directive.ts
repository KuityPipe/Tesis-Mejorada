import { AfterViewInit, Directive, ElementRef, Input, OnDestroy } from '@angular/core';

/**
 * `appReveal` — hace que el elemento aparezca con un fade+slide-up suave
 * al entrar en el viewport, en vez de aparecer de golpe apenas Angular
 * termina de pintar la lista (que es lo que pasaba en catálogo/reservas/
 * mensajes hasta ahora). Mismo patrón "scroll-triggered reveal" que usan
 * los sitios corporativos de referencia investigados (Hostinger, Canva,
 * tendencias SaaS 2026) — motion con propósito (guía la vista), no
 * decorativo, y se apaga solo si el usuario pidió `prefers-reduced-motion`
 * (ver la media query en global.scss, no acá: la clase se agrega igual,
 * es el CSS el que decide si hay transición o el estado final se aplica
 * directo).
 *
 * `[appRevealDelay]` (ms) permite escalonar varios elementos de una misma
 * lista (ver catalogo.page.html/reservas.page.html: `[appRevealDelay]="i * 60"`
 * con `*ngFor="let x of lista; let i = index"`) para que entren en cascada
 * en vez de todos a la vez.
 *
 * IntersectionObserver en vez de un `(scroll)` a mano: nativo del
 * navegador, no dispara en cada pixel de scroll (mejor para
 * rendimiento/Core Web Vitals, mismo punto que señala la investigación de
 * tendencias 2026) y funciona igual en `ion-content` (que ya expone su
 * scroller real vía `::part(scroll)`, no hace falta nada especial).
 */
@Directive({
  selector: '[appReveal]',
  standalone: false,
})
export class RevealDirective implements AfterViewInit, OnDestroy {
  @Input() appRevealDelay = 0;

  private observador?: IntersectionObserver;

  constructor(private readonly elementRef: ElementRef<HTMLElement>) {}

  ngAfterViewInit(): void {
    const elemento = this.elementRef.nativeElement;
    elemento.classList.add('ks-reveal');
    elemento.style.transitionDelay = `${this.appRevealDelay}ms`;

    if (typeof IntersectionObserver === 'undefined') {
      // Entorno de test (jsdom) u otro sin soporte real — se muestra directo, no hay animación que verificar.
      elemento.classList.add('ks-revealed');
      return;
    }

    this.observador = new IntersectionObserver(
      (entradas) => {
        for (const entrada of entradas) {
          if (entrada.isIntersecting) {
            elemento.classList.add('ks-revealed');
            this.observador?.unobserve(elemento);
          }
        }
      },
      { threshold: 0.1 },
    );
    this.observador.observe(elemento);
  }

  ngOnDestroy(): void {
    this.observador?.disconnect();
  }
}
