import { Component, Input } from '@angular/core';

/**
 * Skeleton screen compartido — reemplaza el `<ion-spinner>` centrado que
 * usaban catálogo/reservas/mensajes mientras cargan. Un spinner no dice
 * nada sobre la forma del contenido que viene; un skeleton con la silueta
 * real (foto + 2 líneas para una card, avatar + 2 líneas para una fila)
 * hace que la espera se sienta más corta y evita el "salto" de layout
 * cuando el contenido real reemplaza al spinner — el punto que señala la
 * investigación de skeleton screens vs. loading indicators.
 *
 * `ion-skeleton-text` (con `animated`) ya trae el efecto shimmer nativo de
 * Ionic — no hace falta reinventarlo, solo darle la forma correcta según
 * `variante`.
 */
@Component({
  selector: 'app-skeleton',
  templateUrl: './skeleton.html',
  styleUrls: ['./skeleton.scss'],
  standalone: false,
})
export class SkeletonComponent {
  @Input() variante: 'card' | 'fila' = 'card';
  @Input() cantidad = 4;

  get repeticiones(): number[] {
    return Array.from({ length: this.cantidad }, (_, i) => i);
  }
}
