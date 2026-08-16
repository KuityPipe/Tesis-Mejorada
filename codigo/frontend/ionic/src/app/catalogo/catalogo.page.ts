import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { InfiniteScrollCustomEvent } from '@ionic/angular';

import { Ubicacion } from '../core/ubicacion';
import { Catalogos, RegionCatalogo } from '../registro/catalogos';
import { FiltrosCatalogo, Publicaciones, PublicacionResumen } from './publicaciones';

/** Múltiplos de 3 km, como se definió con el usuario (ver docs/BACKLOG.md, "Búsqueda por geolocalización"). */
export const RADIOS_KM = [3, 6, 9, 12, 15, 18];

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
 *
 * Filtros (búsqueda/región/calificación/orden) — mismo `.ks-filter-bar`
 * que `catalogo.html` del sitio Django, mismos query params que ya acepta
 * `PublicacionListView` (`q`/`region`/`calificacion`/`orden`). `q` inicial
 * puede llegar por query param (`?q=...`) desde el buscador rápido del
 * home marketing (`inicio.page`), igual que el `<form method="get">` de
 * Django navega a `/servicios/?q=...`.
 */
@Component({
  selector: 'app-catalogo',
  templateUrl: './catalogo.page.html',
  styleUrls: ['./catalogo.page.scss'],
  standalone: false,
})
export class CatalogoPage implements OnInit {
  publicaciones: PublicacionResumen[] = [];
  regiones: RegionCatalogo[] = [];
  cargandoInicial = true;
  hayMas = true;
  /** Total de resultados del filtro actual (respuesta.count de DRF) — mismo dato que {{ total_publicaciones }} en catalogo.html. */
  total = 0;
  private pagina = 1;

  filtros: FiltrosCatalogo = { orden: 'recientes' };

  radiosKm = RADIOS_KM;
  /** true mientras se espera el permiso/posición del dispositivo — deshabilita el botón para no disparar dos pedidos de permiso en paralelo si el usuario lo toca dos veces. */
  buscandoUbicacion = false;
  /** true si ya se obtuvo una posición real — recién ahí se muestra el selector de radio; si el usuario negó el permiso, el filtro de radio no aparece (sin fallback a comuna todavía, ver core/ubicacion.ts). */
  ubicacionActiva = false;

  constructor(
    private readonly api: Publicaciones,
    private readonly catalogos: Catalogos,
    private readonly ubicacion: Ubicacion,
    private readonly ruta: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const qInicial = this.ruta.snapshot.queryParamMap.get('q');
    if (qInicial) {
      this.filtros.q = qInicial;
    }
    this.catalogos.regiones().subscribe({
      next: (regiones) => (this.regiones = regiones),
      error: () => {
        // Sin regiones el filtro por región queda vacío, pero el resto del catálogo sigue funcionando.
      },
    });
    this.cargarPagina();
  }

  cargarMas(evento: InfiniteScrollCustomEvent): void {
    this.pagina++;
    this.cargarPagina(evento);
  }

  /**
   * Se llama al tocar "Buscar cerca de mí" — pide la posición real del
   * dispositivo (`Ubicacion.posicionActual()`, cubre web y nativo con la
   * misma llamada) y, si el usuario da el permiso, la deja cargada en
   * `filtros.lat`/`lng` para que el catálogo empiece a mostrar
   * `distancia_km` y habilite el selector de radio. Si el usuario niega el
   * permiso o el dispositivo no puede resolver la posición, no rompe nada:
   * el catálogo sigue mostrando todo, sin filtro de radio.
   */
  async usarMiUbicacion(): Promise<void> {
    this.buscandoUbicacion = true;
    const posicion = await this.ubicacion.posicionActual();
    this.buscandoUbicacion = false;
    if (!posicion) {
      this.ubicacionActiva = false;
      return;
    }
    this.ubicacionActiva = true;
    this.filtros.lat = posicion.lat;
    this.filtros.lng = posicion.lng;
    this.aplicarFiltros();
  }

  /** Se llama al sacar el filtro de radio ("Ver todos") — la ubicación es un filtro de conveniencia, no un límite duro: siempre tiene que ser posible volver a ver el catálogo completo. */
  quitarUbicacion(): void {
    this.ubicacionActiva = false;
    delete this.filtros.lat;
    delete this.filtros.lng;
    delete this.filtros.radio_km;
    if (this.filtros.orden === 'cercania') {
      this.filtros.orden = 'recientes';
    }
    this.aplicarFiltros();
  }

  /** Se llama al tocar "Aplicar filtros" — reinicia la paginación en vez de acumular sobre resultados de otro filtro. */
  aplicarFiltros(): void {
    this.pagina = 1;
    this.publicaciones = [];
    this.hayMas = true;
    this.cargandoInicial = true;
    this.cargarPagina();
  }

  private cargarPagina(eventoScroll?: InfiniteScrollCustomEvent): void {
    this.api.listar(this.pagina, this.filtros).subscribe({
      next: (respuesta) => {
        // Se concatena, no se reemplaza — cada página nueva se agrega al
        // final de lo que ya había, que es justo lo que necesita el
        // scroll infinito (a diferencia de la paginación por botones del
        // template, donde cada página reemplaza a la anterior).
        this.publicaciones = [...this.publicaciones, ...respuesta.results];
        this.total = respuesta.count;
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
