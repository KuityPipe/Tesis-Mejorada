import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { RetornoPage } from './retorno.page';

const routes: Routes = [
  {
    path: '',
    component: RetornoPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class RetornoPageRoutingModule {}
