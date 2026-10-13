import { Component, Input } from '@angular/core';

/**
 * Animación de verificación lograda (el "momento estrella" de la propuesta de la Fase 6): un anillo que se llena y
 * un visto que se dibuja. Con `prefers-reduced-motion` aparece ya completa, sin animar. El anuncio para lector de
 * pantalla viaja en el `role="status"` (no en el dibujo, que es decorativo).
 */
@Component({
  selector: 'app-verif-exito',
  templateUrl: './verif-exito.html',
  styleUrls: ['./verif-exito.scss'],
  standalone: false,
})
export class VerifExitoComponent {
  @Input() mensaje = 'Identidad verificada';
}
