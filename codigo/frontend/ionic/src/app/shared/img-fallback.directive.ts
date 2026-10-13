import { Directive, HostListener } from '@angular/core';

/**
 * Si una imagen no carga (archivo faltante, URL vieja), en vez de mostrar el ícono roto del navegador con su texto
 * alternativo encima del diseño, la oculta: el contenedor conserva su fondo de marca como marcador de posición.
 * Se aplica sola a todo `<img>` de las páginas que importan `SharedModule`.
 */
@Directive({
  selector: 'img',
  standalone: false,
})
export class ImgFallbackDirective {
  @HostListener('error', ['$event'])
  alFallar(evento: Event): void {
    (evento.target as HTMLImageElement).classList.add('ks-img-rota');
  }
}
