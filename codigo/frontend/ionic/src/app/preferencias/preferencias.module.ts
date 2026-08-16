import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { PreferenciasPageRoutingModule } from './preferencias-routing.module';
import { SharedModule } from '../shared/shared.module';

import { PreferenciasPage } from './preferencias.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    PreferenciasPageRoutingModule,
    SharedModule
  ],
  declarations: [PreferenciasPage]
})
export class PreferenciasPageModule {}
