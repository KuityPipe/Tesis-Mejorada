import { Component, OnInit } from '@angular/core';

import { Contrataciones, ContratacionResumen } from '../contrataciones/contrataciones';

/** Listado de contrataciones propias (como cliente o como proveedor) — equivalente Ionic de `reservas_view`. Fase 4 del plan de migración. */
@Component({
  selector: 'app-reservas',
  templateUrl: './reservas.page.html',
  styleUrls: ['./reservas.page.scss'],
  standalone: false,
})
export class ReservasPage implements OnInit {
  contrataciones: ContratacionResumen[] = [];
  cargando = true;

  constructor(private readonly contratacionesApi: Contrataciones) {}

  ngOnInit(): void {
    this.contratacionesApi.listar().subscribe({
      next: (contrataciones) => {
        this.contrataciones = contrataciones;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  colorEstado(estado: string): string {
    return this.contratacionesApi.colorEstado(estado);
  }
}
