import { Component } from '@angular/core';
import { Router } from '@angular/router';

/** Página 404: una dirección que no existe (enlace viejo, error de tipeo). Ofrece volver o buscar. */
@Component({
  selector: 'app-no-encontrado',
  templateUrl: './no-encontrado.page.html',
  styleUrls: ['./no-encontrado.page.scss'],
  standalone: false,
})
export class NoEncontradoPage {
  q = '';

  constructor(private readonly router: Router) {}

  buscar(): void {
    this.router.navigate(['/catalogo'], { queryParams: this.q.trim() ? { q: this.q.trim() } : {} });
  }
}
