import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { Publicaciones, PublicacionDetalle } from '../publicaciones';

/** Detalle público de una publicación — equivalente Ionic de `publicacion_detalle_view`. El `puede_contratar`/botón de contratar del template no está acá todavía (llega con la fase de contrataciones del plan de migración). */
@Component({
  selector: 'app-detalle',
  templateUrl: './detalle.page.html',
  styleUrls: ['./detalle.page.scss'],
  standalone: false,
})
export class DetallePage implements OnInit {
  publicacion: PublicacionDetalle | null = null;
  cargando = true;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly api: Publicaciones,
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
      },
      error: () => {
        this.cargando = false;
      },
    });
  }
}
