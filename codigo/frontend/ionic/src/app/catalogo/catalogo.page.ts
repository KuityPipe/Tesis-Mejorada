import { Component, OnInit } from '@angular/core';
import { InfiniteScrollCustomEvent } from '@ionic/angular';

import { Auth } from '../core/auth';
import { Publicaciones, PublicacionResumen } from './publicaciones';

/**
 * Catálogo público (Fase 2 del plan de migración, ver
 * docs/PLAN_MIGRACION_IONIC.md) — equivalente Ionic de `/servicios/`
 * (catalogo_view en views.py). Sin guard: es pública a propósito.
 *
 * Pagina con scroll infinito en vez de botones "anterior/siguiente" como
 * el template Django — más natural en mobile. `ion-infinite-scroll`
 * dispara `(ionInfinite)` cuando el usuario llega cerca del final de la
 * lista; `[disabled]="!hayMas"` lo apaga solo cuando el backend ya no
 * tiene más páginas (`respuesta.next === null`, el mismo campo que arma
 * `PageNumberPagination` de DRF).
 */
@Component({
  selector: 'app-catalogo',
  templateUrl: './catalogo.page.html',
  styleUrls: ['./catalogo.page.scss'],
  standalone: false,
})
export class CatalogoPage implements OnInit {
  publicaciones: PublicacionResumen[] = [];
  cargandoInicial = true;
  hayMas = true;
  private pagina = 1;

  constructor(
    private readonly api: Publicaciones,
    readonly auth: Auth,
  ) {}

  ngOnInit(): void {
    this.cargarPagina();
  }

  cargarMas(evento: InfiniteScrollCustomEvent): void {
    this.pagina++;
    this.cargarPagina(evento);
  }

  private cargarPagina(eventoScroll?: InfiniteScrollCustomEvent): void {
    this.api.listar(this.pagina).subscribe({
      next: (respuesta) => {
        // Se concatena, no se reemplaza — cada página nueva se agrega al
        // final de lo que ya había, que es justo lo que necesita el
        // scroll infinito (a diferencia de la paginación por botones del
        // template, donde cada página reemplaza a la anterior).
        this.publicaciones = [...this.publicaciones, ...respuesta.results];
        this.hayMas = respuesta.next !== null;
        this.cargandoInicial = false;
        eventoScroll?.target.complete();
      },
      error: () => {
        this.cargandoInicial = false;
        eventoScroll?.target.complete();
      },
    });
  }
}
