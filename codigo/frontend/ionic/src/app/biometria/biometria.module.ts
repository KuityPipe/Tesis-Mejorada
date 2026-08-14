import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { IonicModule } from '@ionic/angular';

import { BiometriaPageRoutingModule } from './biometria-routing.module';

import { BiometriaPage } from './biometria.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    IonicModule,
    BiometriaPageRoutingModule
  ],
  declarations: [BiometriaPage]
})
export class BiometriaPageModule {}
