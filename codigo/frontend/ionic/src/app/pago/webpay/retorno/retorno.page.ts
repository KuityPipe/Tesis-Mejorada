import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { Pagos } from '../../pagos';

/**
 * `/pago/webpay/retorno` — a donde Transbank redirige de vuelta al
 * navegador tras el pago (equivalente Ionic de `pago_webpay_retorno_view`).
 * Sin `authGuard`: quien llega acá puede tener el token JWT vencido tras
 * el rato afuera de la SPA — el propio backend (`PagoWebpayConfirmarView`)
 * tampoco exige uno, ver `Pagos.confirmarWebpay`.
 */
@Component({
  selector: 'app-webpay-retorno',
  templateUrl: './retorno.page.html',
  styleUrls: ['./retorno.page.scss'],
  standalone: false,
})
export class RetornoPage implements OnInit {
  cargando = true;
  aprobado = false;
  mensaje = '';
  contratacionId: number | null = null;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly pagosApi: Pagos,
  ) {}

  ngOnInit(): void {
    const params = this.route.snapshot.queryParamMap;
    const tokenWs = params.get('token_ws') ?? undefined;
    const tbkToken = params.get('TBK_TOKEN') ?? undefined;

    this.pagosApi.confirmarWebpay({ token_ws: tokenWs, TBK_TOKEN: tbkToken }).subscribe({
      next: (respuesta) => {
        this.cargando = false;
        this.aprobado = respuesta.aprobado;
        this.mensaje = respuesta.mensaje;
        this.contratacionId = respuesta.contratacion_id;
      },
      error: () => {
        this.cargando = false;
        this.mensaje = 'No pudimos confirmar el pago con Webpay.';
      },
    });
  }

  volver(): void {
    if (this.contratacionId) {
      this.router.navigateByUrl(`/contratacion/${this.contratacionId}`);
    } else {
      this.router.navigateByUrl('/reservas');
    }
  }
}
