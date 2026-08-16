import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { Auth } from '../../core/auth';
import { Retroalimentacion } from '../../core/retroalimentacion';
import { Contrataciones } from '../../contrataciones/contrataciones';
import { Publicaciones, PublicacionDetalle } from '../publicaciones';

/**
 * Detalle público de una publicación — equivalente Ionic de
 * `publicacion_detalle_view`. El botón "Contratar" (Fase 4 del plan de
 * migración) llama a `Contrataciones.solicitar` y redirige al detalle de
 * la contratación recién creada — a diferencia del template, acá no hay
 * un `puede_contratar` precalculado por el backend: sin sesión, el botón
 * manda a `/login` directo; logueado, el propio `POST` devuelve un 400 si
 * ya hay una solicitud activa o es la propia publicación, mostrado tal cual.
 */
@Component({
  selector: 'app-detalle',
  templateUrl: './detalle.page.html',
  styleUrls: ['./detalle.page.scss'],
  standalone: false,
})
export class DetallePage implements OnInit {
  publicacion: PublicacionDetalle | null = null;
  cargando = true;
  contratando = false;
  errorContratar: string | null = null;

  /** Embed de Google Maps sin API key (`output=embed`) — `SafeResourceUrl` porque Angular sanitiza cualquier URL puesta en `[src]` de un iframe por defecto; acá es seguro saltarse eso porque la URL se arma solo con los números de latitud/longitud del backend, nunca con texto libre. */
  mapaUrl: SafeResourceUrl | null = null;
  /** Mismas coordenadas, para el link "Abrir en Google Maps" (`https://www.google.com/maps?q=lat,lng`) — ese sí es un `<a>` normal, no hace falta sanitizar nada. */
  enlaceGoogleMaps: string | null = null;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly api: Publicaciones,
    private readonly auth: Auth,
    private readonly contratacionesApi: Contrataciones,
    private readonly retroalimentacion: Retroalimentacion,
    private readonly sanitizer: DomSanitizer,
  ) {}

  ngOnInit(): void {
    // `snapshot.paramMap` alcanza acá (no hace falta suscribirse a
    // `paramMap` como Observable): esta página siempre se recrea desde
    // cero al navegar a otro :id (no hay forma de ir de un detalle a otro
    // sin volver a montar el componente), así que no hay riesgo de leer
    // un id viejo.
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.detalle(id).subscribe({
      next: (publicacion) => {
        this.publicacion = publicacion;
        this.cargando = false;
        const { latitud, longitud } = publicacion.proveedor;
        if (latitud !== null && longitud !== null) {
          this.enlaceGoogleMaps = `https://www.google.com/maps?q=${latitud},${longitud}`;
          this.mapaUrl = this.sanitizer.bypassSecurityTrustResourceUrl(`https://maps.google.com/maps?q=${latitud},${longitud}&z=14&output=embed`);
        }
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  get estaAutenticado(): boolean {
    return this.auth.estaAutenticado();
  }

  contratar(): void {
    if (!this.publicacion || this.contratando) {
      return;
    }
    if (!this.estaAutenticado) {
      this.router.navigateByUrl('/login');
      return;
    }
    this.contratando = true;
    this.errorContratar = null;
    this.contratacionesApi.solicitar(this.publicacion.id_publicacion).subscribe({
      next: (contratacion) => {
        this.contratando = false;
        this.retroalimentacion.exito('Solicitud enviada al proveedor.');
        this.router.navigateByUrl(`/contratacion/${contratacion.id_contratacion}`);
      },
      error: (error) => {
        this.contratando = false;
        this.errorContratar = error.error?.detail ?? 'No se pudo enviar la solicitud.';
      },
    });
  }
}
