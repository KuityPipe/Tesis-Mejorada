import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { Auth, DatosRegistro } from '../core/auth';
import { Retroalimentacion } from '../core/retroalimentacion';
import { Catalogos, ComunaCatalogo, RegionCatalogo } from './catalogos';

/**
 * Registro de cuenta — equivalente Ionic de `/registro/` (`register_view`).
 * Fase 3 del plan de migración (docs/PLAN_MIGRACION_IONIC.md).
 */
@Component({
  selector: 'app-registro',
  templateUrl: './registro.page.html',
  styleUrls: ['./registro.page.scss'],
  standalone: false,
})
export class RegistroPage implements OnInit {
  formulario = this.fb.nonNullable.group({
    rut: ['', Validators.required],
    nombre1: ['', Validators.required],
    nombre2: [''],
    apellido1: ['', Validators.required],
    apellido2: [''],
    edad: [18, [Validators.required, Validators.min(18), Validators.max(120)]],
    telefono: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    direccion: [''],
    region: [null as number | null, Validators.required],
    comuna: [{ value: null as number | null, disabled: true }, Validators.required],
    es_proveedor: [false],
    password: ['', [Validators.required, Validators.minLength(8)]],
    password_confirm: ['', Validators.required],
  });

  regiones: RegionCatalogo[] = [];
  comunas: ComunaCatalogo[] = [];
  enviando = false;
  errorGeneral: string | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly catalogos: Catalogos,
    private readonly router: Router,
    private readonly retroalimentacion: Retroalimentacion,
  ) {}

  ngOnInit(): void {
    this.catalogos.regiones().subscribe((regiones) => (this.regiones = regiones));
  }

  /** Se dispara con (ionChange) del <ion-select> de región — repuebla el de comuna, mismo patrón que el <select onchange> de registroinicio.html. */
  alCambiarRegion(regionId: number): void {
    this.formulario.controls.comuna.reset();
    this.formulario.controls.comuna.disable();
    this.comunas = [];
    if (!regionId) {
      return;
    }
    this.catalogos.comunas(regionId).subscribe((comunas) => {
      this.comunas = comunas;
      this.formulario.controls.comuna.enable();
    });
  }

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.errorGeneral = null;
    // region/comuna quedan tipados `number | null` porque arrancan en
    // `null` — Angular typed forms no estrecha el tipo solo por tener
    // Validators.required. El `!` acá es seguro porque `formulario.invalid`
    // ya se chequeó arriba.
    const valores = this.formulario.getRawValue();
    const datos: DatosRegistro = { ...valores, region: valores.region!, comuna: valores.comuna! };
    this.auth.registrar(datos).subscribe({
      next: () => {
        this.enviando = false;
        this.retroalimentacion.exito('Cuenta creada — ahora inicia sesión.');
        // Sin auto-login (ver Auth.registrar) — vuelve a /login con la cuenta ya creada.
        this.router.navigateByUrl('/login');
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        this.aplicarErroresDelServidor(error);
      },
    });
  }

  /** Mensaje a mostrar bajo un campo — null si no hay error o el usuario todavía no lo tocó (evita mostrar "requerido" antes de que llegue a escribir). */
  mensajeError(campo: string): string | null {
    const control = this.formulario.get(campo);
    if (!control || !control.touched || !control.errors) {
      return null;
    }
    if (control.errors['servidor']) return control.errors['servidor'];
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['email']) return 'Correo inválido.';
    if (control.errors['minlength']) return `Mínimo ${control.errors['minlength'].requiredLength} caracteres.`;
    if (control.errors['min']) return `Mínimo ${control.errors['min'].min}.`;
    if (control.errors['max']) return `Máximo ${control.errors['max'].max}.`;
    return 'Dato inválido.';
  }

  /** `error.error` es el `form.errors` de Django tal cual — `{ campo: ["mensaje"] }`, con errores generales bajo `"__all__"`. */
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
