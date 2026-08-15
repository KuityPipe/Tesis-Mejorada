import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { Auth } from '../core/auth';

/**
 * `standalone: false` (explícito, distinto del default de Angular ≥17)
 * porque este proyecto sigue el estilo con `NgModule` del scaffold
 * original de `ionic start` (ver login.module.ts, que declara esta
 * clase) — un componente standalone no puede aparecer en
 * `declarations: [...]` de un NgModule, así que hay que ser explícito acá
 * o `ng build` falla con el error NG6008.
 */
@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: false,
})
export class LoginPage {
  // `FormBuilder.nonNullable.group(...)` arma un Reactive Form (a
  // diferencia de los Template-Driven Forms con `ngModel`, más parecidos
  // a los forms de Django): el estado del formulario vive acá en la
  // clase, no en el HTML, y `.nonNullable` evita que TypeScript infiera
  // los controles como `string | null` (sin eso, cada `.value` habría
  // que castearlo). El array `[valorInicial, validadores]` en cada campo
  // es el equivalente Angular a los `validators=[...]` de un `forms.Form`
  // de Django.
  formulario = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  enviando = false;
  errorMensaje: string | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly router: Router,
  ) {}

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      return;
    }

    this.enviando = true;
    this.errorMensaje = null;
    const { email, password } = this.formulario.getRawValue();

    // `.subscribe({ next, error })` es lo que realmente dispara la
    // request HTTP (ver el comentario de `Auth.login` en core/auth.ts) —
    // hasta este punto `this.auth.login(...)` solo había armado la receta
    // del Observable, sin hacer ninguna llamada de red todavía.
    this.auth.login(email, password).subscribe({
      next: () => {
        this.enviando = false;
        this.router.navigateByUrl('/home');
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        // El backend (KeyServApp/api/views.py) ya devuelve mensajes en
        // español listos para mostrar (401 credenciales incorrectas, 429
        // demasiados intentos) — no hace falta traducirlos acá.
        this.errorMensaje = error.error?.detail ?? 'No se pudo iniciar sesión. Prueba de nuevo.';
      },
    });
  }
}
