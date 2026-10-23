import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { IonicModule } from '@ionic/angular';

import { SharedModule } from '../shared/shared.module';
import { CalculadoraPage } from './calculadora.page';

// Pública: ponerle precio a un trabajo no requiere cuenta (con cuenta se pueden guardar plantillas).
const routes: Routes = [{ path: '', component: CalculadoraPage }];

@NgModule({
  imports: [CommonModule, FormsModule, ReactiveFormsModule, IonicModule, RouterModule.forChild(routes), SharedModule],
  declarations: [CalculadoraPage],
})
export class CalculadoraPageModule {}
