import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { EditarPageRoutingModule } from './editar-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { EditarPage } from './editar.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    EditarPageRoutingModule,
    SharedModule
  ],
  declarations: [EditarPage]
})
export class EditarPageModule {}
