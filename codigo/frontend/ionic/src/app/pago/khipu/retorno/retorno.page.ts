import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { Pagos } from '../../pagos';

/**
 * `/pago/khipu/retorno/:id` — a donde Khipu redirige de vuelta al
 * navegador (aprobado o cancelado), equivalente Ionic de
 * `pago_khipu_retorno_view`. La verdad sobre si se pagó la trae el
 * webhook (servidor-a-servidor, sigue en Django), pero acá se reconsulta
 * igual por UX — ver `Pagos.estadoKhipu`.
 */
@Component({
  selector: 'app-khipu-retorno',
  templateUrl: './retorno.page.html',
  styleUrls: ['./retorno.page.scss'],
  standalone: false,
})
export class RetornoPage implements OnInit {
  contratacionId!: number;
  cargando = true;
  aprobado = false;
  mensaje = '';

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly pagosApi: Pagos,
  ) {}

  ngOnInit(): void {
    this.contratacionId = Number(this.route.snapshot.paramMap.get('id'));
    this.pagosApi.estadoKhipu(this.contratacionId).subscribe({
      next: (respuesta) => {
        this.cargando = false;
        this.aprobado = respuesta.aprobado;
        this.mensaje = respuesta.mensaje;
      },
      error: () => {
        this.cargando = false;
        this.mensaje = 'No pudimos consultar el estado del pago.';
      },
    });
  }

  volver(): void {
    this.router.navigateByUrl(`/contratacion/${this.contratacionId}`);
  }
}
