import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { BiometriaPage } from './biometria.page';

const routes: Routes = [
  {
    path: '',
    component: BiometriaPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class BiometriaPageRoutingModule {}
