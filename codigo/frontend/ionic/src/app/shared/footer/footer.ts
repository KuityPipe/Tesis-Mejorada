import { Component } from '@angular/core';

/**
 * Footer compartido (marca + links + copyright) — equivalente Ionic del
 * `<footer class="ks-footer">` de `base.html` en el sitio Django, que
 * aparece en todas las páginas del sitio. Acá se usa solo en las pantallas
 * "raíz" (login/inicio/catálogo/home — las que tienen logo en el header,
 * ver el comentario sobre `.ks-toolbar-logo` en CLAUDE.md), no en las
 * alcanzadas con botón "atrás", igual criterio que ya se usó para el logo.
 *
 * Componente aparte en `app/shared/` (no repetido por página) para no
 * duplicar el mismo bloque de HTML+links en 4 lugares — se declara/exporta
 * una sola vez en `SharedModule` e importa donde haga falta.
 */
@Component({
  selector: 'app-footer',
  templateUrl: './footer.html',
  styleUrls: ['./footer.scss'],
  standalone: false,
})
export class FooterComponent {
  readonly anioActual = new Date().getFullYear();
}
