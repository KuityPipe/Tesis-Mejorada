import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

import { Auth } from '../../core/auth';
import { Retroalimentacion } from '../../core/retroalimentacion';
import { Catalogos, ComunaCatalogo, RegionCatalogo } from '../../registro/catalogos';

/**
 * Editar perfil — equivalente Ionic de `/perfil/editar/`
 * (`editar_perfil_view`). Fase 3 del plan de migración.
 */
@Component({
  selector: 'app-editar',
  templateUrl: './editar.page.html',
  styleUrls: ['./editar.page.scss'],
  standalone: false,
})
export class EditarPage implements OnInit {
  formulario = this.fb.nonNullable.group({
    nombre_usuario: ['', Validators.required],
    nombre2_usuario: [''],
    apellido_usuario: ['', Validators.required],
    apellido2_usuario: [''],
    telefono: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    direccion_usuario: [''],
    region: [null as number | null, Validators.required],
    comuna: [{ value: null as number | null, disabled: true }, Validators.required],
  });

  regiones: RegionCatalogo[] = [];
  comunas: ComunaCatalogo[] = [];
  fotoSeleccionada: File | null = null;
  cargando = true;
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

    this.auth.me().subscribe((usuario) => {
      this.formulario.patchValue({
        nombre_usuario: usuario.nombre_usuario,
        nombre2_usuario: usuario.nombre2_usuario ?? '',
        apellido_usuario: usuario.apellido_usuario,
        apellido2_usuario: usuario.apellido2_usuario ?? '',
        telefono: usuario.telefono,
        email: usuario.email,
        direccion_usuario: usuario.direccion_usuario ?? '',
        region: usuario.region,
      });

      // Precarga el select de comuna con la comuna actual — mismo problema
      // que alCambiarRegion() en registro.page.ts, pero acá además hay que
      // dejar seleccionada la comuna que ya tenía (no arranca en blanco).
      if (usuario.region) {
        this.catalogos.comunas(usuario.region).subscribe((comunas) => {
          this.comunas = comunas;
          this.formulario.controls.comuna.enable();
          this.formulario.controls.comuna.setValue(usuario.comuna);
        });
      }

      this.cargando = false;
    });
  }

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

  alElegirFoto(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.fotoSeleccionada = input.files?.[0] ?? null;
  }

  enviar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.errorGeneral = null;

    // FormData en vez de un objeto plano: es lo que Auth.actualizarPerfil
    // espera (necesita poder llevar foto_perfil como archivo binario, no
    // como JSON) — ver el comentario ahí.
    const datosFormulario = this.formulario.getRawValue();
    const formData = new FormData();
    for (const [campo, valor] of Object.entries(datosFormulario)) {
      formData.set(campo, String(valor ?? ''));
    }
    if (this.fotoSeleccionada) {
      formData.set('foto_perfil', this.fotoSeleccionada);
    }

    this.auth.actualizarPerfil(formData).subscribe({
      next: () => {
        this.enviando = false;
        this.retroalimentacion.exito('Perfil actualizado.');
        this.router.navigateByUrl('/home');
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        this.aplicarErroresDelServidor(error);
      },
    });
  }

  mensajeError(campo: string): string | null {
    const control = this.formulario.get(campo);
    if (!control || !control.touched || !control.errors) {
      return null;
    }
    if (control.errors['servidor']) return control.errors['servidor'];
    if (control.errors['required']) return 'Campo requerido.';
    if (control.errors['email']) return 'Correo inválido.';
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
