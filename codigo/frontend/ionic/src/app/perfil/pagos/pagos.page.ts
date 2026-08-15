import { Component, OnInit } from '@angular/core';

import { Pagos, PagoHistorial } from '../../pago/pagos';

const COLOR_ESTADO: Record<string, string> = {
  PENDIENTE: 'warning',
  PAGADO: 'success',
  RECHAZADO: 'danger',
  ANULADO: 'medium',
};

/**
 * Historial de pagos — equivalente Ionic de `/historial-pagos/`
 * (`historial_pagos_view`, `historial_pagos.html`). Solo los pagos donde
 * el usuario logueado es el cliente (ver `PagoHistorialView`, backend) —
 * un proveedor ve el estado de un pago puntual dentro de la contratación
 * misma, no tiene un historial propio acá.
 */
@Component({
  selector: 'app-pagos',
  templateUrl: './pagos.page.html',
  styleUrls: ['./pagos.page.scss'],
  standalone: false,
})
export class PagosPage implements OnInit {
  pagos: PagoHistorial[] = [];
  cargando = true;

  constructor(private readonly api: Pagos) {}

  ngOnInit(): void {
    this.api.historial().subscribe({
      next: (pagos) => {
        this.pagos = pagos;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  colorEstado(estado: string): string {
    return COLOR_ESTADO[estado] ?? 'medium';
  }

  iconoMetodo(metodo: string): string {
    return metodo === 'WEBPAY' ? 'card-outline' : 'business-outline';
  }
}
