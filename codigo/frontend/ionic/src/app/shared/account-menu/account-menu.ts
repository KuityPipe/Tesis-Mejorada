import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { Auth } from '../../core/auth';
import { Notificaciones } from '../../core/notificaciones';

// Contador a nivel de módulo — mismo motivo que en top-nav.ts: cada
// instancia nueva de este componente (una por navegación entre las 4
// pantallas raíz) se lleva ids de trigger propios, para que el
// `ion-popover` de turno nunca pueda quedar mirando un id reciclado de
// una instancia anterior ya destruida.
let contadorInstancias = 0;

/**
 * Accesos rápidos de cuenta, lado derecho del header — ver `TopNavComponent`
 * (mismo directorio padre) para por qué esto vive en un componente propio
 * en vez de compartir uno solo con los links de navegación: cada uno se
 * usa como `<app-top-nav slot="start">`/`<app-account-menu slot="end">`
 * directo en el `ion-toolbar` de la página.
 *
 * Sin sesión: un ícono de ingresar (antes era el botón de texto
 * "Ingresar", que el usuario marcó como feo). Con sesión: acceso directo
 * a la bandeja de entrada (con badge de no leídos) + el nombre del
 * usuario, que al tocarlo abre un menú (`ion-popover`) con cuenta/bandeja
 * de entrada/contrataciones/preferencias/cerrar sesión — antes era solo
 * un botón "Mi perfil" sin más opciones.
 */
@Component({
  selector: 'app-account-menu',
  templateUrl: './account-menu.html',
  styleUrls: ['./account-menu.scss'],
  standalone: false,
})
export class AccountMenuComponent implements OnInit {
  readonly mensajesNoLeidos$ = this.notificaciones.noLeidos$;
  readonly idTriggerCuenta = `ks-cuenta-trigger-${contadorInstancias++}`;
  readonly idTriggerIngresar = `ks-ingresar-trigger-${contadorInstancias++}`;
  nombreUsuario = '';

  constructor(
    readonly auth: Auth,
    private readonly notificaciones: Notificaciones,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    // Solo hace falta el nombre para mostrarlo en el botón de cuenta — sin
    // sesión no hay nada que pedir. `auth.me()` es liviano (un solo GET),
    // aceptable pagarlo una vez por carga de una pantalla raíz.
    if (this.auth.estaAutenticado()) {
      this.auth.me().subscribe((usuario) => (this.nombreUsuario = usuario.nombre_usuario));
    }
  }

  get inicialUsuario(): string {
    return (this.nombreUsuario || '?').charAt(0).toUpperCase();
  }

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
