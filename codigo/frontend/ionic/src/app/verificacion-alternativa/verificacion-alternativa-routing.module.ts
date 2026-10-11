import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { VerificacionAlternativaPage } from './verificacion-alternativa.page';

const routes: Routes = [{ path: '', component: VerificacionAlternativaPage }];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class VerificacionAlternativaPageRoutingModule {}
