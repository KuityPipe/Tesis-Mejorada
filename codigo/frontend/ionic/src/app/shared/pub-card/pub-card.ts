import { Component, Input } from '@angular/core';

import { PublicacionResumen } from '../../catalogo/publicaciones';

/**
 * Tarjeta de una publicación con vista previa animada: foto a tarjeta completa y, al pasar el mouse o enfocarla con
 * el teclado, un panel de vidrio sube con el resumen, el proveedor, su calificación y el botón para abrirla (una
 * mini-versión de la página de detalle). En pantallas táctiles no hay "hover", así que el resumen queda siempre visible.
 * Se usa en el catálogo y en los destacados del inicio.
 */
@Component({
  selector: 'app-pub-card',
  templateUrl: './pub-card.html',
  styleUrls: ['./pub-card.scss'],
  standalone: false,
})
export class PubCardComponent {
  @Input({ required: true }) publicacion!: PublicacionResumen;
  /** `tarjeta` (foto grande con vista previa al pasar el mouse) o `fila` (lista horizontal con más detalle a la vista). */
  @Input() modo: 'tarjeta' | 'fila' = 'tarjeta';

  alFallarFoto(): void {
    this.publicacion.imagen_portada = null;
  }
}
