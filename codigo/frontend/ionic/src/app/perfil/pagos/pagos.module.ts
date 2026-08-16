import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { PagosPageRoutingModule } from './pagos-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { PagosPage } from './pagos.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    PagosPageRoutingModule,
    SharedModule
  ],
  declarations: [PagosPage]
})
export class PagosPageModule {}
