/**
 * Opciones de las preguntas voluntarias de impacto (docs/adr/0008). Los valores son los del backend
 * (`Usuario.SITUACIONES_LABORALES`, `Usuario.GENEROS`, `Publicaciones.TIPOS_SERVICIO`, `Valoracion.RESPUESTAS_REEMPLAZO`).
 */
export const FINALIDAD_IMPACTO =
  'Usamos estas respuestas solo para medir el impacto de KeyServ en el empleo. Son opcionales, no cambian tu acceso ni lo que ven otras personas, ' +
  'solo se reportan agregadas (nunca de forma individual) y puedes cambiarlas o borrarlas cuando quieras desde Preferencias.';

export const SITUACIONES_LABORALES = [
  { valor: 'SIN_TRABAJO', etiqueta: 'Sin trabajo' },
  { valor: 'INFORMAL', etiqueta: 'Trabajo informal (sin contrato ni boleta)' },
  { valor: 'FORMAL', etiqueta: 'Trabajo formal (con contrato o boletas)' },
  { valor: 'ESTUDIANTE', etiqueta: 'Estudiante' },
  { valor: 'NO_DICE', etiqueta: 'Prefiero no decir' },
];

export const GENEROS = [
  { valor: 'MUJER', etiqueta: 'Mujer' },
  { valor: 'HOMBRE', etiqueta: 'Hombre' },
  { valor: 'OTRO', etiqueta: 'Otro' },
  { valor: 'NO_DICE', etiqueta: 'Prefiero no decir' },
];

export const TIPOS_SERVICIO = [
  { valor: 'REPARACION', etiqueta: 'Reparación' },
  { valor: 'MANTENCION', etiqueta: 'Mantención' },
  { valor: 'INSTALACION_NUEVA', etiqueta: 'Instalación nueva' },
  { valor: 'OTRO', etiqueta: 'Otro' },
];

export const RESPUESTAS_REEMPLAZO = [
  { valor: 'SI', etiqueta: 'Sí' },
  { valor: 'NO', etiqueta: 'No' },
  { valor: 'NO_APLICA', etiqueta: 'No aplica' },
];

/** Los servicios de reparación y mantención son los que se preguntan por "evitó comprar uno nuevo". */
export function esReparacionOMantencion(tipo: string | null | undefined): boolean {
  return tipo === 'REPARACION' || tipo === 'MANTENCION';
}
