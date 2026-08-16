import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { ConfirmarPageRoutingModule } from './confirmar-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { ConfirmarPage } from './confirmar.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    ConfirmarPageRoutingModule,
    SharedModule
  ],
  declarations: [ConfirmarPage]
})
export class ConfirmarPageModule {}
