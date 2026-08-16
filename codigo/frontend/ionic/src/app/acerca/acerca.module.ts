import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { AcercaPageRoutingModule } from './acerca-routing.module';
import { SharedModule } from '../shared/shared.module';

import { AcercaPage } from './acerca.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    AcercaPageRoutingModule,
    SharedModule
  ],
  declarations: [AcercaPage]
})
export class AcercaPageModule {}
