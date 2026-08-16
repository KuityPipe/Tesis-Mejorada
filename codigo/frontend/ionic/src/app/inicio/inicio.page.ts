import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

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
export class InicioPage implements OnInit {
  destacadas: PublicacionResumen[] = [];
  cargandoDestacadas = true;
  q = '';

  constructor(
    private readonly api: Publicaciones,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
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

  buscarTag(termino: string): void {
    this.router.navigate(['/catalogo'], { queryParams: { q: termino } });
  }
}
