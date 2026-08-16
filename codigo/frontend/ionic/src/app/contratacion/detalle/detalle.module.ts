import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { DetallePageRoutingModule } from './detalle-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { DetallePage } from './detalle.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    DetallePageRoutingModule,
    SharedModule
  ],
  declarations: [DetallePage]
})
export class DetallePageModule {}
