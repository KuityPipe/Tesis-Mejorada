import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';

import { FooterComponent } from './footer/footer';
import { EmptyStateComponent } from './empty-state/empty-state';
import { SkeletonComponent } from './skeleton/skeleton';
import { RevealDirective } from './reveal.directive';
import { TopNavComponent } from './top-nav/top-nav';
import { AccountMenuComponent } from './account-menu/account-menu';

/**
 * Módulo de componentes/directivas reutilizables entre páginas —
 * `FooterComponent` (ver footer/footer.ts) más, desde el pulido de
 * microinteracciones (base de animaciones/estados vacíos/skeletons
 * inspirada en patrones de sitios corporativos 2026), `EmptyStateComponent`,
 * `SkeletonComponent` y `RevealDirective` (`appReveal`). `IonicModule` se
 * agrega acá porque `EmptyStateComponent`/`SkeletonComponent` usan
 * `ion-icon`/`ion-button`/`ion-skeleton-text` en su propio template. A
 * diferencia de los módulos "page" (CatalogoPageModule, etc.),
 * `RouterModule` se importa acá directamente en vez de depender del
 * re-export de un `*-routing.module`, porque `SharedModule` no tiene rutas
 * propias.
 */
@NgModule({
  imports: [CommonModule, RouterModule, IonicModule],
  declarations: [FooterComponent, EmptyStateComponent, SkeletonComponent, RevealDirective, TopNavComponent, AccountMenuComponent],
  exports: [FooterComponent, EmptyStateComponent, SkeletonComponent, RevealDirective, TopNavComponent, AccountMenuComponent],
})
export class SharedModule {}
