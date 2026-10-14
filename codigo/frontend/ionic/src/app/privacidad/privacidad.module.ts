import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';

import { IonicModule } from '@ionic/angular';

import { SharedModule } from '../shared/shared.module';
import { PrivacidadPage } from './privacidad.page';

// Pública: la política de privacidad se puede leer sin iniciar sesión (y es el link que pide Play Store).
const routes: Routes = [{ path: '', component: PrivacidadPage }];

@NgModule({
  imports: [CommonModule, IonicModule, RouterModule.forChild(routes), SharedModule],
  declarations: [PrivacidadPage],
})
export class PrivacidadPageModule {}
