import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';

import { SharedModule } from '../shared/shared.module';
import { VerificacionAlternativaPageRoutingModule } from './verificacion-alternativa-routing.module';
import { VerificacionAlternativaPage } from './verificacion-alternativa.page';

@NgModule({
  imports: [CommonModule, FormsModule, RouterModule, IonicModule, VerificacionAlternativaPageRoutingModule, SharedModule],
  declarations: [VerificacionAlternativaPage],
})
export class VerificacionAlternativaPageModule {}
