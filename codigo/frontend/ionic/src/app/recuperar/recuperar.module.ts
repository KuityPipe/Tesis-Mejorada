import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { RecuperarPageRoutingModule } from './recuperar-routing.module';
import { SharedModule } from '../shared/shared.module';

import { RecuperarPage } from './recuperar.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    RecuperarPageRoutingModule,
    SharedModule
  ],
  declarations: [RecuperarPage]
})
export class RecuperarPageModule {}
