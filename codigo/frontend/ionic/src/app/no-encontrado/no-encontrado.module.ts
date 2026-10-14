import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { IonicModule } from '@ionic/angular';

import { SharedModule } from '../shared/shared.module';
import { NoEncontradoPage } from './no-encontrado.page';

const routes: Routes = [{ path: '', component: NoEncontradoPage }];

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, RouterModule.forChild(routes), SharedModule],
  declarations: [NoEncontradoPage],
})
export class NoEncontradoPageModule {}
