import { Component } from '@angular/core';

import { Tema } from '../../core/tema';

/** Botón sol/luna del header: cambia entre modo claro y oscuro en cualquier pantalla. */
@Component({
  selector: 'app-tema-toggle',
  template: `
    <ion-buttons>
      <ion-button (click)="alternar()" [attr.aria-label]="esOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'">
        <ion-icon slot="icon-only" [name]="esOscuro ? 'sunny-outline' : 'moon-outline'"></ion-icon>
      </ion-button>
    </ion-buttons>
  `,
  styles: [':host { display: contents; }'],
  standalone: false,
})
export class TemaToggleComponent {
  esOscuro = this.tema.obtenerActual() === 'dark';

  constructor(private readonly tema: Tema) {}

  alternar(): void {
    this.tema.alternar();
    this.esOscuro = this.tema.obtenerActual() === 'dark';
  }
}
