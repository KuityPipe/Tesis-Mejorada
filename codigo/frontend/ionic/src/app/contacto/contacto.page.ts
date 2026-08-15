import { Component } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { Auth } from '../core/auth';
import { Contacto } from './contacto';

/**
 * Contacto — equivalente Ionic de `/contacto/` (`contacto_view`,
 * `contacto.html`). Antes no existía ningún equivalente ni backend (ver
 * ContactoView, api/views.py, agregado en esta misma pasada) — `contacto_view`
 * seguía siendo 100% template.
 *
 * `nombre_contacto`/`email_contacto` solo son obligatorios si no hay sesión
 * iniciada, mismo criterio que `ContactoForm(requiere_datos_contacto=...)`
 * del lado del backend — acá se decide con `auth.estaAutenticado()`.
 */
@Component({
  selector: 'app-contacto',
  templateUrl: './contacto.page.html',
  styleUrls: ['./contacto.page.scss'],
  standalone: false,
})
export class ContactoPage {
  requiereDatosContacto = !this.auth.estaAutenticado();

  formulario = this.fb.nonNullable.group({
    asunto_consulta: ['', Validators.required],
    descripcion: ['', Validators.required],
    nombre_contacto: [''],
    email_contacto: [''],
  });

  enviando = false;
  enviadoOk = false;
  errorGeneral: string | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly api: Contacto,
  ) {
    if (this.requiereDatosContacto) {
      this.formulario.controls.nombre_contacto.addValidators(Validators.required);
      this.formulario.controls.email_contacto.addValidators([Validators.required, Validators.email]);
    }
  }

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.errorGeneral = null;
    this.enviadoOk = false;
    this.api.enviar(this.formulario.getRawValue()).subscribe({
      next: () => {
        this.enviando = false;
        this.enviadoOk = true;
        this.formulario.reset({ asunto_consulta: '', descripcion: '', nombre_contacto: '', email_contacto: '' });
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        this.errorGeneral = this.extraerMensajeError(error);
      },
    });
  }

  /**
   * `error.error` puede venir en dos formas distintas según qué falló:
   * `{campo: ["mensaje"]}` (errores de validación de `ContactoForm`, mismo
   * formato que `RegistroForm`) o `{detail: "mensaje"}` (errores genéricos
   * de DRF, ej. un 401 si el JWT guardado ya venció — este endpoint es
   * público, pero `authInterceptor` igual adjunta el token si hay uno
   * guardado, y un token vencido falla la autenticación antes de llegar a
   * `AllowAny`). Cubre ambos en vez de asumir que todo valor es un array.
   */
  private extraerMensajeError(error: HttpErrorResponse): string {
    if (typeof error.error !== 'object' || error.error === null) {
      return 'No se pudo enviar tu consulta. Probá de nuevo en unos minutos.';
    }
    return Object.values(error.error)
      .map((valor) => (Array.isArray(valor) ? valor.join(' ') : String(valor)))
      .join(' ');
  }

  mensajeError(campo: string): string | null {
    const control = this.formulario.get(campo);
    if (!control || !control.touched || !control.errors) {
      return null;
    }
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['email']) return 'Correo inválido.';
    return 'Dato inválido.';
  }
}
