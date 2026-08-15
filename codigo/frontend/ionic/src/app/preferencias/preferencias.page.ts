import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { Auth } from '../core/auth';
import { Tema, Tema3Estados } from '../core/tema';

/**
 * Preferencias de la cuenta — equivalente Ionic de `/preferencias-cuenta/`
 * (`preferencias_cuenta_view`). Fase 3 del plan de migración.
 *
 * Dos `FormGroup` independientes en la misma página, cada uno contra un
 * endpoint aparte (`PUT /api/auth/preferencias/` y
 * `POST /api/auth/cambiar-password/`) — mismo criterio que el template
 * (dos `<form>` distinguidos por un campo oculto `form`), solo que acá cada
 * uno ya es su propia request en vez de compartir una.
 */
@Component({
  selector: 'app-preferencias',
  templateUrl: './preferencias.page.html',
  styleUrls: ['./preferencias.page.scss'],
  standalone: false,
})
export class PreferenciasPage implements OnInit {
  formularioPreferencias = this.fb.nonNullable.group({
    notificaciones_sonido: [true],
  });

  formularioPassword = this.fb.nonNullable.group({
    password_actual: ['', Validators.required],
    password: ['', [Validators.required, Validators.minLength(8)]],
    password_confirm: ['', Validators.required],
  });

  cargando = true;
  guardandoPreferencias = false;
  preferenciasGuardadasOk = false;
  cambiandoPassword = false;
  passwordCambiadaOk = false;
  errorPassword: string | null = null;

  temaActual: Tema3Estados = 'light';

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly tema: Tema,
  ) {}

  ngOnInit(): void {
    this.temaActual = this.tema.obtenerActual();
    this.auth.me().subscribe((usuario) => {
      this.formularioPreferencias.patchValue({ notificaciones_sonido: usuario.notificaciones_sonido });
      this.cargando = false;
    });
  }

  alternarTema(): void {
    this.tema.alternar();
    this.temaActual = this.tema.obtenerActual();
  }

  guardarPreferencias(): void {
    if (this.guardandoPreferencias) {
      return;
    }
    this.guardandoPreferencias = true;
    this.preferenciasGuardadasOk = false;

    const { notificaciones_sonido } = this.formularioPreferencias.getRawValue();
    this.auth.actualizarPreferencias(notificaciones_sonido).subscribe({
      next: () => {
        this.guardandoPreferencias = false;
        this.preferenciasGuardadasOk = true;
      },
      error: () => {
        this.guardandoPreferencias = false;
      },
    });
  }

  cambiarPassword(): void {
    if (this.formularioPassword.invalid || this.cambiandoPassword) {
      this.formularioPassword.markAllAsTouched();
      return;
    }
    this.cambiandoPassword = true;
    this.errorPassword = null;
    this.passwordCambiadaOk = false;

    const { password_actual, password, password_confirm } = this.formularioPassword.getRawValue();
    this.auth.cambiarPassword(password_actual, password, password_confirm).subscribe({
      next: () => {
        this.cambiandoPassword = false;
        this.passwordCambiadaOk = true;
        this.formularioPassword.reset({ password_actual: '', password: '', password_confirm: '' });
      },
      error: (error: HttpErrorResponse) => {
        this.cambiandoPassword = false;
        this.aplicarErroresDelServidor(error);
      },
    });
  }

  mensajeErrorPassword(campo: string): string | null {
    const control = this.formularioPassword.get(campo);
    if (!control || !control.touched || !control.errors) {
      return null;
    }
    if (control.errors['servidor']) return control.errors['servidor'];
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['minlength']) return 'Mínimo 8 caracteres.';
    return 'Dato inválido.';
  }

  private aplicarErroresDelServidor(error: HttpErrorResponse): void {
    const errores: Record<string, string[]> = error.error ?? {};
    const generales: string[] = [];

    for (const [campo, mensajes] of Object.entries(errores)) {
      const control = campo === '__all__' ? null : this.formularioPassword.get(campo);
      if (control) {
        control.setErrors({ servidor: mensajes.join(' ') });
        control.markAsTouched();
      } else {
        generales.push(...mensajes);
      }
    }

    this.errorPassword = generales.length ? generales.join(' ') : null;
  }
}
