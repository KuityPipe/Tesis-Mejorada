import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { AlertController } from '@ionic/angular';
import { forkJoin } from 'rxjs';

import { Auth, DocumentoPerfil } from '../../core/auth';
import { Catalogos } from '../../registro/catalogos';

/**
 * Perfil de proveedor extendido — equivalente Ionic de `/perfil/crear/`
 * (`crear_perfil_view`, `CrearPerfilForm`). Fase 3 del plan de migración.
 *
 * `areas_servicio` no es un `FormControl`: los checkboxes de categoría se
 * llevan a mano en `areasSeleccionadas` (un `Set<string>`, más simple que
 * un `FormArray` para esta cantidad fija de opciones) porque el backend
 * espera el mismo campo `areas_servicio` repetido varias veces en el
 * `FormData` (`CrearPerfilForm.areas_servicio` es un
 * `MultipleChoiceField`), no un array serializado.
 */
@Component({
  selector: 'app-proveedor',
  templateUrl: './proveedor.page.html',
  styleUrls: ['./proveedor.page.scss'],
  standalone: false,
})
export class ProveedorPage implements OnInit {
  formulario = this.fb.nonNullable.group({
    experiencia: [''],
    otra_area_servicio: [''],
  });

  categorias: string[] = [];
  areasSeleccionadas = new Set<string>();
  documentos: DocumentoPerfil[] = [];
  fotoSeleccionada: File | null = null;
  archivosSeleccionados: File[] = [];
  cargando = true;
  enviando = false;
  errorGeneral: string | null = null;
  documentosRechazados: string[] = [];
  guardadoOk = false;

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: Auth,
    private readonly catalogos: Catalogos,
    private readonly alertController: AlertController,
  ) {}

  ngOnInit(): void {
    // Los tres datos son independientes entre sí (catálogo fijo, perfil
    // propio, documentos ya subidos) — forkJoin los pide en paralelo en vez
    // de encadenarlos, y recién arma la pantalla cuando los tres llegaron.
    forkJoin({
      categorias: this.catalogos.categorias(),
      usuario: this.auth.me(),
      documentos: this.auth.documentosPerfil(),
    }).subscribe(({ categorias, usuario, documentos }) => {
      this.categorias = categorias;

      // Mismo criterio que CrearPerfilForm.__init__ (forms.py): separar lo
      // ya guardado en `areas_servicio` (un string separado por comas) entre
      // lo que coincide con una categoría predefinida y lo que es texto libre.
      const actuales = (usuario.areas_servicio || '').split(',').map((a) => a.trim()).filter(Boolean);
      this.areasSeleccionadas = new Set(actuales.filter((a) => categorias.includes(a)));
      const libres = actuales.filter((a) => !categorias.includes(a));

      this.formulario.patchValue({
        experiencia: usuario.experiencia ?? '',
        otra_area_servicio: libres.join(', '),
      });
      this.documentos = documentos;
      this.cargando = false;
    });
  }

  alternarArea(categoria: string, marcada: boolean): void {
    if (marcada) {
      this.areasSeleccionadas.add(categoria);
    } else {
      this.areasSeleccionadas.delete(categoria);
    }
  }

  alElegirFoto(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.fotoSeleccionada = input.files?.[0] ?? null;
  }

  alElegirDocumentos(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    this.archivosSeleccionados = input.files ? Array.from(input.files) : [];
  }

  enviar(): void {
    if (this.enviando) {
      return;
    }
    this.enviando = true;
    this.errorGeneral = null;
    this.documentosRechazados = [];
    this.guardadoOk = false;

    const formData = new FormData();
    // `.append` (no `.set`) a propósito: el backend espera `areas_servicio`
    // repetido una vez por cada categoría marcada, no un valor solo.
    for (const area of this.areasSeleccionadas) {
      formData.append('areas_servicio', area);
    }
    const datosFormulario = this.formulario.getRawValue();
    formData.set('otra_area_servicio', datosFormulario.otra_area_servicio);
    formData.set('experiencia', datosFormulario.experiencia);
    if (this.fotoSeleccionada) {
      formData.set('foto_perfil', this.fotoSeleccionada);
    }
    for (const archivo of this.archivosSeleccionados) {
      formData.append('documentos', archivo);
    }

    this.auth.actualizarPerfilProveedor(formData).subscribe({
      next: (respuesta) => {
        this.enviando = false;
        this.guardadoOk = true;
        this.documentosRechazados = respuesta.documentos_rechazados;
        this.archivosSeleccionados = [];
        this.auth.documentosPerfil().subscribe((documentos) => (this.documentos = documentos));
      },
      error: (_error: HttpErrorResponse) => {
        this.enviando = false;
        this.errorGeneral = 'No se pudo guardar el perfil. Revisa los datos e intenta de nuevo.';
      },
    });
  }

  async confirmarEliminarDocumento(documento: DocumentoPerfil): Promise<void> {
    const alerta = await this.alertController.create({
      header: 'Eliminar documento',
      message: `¿Eliminar "${documento.nombre_documento}"?`,
      buttons: [
        { text: 'Cancelar', role: 'cancel' },
        {
          text: 'Eliminar',
          role: 'destructive',
          handler: () => this.eliminarDocumento(documento),
        },
      ],
    });
    await alerta.present();
  }

  private eliminarDocumento(documento: DocumentoPerfil): void {
    this.auth.eliminarDocumentoPerfil(documento.id_documento).subscribe(() => {
      this.documentos = this.documentos.filter((d) => d.id_documento !== documento.id_documento);
    });
  }
}
