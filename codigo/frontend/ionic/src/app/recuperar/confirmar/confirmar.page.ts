import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';

import { Auth } from '../../core/auth';

/**
 * Recuperación de contraseña, Paso 2 — equivalente Ionic de
 * `/recuperar/confirmar/<token>/` (`recuperar_confirmar_view`).
 */
@Component({
  selector: 'app-confirmar',
  templateUrl: './confirmar.page.html',
  styleUrls: ['./confirmar.page.scss'],
  standalone: false,
})
export class ConfirmarPage implements OnInit {
  formulario = this.fb.nonNullable.group({
    password: ['', [Validators.required, Validators.minLength(8)]],
    password_confirm: ['', Validators.required],
  });

  private token = '';
  validando = true;
  tokenValido = false;
  enviando = false;
  exito = false;
  errorGeneral: string | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    // A diferencia de login/detalle.page, acá sí conviene chequear el
    // token ANTES de mostrar el formulario — evita que alguien llene una
    // contraseña nueva para descubrir recién al final que el link ya
    // venció (mismo criterio que recuperar_confirmar_view del template,
    // que hace este chequeo con un GET antes de renderizar el form).
    this.token = this.route.snapshot.paramMap.get('token') ?? '';
    this.auth.validarTokenRecuperacion(this.token).subscribe({
      next: () => {
        this.validando = false;
        this.tokenValido = true;
      },
      error: () => {
        this.validando = false;
        this.tokenValido = false;
      },
    });
  }

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.errorGeneral = null;
    const { password, password_confirm } = this.formulario.getRawValue();

    this.auth.confirmarRecuperacion(this.token, password, password_confirm).subscribe({
      next: () => {
        this.enviando = false;
        this.exito = true;
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        this.aplicarErroresDelServidor(error);
      },
    });
  }

  irALogin(): void {
    this.router.navigateByUrl('/login');
  }

  mensajeError(campo: string): string | null {
    const control = this.formulario.get(campo);
    if (!control || !control.touched || !control.errors) {
      return null;
    }
    if (control.errors['servidor']) return control.errors['servidor'];
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['minlength']) return `Mínimo ${control.errors['minlength'].requiredLength} caracteres.`;
    return 'Dato inválido.';
  }

  private aplicarErroresDelServidor(error: HttpErrorResponse): void {
    const errores: Record<string, string[]> = error.error ?? {};
    const generales: string[] = [];

    for (const [campo, mensajes] of Object.entries(errores)) {
      const control = campo === '__all__' ? null : this.formulario.get(campo);
      if (control) {
        control.setErrors({ servidor: mensajes.join(' ') });
      } else {
        generales.push(...mensajes);
      }
    }

    this.errorGeneral = generales.length ? generales.join(' ') : 'Revisa los datos del formulario.';
  }
}
