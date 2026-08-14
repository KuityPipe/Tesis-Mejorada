import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { BiometriaPageRoutingModule } from './biometria-routing.module';

import { BiometriaPage } from './biometria.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    BiometriaPageRoutingModule
  ],
  declarations: [BiometriaPage]
})
export class BiometriaPageModule {}
