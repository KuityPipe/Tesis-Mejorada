import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { ContactoPageRoutingModule } from './contacto-routing.module';
import { SharedModule } from '../shared/shared.module';

import { ContactoPage } from './contacto.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    ContactoPageRoutingModule,
    SharedModule
  ],
  declarations: [ContactoPage]
})
export class ContactoPageModule {}
