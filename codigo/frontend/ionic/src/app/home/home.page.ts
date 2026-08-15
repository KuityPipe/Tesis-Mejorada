import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';

import { Auth, Usuario } from '../core/auth';
import { Contrataciones, ContratacionResumen } from '../contrataciones/contrataciones';
import { Notificaciones } from '../core/notificaciones';
import { Resenas, ResenaRecibida } from './resenas';

const ESTADOS_ACTIVOS = ['SOLICITADA', 'CONFIRMADA', 'EN_CURSO'];

/**
 * Pantalla protegida (`canActivate: [authGuard]` en app-routing.module.ts)
 * que reemplaza el "Blank" que trae `ionic start` por defecto — primer
 * lugar al que llega un usuario ya logueado. `OnInit`/`ngOnInit` es el
 * lifecycle hook de Angular que corre una vez, después de que Angular ya
 * armó el componente y resolvió sus `@Input()` (acá no hay ninguno) — es
 * el lugar correcto para disparar la carga inicial de datos, no el
 * constructor (que todavía no debería hacer trabajo async).
 */
@Component({
  selector: 'app-home',
  templateUrl: 'home.page.html',
  styleUrls: ['home.page.scss'],
  standalone: false,
})
export class HomePage implements OnInit {
  usuario: Usuario | null = null;
  cargando = true;
  trabajosActuales: ContratacionResumen[] = [];
  resenasRecibidas: ResenaRecibida[] = [];

  // Badge de no leídos en el tile "Mensajes" — equivalente Ionic del badge
  // que Django pinta en el ícono de chat del header (contar_mensajes_no_leidos,
  // base.html). Ahora en vivo (polling cada 15s vía Notificaciones, ver
  // core/notificaciones.ts) en vez de una foto fija tomada solo al entrar.
  readonly mensajesNoLeidos$ = this.notificaciones.noLeidos$;

  constructor(
    private readonly auth: Auth,
    private readonly router: Router,
    private readonly contratacionesApi: Contrataciones,
    private readonly notificaciones: Notificaciones,
    private readonly resenasApi: Resenas,
    private readonly alertController: AlertController,
  ) {}

  ngOnInit(): void {
    // El guard ya garantiza que hay un access token al llegar acá, pero no
    // que siga vigente (todavía no hay endpoint de refresh) — un 401 acá
    // significa "sesión vencida", no un bug.
    this.auth.me().subscribe({
      next: (usuario) => {
        this.usuario = usuario;
        this.cargando = false;
      },
      error: () => {
        this.auth.logout();
        this.router.navigateByUrl('/login');
      },
    });

    // "Trabajos actuales" (equivalente Ionic de /inicio/ en el sitio
    // Django) — mismas 3 primeras contrataciones no cerradas, para que el
    // dashboard sirva de vistazo rápido en vez de mandar directo a la
    // lista completa (/reservas).
    this.contratacionesApi.listar().subscribe({
      next: (contrataciones) => {
        this.trabajosActuales = contrataciones.filter((c) => ESTADOS_ACTIVOS.includes(c.estado)).slice(0, 3);
      },
      error: () => {
        // Si falla, el dashboard simplemente no muestra esta sección — no es crítico como el auth.me() de arriba.
      },
    });

    // Reseñas recibidas — equivalente Ionic de la sección homónima de
    // perfil.html, sin cap (Django tampoco pagina esto).
    this.resenasApi.recibidas().subscribe({
      next: (resenas) => {
        this.resenasRecibidas = resenas;
      },
      error: () => {
        // No crítico — la sección simplemente no aparece.
      },
    });
  }

  colorEstado(estado: string): string {
    return this.contratacionesApi.colorEstado(estado);
  }

  etiquetaEstado(estado: string): string {
    return this.contratacionesApi.etiquetaEstado(estado);
  }

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }

  /**
   * Equivalente Ionic del botón "Convertirme en proveedor"/"Dejar de
   * ofrecer servicios" de `perfil.html` — mismo criterio: confirmar antes
   * de DESACTIVAR (perder la posibilidad de publicar nuevos servicios
   * hasta reactivarlo), no al activar, que no tiene ninguna consecuencia
   * que perder.
   */
  async alternarProveedor(): Promise<void> {
    if (!this.usuario) {
      return;
    }
    if (this.usuario.es_proveedor) {
      const alerta = await this.alertController.create({
        header: 'Dejar de ofrecer servicios',
        message: 'No vas a poder crear publicaciones nuevas hasta que lo actives de nuevo. Tus publicaciones existentes siguen visibles.',
        buttons: [
          { text: 'Cancelar', role: 'cancel' },
          { text: 'Dejar de ofrecer', role: 'destructive', handler: () => this.enviarAlternarProveedor() },
        ],
      });
      await alerta.present();
    } else {
      this.enviarAlternarProveedor();
    }
  }

  private enviarAlternarProveedor(): void {
    this.auth.alternarProveedor().subscribe((usuario) => (this.usuario = usuario));
  }
}
