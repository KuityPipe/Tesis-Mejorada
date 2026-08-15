import { Component, OnInit } from '@angular/core';

import { Conversaciones, ConversacionResumen } from './conversaciones';
import { Contrataciones } from '../contrataciones/contrataciones';

/**
 * Bandeja de entrada — equivalente Ionic de `/chat/` (`chat_view`,
 * `chat.html`). Un chat por trabajo: cada fila navega directo a
 * `/contratacion/:id`, donde el chat ya vive embebido (`contratacion/
 * detalle/detalle.page`) — no hay una pantalla de conversación propia acá,
 * mismo criterio que `conversacion_detalle_view` (Django), que redirige a
 * `contratacion_detalle` apenas la conversación tiene un trabajo asociado
 * (el caso normal desde la Fase 5 "chat por trabajo").
 */
@Component({
  selector: 'app-mensajes',
  templateUrl: './mensajes.page.html',
  styleUrls: ['./mensajes.page.scss'],
  standalone: false,
})
export class MensajesPage implements OnInit {
  conversaciones: ConversacionResumen[] = [];
  cargando = true;

  constructor(
    private readonly api: Conversaciones,
    private readonly contratacionesApi: Contrataciones,
  ) {}

  ngOnInit(): void {
    this.api.listar().subscribe({
      next: (conversaciones) => {
        this.conversaciones = conversaciones;
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
}
