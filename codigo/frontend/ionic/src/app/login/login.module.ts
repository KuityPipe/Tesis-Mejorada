import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { LoginPageRoutingModule } from './login-routing.module';

import { LoginPage } from './login.page';

/**
 * Cada página de Ionic tiene su propio NgModule "feature" (patrón del
 * `ionic generate page`, no una decisión de este proyecto) — se carga
 * perezosamente (`loadChildren` en app-routing.module.ts) solo cuando el
 * usuario navega a /login, en vez de empaquetarse en el bundle inicial.
 * `ReactiveFormsModule` se agregó a mano acá (el schematic no lo incluye
 * por defecto) porque login.page.ts usa `FormBuilder`/`[formGroup]`.
 */
@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    LoginPageRoutingModule
  ],
  declarations: [LoginPage]
})
export class LoginPageModule {}
