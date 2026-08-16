import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { IonicModule } from '@ionic/angular';

import { ReservasPageRoutingModule } from './reservas-routing.module';
import { SharedModule } from '../shared/shared.module';

import { ReservasPage } from './reservas.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    IonicModule,
    ReservasPageRoutingModule,
    SharedModule
  ],
  declarations: [ReservasPage]
})
export class ReservasPageModule {}
