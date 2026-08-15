import { Component, OnInit } from '@angular/core';

import { Auth, Usuario } from '../core/auth';
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

  busqueda = '';
  desde = '';
  hasta = '';
  filtroEstado = 'TODAS';

  constructor(
    private readonly auth: Auth,
    private readonly contratacionesApi: Contrataciones,
  ) {}

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
}
