import { Component } from '@angular/core';

/**
 * Página institucional estática — equivalente Ionic de `/acerca-de-nosotros/`
 * (`acerca_de_nosotros_view`, `Acercadeenosotros.html`). Sin backend: mismo
 * contenido fijo que el template Django, portado a mano. El carrusel
 * Bootstrap de "pilares" del template no tiene equivalente directo en
 * Ionic (no vale la pena traer una librería de carrusel para esto) — acá
 * los 4 pilares van en un grid estático (`.ks-feature-grid`), igual
 * contenido, sin el efecto de carrusel.
 */
@Component({
  selector: 'app-acerca',
  templateUrl: './acerca.page.html',
  styleUrls: ['./acerca.page.scss'],
  standalone: false,
})
export class AcercaPage {}
