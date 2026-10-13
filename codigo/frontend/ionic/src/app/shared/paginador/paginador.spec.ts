import { PaginadorComponent } from './paginador';

describe('PaginadorComponent', () => {
  function crear(total: number, pagina: number): PaginadorComponent {
    const c = new PaginadorComponent();
    c.total = total;
    c.pagina = pagina;
    return c;
  }

  it('calcula el total de páginas con 20 por página', () => {
    expect(crear(20, 1).totalPaginas).toBe(1);
    expect(crear(21, 1).totalPaginas).toBe(2);
    expect(crear(0, 1).totalPaginas).toBe(1);
  });

  it('muestra todas las páginas cuando son pocas', () => {
    expect(crear(60, 1).paginas).toEqual([1, 2, 3]);
  });

  it('usa "…" para los saltos en listas largas', () => {
    expect(crear(400, 10).paginas).toEqual([1, '…', 9, 10, 11, '…', 20]);
  });

  it('informa el rango mostrado', () => {
    expect(crear(63, 2).rango).toBe('21–40 de 63');
  });

  it('emite solo páginas válidas y distintas de la actual', () => {
    const c = crear(60, 2);
    const emitidas: number[] = [];
    c.cambioPagina.subscribe((p) => emitidas.push(p));
    c.ir(2);
    c.ir('…');
    c.ir(0);
    c.ir(4);
    c.ir(3);
    expect(emitidas).toEqual([3]);
  });
});
