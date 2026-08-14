import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';

import { Auth } from '../core/auth';

/**
 * Recuperación de contraseña, Paso 1 — equivalente Ionic de `/recuperar/`
 * (`recuperar_view`). Fase 3 del plan de migración.
 */
@Component({
  selector: 'app-recuperar',
  templateUrl: './recuperar.page.html',
  styleUrls: ['./recuperar.page.scss'],
  standalone: false,
})
export class RecuperarPage {
  formulario = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    telefono: ['', Validators.required],
  });

  enviando = false;
  // Un solo mensaje para éxito Y error de validación de campos — el
  // backend nunca distingue "cuenta no existe" de "cuenta existe", así
  // que del lado de acá tampoco hay un estado de "éxito" separado que
  // mostrar con más detalle.
  mensaje: string | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
  ) {}

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    const { email, telefono } = this.formulario.getRawValue();
    this.auth.solicitarRecuperacion(email, telefono).subscribe({
      next: (respuesta) => {
        this.enviando = false;
        this.mensaje = respuesta.detail;
      },
      error: () => {
        this.enviando = false;
        this.mensaje = 'No se pudo procesar la solicitud. Probá de nuevo en unos minutos.';
      },
    });
  }
}
