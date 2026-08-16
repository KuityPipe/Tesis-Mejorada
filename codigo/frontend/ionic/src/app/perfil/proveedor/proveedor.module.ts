import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { ProveedorPageRoutingModule } from './proveedor-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { ProveedorPage } from './proveedor.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    ProveedorPageRoutingModule,
    SharedModule
  ],
  declarations: [ProveedorPage]
})
export class ProveedorPageModule {}
