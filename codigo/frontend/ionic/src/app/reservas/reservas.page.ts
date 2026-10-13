import { Component, OnInit } from '@angular/core';

import { Auth, Usuario } from '../core/auth';
import { Coordenada, Ubicacion } from '../core/ubicacion';
import { Contrataciones, ContratacionResumen } from '../contrataciones/contrataciones';

interface FiltroEstado {
  valor: string;
  etiqueta: string;
}

const ESTADOS_FILTRO: FiltroEstado[] = [
  { valor: 'TODAS', etiqueta: 'Todas' },
  { valor: 'SOLICITADA', etiqueta: 'Solicitadas' },
  { valor: 'CONFIRMADA', etiqueta: 'Confirmadas' },
  { valor: 'EN_CURSO', etiqueta: 'En curso' },
  { valor: 'COMPLETADA', etiqueta: 'Completadas' },
  { valor: 'CANCELADA', etiqueta: 'Canceladas' },
];

/**
 * Listado de contrataciones propias (como cliente o como proveedor) —
 * equivalente Ionic de `reservas_view`/reservas.html. Fase 4 del plan de
 * migración, con paridad visual agregada después (grid con foto + filtros)
 * al comparar contra el sitio Django: `reservas_view` no filtra nada del
 * lado del servidor (trae todas las contrataciones del usuario tal cual),
 * el filtrado de reservas.html es enteramente client-side (JS sobre el DOM
 * ya renderizado) — acá se replica el mismo criterio pero sobre el array
 * ya traído por la API, sin pedirle filtros al backend.
 *
 * Simplificación real respecto a Django: reservas.html tiene un atajo
 * "confirmar"/"completar" con form inline (contraseña + monto) directo
 * en cada tarjeta. Acá esas dos acciones no se duplican — se resuelven
 * entrando al detalle (`/contratacion/:id`), que ya tiene el flujo
 * completo de reautenticación. Todas las tarjetas no completadas muestran
 * "Ver detalle"; solo COMPLETADA (rol cliente) distingue "Calificar" de
 * "Ya calificaste este trabajo", igual que Django.
 */
@Component({
  selector: 'app-reservas',
  templateUrl: './reservas.page.html',
  styleUrls: ['./reservas.page.scss'],
  standalone: false,
})
export class ReservasPage implements OnInit {
  readonly estadosFiltro = ESTADOS_FILTRO;

  usuario: Usuario | null = null;
  contrataciones: ContratacionResumen[] = [];
  filtradas: ContratacionResumen[] = [];
  cargando = true;
  /** Cómo se muestran las contrataciones: tarjetas con foto o lista compacta (se recuerda la elección). */
  vista: 'cuadros' | 'lista' = ReservasPage.vistaGuardada();

  /** Contrataciones por página; con más, se navega entre páginas (1, 2, 3…). */
  readonly porPagina = 20;
  pagina = 1;

  busqueda = '';
  desde = '';
  hasta = '';
  filtroEstado = 'TODAS';

  constructor(
    private readonly auth: Auth,
    private readonly contratacionesApi: Contrataciones,
    private readonly ubicacion: Ubicacion,
  ) {}

  /** Posición de la persona, solo si la compartió con "Mostrar distancias". */
  miPosicion: Coordenada | null = null;
  buscandoUbicacion = false;

  async mostrarDistancias(): Promise<void> {
    this.buscandoUbicacion = true;
    this.miPosicion = await this.ubicacion.posicionActual();
    this.buscandoUbicacion = false;
  }

  quitarDistancias(): void {
    this.miPosicion = null;
  }

  /** Kilómetros en línea recta (Haversine) hasta la comuna del proveedor; null si no hay posición o la comuna no tiene coordenada. */
  distanciaKm(c: ContratacionResumen): number | null {
    if (!this.miPosicion || c.proveedor_latitud == null || c.proveedor_longitud == null) return null;
    const rad = (grados: number) => (grados * Math.PI) / 180;
    const dLat = rad(c.proveedor_latitud - this.miPosicion.lat);
    const dLng = rad(c.proveedor_longitud - this.miPosicion.lng);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(rad(this.miPosicion.lat)) * Math.cos(rad(c.proveedor_latitud)) * Math.sin(dLng / 2) ** 2;
    return Math.round(6371 * 2 * Math.asin(Math.sqrt(a)) * 10) / 10;
  }

  private static vistaGuardada(): 'cuadros' | 'lista' {
    try {
      return localStorage.getItem('ks-vista-reservas') === 'lista' ? 'lista' : 'cuadros';
    } catch {
      return 'cuadros';
    }
  }

  cambiarVista(vista: 'cuadros' | 'lista'): void {
    this.vista = vista;
    try {
      localStorage.setItem('ks-vista-reservas', vista);
    } catch {
      /* sin localStorage: el cambio se aplica igual, solo no se recuerda */
    }
  }

  ngOnInit(): void {
    this.auth.me().subscribe({
      next: (usuario) => (this.usuario = usuario),
    });

    this.contratacionesApi.listar().subscribe({
      next: (contrataciones) => {
        this.contrataciones = contrataciones;
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  colorEstado(estado: string): string {
    return this.contratacionesApi.colorEstado(estado);
  }

  etiquetaEstado(estado: string): string {
    return this.contratacionesApi.etiquetaEstado(estado);
  }

  /** true si el usuario logueado es el cliente de esta contratación (no el proveedor). */
  esCliente(c: ContratacionResumen): boolean {
    return c.cliente === this.usuario?.id_usuario;
  }

  contraparteNombre(c: ContratacionResumen): string {
    return this.esCliente(c) ? c.proveedor_nombre : c.cliente_nombre;
  }

  /** Cuenta de contrataciones para el chip de estado — 'TODAS' cuenta todo, el resto filtra por `estado`. */
  contador(valorFiltro: string): number {
    if (valorFiltro === 'TODAS') {
      return this.contrataciones.length;
    }
    return this.contrataciones.filter((c) => c.estado === valorFiltro).length;
  }

  elegirFiltro(valor: string): void {
    this.filtroEstado = valor;
    this.aplicarFiltros();
  }

  limpiarFiltros(): void {
    this.busqueda = '';
    this.desde = '';
    this.hasta = '';
    this.filtroEstado = 'TODAS';
    this.aplicarFiltros();
  }

  /** Mismo criterio que aplicarFiltros() en reservas.html: estado + texto (título o contraparte) + rango de fecha, todo en memoria sobre lo ya traído. */
  aplicarFiltros(): void {
    const texto = this.busqueda.trim().toLowerCase();

    this.pagina = 1;
    this.filtradas = this.contrataciones.filter((c) => {
      const pasaEstado = this.filtroEstado === 'TODAS' || c.estado === this.filtroEstado;
      const pasaTexto = !texto
        || c.publicacion_titulo.toLowerCase().includes(texto)
        || this.contraparteNombre(c).toLowerCase().includes(texto);
      const fecha = c.fecha_creacion.slice(0, 10);
      const pasaDesde = !this.desde || fecha >= this.desde;
      const pasaHasta = !this.hasta || fecha <= this.hasta;
      return pasaEstado && pasaTexto && pasaDesde && pasaHasta;
    });
  }

  /** Las contrataciones de la página actual. */
  get visibles(): ContratacionResumen[] {
    const inicio = (this.pagina - 1) * this.porPagina;
    return this.filtradas.slice(inicio, inicio + this.porPagina);
  }

  irAPagina(pagina: number): void {
    this.pagina = pagina;
    document.getElementById('listado-reservas')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
