import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { Auth, Usuario } from '../core/auth';

@Component({
  selector: 'app-home',
  templateUrl: 'home.page.html',
  styleUrls: ['home.page.scss'],
  standalone: false,
})
export class HomePage implements OnInit {
  usuario: Usuario | null = null;
  cargando = true;

  constructor(
    private readonly auth: Auth,
    private readonly router: Router,
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
  }

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
