import { Component, OnDestroy } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

import { Notificaciones } from './core/notificaciones';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
export class AppComponent implements OnDestroy {
  private readonly suscripcion: Subscription;
  private elementoScroll: HTMLElement | null = null;
  private readonly alScrollear = () => {
    if (!this.elementoScroll) return;
    // La barrita de colores del header se desplaza con el scroll (ver `ion-toolbar::after` en global.scss).
    // Avance real por la página (0 arriba, 100 al final): el color recorre toda la barra de principio a fin, sin importar el largo.
    const { scrollTop, scrollHeight, clientHeight } = this.elementoScroll;
    const avance = scrollHeight > clientHeight ? (scrollTop / (scrollHeight - clientHeight)) * 100 : 0;
    document.documentElement.style.setProperty('--ks-barra-x', `${avance.toFixed(1)}%`);
  };

  // Arranca el polling del badge de mensajes (ver core/notificaciones.ts)
  // una sola vez para toda la vida de la app — el propio servicio se
  // encarga de no hacer nada mientras no haya sesión iniciada.
  constructor(private readonly notificaciones: Notificaciones, router: Router) {
    this.notificaciones.iniciar();
    this.suscripcion = router.events.pipe(filter((e) => e instanceof NavigationEnd)).subscribe(() => {
      // Espera a que Ionic termine de montar la página nueva antes de buscar su contenedor de scroll.
      setTimeout(() => this.engancharScroll(), 350);
    });
  }

  private async engancharScroll(): Promise<void> {
    this.elementoScroll?.removeEventListener('scroll', this.alScrollear);
    const paginas = document.querySelectorAll('.ion-page:not(.ion-page-hidden) ion-content');
    const contenido = paginas[paginas.length - 1] as (HTMLElement & { getScrollElement?: () => Promise<HTMLElement> }) | undefined;
    this.elementoScroll = contenido?.getScrollElement ? await contenido.getScrollElement() : null;
    this.elementoScroll?.addEventListener('scroll', this.alScrollear, { passive: true });
    document.documentElement.style.setProperty('--ks-barra-x', '0%');
  }

  ngOnDestroy(): void {
    this.suscripcion.unsubscribe();
    this.elementoScroll?.removeEventListener('scroll', this.alScrollear);
  }
}
