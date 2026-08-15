import { Component, OnInit } from '@angular/core';
import { NativeBiometric, BiometryType } from '@capgo/capacitor-native-biometric';

import { Auth } from '../core/auth';

/**
 * Verificación biométrica nativa (Face ID / huella del teléfono) —
 * equivalente Ionic de `/rostro/`/`/huella/` (RF001), pero usando el
 * sensor del propio dispositivo en vez de procesar la imagen en el
 * servidor. Fase 5 del plan de migración. En `ng serve` normal (sin
 * build nativo) el plugin cae en su implementación dummy para web,
 * donde `isAvailable()` devuelve `isAvailable: false` — es esperado,
 * no un error: esta pantalla solo funciona de verdad en un build
 * Android/iOS real.
 */
@Component({
  selector: 'app-biometria',
  templateUrl: './biometria.page.html',
  styleUrls: ['./biometria.page.scss'],
  standalone: false,
})
export class BiometriaPage implements OnInit {
  cargando = true;
  disponible = false;
  tipoBiometria = '';
  yaVerificado = false;
  verificando = false;
  error: string | null = null;
  exito = false;

  constructor(private readonly auth: Auth) {}

  ngOnInit(): void {
    this.auth.me().subscribe((usuario) => {
      this.yaVerificado = usuario.verificado_biometricamente;
    });

    NativeBiometric.isAvailable()
      .then((resultado) => {
        this.disponible = resultado.isAvailable;
        this.tipoBiometria = this.nombreTipo(resultado.biometryType);
        this.cargando = false;
      })
      .catch(() => {
        this.disponible = false;
        this.cargando = false;
      });
  }

  private nombreTipo(tipo: BiometryType): string {
    switch (tipo) {
      case BiometryType.FACE_ID:
        return 'Face ID';
      case BiometryType.TOUCH_ID:
        return 'Touch ID';
      case BiometryType.FINGERPRINT:
        return 'huella dactilar';
      case BiometryType.FACE_AUTHENTICATION:
        return 'reconocimiento facial';
      case BiometryType.IRIS_AUTHENTICATION:
        return 'iris';
      case BiometryType.MULTIPLE:
        return 'biometría del dispositivo';
      default:
        return 'biometría del dispositivo';
    }
  }

  async verificar(): Promise<void> {
    if (this.verificando) {
      return;
    }
    this.verificando = true;
    this.error = null;

    try {
      // Rechaza (throw) si el usuario cancela o falla la verificación —
      // no devuelve un booleano, ver definitions.d.ts del plugin.
      await NativeBiometric.verifyIdentity({
        title: 'Verificación biométrica',
        reason: 'Confirma tu identidad para verificar tu cuenta de KeyServ.',
      });
    } catch {
      this.verificando = false;
      this.error = 'No se pudo verificar tu identidad.';
      return;
    }

    // Recién acá se avisa al backend — el enclave seguro del dispositivo
    // ya confirmó la identidad, esto solo actualiza el flag en la cuenta.
    this.auth.verificarBiometriaNativa().subscribe({
      next: () => {
        this.verificando = false;
        this.exito = true;
        this.yaVerificado = true;
      },
      error: () => {
        this.verificando = false;
        this.error = 'Se verificó tu identidad, pero no pudimos guardarlo en tu cuenta. Probá de nuevo.';
      },
    });
  }
}
