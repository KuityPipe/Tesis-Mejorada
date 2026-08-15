import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { CatalogoPageRoutingModule } from './catalogo-routing.module';
import { SharedModule } from '../shared/shared.module';

import { CatalogoPage } from './catalogo.page';

// `routerLink` en catalogo.page.html funciona sin importar RouterModule acá
// a mano: CatalogoPageRoutingModule ya lo re-exporta (ver
// catalogo-routing.module.ts, `exports: [RouterModule]`), y ese módulo
// está importado abajo — así es como los demás módulos "page" de Ionic
// resuelven esto también (ver home.module.ts).
@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    CatalogoPageRoutingModule,
    SharedModule
  ],
  declarations: [CatalogoPage]
})
export class CatalogoPageModule {}
