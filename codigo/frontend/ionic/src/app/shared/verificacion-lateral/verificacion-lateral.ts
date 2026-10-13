import { Component, Input } from '@angular/core';

/**
 * Columna lateral de las tres pantallas de verificación de identidad (biometría del teléfono, rostro, vía sin
 * biometría): muestra las tres opciones con la actual resaltada y deja explícito qué se guarda, para que la
 * persona decida con información y para aprovechar el ancho de la pantalla con contenido útil.
 */
@Component({
  selector: 'app-verificacion-lateral',
  templateUrl: './verificacion-lateral.html',
  styleUrls: ['./verificacion-lateral.scss'],
  standalone: false,
})
export class VerificacionLateralComponent {
  @Input() actual: 'nativa' | 'rostro' | 'alternativa' = 'nativa';

  readonly opciones = [
    { id: 'nativa', ruta: '/biometria', icono: 'finger-print-outline', titulo: 'Biometría del teléfono', detalle: 'La más rápida y privada: tu huella o rostro nunca salen del teléfono.', recomendada: true },
    { id: 'rostro', ruta: '/rostro', icono: 'scan-outline', titulo: 'Reconocimiento facial', detalle: 'Con la cámara. Guardamos solo un código cifrado, nunca tus fotos.', recomendada: false },
    { id: 'alternativa', ruta: '/verificacion-alternativa', icono: 'document-text-outline', titulo: 'Sin biometría', detalle: 'Código por correo y revisión de tu documento por una persona. Más lenta.', recomendada: false },
  ] as const;
}
