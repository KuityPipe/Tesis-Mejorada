import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { FooterComponent } from './footer/footer';

/**
 * Módulo de componentes reutilizables entre páginas — hoy solo
 * `FooterComponent` (ver footer/footer.ts). A diferencia de los módulos
 * "page" (CatalogoPageModule, etc.), `RouterModule` se importa acá
 * directamente en vez de depender del re-export de un `*-routing.module`,
 * porque `SharedModule` no tiene rutas propias.
 */
@NgModule({
  imports: [CommonModule, RouterModule],
  declarations: [FooterComponent],
  exports: [FooterComponent],
})
export class SharedModule {}
