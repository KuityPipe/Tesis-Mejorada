import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PagosPage } from './pagos.page';

const routes: Routes = [
  {
    path: '',
    component: PagosPage,
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PagosPageRoutingModule {}
