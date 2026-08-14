import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { Auth } from '../core/auth';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: false,
})
export class LoginPage {
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
        this.errorMensaje = error.error?.detail ?? 'No se pudo iniciar sesión. Probá de nuevo.';
      },
    });
  }
}
