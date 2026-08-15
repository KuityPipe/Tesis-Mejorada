import { Component, OnInit } from '@angular/core';

import { Publicaciones, PublicacionPropia } from '../../catalogo/publicaciones';

const COLOR_ESTADO: Record<string, string> = {
  PENDIENTE: 'warning',
  APROBADA: 'success',
  RECHAZADA: 'danger',
};

/**
 * Mis publicaciones — equivalente Ionic de la sección "Mis publicaciones"
 * de `perfil.html` (Django), acá como pantalla propia en vez de una
 * sección dentro de `home.page` para no seguir sobrecargando esa pantalla
 * (que ya reemplaza a `/inicio/`, no a `/perfil/`). Muestra cualquier
 * estado_moderacion (pendiente/aprobada/rechazada) — a diferencia del
 * catálogo público, acá el dueño necesita ver el estado real.
 */
@Component({
  selector: 'app-publicaciones',
  templateUrl: './publicaciones.page.html',
  styleUrls: ['./publicaciones.page.scss'],
  standalone: false,
})
export class PublicacionesPage implements OnInit {
  publicaciones: PublicacionPropia[] = [];
  cargando = true;

  constructor(private readonly api: Publicaciones) {}

  ngOnInit(): void {
    this.api.mias().subscribe({
      next: (publicaciones) => {
        this.publicaciones = publicaciones;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  colorEstado(estado: string): string {
    return COLOR_ESTADO[estado] ?? 'medium';
  }
}
