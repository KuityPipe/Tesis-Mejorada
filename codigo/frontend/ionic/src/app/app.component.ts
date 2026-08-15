import { Component } from '@angular/core';

import { Notificaciones } from './core/notificaciones';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
export class AppComponent {
  // Arranca el polling del badge de mensajes (ver core/notificaciones.ts)
  // una sola vez para toda la vida de la app — el propio servicio se
  // encarga de no hacer nada mientras no haya sesión iniciada.
  constructor(private readonly notificaciones: Notificaciones) {
    this.notificaciones.iniciar();
  }
}
