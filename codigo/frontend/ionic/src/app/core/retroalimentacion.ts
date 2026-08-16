import { Injectable } from '@angular/core';
import { ToastController } from '@ionic/angular';

/**
 * Toast de retroalimentación (éxito) — hasta ahora las acciones que
 * terminan bien (guardar perfil, confirmar/completar una contratación,
 * calificar, cambiar contraseña, etc.) simplemente navegaban a otra
 * pantalla sin ningún aviso, a diferencia de Django (`messages.success`,
 * visible en cada template vía `base.html`). Este servicio es el
 * equivalente Ionic: un `ion-toast` corto, con ícono y la paleta de marca,
 * que no bloquea la navegación (a diferencia de un `AlertController`, que
 * exige un tap para cerrar) — mismo criterio que un toast de éxito en
 * cualquier app nativa.
 */
@Injectable({ providedIn: 'root' })
export class Retroalimentacion {
  constructor(private readonly toastCtrl: ToastController) {}

  async exito(mensaje: string): Promise<void> {
    const toast = await this.toastCtrl.create({
      message: mensaje,
      duration: 2600,
      position: 'top',
      icon: 'checkmark-circle',
      cssClass: 'ks-toast-exito',
      swipeGesture: 'vertical',
    });
    await toast.present();
  }
}
