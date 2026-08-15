import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PublicacionesPage } from './publicaciones.page';

const routes: Routes = [
  {
    path: '',
    component: PublicacionesPage,
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PublicacionesPageRoutingModule {}
