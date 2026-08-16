import { Component } from '@angular/core';

// Contador a nivel de módulo (no de instancia) — cada vez que Angular crea
// un TopNavComponent nuevo (una por cada navegación entre las 4 pantallas
// raíz, ver comentario de la clase) se lleva un id de trigger distinto.
let contadorInstancias = 0;

/**
 * Links de navegación superior — Inicio/Servicios/Acerca de nosotros/
 * Contacto, en el mismo renglón del header junto al logo (pedido
 * explícito del usuario: "la barra debería estar después del logo", un
 * solo renglón, no un segundo `ion-toolbar` aparte como en la primera
 * versión). El link activo (`.ks-nav-active`, ver global.scss) ya indica
 * en qué página está el usuario — no hace falta un `ion-title` aparte
 * repitiendo lo mismo.
 *
 * Separado de `AccountMenuComponent` (mismo directorio padre `shared/`) a
 * propósito: cada uno se usa como `<app-top-nav slot="start">`/
 * `<app-account-menu slot="end">` directo en el `ion-toolbar` de la
 * página — el atributo `slot` de Web Components solo distribuye hijos
 * DIRECTOS del shadow host (`ion-toolbar`); un `slot="start"` puesto en un
 * `<ion-buttons>` que vive dentro de OTRO componente Angular (un nieto de
 * `ion-toolbar`, no un hijo) no hace nada — el browser lo ignora y todo
 * el contenido cae en el slot por defecto (el área central de
 * `ion-title`), que es justo el bug que hizo que el logo y el resto del
 * header se vieran rotos/en dos renglones en la primera versión de este
 * componente (cuando intentaba resolver start+end en un solo `app-top-nav`).
 *
 * `idTrigger` con sufijo numérico (no un id fijo como "ks-nav-trigger" a
 * secas) — pedido del usuario tras notar que el menú "a veces se traba y
 * no muestra la lista". Cada navegación entre las 4 pantallas raíz
 * destruye la instancia vieja de este componente y crea una nueva; con
 * un id fijo reutilizado, el `<ion-popover trigger="...">` de turno busca
 * ese id por `document.getElementById` y puede quedarse mirando una
 * referencia obsoleta si el ciclo de destrucción/creación de Angular y el
 * de registro interno de Ionic no calzan perfecto (más probable si la
 * pestaña estuvo en segundo plano, que es justo lo que el usuario notó:
 * "puede pasar porque estoy en otra ventana"). Un id único por instancia
 * elimina esa colisión de raíz — no hay ningún id viejo con el que
 * confundirse.
 */
@Component({
  selector: 'app-top-nav',
  templateUrl: './top-nav.html',
  styleUrls: ['./top-nav.scss'],
  standalone: false,
})
export class TopNavComponent {
  readonly idTrigger = `ks-nav-trigger-${contadorInstancias++}`;
}
