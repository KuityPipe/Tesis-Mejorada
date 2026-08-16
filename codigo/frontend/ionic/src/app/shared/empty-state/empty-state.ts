import { Component, Input } from '@angular/core';

/**
 * Estado vacío compartido — hasta ahora cada pantalla con una lista que
 * puede venir vacía (reservas, mensajes, "Mis publicaciones") resolvía
 * eso con un `<ion-text>` de una sola línea de texto gris. La
 * investigación de patrones 2026 (empty states "activos", no solo un
 * aviso pasivo) es clara: ícono + mensaje + una acción concreta de
 * regreso convierte un callejón sin salida en el siguiente paso obvio —
 * por eso `ctaTexto`/`ctaLink` son opcionales pero casi siempre se pasan.
 *
 * Un solo componente en vez de repetir el mismo bloque de HTML en cada
 * página, mismo criterio que `FooterComponent`.
 */
@Component({
  selector: 'app-empty-state',
  templateUrl: './empty-state.html',
  styleUrls: ['./empty-state.scss'],
  standalone: false,
})
export class EmptyStateComponent {
  @Input() icono = 'file-tray-outline';
  @Input() titulo = 'Nada por acá todavía';
  @Input() mensaje?: string;
  @Input() ctaTexto?: string;
  @Input() ctaLink?: string | (string | number)[];
}
