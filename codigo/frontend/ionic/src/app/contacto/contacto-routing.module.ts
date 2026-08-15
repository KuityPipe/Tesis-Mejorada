import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ContactoPage } from './contacto.page';

const routes: Routes = [
  {
    path: '',
    component: ContactoPage,
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ContactoPageRoutingModule {}
