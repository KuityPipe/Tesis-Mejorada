import { Component, EventEmitter, Input, Output } from '@angular/core';

/**
 * Paginador numerado (« 1 2 3 … N »): se usa en Servicios y Mis contrataciones, con 20 elementos por página.
 * No pide datos por sí mismo: avisa la página elegida con `cambioPagina` y quien lo usa decide qué mostrar.
 */
@Component({
  selector: 'app-paginador',
  templateUrl: './paginador.html',
  styleUrls: ['./paginador.scss'],
  standalone: false,
})
export class PaginadorComponent {
  @Input() total = 0;
  @Input() pagina = 1;
  @Input() porPagina = 20;
  @Output() cambioPagina = new EventEmitter<number>();

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.total / this.porPagina));
  }

  /** Primer y último elemento mostrados ("21–40 de 63"). */
  get rango(): string {
    if (!this.total) return '0';
    const desde = (this.pagina - 1) * this.porPagina + 1;
    const hasta = Math.min(this.pagina * this.porPagina, this.total);
    return `${desde}–${hasta} de ${this.total}`;
  }

  /** Números de página a mostrar: siempre la primera y la última, y una ventana alrededor de la actual con "…" en los saltos. */
  get paginas(): (number | '…')[] {
    const n = this.totalPaginas;
    const visibles = new Set<number>([1, n, this.pagina - 1, this.pagina, this.pagina + 1]);
    const ordenadas = [...visibles].filter((p) => p >= 1 && p <= n).sort((a, b) => a - b);
    const resultado: (number | '…')[] = [];
    ordenadas.forEach((p, i) => {
      if (i > 0 && p - ordenadas[i - 1] > 1) resultado.push('…');
      resultado.push(p);
    });
    return resultado;
  }

  ir(pagina: number | '…'): void {
    if (pagina === '…' || pagina === this.pagina || pagina < 1 || pagina > this.totalPaginas) return;
    this.cambioPagina.emit(pagina);
  }
}
