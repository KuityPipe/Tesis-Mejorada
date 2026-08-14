import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { RecuperarPage } from './recuperar.page';

const routes: Routes = [
  {
    path: '',
    component: RecuperarPage
  },
  {
    // :token es el link firmado del correo (ver ConfirmarPage y
    // KeyServApp/api/views.py RecuperarConfirmarView).
    path: 'confirmar/:token',
    loadChildren: () => import('./confirmar/confirmar.module').then( m => m.ConfirmarPageModule)
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class RecuperarPageRoutingModule {}
