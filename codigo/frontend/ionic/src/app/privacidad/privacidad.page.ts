import { AfterViewInit, Component, ElementRef, OnDestroy } from '@angular/core';

import { desplazarTrasNavegar } from '../shared/desplazamiento';

interface Dato {
  icono: string;
  titulo: string;
  texto: string;
}

interface Plazo {
  valor: string;
  unidad: string;
  titulo: string;
  nota: string;
}

interface Tercero {
  icono: string;
  nombre: string;
  funcion: string;
  detalle: string;
}

interface Derecho {
  icono: string;
  titulo: string;
  texto: string;
}

/**
 * Política de privacidad — versión Ionic de la página que antes solo existía como plantilla de Django
 * (`/privacidad/` en el host de la API, con el diseño y la navegación antiguos). El texto conserva lo mismo que
 * esa política; acá solo cambia la presentación (índice con seguimiento de lectura, tarjetas, plazos visuales).
 */
@Component({
  selector: 'app-privacidad',
  templateUrl: './privacidad.page.html',
  styleUrls: ['./privacidad.page.scss'],
  standalone: false,
})
export class PrivacidadPage implements AfterViewInit, OnDestroy {
  readonly actualizacion = 'agosto de 2026';

  readonly esencial = [
    { icono: 'scan-outline', valor: '0', etiqueta: 'fotos de tu rostro guardadas', detalle: 'Solo un código cifrado, y solo si eliges el reconocimiento facial.' },
    { icono: 'hourglass-outline', valor: '180', etiqueta: 'días dura tu verificación', detalle: 'Pasado ese plazo se repite; así nadie queda verificado para siempre.' },
    { icono: 'time-outline', valor: '30', etiqueta: 'días para responder tus solicitudes', detalle: 'Corregir o consultar tus datos tiene un plazo máximo.' },
    { icono: 'hand-left-outline', valor: '0', etiqueta: 'datos vendidos a terceros', detalle: 'Solo compartimos lo mínimo para que la plataforma funcione.' },
  ];

  readonly indice = [
    { id: 'datos', icono: 'person-outline', texto: 'Qué datos recolectamos' },
    { id: 'terceros', icono: 'git-network-outline', texto: 'Con quién compartimos' },
    { id: 'plazos', icono: 'time-outline', texto: 'Cuánto los guardamos' },
    { id: 'proteccion', icono: 'shield-checkmark-outline', texto: 'Cómo los protegemos' },
    { id: 'derechos', icono: 'checkmark-done-outline', texto: 'Tus derechos' },
    { id: 'contacto', icono: 'mail-outline', texto: 'Menores y contacto' },
  ];

  readonly datos: Dato[] = [
    {
      icono: 'id-card-outline',
      titulo: 'Datos de cuenta',
      texto: 'Nombre, apellido, RUT, email, edad, teléfono, dirección, comuna y región. La contraseña nunca se guarda en texto plano: se almacena con un hash PBKDF2 irreversible.',
    },
    {
      icono: 'finger-print-outline',
      titulo: 'Datos biométricos (identidad)',
      texto: 'Si verificas tu identidad con reconocimiento facial, guardamos un vector numérico derivado de tu rostro (128 números, no una foto): las imágenes de la captura se procesan y se descartan al momento, nunca se almacenan. Si usas la biometría nativa del teléfono (Face ID o huella en la app Android), esa verificación ocurre dentro del hardware seguro de tu dispositivo: nuestro servidor nunca ve ese dato, solo recibe la confirmación de que el teléfono la aprobó.',
    },
    {
      icono: 'videocam-outline',
      titulo: 'Verificación de identidad con video',
      texto: 'Es opcional: si eliges verificarte sin la biometría de tu teléfono, subes una foto de tu cédula y un video corto con tu cara y tu cédula juntas, diciendo tu nombre y un número que te mostramos. Es un dato sensible: una persona del equipo lo mira para comparar tu cara con la foto de tu cédula, queda en almacenamiento privado y se elimina apenas se aprueba o rechaza la solicitud (o a los 30 días si nadie la resuelve, o al eliminar tu cuenta). Solo se hace si aceptas expresamente.',
    },
    {
      icono: 'images-outline',
      titulo: 'Documentos e imágenes',
      texto: 'Foto de perfil, fotos de las publicaciones, certificados o documentos que un proveedor suba para respaldar su perfil, y fotos adjuntas a calificaciones o mensajes de chat. Los documentos de identidad se guardan en almacenamiento privado, nunca en una URL pública: solo tú y, si corresponde, un moderador autorizado pueden verlos.',
    },
    {
      icono: 'location-outline',
      titulo: 'Ubicación',
      texto: 'Si activas la búsqueda por cercanía en el catálogo, tu posición se usa para calcular distancias en esa consulta puntual; no queda guardada asociada a tu cuenta.',
    },
    {
      icono: 'card-outline',
      titulo: 'Pagos',
      texto: 'KeyServ nunca ve ni almacena el número de tu tarjeta ni tus credenciales bancarias: eso lo procesan directamente Transbank (Webpay), Khipu, Flow o Mercado Pago, fuera de nuestros servidores. Solo guardamos el resultado (monto, método y estado: pagado, rechazado o anulado) para tu historial de pagos.',
    },
    {
      icono: 'chatbubbles-outline',
      titulo: 'Mensajes',
      texto: 'El chat de cada trabajo contratado se guarda mientras el trabajo esté activo. En trabajos cerrados, el historial se elimina automáticamente a los 90 días, a menos que lo hayas exportado como respaldo: en ese caso queda excluido del borrado automático.',
    },
    {
      icono: 'warning-outline',
      titulo: 'Seguridad de la cuenta',
      texto: 'Registramos la dirección IP y una ubicación aproximada (a nivel de ciudad, con una base de datos local, sin consultar servicios externos) cuando detectamos un intento de acceso sospechoso, por ejemplo alguien intentando ver una conversación o un documento que no le pertenece. Es exclusivamente para seguridad, no para perfilar tu ubicación habitual.',
    },
  ];

  readonly terceros: Tercero[] = [
    { icono: 'card-outline', nombre: 'Transbank, Khipu, Flow y Mercado Pago', funcion: 'Pagos', detalle: 'Procesan los pagos con tarjeta o transferencia, según el medio que elijas. Transbank y Khipu solo reciben el monto a cobrar; Flow y Mercado Pago reciben además tu correo, que exigen para registrar el pago.' },
    { icono: 'cloud-outline', nombre: 'Render, Neon y Netlify', funcion: 'Alojamiento', detalle: 'Alojan el backend, la base de datos y el frontend. Sus servidores están fuera de Chile: Estados Unidos y Brasil.' },
    { icono: 'logo-github', nombre: 'GitHub', funcion: 'Código y mantenimiento', detalle: 'Aloja el código y ejecuta las tareas automáticas de mantenimiento, como la retención de datos.' },
    { icono: 'earth-outline', nombre: 'DB-IP', funcion: 'Geolocalización local', detalle: 'La base de ubicación aproximada por IP se descarga una vez; no se consulta un servicio externo en cada acceso.' },
    { icono: 'sparkles-outline', nombre: 'NVIDIA', funcion: 'Asistente con IA', detalle: 'Antes de enviar tu mensaje ocultamos RUT, correos, teléfonos, números largos, direcciones y nombres que indiques de forma explícita (no podemos garantizar detectarlos todos), y el asistente no recibe datos de tu cuenta ni biométricos. Aun así, no escribas datos personales en ese chat. No guardamos el contenido de la conversación.' },
    { icono: 'map-outline', nombre: 'OpenStreetMap', funcion: 'Mapa de contacto', detalle: 'La sección de contacto de la portada muestra un mapa embebido con la oficina (ficticia en la demo); carga contenido de OpenStreetMap, sujeto a su política de privacidad.' },
    { icono: 'navigate-outline', nombre: 'Google Maps', funcion: 'Mapa de publicaciones', detalle: 'El detalle de una publicación puede mostrar un mapa con la ubicación aproximada del proveedor (a nivel de comuna, no la dirección exacta); carga contenido de Google, sujeto a su política.' },
  ];

  readonly plazos: Plazo[] = [
    { valor: '∞', unidad: 'hasta que decidas', titulo: 'Vector de tu rostro', nota: 'Se conserva hasta que retires tu consentimiento o elimines tu cuenta. Si te opones o lo revocas, se borra al instante.' },
    { valor: '180', unidad: 'días', titulo: 'Vigencia de la verificación', nota: 'Pasado ese plazo hay que repetirla.' },
    { valor: '365', unidad: 'días', titulo: 'Registro de verificaciones', nota: 'Qué método, cuándo y con qué resultado. Nunca contiene datos biométricos.' },
    { valor: '90', unidad: 'días', titulo: 'Chats de trabajos cerrados', nota: 'Se eliminan, salvo que los hayas exportado como respaldo.' },
    { valor: '365', unidad: 'días', titulo: 'Accesos sospechosos', nota: 'Dirección IP y ubicación aproximada, solo para seguridad.' },
    { valor: '30', unidad: 'días', titulo: 'Sesiones vencidas', nota: 'Pasado ese plazo se eliminan.' },
    { valor: '§', unidad: 'por ley', titulo: 'Contratos y pagos', nota: 'Los conservamos aunque elimines tu cuenta, por obligaciones tributarias y contables; se desvinculan de tus datos personales.' },
  ];

  readonly proteccion: Dato[] = [
    { icono: 'key-outline', titulo: 'Contraseñas y vector facial', texto: 'Las contraseñas usan hash PBKDF2, nunca texto plano. El vector de tu rostro se guarda cifrado.' },
    { icono: 'lock-closed-outline', titulo: 'Almacenamiento privado', texto: 'Documentos de identidad y certificados quedan en almacenamiento privado, nunca en una URL pública adivinable.' },
    { icono: 'document-attach-outline', titulo: 'Archivos validados', texto: 'Todo archivo subido pasa por una validación real de contenido antes de guardarse, no solo de extensión.' },
    { icono: 'speedometer-outline', titulo: 'Límite de intentos', texto: 'Hay límite de intentos en el login y en las acciones que piden confirmar tu contraseña, para frenar ataques de fuerza bruta.' },
    { icono: 'globe-outline', titulo: 'HTTPS', texto: 'Las conexiones van cifradas con HTTPS, obligatorio en producción.' },
  ];

  readonly derechos: Derecho[] = [
    { icono: 'download-outline', titulo: 'Descargar', texto: 'Una copia de todos tus datos.' },
    { icono: 'create-outline', titulo: 'Corregir', texto: 'Tú mismo, o pídenos que lo hagamos: respondemos en máximo 30 días.' },
    { icono: 'hand-right-outline', titulo: 'Oponerte', texto: 'Al tratamiento biométrico. Se aplica al instante.' },
    { icono: 'pause-circle-outline', titulo: 'Bloquear', texto: 'El tratamiento de tu cuenta, de forma reversible.' },
    { icono: 'trash-outline', titulo: 'Eliminar', texto: 'Tu cuenta y tus datos personales.' },
  ];

  seccionActiva = 'datos';
  private observador?: IntersectionObserver;

  constructor(private readonly elemento: ElementRef<HTMLElement>) {}

  ngAfterViewInit(): void {
    if (typeof IntersectionObserver === 'undefined') return;
    // La sección "activa" del índice es la que cruza la franja alta de la pantalla mientras se lee.
    this.observador = new IntersectionObserver(
      (entradas) => {
        const visible = entradas.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (visible) this.seccionActiva = visible.target.id;
      },
      { rootMargin: '-90px 0px -65% 0px', threshold: 0 },
    );
    this.indice.forEach((item) => {
      const seccion = this.elemento.nativeElement.querySelector(`#${item.id}`);
      if (seccion) this.observador?.observe(seccion);
    });
  }

  ngOnDestroy(): void {
    this.observador?.disconnect();
  }

  irA(id: string): void {
    this.seccionActiva = id;
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /** Los links "Inicio" / "Contacto" de esta página llevan a la portada y bajan a la sección. */
  ir(fragmento?: string): void {
    desplazarTrasNavegar(fragmento);
  }
}
