import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { RetornoPageRoutingModule } from './retorno-routing.module';

import { RetornoPage } from './retorno.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    RetornoPageRoutingModule
  ],
  declarations: [RetornoPage]
})
export class RetornoPageModule {}
