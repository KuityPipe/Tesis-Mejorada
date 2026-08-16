import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { MensajesPageRoutingModule } from './mensajes-routing.module';
import { SharedModule } from '../shared/shared.module';

import { MensajesPage } from './mensajes.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    MensajesPageRoutingModule,
    SharedModule
  ],
  declarations: [MensajesPage]
})
export class MensajesPageModule {}
