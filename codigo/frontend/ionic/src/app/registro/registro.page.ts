import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { Auth, DatosRegistro } from '../core/auth';
import { Retroalimentacion } from '../core/retroalimentacion';
import { FINALIDAD_IMPACTO, GENEROS, SITUACIONES_LABORALES } from '../core/impacto';
import { normalizarRut, validadorRut } from '../core/rut';
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
    rut: ['', [Validators.required, validadorRut]],
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
    acepta_politica: [false, Validators.requiredTrue],
    // Preguntas voluntarias de impacto (ADR 0008): no bloquean el registro.
    situacion_laboral_previa: [''],
    genero: [''],
  });

  readonly situaciones = SITUACIONES_LABORALES;
  readonly generos = GENEROS;
  readonly finalidadImpacto = FINALIDAD_IMPACTO;

  readonly pasos = [
    { n: 1, titulo: 'Tus datos', detalle: 'Quién eres y cómo contactarte' },
    { n: 2, titulo: 'Ubicación', detalle: 'Dónde ofreces o buscas servicios' },
    { n: 3, titulo: 'Tu cuenta', detalle: 'Tipo de cuenta y contraseña' },
  ];

  /** La lista de regiones se abre del ancho de su contenido, no del campo (si no, corta "Región de Arica y Parinacota"). */
  readonly opcionesLista = { size: 'auto' };
  readonly opcionesComuna = { header: 'Elige tu comuna' };

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

  /** Un paso está completo cuando todos sus campos obligatorios son válidos. */
  pasoCompleto(n: number): boolean {
    const c = this.formulario.controls;
    if (n === 1) return [c.rut, c.nombre1, c.apellido1, c.edad, c.telefono, c.email].every((campo) => campo.valid);
    if (n === 2) return c.region.valid && c.comuna.value != null;
    return c.password.valid && c.password_confirm.valid && this.clavesCoinciden && c.acepta_politica.value;
  }

  /** El paso que toca llenar ahora: el primero que todavía no está completo. */
  get pasoActual(): number {
    return this.pasos.find((paso) => !this.pasoCompleto(paso.n))?.n ?? 0;
  }

  get progreso(): number {
    return (this.pasos.filter((paso) => this.pasoCompleto(paso.n)).length / this.pasos.length) * 100;
  }

  get clavesCoinciden(): boolean {
    const { password, password_confirm } = this.formulario.getRawValue();
    return !!password && password === password_confirm;
  }

  /** Orientativo (no reemplaza la validación del servidor): suma un punto por cada buena práctica. */
  get fuerzaClave(): { nivel: number; etiqueta: string } {
    const clave = this.formulario.controls.password.value;
    const puntos =
      Number(clave.length >= 8) +
      Number(/[a-z]/.test(clave) && /[A-Z]/.test(clave)) +
      Number(/\d/.test(clave)) +
      Number(/[^A-Za-z0-9]/.test(clave) || clave.length >= 12);
    return { nivel: puntos, etiqueta: ['Muy débil', 'Débil', 'Aceptable', 'Buena', 'Fuerte'][puntos] };
  }

  /** "Providencia, Región Metropolitana": confirma lo elegido en la sección de ubicación. */
  get ubicacionElegida(): { comuna: string; region: string } | null {
    const { region, comuna } = this.formulario.getRawValue();
    const nombreComuna = this.comunas.find((c) => c.id_comuna === comuna)?.nombre_comuna;
    const nombreRegion = this.regiones.find((r) => r.id_region === region)?.nombre_region;
    return nombreComuna && nombreRegion ? { comuna: nombreComuna, region: nombreRegion } : null;
  }

  /** Al salir del campo RUT lo deja en el formato que guarda el servidor (`12345678-5`): sin puntos y con guion. */
  ordenarRut(): void {
    const control = this.formulario.controls.rut;
    if (control.value) control.setValue(normalizarRut(control.value));
  }

  elegirTipo(proveedor: boolean): void {
    this.formulario.controls.es_proveedor.setValue(proveedor);
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
    // El servidor guarda el RUT sin puntos (máx. 10 caracteres): se limpian por si la persona los escribió.
    const rut = normalizarRut(valores.rut);
    // Solo dígitos y sin el código de país: la base guarda el teléfono como entero de 32 bits.
    const digitos = valores.telefono.replace(/\D/g, '');
    const telefono = digitos.length > 9 && digitos.startsWith('56') ? digitos.slice(2) : digitos;
    const datos: DatosRegistro = { ...valores, rut, telefono, region: valores.region!, comuna: valores.comuna! };
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
    if (campo === 'acepta_politica') return 'Debes aceptar la política de privacidad para crear tu cuenta.';
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['rut']) return 'RUT inválido. Revisa el dígito verificador; ejemplo: 12345678-5.';
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
