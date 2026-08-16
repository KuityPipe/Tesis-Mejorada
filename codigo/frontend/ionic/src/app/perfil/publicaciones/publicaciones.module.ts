import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { PublicacionesPageRoutingModule } from './publicaciones-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { PublicacionesPage } from './publicaciones.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    PublicacionesPageRoutingModule,
    SharedModule
  ],
  declarations: [PublicacionesPage]
})
export class PublicacionesPageModule {}
