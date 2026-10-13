import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

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
export class InicioPage implements OnInit {
  destacadas: PublicacionResumen[] = [];
  cargandoDestacadas = true;
  q = '';

  /** Categorías de la portada: nombre visible, término de búsqueda (sin tildes) e ícono de fondo. */
  readonly categorias = [
    { nombre: 'Gasfitería', q: 'gasfiteria', icono: 'water-outline' },
    { nombre: 'Electricidad', q: 'electricidad', icono: 'flash-outline' },
    { nombre: 'Jardinería', q: 'jardineria', icono: 'leaf-outline' },
    { nombre: 'Limpieza', q: 'limpieza', icono: 'sparkles-outline' },
    { nombre: 'Pintura', q: 'pintura', icono: 'color-palette-outline' },
    { nombre: 'Carpintería', q: 'carpinteria', icono: 'hammer-outline' },
    { nombre: 'Mudanzas', q: 'mudanzas', icono: 'cube-outline' },
    { nombre: 'Cerrajería', q: 'cerrajeria', icono: 'key-outline' },
  ];

  constructor(
    private readonly api: Publicaciones,
    private readonly router: Router,
    private readonly auth: Auth,
  ) {}

  /** El aviso "¿Ofreces servicios?" invita a registrarse: solo tiene sentido sin sesión. */
  get conSesion(): boolean {
    return this.auth.estaAutenticado();
  }

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

  /** Lleva la vista a la sección de servicios (el botón "Desliza" del hero). */
  irAServicios(): void {
    document.getElementById('servicios')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  buscarTag(termino: string): void {
    this.router.navigate(['/catalogo'], { queryParams: { q: termino } });
  }
}
