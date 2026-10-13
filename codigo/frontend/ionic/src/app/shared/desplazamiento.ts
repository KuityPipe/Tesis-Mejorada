/**
 * Desplazamiento de la página visible tras navegar por los links del header/footer: hacia una sección (`#acerca`,
 * `#contacto`) o, sin fragmento, hasta arriba de todo. Se hace aparte de la navegación porque el router ignora un
 * link a la URL en la que ya estás, y en ese caso el usuario igual espera que la página se mueva.
 */
export function desplazarTrasNavegar(fragmento?: string): void {
  setTimeout(async () => {
    if (fragmento) {
      document.getElementById(fragmento)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    const paginas = document.querySelectorAll('.ion-page:not(.ion-page-hidden) ion-content');
    const contenido = paginas[paginas.length - 1] as (HTMLElement & { scrollToTop?: (ms: number) => Promise<void> }) | undefined;
    await contenido?.scrollToTop?.(400);
  }, 450);
}
