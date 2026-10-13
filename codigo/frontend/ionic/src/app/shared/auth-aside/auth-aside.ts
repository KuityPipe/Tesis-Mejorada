import { Component } from '@angular/core';

/**
 * Panel de marca que acompaña a los formularios de acceso (login, registro, recuperar contraseña) en pantallas
 * anchas: da contexto y confianza en vez de dejar un formulario angosto con espacio vacío a los lados.
 */
@Component({
  selector: 'app-auth-aside',
  templateUrl: './auth-aside.html',
  styleUrls: ['./auth-aside.scss'],
  standalone: false,
})
export class AuthAsideComponent {}
