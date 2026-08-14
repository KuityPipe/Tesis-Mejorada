import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { Auth, Usuario } from '../core/auth';
import { Contrataciones, ContratacionResumen } from '../contrataciones/contrataciones';

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

  constructor(
    private readonly auth: Auth,
    private readonly router: Router,
    private readonly contratacionesApi: Contrataciones,
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
  }

  colorEstado(estado: string): string {
    return this.contratacionesApi.colorEstado(estado);
  }

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
